import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='/app/.env')


def get_slack_webhook_url():
    return os.getenv('SLACK_WEBHOOK_URL')


def get_slack_webhook_merge_url():
    return os.getenv('SLACK_WEBHOOK_MERGE_URL')


def get_slack_webhook_yahoo_url():
    return os.getenv('SLACK_WEBHOOK_YAHOO_URL')


def get_groq_api_key():
    return os.getenv('GROQ_API_KEY')


def get_headers():
    return {'User-Agent': os.getenv('USER_AGENT')}


def get_groq_message():
    return os.getenv('GROQ_MESSAGE')
