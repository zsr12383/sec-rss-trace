import requests
import logging

import get_env

logger = logging.getLogger(__name__)

from enum import Enum


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
    return f'URL:{url} - Method:{method} - Content: {content}'


class RequestHelper:
    def __init__(self, slack_webhook_url):
        self.slack_webhook_url = slack_webhook_url
        self.headers = get_env.get_headers()

    @staticmethod
    def generate_message_body(entry) -> str:
        return f"New entry found:\n\tTitle: {entry.title}\n\tLink: {entry.link}"

    @staticmethod
    def add_message(message: str, key: str, to_add: str) -> str:
        return message + f'\n\t{key}: t{to_add}'

    def request_with_exception(self, url, method=Method.GET.value, params=None, json=None, headers=None):
        response = None
        logging.info(generate_log_msg(url, method, 'Request Start'))
        headers = self.headers if headers is None else headers
        try:
            if method == Method.GET.value:
                response = requests.get(url, headers=headers, params=params, timeout=(5, 10))
            elif method == Method.POST.value:
                response = requests.post(url, headers=headers, params=params, timeout=(5, 10), json=json)
            response.raise_for_status()
            logging.info(generate_log_msg(url, method, 'Request End'))
        except requests.exceptions.Timeout:
            err_log_msg = generate_log_msg(url, method, 'Request Timeout')
            logging.exception(err_log_msg)
            if url != self.slack_webhook_url:
                self.send_to_slack(err_log_msg)
            return None
        except requests.exceptions.RequestException as e:
            msg = generate_log_msg(url, method, str(e))
            logging.exception(msg)
            if url != self.slack_webhook_url:
                self.send_to_slack(msg)
            return None
        return response

    def send_to_slack(self, message):
        border = '\n' + '=' * 32
        payload = {"text": message + border}
        self.request_with_exception(self.slack_webhook_url, json=payload, method=Method.POST.value)
