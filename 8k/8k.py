import logging
import time
from urllib.parse import urljoin

import schedule
from bs4 import BeautifulSoup

from get_env import get_slack_webhook_merge_url, get_groq_api_key, get_groq_message
from nasdaq import get_nasdaq_top_stocks
from request_helper import Request_Helper
from sc13.sc13bot import Sc13Bot
from groq import Groq

logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class EightKBot(Sc13Bot):
    def __init__(self, keywords, rss_url, request: Request_Helper, groq_client: Groq):
        super().__init__(keywords, rss_url, request)
        self.groq_client = groq_client
        self.groq_msg = get_groq_message()

    def extract_8_k_doc(self, doc):
        table = doc.find('table', class_='tableFile')
        # tbody = table.find('tbody')
        tbody = table
        second_row = tbody.find_all('tr')[1]
        third_cell = second_row.find_all('td')[2]
        link = third_cell.find('a')
        href = link['href'] if link else None
        full_url = urljoin(self.base_url, href) if href else None
        full_url = full_url.replace("ix?doc=/", "", 1)
        response = self.request.request_with_exception(full_url)
        return BeautifulSoup(response.text, 'html.parser')

    def do_entry_process(self, entry):
        time.sleep(0.5)
        response = self.request.request_with_exception(entry.link)
        if response is None: return
        doc = BeautifulSoup(response.text, 'html.parser')
        try:
            time.sleep(0.5)
            doc = self.extract_8_k_doc(doc)
        except Exception as e:
            logging.error(e)
            self.request.send_to_slack(str(e))
            return

        if signum := self.check_signal_by_groq(doc):
            self.send_to_slack_keyword(entry, f"groq signal${signum}")
            return

        contain_keyword = self.find_contain_keyword(doc)
        if not contain_keyword: return
        self.send_to_slack_keyword(entry, contain_keyword)

    def check_signal_by_groq(self, doc):
        text = ' '.join([element.get_text() for element in doc.find_all()]).lower()
        text = text + self.groq_msg

        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                model="llama-3.1-70b-versatile"
            )
            res = chat_completion.choices[0].message.content
            if res and not res.startswith('0'): return res[0]
        except Exception as e:
            logging.error(e)
        return False


if __name__ == '__main__':
    logging.info("process start")
    request_helper = Request_Helper(get_slack_webhook_merge_url())
    eight_k_rss_url = 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=8-K&company=&dateb=&owner=include&start=0&count=40&output=atom'
    eight_k_bot = EightKBot(
        get_nasdaq_top_stocks(50, request_helper).union({'M&A', 'Acquisition', 'Merger', 'Takeover'}), eight_k_rss_url,
        request_helper, Groq(api_key=get_groq_api_key()))
    schedule.every(2).minutes.do(eight_k_bot.check_rss_feed)
    while True:
        schedule.run_pending()
        time.sleep(1)
