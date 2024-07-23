import os

from dotenv import load_dotenv

load_dotenv()


def get_slack_token():
    return os.getenv('SLACK_API_TOKEN')


def get_slack_channel_id():
    return os.getenv('SLACK_CHANNEL_ID')


def get_slack_webhook_url():
    return os.getenv('SLACK_WEBHOOK_URL')


def get_headers():
    return {'User-Agent': os.getenv('USER_AGENT')}
