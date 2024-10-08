import schedule
from bs4 import BeautifulSoup
from groq import Groq

from GroqHelper import GroqHelper
from RssBot import RssBot
from get_env import get_slack_webhook_yahoo_url, get_groq_api_key, get_groq_message
from yahoo_keyword import get_yahoo_keywords, get_magnificent
from requesthelper import RequestHelper
import xml.etree.ElementTree as ET
import logging
import time
import re
from datetime import datetime, timedelta, timezone


# .replace(tzinfo=timezone.utc) 이게 없으면 문제가 발생함
def parse_rss(content):
    root = ET.fromstring(content)
    items = root.findall(".//item")
    return [(item.find("title").text, item.find("link").text,
             datetime.strptime(item.find("pubDate").text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)) for item
            in items]


def all_contained_magnificent(keywords):
    return set(keywords).issubset(get_magnificent())


class YahooBot(RssBot):
    def __init__(self, keywords, rss_url, request: RequestHelper, groq_client: Groq):
        super().__init__(keywords, rss_url, request)
        self.last_items = set()
        self.groq_client = groq_client
        self.groq_msg = get_groq_message()

    def get_entries(self):
        response = self.request_helper.request_with_exception(self.rss_url)
        current_items = set(parse_rss(response.content))
        new_items = current_items - self.last_items
        self.last_items = self.last_items.union(new_items)

        current_time = datetime.now(timezone.utc)
        time_threshold = current_time - timedelta(days=7)
        filtered_items = filter(
            lambda item: item[2] > time_threshold,
            self.last_items
        )
        self.last_items = set(filtered_items)
        return new_items

    def send_to_slack_keyword(self, entry, keywords):
        message = f"New entry found:\n\tTitle: {entry['title']}\n\tLink: {entry['link']}\n\tKeyword: {keywords}"
        self.request_helper.send_to_slack(message)

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
        response = self.request_helper.request_with_exception(entry['link'])
        if response is None: return
        doc = BeautifulSoup(response.text, 'html.parser')

        groq_answer = self.check_signal_by_groq(doc)
        contain_keyword = self.find_contain_keyword(doc)

        msg = RequestHelper.generate_message_body_for_yahoo(entry['title'], entry['link'])
        if groq_answer is not None and not groq_answer.startswith('0'):
            msg = RequestHelper.add_message(msg, "groq_answer", groq_answer)
        if contain_keyword:
            msg = RequestHelper.add_message(msg, "keywords", str(contain_keyword))
        if msg == RequestHelper.generate_message_body_for_yahoo(entry['title'], entry['link']): return
        self.request_helper.send_to_slack(msg)

    def do_entries_process(self, entries):
        for title, link, _ in entries:
            entry = {'title': title, 'link': link}
            self.do_entry_process(entry)

    def check_signal_by_groq(self, doc):
        article_body = doc.find('div', {'class': 'caas-body'})
        if article_body is None: return None
        text = ' '.join([element.get_text() for element in
                         article_body.find_all(
                             ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ol', 'ul', 'li'])]).lower()
        logging.info(text)
        return GroqHelper.ask_groq(text, self.groq_msg, self.groq_client, self.request_helper)


if __name__ == '__main__':
    request_helper = RequestHelper(get_slack_webhook_yahoo_url())
    yahoo_rss_url = 'https://finance.yahoo.com/rss/topstories'
    yahoo_bot = YahooBot(get_yahoo_keywords().union(get_magnificent()), yahoo_rss_url, request_helper,
                         Groq(api_key=get_groq_api_key()))
    schedule.every(10).minutes.do(yahoo_bot.check_rss_feed)
    while True:
        schedule.run_pending()
        time.sleep(1)
