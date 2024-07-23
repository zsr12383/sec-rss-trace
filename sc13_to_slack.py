import feedparser
import requests
import time
import pytz
import schedule
from datetime import datetime, timedelta
from itertools import takewhile
from nasdaq import get_nasdaq_top_stocks
from bs4 import BeautifulSoup

import get_env

keywords = get_nasdaq_top_stocks(50)
keywords = keywords.union({'MS', 'Google'})
headers = get_env.get_headers()
slack_webhook_url = get_env.get_slack_webhook_url()
rss_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=sc%2013&company=&dateb=&owner=include&start=0&count=40&output=atom"

# 초기 last_updated 값을 현재 미 동부 시각에서 -2시간으로 설정
eastern = pytz.timezone('US/Eastern')
last_updated = (datetime.now(eastern) - timedelta(hours=48)).strftime('%Y-%m-%dT%H:%M:%S-04:00')


def fetch_feed(url):
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return feedparser.parse(response.content)


def fetch(url):
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return BeautifulSoup(response.text, 'html.parser')


def send_to_slack(message):
    payload = {"text": message}
    requests.post(slack_webhook_url, json=payload)


def find_contain_keyword(doc):
    for tag in doc.find_all():
        text = tag.get_text()
        for keyword in keywords:
            if keyword in text:
                return keyword
    return None


def is_new_doc(entry):
    return entry.updated > last_updated


def check_rss_feed():
    global last_updated
    feed = fetch_feed(rss_url)
    entries = feed.entries
    tmp_updated = entries[0].updated
    need_check_entries = takewhile(is_new_doc, entries)
    new_entries = []

    for entry in need_check_entries:
        time.sleep(0.3)
        doc = fetch(entry.link)
        contain_keyword = find_contain_keyword(doc)
        if not contain_keyword: continue
        entry['keyword'] = contain_keyword
        new_entries.append(entry)

    last_updated = max(last_updated, tmp_updated)
    if new_entries:
        for entry in new_entries:
            message = f"New entry found:\n\tTitle: {entry.title}\n\tLink: {entry.link}\n\tUpdated: {entry.updated}\n\tKeyword: {entry.keyword}"
            send_to_slack(message)


if __name__ == '__main__':
    schedule.every(1).minutes.do(check_rss_feed)
    while True:
        schedule.run_pending()
        time.sleep(1)
