# The RealityCheckBot - A Fact-Checking Reddit Bot

Project's aim is to bring a bit more context to comment threads of social media. Leveraging GPT's AI senitiment analysis capabiliites eases the difficult work of matching what someone is trying to say with the string that represents their words in a comment. Natural Languague processing advancements allow us to distill a comments sentiment down to a list of claims. We can expound on those claims by finding related claims (expanding context), then using known and trusted fact-checking tools available online we can try and validate those claims and report any and all source references that may add to a claims justification. Culminating in the posting of a reply to the invoking comment with the details of the claims used, justifications found and general bot info. 

## Screen Shot
<img width="744" alt="Sample Comment thread from private subreddit" src="https://github.com/dyodji/RealityCheck/assets/2623613/b68c78cc-be51-4c2a-ace6-9284c15de600">

## Invoking /RealityCheckBot

To invoke the bot, as a logged in user on Reddit, reply to a post or comment within a list of configured subReddits (see config.ini) with:
  1. `/RealityCheck` or any one of the configured triggers (e.g. /RealityCheckBot, /forReal, /furReel... see config.ini)
  2. `/RealityCheck additional claim here` if you care to attempt to summarize the claim yourself. To remain unbias, both the original and summary claims will be researched, with priorty/emphasis given to the original.

The bot will auto reply, to the invoking comment(question: should it be to the parent? what's common/best practice?), once it's done analyzing it's findings. 

## Getting Started with Local Development

Currently set up to run as a Repl on Repl.it, there's no reason it can't run locally:

1. Ensure you have a suitable version of Python installed (3.8 or newer is recommended).

2. Fork and clone this repository to your local machine.

3. Install the required packages using pip:

`pip install -r requirements.txt`

4. Obtain your Reddit API keys by creating a Reddit application. (see instructions [here](#obtain-client-id-and-secret-from-reddit))

5. Rename the `config.sample.ini` file to `config.ini` and fill in your API keys in the appropriate fields.

6. Run the bot using the command:

`python realityCheckBot.py`

## Obtain Client ID and Secret from Reddit

1. Log into Reddit with your user account.

2. Navigate to the [app preferences page](https://www.reddit.com/prefs/apps)

3. Scroll down to the "Developed Applications" section and click on the "Create App" or "Create Another App" button.

4. Fill out the application form:
"name": This is the name of your app.
"App type": Choose "script" for personal use or automation.
"description": You can leave this blank.
"about url": You can leave this blank.
"redirect uri": Enter "http://localhost:8000" (without quotes).
"permissions": Leave at default level.

5. Click the "Create app" button at the bottom when you are done.

After the application is created, Reddit will provide you with a client ID and a client secret. You will need these for authentication with [PRAW (the Python Reddit API Wrapper)](https://pypi.org/project/praw/).

## Contributing

Contributions are welcomed! If you've found a bug or have a suggestion for improvement, feel free to create an issue or submit a pull request. We follow the standard [GitHub Flow](https://guides.github.com/introduction/flow/) for contributions.

## License

This project is open-source, licensed under the MIT License. See the `LICENSE` file for more details.

## Final Words

We're committed to the ongoing development of RealityCheck and its mission for more truth in the social media landscape. Thank you for your interest and support! If you know how to run a goFundMe or patreon to pay for hosting and API access, reach out please :)
