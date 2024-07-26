import requests
import logging

import get_env

logger = logging.getLogger(__name__)
headers = get_env.get_headers()
slack_webhook_url = get_env.get_slack_webhook_url()

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


def request_with_exception(url, method=Method.GET.value, headers=headers, params=None, json=None):
    response = None
    logging.info(generate_log_msg(url, method, 'Request Start'))
    try:
        if (method == Method.GET.value):
            response = requests.get(url, headers=headers, params=params, timeout=(5, 10))
        elif (method == Method.POST.value):
            response = requests.post(url, headers=headers, params=params, timeout=(5, 10), json=json)
        response.raise_for_status()
        logging.info(generate_log_msg(url, method, 'Request End'))
    except requests.exceptions.Timeout:
        err_log_msg = generate_log_msg(url, method, 'Request Timeout')
        logging.exception(err_log_msg)
        if url != slack_webhook_url:
            send_to_slack(err_log_msg)
    except requests.exceptions.RequestException as e:
        msg = generate_log_msg(url, method, str(e))
        logging.exception(msg)
        if url != slack_webhook_url:
            send_to_slack(msg)
    return response


def send_to_slack(message):
    payload = {"text": message}
    request_with_exception(slack_webhook_url, json=payload, method=Method.POST.value)
