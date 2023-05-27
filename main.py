import ast
import json
import praw
import requests
import time
import logging
import openai
import configparser
import math
import textwrap
from unittest.mock import MagicMock


class RealityCheckBot:

  def __init__(self):
    self.config = self.load_config()
    self.reddit = self.init_reddit()
    self.logger = self.init_logger()
    self.claimbuster = self.config_claimbuster()
    self.botname = self.config['BOT']['NAME']
    self.triggers = ast.literal_eval(self.config['BOT']['TRIGGERS'])
    self.gptModel = self.config['GPT']['MODEL']
    self.subRedditList = self.config['REDDIT']['SUBREDDIT_LIST']
    self.isDevMode = self.config.getboolean("BOT", "DEV_MODE")
    self.POST_TO_REDDIT_ENABLED = self.config.getboolean(
      'REDDIT', 'POST_ENABLED')
    self.checkers = {
      "Google Fact-Check API":
      "https://developers.google.com/fact-check/tools/api"
    }
    self.last_request_time = 0
    self.rate_limit_remaining = 60

    self.openai_retry_delay = self.config.getint(
      'OPENAI', 'RETRY_DELAY')  # delay starts at 1 second
    self.openai_max_retries = self.config.getint(
      'OPENAI', 'MAX_RETRIES')  # maximum number of retries
    self.openai_retry = 0
    openai.api_key = self.config['OPENAI']['API_KEY']

    self.mock_comment_1 = self.mock_comment(
      body="/furReel Trump knew he couldnt declassify those documents",
      is_root=False,
      submission={
        "title": "Mock Submission Title",
        "selftext": "This is a mock post for testing."
      },
      parent_body=textwrap.dedent(
        """what the attorneys describe as the \"ongoing injustice that is being perpetrated\" by special counsel Jack Smith and says that no president has been \"baselessly investigated\" in such an \"unlawful fashion.\"
      Unlawful investigation? Are Trump’s lawyers delusional? Trump was contacted about missing top secret documents. He lied and said he didn’t have them. Someone inside Mar-o-lago ratted Trump out and a court approved a search warrant. The feds found the documents in a closet. There’s also evidence 
      Trump has hidden other documents as well and still has them.

      Are they meeting face to face with Garland to tell him they have dirt on him?
      """))

    self.local_comments = [
      self.mock_comment_1,
    ]

  # "lasers in space caused the california wildfires in 2016",
  # "It's events like these drag queens reading to children events that groom and sexualize children",
  # "that election was so rigged, it's clear that Trump won",
  # "the democrats stole the election in 2020",
  # "Because the Moon and sun are visible in the daytime proves Earth is flat",
  # "US Veterans were kicked out of hotels in favor of immigrants in NYC"
  def mock_comment(self, body, is_root, submission, parent_body):
    comment = MagicMock()

    comment.body = body
    comment.is_root = is_root

    submission_obj = MagicMock()
    submission_obj.title = submission['title']
    submission_obj.selftext = submission['selftext']
    comment.submission = submission_obj

    parent_comment = MagicMock()
    parent_comment.body = parent_body
    comment.parent.return_value = parent_comment

    return comment

  def load_config(self):
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

  def init_reddit(self):
    # Initialize Reddit instance with your app credentials
    reddit = praw.Reddit(client_id=self.config['REDDIT']['CLIENT_ID'],
                         client_secret=self.config['REDDIT']['CLIENT_SECRET'],
                         user_agent=self.config['REDDIT']['USER_AGENT'],
                         username=self.config['REDDIT']['USERNAME'],
                         password=self.config['REDDIT']['PASSWORD'])
    return reddit

  def init_logger(self):
    logger = logging.getLogger("furReelLogger")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logfile_handler = logging.FileHandler(
      self.config["LOGGING"]["LOG_FILE_NAME"])
    logfile_handler.setLevel(logging.DEBUG)
    logfile_handler.setFormatter(formatter)
    logger.addHandler(logfile_handler)
    return logger

  def config_claimbuster(self):
    claimbuster = {
      'api_key': self.config['CLAIMBUSTER']['API_KEY'],
      'api_prefix': self.config['CLAIMBUSTER']['API_PREFIX']
    }
    return claimbuster

  def extract_claims(self, text, retry=0):
    try:
      response = openai.ChatCompletion.create(
        model=self.config["GPT"]["MODEL"],
        temperature=0.2,
        max_tokens=1000,
        messages=[{
          "role":
          "system",
          "name":
          "furReelBot",
          "content":
          "We are working towards the important goal of stopping the spread of disinformation on social media. We have a bot that helps in this process by examining comments or posts from social media and checking their veracity. To do this effectively, we use the ClaimBuster API, which needs clear, concise, and specific statements or 'claims' to be submitted for checking in order to work effectively. It's crucial to extract these claims in an unbiased manner."
        }, {
          "role":
          "user",
          "content":
          f"Given the following text: |||{text}|||, I want you to break down the text and extract as many distinct factual claims as you can. Ensure these claims are specific, succinct, and easily verifiable. If a claim is complex, break it down into its constituent claims and include these in the list as well. For example, if the text is 'John believes that the earth is flat', not only should 'John believes that the earth is flat' be included as a claim, but also 'the earth is flat'. The output should be a Python list of strings with necessary escaping, starting with the original text, followed by the extracted claims. For example, ['John believes that the earth is flat', 'the earth is flat','John believes something']. Do your best to order them from most to least relavent to the gist of the original text. Avoid super vague claims like 'he knew'"
        }])
      return response['choices'][0]['message']['content']
    except openai.error.RateLimitError:
      if retry < self.openai_max_retries:
        self.logger.error(
          f"Rate limit hit. Waiting for {self.openai_retry_delay} seconds. Retry[{retry}]"
        )
        time.sleep(self.openai_retry_delay)
        self.openai_retry_delay *= 2  # double the delay
        return self.extract_claims(text, retry + 1)  # Added return here
      else:
        self.logger.error("Max retries hit. Please try again later.")
        return []

  def score_claim(self, text):
    self.logger.debug("Scoring claim...")
    headers = {"x-api-key": self.claimbuster['api_key']}
    try:
      response = requests.get(
        f"{self.claimbuster['api_prefix']}/score/text/{text}", headers=headers)
      try:
        json_obj = json.loads(response.text)
      except json.JSONDecodeError:
        self.logger.error(f"Failed to parse JSON response: {response.text}")
        return 0
      formatted_json_string = json.dumps(json_obj, indent=4)
      self.logger.debug(formatted_json_string)
      try:
        score = float(json_obj["results"][0]["score"])
        self.logger.info(f"Score:[{score}]")
        return score
      except ValueError:
        err = f"Cannot convert [{json_obj['results'][0]['score']}] to a float."
        self.logger.error(err)
      except (KeyError, IndexError):
        self.logger.error(f"Unexpected JSON format: {formatted_json_string}")
    except requests.exceptions.RequestException as e:
      self.logger.error(f"Failed to request claim score: {e}")
    return 0

  def format_reddit_comment(self, claim_responses):
    formatted_comments = []

    for claim_response in claim_responses:
      claim = claim_response.get("claim")
      origin = claim_response.get("origin")
      justifications = claim_response.get("justification")

      # only process this claim if there are justifications
      if justifications:
        formatted_comment = f"**Claim:** ***{claim}***  \n"
        suffix = ""
        if ("Claim Matcher" in origin):
          suffix = " similar claims"
        elif ("Knowledge" in origin):
          suffix = " related questions"
        formatted_comment += f"`{origin} found the following{suffix}:`  \n"

        for justification in justifications:
          truth_rating = justification.get("truth_rating")
          search = justification.get("search")
          url = justification.get("url")
          similar_claim = justification.get("claim")
          question = justification.get("question")
          justification_text = justification.get("justification")
          source = justification.get("source")

          if similar_claim:
            formatted_comment += f"* Claim: ***{similar_claim}***  \n"
          if question:
            if question == "What lied?": continue
            formatted_comment += f"* **Question:** {question}  \n"
          if truth_rating and truth_rating != "Indeterminable":
            formatted_comment += f"   * **Truth rating:** {truth_rating}  \n"
          if search:
            if self.checkers[search] != None:
              search = f"[{search}]({self.checkers[search]})"
            formatted_comment += f"   * **Checker:** {search}  \n"
          if justification_text:
            output = justification_text.replace("\n", "  \n")
            formatted_comment += f"   * **Answer Found:**  \n {output}  \n"
          if source:
            formatted_comment += f"   * **Fact Checker:** {source}  \n"
          if url:
            formatted_comment += f"   * **URL:** {url}  \n"

          formatted_comment += "\n"

        # add this claim's formatted comment to the list
        formatted_comments.append(formatted_comment)

    return "  \n".join(formatted_comments)

  def generate_footer(self):
    return (
      "  \n  \n***  \n  \n###### Beep boop! I'm a bot! RealityCheck, here to help combat disinformation on social media by bringing more context to the conversation auto-magically via AI tools and some elbow grease!  \n"
      "###### I do my best to extract what appear to be fact-checkable 'claims' from submitted comments and posts using OpenAI's GPT-4 for sentiment analysis. These claims are then sent to the ClaimBuster API for analysis, and finally, processed and summarized by yours truly.  \n"
      "###### Note: Please read and understand the 'claims' carefully, as they may not match the original comments intent. They are meant as a tool to expand the context and sourcing for the current conversation and not necessarily support one side of any argument over the other.  \n"
      "###### The provided truth ratings and justifications are based on public data and algorithms, and therefore may not be completely accurate or exhaustive.  \n"
      "###### Remember to always cross-verify information and approach discussions with both a critical mind and a grain of salt.  \n"
      "###### Please visit the RealityCheck project home (http://www.yeahwhateverruss.com), OpenAi ChatGPT: https://openai.com/product/chatgpt,  the ClaimBuster web site : https://idir.uta.edu/claimbuster/ for more information or to help in the cause! Let's learn more together!"
    )

  def check_claim_against_knowledge_base(self, text):
    self.logger.debug("Check claim against Knowledge Bases")
    headers = {"x-api-key": self.claimbuster['api_key']}
    response = requests.get(
      f"{self.claimbuster['api_prefix']}/query/knowledge_bases/{text}",
      headers=headers)
    json_obj = json.loads(response.text)
    json_str_pretty = json.dumps(json_obj, indent=4)
    self.logger.debug(f"CB_KnowledgeBase API RESULT: {json_str_pretty}")
    return json_str_pretty

  def check_claim(self, text):
    self.logger.debug(
      "Check claim against ClaimBuster API (proxy to google, snopes etc)")
    headers = {"x-api-key": self.claimbuster['api_key']}
    response = requests.get(
      f"{self.claimbuster['api_prefix']}/query/fact_matcher/{text}",
      headers=headers)
    json_obj = json.loads(response.text)
    json_str_pretty = json.dumps(json_obj, indent=4)
    self.logger.debug(f"CB_FactMatcher API RESULT: {json_str_pretty}")
    return json_str_pretty

  # Wrapper to introduce exponential backoff
  def make_reddit_request(self, action, *args, **kwargs):
    max_retries = 5
    for i in range(max_retries):
      try:
        response = action(*args, **kwargs)
        return response
      except self.prawcore.exceptions.RequestException as e:
        if e.response.status_code == 429:
          print(f"Rate limit exceeded, sleeping for {math.pow(2, i)} seconds.")
          time.sleep(math.pow(2, i))
        else:
          raise e
    raise Exception("Max retries exceeded.")

  def process_comment(self, comment):
    # Check if we're exceeding the rate limit
    if time.time(
    ) - self.last_request_time < 60 and self.rate_limit_remaining <= 0:
      time.sleep(60)  # Wait until we can make another request

    user_claim = None  # look for user claim following the bot trigger
    for trigger in self.triggers:
      if comment.body.lower().startswith(trigger.lower()):
        try:
          if user_claim == None:
            user_claim = comment.body.lower().split(trigger.lower() + ' ',
                                                    1)[1]
        except IndexError:
          pass

    user_claim_list = []
    if user_claim != None:  # have GPT extract claims
      user_claim_list = ast.literal_eval(self.extract_claims(user_claim))
      self.logger.debug(f"USER CLAIM LIST: {user_claim_list}")

    if comment.is_root:  # If this is a top-level comment
      post = comment.submission
      text_to_check = post.title + " " + post.selftext
    else:  # If this is a reply
      parent_comment = comment.parent()
      text_to_check = parent_comment.body

    claims_list = []
    try:  # have GPT extract claims
      claims_list = ast.literal_eval(self.extract_claims(text_to_check))
      self.logger.debug(f"PARENT CLAIMS:{claims_list}")
      if isinstance(claims_list, list) and all(
          isinstance(item, str) for item in claims_list):
        if user_claim_list != None and len(user_claim_list) > 0:
          if isinstance(user_claim_list, list) and all(
              isinstance(item, str) for item in user_claim_list):
            claims_list = [claims_list.pop(0),
                           user_claim_list.pop(0)
                           ] + claims_list + user_claim_list
            self.logger.info(f"combined list:{claims_list}")

          else:
            raise ValueError(
              f"GPT Claims output for User Claim is not a list of strings: {user_claim_list}"
            )
      else:
        raise ValueError(
          f"GPT Claims output for original content is not a list of strings: {claims_list}"
        )
    except json.JSONDecodeError:
      raise ValueError(f"GPT Claims output is not valid JSON: {claims_list}")

    claim_responses = {}

    for claim in claims_list:
      claim_score = self.score_claim(claim)
      if claim_score > .2:
        claimbuster_response = self.check_claim(claim) or ""
        knowledge_base_response = self.check_claim_against_knowledge_base(
          claim) or ""
        debug_info_text = (f"Reddit Comment ID: {comment.id}  \n"
                           f"Reddit Thing ID: {comment.fullname}  \n")
        claim_response_txt = (
          f"{self.format_reddit_comment([json.loads(claimbuster_response), json.loads(knowledge_base_response)])}"
        )
        claim_responses[claim] = {
          "score": claim_score,
          "response": claim_response_txt
        }

    response_text = "Beep Boop! I've been asked to fact check that comment:  \n>" + claims_list.pop(
      0)
    response_text += "  \n  \nI've compiled a list of claims made in your comment/post, as well as any relevant claims that might be helpful in bringing context to this conversation:  \n"
    for claim in claims_list:
      response_text += f"* ***{claim}***  \n"
    response_text += "  \nLet's see what we can find out! "
    if claim_responses.items():
      response_text += "Here's some information I found from fact-checkers around the interwebs:  \n  \n"
      for claim, claim_data in claim_responses.items():
        if len(response_text) < 9000:
          response_text += f"{claim_data['response']}"
        else:
          response_text += "Schwew! That seems like enough... stopping here (also due to 10,000 char limit in reddit comments)"
          break
    else:
      response_text += "Welp! That's embarrassing, I found nothing that can either confirm nor deny any of the claims.  \nHINT: try passing along a claim to validate along with those we extracted from the original comment. Example: `/furReel did you just suggest the earth is flat?`"

    response_text += self.generate_footer()
    self.logger.debug(debug_info_text)
    self.logger.info(response_text)
    if self.POST_TO_REDDIT_ENABLED:
      self.logger.debug("POSTING TO REDDIT")
      self.make_reddit_request(comment.reply, response_text)
      self.last_request_time = time.time()
    else:
      self.logger.info("NOT POSTING THAT TO REDDIT - POSTING DISABLED")

  def main(self):
    # Switch between local data and Reddit based on configuration
    if self.isDevMode:
      self.process_local_data()
    else:
      self.process_reddit_data()

  def process_local_data(self):
    self.logger.info("Dev Mode: Pulling data from local set")
    for comment in self.local_comments:
      triggered = False
      for trigger in self.triggers:
        if comment.body.lower().startswith(trigger.lower()):
          self.logger.debug(f"TRIGGERED BY:{trigger}")
          triggered = True
          break
      if triggered:
        self.process_comment(comment)

  def process_reddit_data(self):
    # Monitor all comments in a subreddit
    self.logger.info(f"Listening for new comments from: {self.subRedditList}")
    for comment in self.reddit.subreddit(
        self.subRedditList).stream.comments(skip_existing=True):
      triggered = False
      for trigger in self.triggers:
        if comment.body.lower().startswith(trigger.lower()):
          self.logger.debug(f"TRIGGERED BY:{trigger}")
          triggered = True
          break
      if triggered: self.process_comment(comment)


if __name__ == "__main__":
  bot = RealityCheckBot()
  bot.main()
