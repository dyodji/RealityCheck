# TODO: make these into tests
# inputText = "lasers in space caused the california wildfires in 2016"
# inputText = "It's events like these drag queens reading to children events that groom and sexualize children"
# inputText= "that election was so rigged, it's clear that Trump won"
# inputText = "the democrats stole the election in 2020"
# inputText = "Because the Moon and sun are visible in the daytime proves Earth is flat"
# inputText = "US Veterans were kicked out of hotels in favor of immigrants in NYC"

import json
import praw
import requests
import time
import logging
import openai
import configparser
import time
import math

class RealityCheckBot:
    def __init__(self):
        self.config = self.load_config()
        self.reddit = self.init_reddit()
        self.logger = self.init_logger()
        self.claimbuster = self.config_claimbuster()
        self.botname = self.config['BOT']['NAME']
        self.gptModel = self.config['GPT']['MODEL']
        self.subRedditList = self.config['BOT']['SUBREDDIT_LIST']
        self.POST_TO_REDDIT_ENABLED = self.config['REDDIT']['POST_ENABLED']
        self.checkers = {
          "Google Fact-Check API":"https://developers.google.com/fact-check/tools/api"
        }
        self.last_request_time = 0
        self.rate_limit_remaining = 60

    def load_config(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        return config

    def init_reddit(self):
        # Initialize Reddit instance with your app credentials
        reddit = praw.Reddit(
            client_id=self.config['REDDIT']['CLIENT_ID'],
            client_secret=self.config['REDDIT']['CLIENT_SECRET'],
            user_agent=self.config['REDDIT']['USER_AGENT'],
            username=self.config['REDDIT']['USERNAME'],
            password=self.config['REDDIT']['PASSWORD']
        )
        return reddit

    def init_logger(self):
        # Set up logging - file and console
     self.logger = logging.getLogger("furReelLogger")
       self.logger.setLevel(logging.DEBUG)
      formatter = logging.Formatter('%(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
       self.logger.addHandler(console_handler)
        logfile_handler = logging.FileHandler(self.config["LOGGING"]["LOG_FILE_NAME"])
        logfile_handler.setLevel(logging.DEBUG)
        logfile_handler.setFormatter(formatter)
       self.logger.addHandler(logfile_handler)
        returnself.logger

    def config_claimbuster(self):
        claimbuster = {
            'api_key': self.config['CLAIMBUSTER']['API_KEY'],
            'api_prefix': self.config['CLAIMBUSTER']['API_PREFIX']
        }
        return claimbuster

    checkers = {
      "Google Fact-Check API":"https://developers.google.com/fact-check/tools/api"
    }
    
  # Initialize a rate limit tracker
  last_request_time = 0
  rate_limit_remaining = 60
   
  def extract_claims(text):
    response = openai.ChatCompletion.create(
      model=gptModel,
      temperature=0.2,
      max_tokens=1000,
      messages=[{
        "role":
        "system",
        "name":
        "furReelBot",
        "content":
        "We have a collective goal to stop the spread of disinformation on social media. We've built a bot where users can submit comments or posts from social media for veracity checking which we do on the backend using ClaimBuster API. This API requires clear and concise statements in order to produce useful or effective results. You should act in the persona of an unbiased fact checker when extracting claims from social media comments and posts"
      }, {
        "role":
        "user",
        "content":
        "Identify as many factual claims as you can in the following statement and return them as a list of strings in JSON format so that our script can then process them through the ClaimBuster API. Include a few similar claims to increase our chances of finding results against the api. Also include the original text as a member of the result list. If two claims are correlated, as in one implies proof of the other, return the combined claim as well: |||Since both the sun and the moon are visible in sky at the same time the earth must flat|||"
      }, {
        "role":
        "assistant",
        "content":
        '["Since both the sun and the moon are visible in sky at the same time the earth must flat","The earth is flat","Because both the Sun and Moon are visible during the day, the earth is flat","The sun and the moon in the sky at the same time prove that the earth is flat"]'
      }, {
        "role":
        "user",
        "content":
        f"Identify as many factual claims as you can in the following statement and return them as a list of strings in JSON format so that our script can then process them through the ClaimBuster API. Include a few similar claims to increase our chances of finding results against the api. Also include the original text as a member of the result list.  If two claims are correlated, as in one implies proof of the other, return the combined claim as well: |||{text}|||"
      }])
    return response['choices'][0]['message']['content']
  
  
  def score_claim(text):
   self.logger.debug(f"Scoring claim...")
    headers = {"x-api-key": claimbuster['api_key']}
    try:
      response = requests.get(f"{claimbuster['api_prefix']}/score/text/{text}",
                              headers=headers)
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
  
  def format_reddit_comment(claim_responses):
      formatted_comments = []
  
      for claim_response in claim_responses:
          claim = claim_response.get("claim")
          origin = claim_response.get("origin")
          justifications = claim_response.get("justification")
  
          # only process this claim if there are justifications
          if justifications:
              formatted_comment = f"**Claim:** ***{claim}***  \n"
              suffix=""
              if("Claim Matcher" in origin):
                suffix = " similar claims"
              elif("Knowledge" in origin):
                suffix = " related questions"
              formatted_comment += f"`{origin} found the following{suffix}:`  \n"
  
              for justification in justifications:
                  truth_rating = justification.get("truth_rating")
                  search = justification.get("search")
                  url = justification.get("url")
                  similar_claim = justification.get("claim")
                  speaker = justification.get("speaker")
                  host = justification.get("host")
                  question = justification.get("question")
                  justification_text = justification.get("justification")
                  source = justification.get("source")
  
                  if similar_claim:
                      formatted_comment += f"* Claim: ***{similar_claim}***  \n"
                  if question:
                      formatted_comment += f"* **Question:** {question}  \n"
                  if truth_rating and truth_rating != "Indeterminable":
                      formatted_comment += f"   * **Truth rating:** {truth_rating}  \n"
                  if search:
                      if checkers[search] != None:
                         search = f"[{search}]({checkers[search]})"
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
  
  
  def generate_footer():
      return (f"  \n  \n***  \n  \n###### Beep boop! I'm a bot! FurReelBot's the name, here to help to stop disinformation on social media!!  \n"
              f"###### I do my best to extract what appear to be fact-checkable 'claims' from regular comments and posts using OpenAI's GPT-4, which are then checked against the ClaimBuster API, and finally, processed and summarized by yours truly.  \n"
              f"###### Note: Please read the 'claims' carefully, as subtle languange changes may change their nuance and meaning and therefore not precisely represent the original statement's intent.  \n"
              f"###### Also Note: The provided truth ratings and justifications are based on public data and algorithms, and therefore may not be completely accurate or exhaustive.  \n"
              f"###### Always cross-verify information and approach discussions with a critical mind.  \n"
  f"###### Please visit the project GitHub Home (coming soon) or the ClaimBuster web site for more info: https://idir.uta.edu/claimbuster/"
              )
  
  def check_claim_against_knowledge_base(text):
   self.logger.debug(f"Check claim against Knowledge Bases")
    headers = {"x-api-key": claimbuster['api_key']}
    response = requests.get(
      f"{claimbuster['api_prefix']}/query/knowledge_bases/{text}",
      headers=headers)
    json_obj = json.loads(response.text)
    json_str_pretty = json.dumps(json_obj, indent=4)
   self.logger.debug(f"CB_KnowledgeBase API RESULT: {json_str_pretty}")
    return json_str_pretty
  
  def check_claim(text):
   self.logger.debug(f"Check claim against ClaimBuster API (proxy to google, snopes etc)")
    headers = {"x-api-key": claimbuster['api_key']}
    response = requests.get(
      f"{claimbuster['api_prefix']}/query/fact_matcher/{text}", headers=headers)
    json_obj = json.loads(response.text)
    json_str_pretty = json.dumps(json_obj, indent=4)
   self.logger.debug(f"CB_FactMatcher API RESULT: {json_str_pretty}")
    return json_str_pretty
  
  # Wrapper to introduce exponential backoff
  def make_reddit_request(action, *args, **kwargs):
      max_retries=5
      for i in range(max_retries):
          try:
              response = action(*args, **kwargs)
              return response
          except prawcore.exceptions.RequestException as e:
              if e.response.status_code == 429:
                  print(f"Rate limit exceeded, sleeping for {math.pow(2, i)} seconds.")
                  time.sleep(math.pow(2, i))
              else:
                  raise e
      raise Exception("Max retries exceeded.")
  
  def main():
    # Monitor all comments in a subreddit
   self.logger.info("Listening for summin' ta do...")
    for comment in reddit.subreddit(subRedditList).stream.comments(skip_existing=True):
        if botname in comment.body:
            if comment.is_root: # If this is a top-level comment
                post = comment.submission
                text_to_check = post.title + " " + post.selftext
            else: # If this is a reply
                parent_comment = comment.parent()
                text_to_check = parent_comment.body
    
            # Check if we're exceeding the rate limit
            if time.time() - last_request_time < 60 and rate_limit_remaining <= 0:
                time.sleep(60)  # Wait until we can make another request
    
            # have GPT extract claims from text
            try:
                claims_list = json.loads(extract_claims(text_to_check))
                if isinstance(claims_list, list) and all(
                    isinstance(item, str) for item in claims_list):
                       self.logger.info("CLAIMS FROM CHAT:"+"\n".join(claims_list))
                else:
                    raise ValueError("GPT Claims output is not a list of strings")
            except json.JSONDecodeError:
                raise ValueError("GPT Claims output is not valid JSON")
              
            claim_responses = {}
            
            for claim in claims_list:
                claim_score = score_claim(claim)
                if claim_score > .2:
                    claimbuster_response = check_claim(claim) or ""
                    knowledge_base_response = check_claim_against_knowledge_base(claim) or ""
                    debug_info_text = (
                        f"Reddit Comment ID: {comment.id}  \n"
                        f"Reddit Thing ID: {comment.fullname}  \n"                  
                    )
                    response_txt = (
                        f"{format_reddit_comment([json.loads(claimbuster_response), json.loads(knowledge_base_response)])}"      
                    )
                    claim_responses[claim] = {"score": claim_score, "response": response_txt}
            
            response_text = "Beep Boop! I've been asked to fact check that comment:  \n>" + claims_list.pop(0)
            response_text += "  \n  \nSeems as if you're trying to say something like:  \n" 
            for claim in claims_list:    
              response_text += f"* ***{claim}***  \n"
            response_text += "  \nLet's verify those claims! Here's some information I found from fact-checkers around them thar interwebs:  \n  \n"
            for claim, claim_data in claim_responses.items():
                response_text += f"{claim_data['response']}"
    
            response_text += generate_footer()
           self.logger.debug(debug_info_text)  
           self.logger.info(response_text)
            if POST_TO_REDDIT_ENABLED == True:
             self.logger.debug(f"POSTING TO REDDIT")
              make_reddit_request(comment.reply,response_text)
              last_request_time = time.time()
        else:
           self.logger.info(".")
  
if __name__ == "__main__":
    bot = FuReelBot()
    bot.main()  
  