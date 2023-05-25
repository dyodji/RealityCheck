# The FurReelBot - A Fact-Checking Reddit Bot

Welcome to The FurReelBot project! This Python-based Reddit bot aims to bring a bit more factuality to the world of social media. It listens for mentions in Reddit comments and uses powerful AI tools like OpenAI's GPT and the ClaimBuster API to fact-check claims.

## Getting Started

To get started with FurRealBot, follow these steps:

1. Ensure you have a suitable version of Python installed (3.8 or newer is recommended).

2. Fork and clone this repository to your local machine.

3. Install the required packages using pip:

`pip install -r requirements.txt`

4. Obtain your Reddit API keys by creating a Reddit application. (see instructions [here](#obtain-client-id-and-secret-from-reddit))

5. Rename the `secrets.sample.ini` file to `secrets.ini` and fill in your API keys in the appropriate fields.

6. Run the bot using the command:

`python furreelbot.py`

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

We're committed to the ongoing development of FurRealBot and its quest for truth in the social media landscape. Thank you for your interest and support!
