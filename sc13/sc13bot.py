import time
import pytz
import schedule
from datetime import datetime, timedelta
from itertools import takewhile

from RssBot import RssBot
from get_env import get_slack_webhook_url
from nasdaq import get_nasdaq_top_stocks
from bs4 import BeautifulSoup
import logging_config
import logging

from request_helper import Request_Helper


class Sc13Bot(RssBot):
    def __init__(self, keywords, rss_url, request_helper: Request_Helper):
        super().__init__(keywords, rss_url, request_helper)
        self.eastern = pytz.timezone('US/Eastern')
        self.last_updated = (datetime.now(self.eastern) - timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%S-04:00')
        self.base_url = 'https://www.sec.gov'

    def is_new_doc(self, entry):
        return entry.updated > self.last_updated

    def do_entry_process(self, entry):
        time.sleep(0.4)
        response = self.request_helper.request_with_exception(entry.link)
        if response is None: return
        doc = BeautifulSoup(response.text, 'html.parser')
        contain_keyword = self.find_contain_keyword(doc)
        if not contain_keyword: return
        self.send_to_slack_keyword(entry, contain_keyword)

    def do_entries_process(self, entries):
        need_check_entries = takewhile(self.is_new_doc, entries)
        for entry in need_check_entries:
            self.do_entry_process(entry)
        self.last_updated = max(self.last_updated, entries[0].updated)


if __name__ == '__main__':
    logging.info("process start")
    request_helper = Request_Helper(get_slack_webhook_url())
    sc13_rss_url = 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=sc%2013&company=&dateb=&owner=include&start=0&count=40&output=atom'
    sc13_bot = Sc13Bot(get_nasdaq_top_stocks(50, request_helper), sc13_rss_url, request_helper)
    schedule.every(2).minutes.do(sc13_bot.check_rss_feed)
    while True:
        schedule.run_pending()
        time.sleep(1)
