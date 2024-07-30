from bs4 import BeautifulSoup
import feedparser

from request_helper import Request_Helper


class RSS_bot():
    def __init__(self, keywords, rss_url, request: Request_Helper):
        self.keywords = [keyword.lower() for keyword in keywords]
        self.rss_url = rss_url
        self.request = request
        request.send_to_slack("process start")

    def find_contain_keyword(self, doc):
        for tag in doc.find_all():
            text = tag.get_text().lower()
            for keyword in self.keywords:
                if keyword in text:
                    return keyword
        return None

    def get_entries(self):
        response = self.request.request_with_exception(self.rss_url)
        feed = feedparser.parse(response.content)
        return feed.entries

    def find_link_has_keyword(self, link):
        try:
            response = self.request.request_with_exception(link)
            doc = BeautifulSoup(response.text, 'html.parser')
            return self.find_contain_keyword(doc)
        except Exception as e:
            return None

    def send_to_slack_keyword(self, entry, keyword):
        message = f"New entry found:\n\tTitle: {entry.title}\n\tLink: {entry.link}\n\tUpdated: {entry.updated}\n\tKeyword: {keyword}"
        self.request.send_to_slack(message)

    def do_entries_process(self, entries):
        for entry in entries:
            contain_keyword = self.find_contain_keyword(entry.link)
            if not contain_keyword: continue
            self.send_to_slack_keyword(entry, contain_keyword)

    def check_rss_feed(self):
        try:
            entries = self.get_entries()
        except Exception as e:
            return
        self.do_entries_process(entries)
