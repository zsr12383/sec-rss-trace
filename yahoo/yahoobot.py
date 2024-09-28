import schedule
from bs4 import BeautifulSoup
from RssBot import RssBot
from get_env import get_slack_webhook_yahoo_url
from yahoo_keyword import get_yahoo_keywords, get_magnificent
from request_helper import Request_Helper
import xml.etree.ElementTree as ET
import logging
import time
import re
from datetime import datetime, timedelta, timezone

logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def parse_rss(content):
    root = ET.fromstring(content)
    items = root.findall(".//item")
    return [(item.find("title").text, item.find("link").text, item.find("pubDate").text) for item in items]


class YahooBot(RssBot):
    def __init__(self, keywords, rss_url, request: Request_Helper):
        super().__init__(keywords, rss_url, request)
        self.last_items = set()

    def get_entries(self):
        response = self.request.request_with_exception(self.rss_url)
        current_items = set(parse_rss(response.content))
        new_items = current_items - self.last_items
        self.last_items.union(current_items)

        current_time = datetime.now(timezone.utc)
        time_threshold = current_time - timedelta(days=1)
        self.last_items = {item for item in self.last_items if
                           datetime.strptime(item[2], "%Y-%m-%dT%H:%M:%SZ") > time_threshold}

        return new_items

    def send_to_slack_keyword(self, entry, keywords):
        message = f"New entry found:\n\tTitle: {entry['title']}\n\tLink: {entry['link']}\n\tKeyword: {keywords}"
        self.request.send_to_slack(message)

    def find_contain_keyword(self, doc):
        article_body = doc.find('div', {'class': 'caas-body'})
        ret = []
        if article_body is None: return ret

        article_text = ' '.join([element.get_text() for element in
                                 article_body.find_all(
                                     ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ol', 'ul', 'li'])]).lower()
        for keyword in self.keywords:
            pattern = fr'\b{keyword}\b'
            if re.search(pattern, article_text, re.IGNORECASE):
                ret.append(keyword)
        return ret

    def do_entry_process(self, entry):
        time.sleep(0.2)
        response = self.request.request_with_exception(entry['link'])
        if response is None: return
        doc = BeautifulSoup(response.text, 'html.parser')
        contain_keywords = self.find_contain_keyword(doc)
        if len(contain_keywords) == 0 or self.all_contained_magnificent(contain_keywords): return
        self.send_to_slack_keyword(entry, contain_keywords)

    def do_entries_process(self, entries):
        for title, link in entries:
            entry = {'title': title, 'link': link}
            self.do_entry_process(entry)

    def all_contained_magnificent(self, keywords):
        return set(keywords).issubset(get_magnificent())


if __name__ == '__main__':
    logging.info("process start")
    request_helper = Request_Helper(get_slack_webhook_yahoo_url())
    yahoo_rss_url = 'https://finance.yahoo.com/rss/topstories'
    yahoo_bot = YahooBot(get_yahoo_keywords().union(get_magnificent()), yahoo_rss_url, request_helper)
    yahoo_bot.check_rss_feed()
    schedule.every(3).minutes.do(yahoo_bot.check_rss_feed)
    while True:
        schedule.run_pending()
        time.sleep(1)
