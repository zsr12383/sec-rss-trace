import sys
from urllib.parse import urljoin

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
from mode import Mode

logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def get_rss_url(mode):
    if mode == Mode.MERGE.value:
        return "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=8-K&company=&dateb=&owner=include&start=0&count=40&output=atom"
    elif mode == Mode.SC13.value:
        return "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=sc%2013&company=&dateb=&owner=include&start=0&count=40&output=atom"


def get_keywords(mode):
    if mode == Mode.MERGE.value:
        return {'merge', 'acqui'}
    elif mode == Mode.SC13.value:
        return get_nasdaq_top_stocks(50).union({'Google'})


class SEC_bot():
    def __init__(self, mode):
        self.keywords = get_keywords(mode)
        self.rss_url = get_rss_url(mode)
        self.eastern = pytz.timezone('US/Eastern')
        self.last_updated = (datetime.now(self.eastern) - timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%S-04:00')
        self.mode = mode
        self.base_url = 'https://www.sec.gov'

    def find_contain_keyword(self, doc):
        for tag in doc.find_all():
            text = tag.get_text()
            for keyword in self.keywords:
                if keyword in text:
                    return keyword
        return None

    def is_new_doc(self, entry):
        return entry.updated > self.last_updated

    def extract_8K_doc(self, doc):
        table = doc.find('table', class_='tableFile')
        # tbody = table.find('tbody')
        tbody = table
        second_row = tbody.find_all('tr')[1]
        third_cell = second_row.find_all('td')[2]
        link = third_cell.find('a')
        href = link['href'] if link else None
        full_url = urljoin(self.base_url, href) if href else None
        full_url = full_url.replace("ix?doc=/", "", 1)
        response = request_with_exception(full_url)
        return BeautifulSoup(response.text, 'html.parser')

    def check_rss_feed(self):
        response = request_with_exception(self.rss_url)
        if response is None: return
        feed = feedparser.parse(response.content)
        entries = feed.entries
        tmp_updated = entries[0].updated
        need_check_entries = takewhile(self.is_new_doc, entries)
        new_entries = []

        for entry in need_check_entries:
            time.sleep(0.4)
            response = request_with_exception(entry.link)
            if response is None: continue
            doc = BeautifulSoup(response.text, 'html.parser')
            if self.mode == Mode.MERGE.value:
                try:
                    time.sleep(0.4)
                    doc = self.extract_8K_doc(doc)
                except Exception as e:
                    logging.error(e)
                    send_to_slack(str(e))
                    continue
            contain_keyword = self.find_contain_keyword(doc)
            if not contain_keyword: continue
            entry['keyword'] = contain_keyword
            new_entries.append(entry)

        self.last_updated = max(self.last_updated, tmp_updated)
        if new_entries:
            for entry in new_entries:
                message = f"New entry found:\n\tTitle: {entry.title}\n\tLink: {entry.link}\n\tUpdated: {entry.updated}\n\tKeyword: {entry.keyword}"
                send_to_slack(message)


if __name__ == '__main__':
    send_to_slack("process start")
    logging.info("process start")
    mode = sys.argv[1]
    if mode is None or mode not in (item.value for item in Mode):
        logging.error('No mode specified')
        raise SystemExit(1)

    sec_bot = SEC_bot(mode)
    schedule.every(2).minutes.do(sec_bot.check_rss_feed)
    while True:
        schedule.run_pending()
        time.sleep(1)
