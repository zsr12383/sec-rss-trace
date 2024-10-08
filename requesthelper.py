import requests
import logging
import time
from enum import Enum
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import get_env

logger = logging.getLogger(__name__)


class Method(Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'
    OPTIONS = 'OPTIONS'
    HEAD = 'HEAD'
    TRACE = 'TRACE'

    def __str__(self) -> str:
        return self.value


def generate_log_msg(url, method, content) -> str:
    return f'URL: {url} - Method: {method} - Content: {content}'


class RequestHelper:
    def __init__(self, slack_webhook_url, max_retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504)):
        self.slack_webhook_url = slack_webhook_url
        self.headers = get_env.get_headers()
        self.border = '\n' + '=' * 64
        self.session = requests.Session()
        retries = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def request_with_exception(self, url, method=Method.GET.value, params=None, json=None, headers=None):
        logging.info(generate_log_msg(url, method, 'Request Start'))
        headers = self.headers if headers is None else headers

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json,
                timeout=(5, 10)
            )
            response.raise_for_status()
            logging.info(generate_log_msg(url, method, 'Request End'))
            return response
        except requests.exceptions.Timeout as e:
            err_log_msg = generate_log_msg(url, method, 'Request Timeout')
            logging.error(err_log_msg)
            if url != self.slack_webhook_url:
                self.send_to_slack(err_log_msg)
            return None
        except requests.exceptions.RequestException as e:
            msg = generate_log_msg(url, method, f'Request failed: {str(e)}')
            logging.error(msg)
            if url != self.slack_webhook_url:
                self.send_to_slack(msg)
            return None

    def send_to_slack(self, message):
        payload = {"text": message + self.border}
        # Avoid infinite recursion by not sending Slack notifications if Slack webhook fails
        try:
            response = self.session.post(
                self.slack_webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=(5, 10)
            )
            response.raise_for_status()
            logging.info('Error message sent to Slack successfully.')
        except requests.exceptions.RequestException as e:
            logging.error(f'Failed to send message to Slack: {e}')
