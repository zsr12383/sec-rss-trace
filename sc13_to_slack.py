import feedparser

import time
import pytz
import schedule
from datetime import datetime, timedelta
from itertools import takewhile
from nasdaq import get_nasdaq_top_stocks
from bs4 import BeautifulSoup
import logging

from request import request_with_exception, send_to_slack

logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

keywords = get_nasdaq_top_stocks(50)
keywords = keywords.union({'Google'})

rss_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=sc%2013&company=&dateb=&owner=include&start=0&count=40&output=atom"

# 초기 last_updated 값을 현재 미 동부 시각에서 -2시간으로 설정
eastern = pytz.timezone('US/Eastern')
last_updated = (datetime.now(eastern) - timedelta(hours=48)).strftime('%Y-%m-%dT%H:%M:%S-04:00')


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
    response = request_with_exception(rss_url)
    if response is None: return
    feed = feedparser.parse(response.content)
    entries = feed.entries
    tmp_updated = entries[0].updated
    need_check_entries = takewhile(is_new_doc, entries)
    new_entries = []

    for entry in need_check_entries:
        time.sleep(0.3)
        response = request_with_exception(entry.link)
        if response is None: continue
        doc = BeautifulSoup(response.text, 'html.parser')
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
    send_to_slack("process start")
    logging.info("process start")
    schedule.every(1).minutes.do(check_rss_feed)
    while True:
        schedule.run_pending()
        time.sleep(1)
