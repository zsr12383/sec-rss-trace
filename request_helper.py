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


class Request_Helper():
    def __init__(self, slack_webhook_url):
        self.slack_webhook_url = slack_webhook_url
        self.headers = get_env.get_headers()

    def generate_log_msg(self, url, method, content) -> str:
        return f'URL:{url} - Method:{method} - Content: {content}'

    def request_with_exception(self, url, method=Method.GET.value, params=None, json=None, headers=None):
        response = None
        logging.info(self.generate_log_msg(url, method, 'Request Start'))
        headers = self.headers if headers is None else headers
        try:
            if method == Method.GET.value:
                response = requests.get(url, headers=headers, params=params, timeout=(5, 10))
            elif method == Method.POST.value:
                response = requests.post(url, headers=headers, params=params, timeout=(5, 10), json=json)
            response.raise_for_status()
            logging.info(self.generate_log_msg(url, method, 'Request End'))
        except requests.exceptions.Timeout:
            err_log_msg = self.generate_log_msg(url, method, 'Request Timeout')
            logging.exception(err_log_msg)
            if url != self.slack_webhook_url:
                self.send_to_slack(err_log_msg)
            return None
        except requests.exceptions.RequestException as e:
            msg = self.generate_log_msg(url, method, str(e))
            logging.exception(msg)
            if url != self.slack_webhook_url:
                self.send_to_slack(msg)
            return None
        return response

    def send_to_slack(self, message):
        payload = {"text": message}
        self.request_with_exception(self.slack_webhook_url, json=payload, method=Method.POST.value)
