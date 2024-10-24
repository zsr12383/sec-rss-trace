from packages.logger import logging_config
import time
import pytz
import schedule
from datetime import datetime, timedelta
from itertools import takewhile

from packages.scrapper.RssBot import RssBot
from packages.utils.get_env import get_slack_webhook_url
from packages.utils.html_body_extractor import html_body_extractor
from packages.scrapper.nasdaq import get_nasdaq_top_stocks
from bs4 import BeautifulSoup

from packages.utils.requesthelper import RequestHelper


class Sc13Bot(RssBot):
    def __init__(self, keywords, rss_url, request_helper: RequestHelper):
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
        body_text = html_body_extractor(doc)
        contain_keyword = self.find_contain_keyword(body_text)
        if not contain_keyword: return
        self.send_to_slack_keyword(entry, contain_keyword)

    def do_entries_process(self, entries):
        need_check_entries = takewhile(self.is_new_doc, entries)
        for entry in need_check_entries:
            self.do_entry_process(entry)
        self.last_updated = max(self.last_updated, entries[0].updated)


if __name__ == '__main__':
    request_helper = RequestHelper(get_slack_webhook_url())
    sc13_rss_url = 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=sc%2013&company=&dateb=&owner=include&start=0&count=40&output=atom'
    sc13_bot = Sc13Bot(get_nasdaq_top_stocks(50, request_helper), sc13_rss_url, request_helper)
    schedule.every(2).minutes.do(sc13_bot.check_rss_feed)
    while True:
        schedule.run_pending()
        time.sleep(1)
