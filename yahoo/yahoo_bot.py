import schedule
from bs4 import BeautifulSoup
from RSS_bot import RSS_bot
from get_env import get_slack_webhook_yahoo_url
from nasdaq import get_nasdaq_top_stocks
from request_helper import Request_Helper
import xml.etree.ElementTree as ET
import logging
import time
import re

logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class Yahoo_bot(RSS_bot):
    def __init__(self, keywords, rss_url, request: Request_Helper):
        super(Yahoo_bot, self).__init__(keywords, rss_url, request)
        self.last_items = set()

    def parse_rss(self, content):
        root = ET.fromstring(content)
        items = root.findall(".//item")
        return [(item.find("title").text, item.find("link").text) for item in items]

    def get_entries(self):
        response = self.request.request_with_exception(self.rss_url)
        current_items = set(self.parse_rss(response.content))
        new_items = current_items - self.last_items
        self.last_items = current_items
        return new_items

    def send_to_slack_keyword(self, entry, keyword):
        message = f"New entry found:\n\tTitle: {entry['title']}\n\tLink: {entry['link']}\n\tKeyword: {keyword}"
        self.request.send_to_slack(message)

    def find_contain_keyword(self, doc):
        article_body = doc.find('div', {'class': 'caas-body'})
        if article_body is None: return None
        article_text = ' '.join([element.get_text() for element in
                                 article_body.find_all(
                                     ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ol', 'ul', 'li'])]).lower()
        for keyword in self.keywords:
            pattern = fr'\b{keyword}\b'
            if re.search(pattern, article_text, re.IGNORECASE):
                return keyword
        return None

    def do_entry_process(self, entry):
        time.sleep(0.2)
        response = self.request.request_with_exception(entry['link'])
        if response is None: return
        doc = BeautifulSoup(response.text, 'html.parser')
        contain_keyword = self.find_contain_keyword(doc)
        if not contain_keyword: return
        self.send_to_slack_keyword(entry, contain_keyword)

    def do_entries_process(self, entries):
        for title, link in entries:
            entry = {'title': title, 'link': link}
            self.do_entry_process(entry)


if __name__ == '__main__':
    logging.info("process start")
    request_helper = Request_Helper(get_slack_webhook_yahoo_url())
    yahoo_rss_url = 'https://finance.yahoo.com/rss/topstories'
    yahoo_bot = Yahoo_bot(get_nasdaq_top_stocks(50, request_helper), yahoo_rss_url, request_helper)
    schedule.every(2).minutes.do(yahoo_bot.check_rss_feed)
    while True:
        schedule.run_pending()
        time.sleep(1)
