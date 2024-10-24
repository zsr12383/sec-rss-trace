from packages.logger import logging_config
from bs4 import BeautifulSoup
import feedparser
import re
from packages.utils.requesthelper import RequestHelper
import logging
from threading import Lock

logger = logging.getLogger(__name__)


class RssBot:
    def __init__(self, keywords, rss_url, request_helper: RequestHelper):
        self.keywords = [keyword.lower() for keyword in keywords]
        self.rss_url = rss_url
        self.request_helper = request_helper
        logging.info("process start")
        request_helper.send_to_slack("process start")

        self.is_running = False
        self.lock = Lock()

    def find_contain_keyword(self, text):
        ret = []
        for keyword in self.keywords:
            pattern = fr'\b{keyword}\b'
            if re.search(pattern, text, re.IGNORECASE):
                ret.append(keyword)
        return ret

    def get_entries(self):
        response = self.request_helper.request_with_exception(self.rss_url)
        feed = feedparser.parse(response.content)
        return feed.entries

    def find_link_has_keyword(self, link):
        try:
            response = self.request_helper.request_with_exception(link)
            doc = BeautifulSoup(response.text, 'html.parser')
            return self.find_contain_keyword(doc)
        except Exception as e:
            return None

    def send_to_slack_keyword(self, entry, keywords):
        message = f"New entry found:\n\tTitle: {entry.title}\n\tLink: {entry.link}\n\tKeyword: {keywords}"
        self.request_helper.send_to_slack(message)

    def do_entries_process(self, entries):
        for entry in entries:
            contain_keywords = self.find_contain_keyword(entry.link)
            if len(contain_keywords) == 0: continue
            self.send_to_slack_keyword(entry, contain_keywords)

    def check_rss_feed(self):
        if self.lock.locked():
            logging.info("Previous job still running, skipping this execution.")
            return
        with self.lock:
            try:
                entries = self.get_entries()
            except Exception as e:
                logging.error(e)
                self.request_helper.send_to_slack(str(e))
                return
            self.do_entries_process(entries)
