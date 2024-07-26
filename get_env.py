import os
import sys
from dotenv import load_dotenv
from mode import Mode

load_dotenv()
mode = sys.argv[1]


def get_slack_token():
    return os.getenv('SLACK_API_TOKEN')


def get_slack_channel_id():
    return os.getenv('SLACK_CHANNEL_ID')


def get_slack_webhook_url():
    if mode == Mode.SC13.value:
        return os.getenv('SLACK_WEBHOOK_URL')
    return os.getenv('SLACK_WEBHOOK_MERGE_URL')


def get_headers():
    return {'User-Agent': os.getenv('USER_AGENT')}
