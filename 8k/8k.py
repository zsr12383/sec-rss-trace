import logging
import time
from urllib.parse import urljoin

import schedule
from bs4 import BeautifulSoup

from get_env import get_slack_webhook_merge_url, get_groq_api_key, get_groq_message
from nasdaq import get_nasdaq_top_stocks
from requesthelper import RequestHelper
from sc13.sc13bot import Sc13Bot
from groq import Groq
from GroqHelper import GroqHelper
from html_body_extractor import html_body_extractor
import logging_config


class EightKBot(Sc13Bot):
    def __init__(self, keywords, rss_url, request_helper_instance: RequestHelper, groq_client: Groq):
        super().__init__(keywords, rss_url, request_helper_instance)
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
        # 이게 정적인 문서 조회하는 링크, 그냥 요청 시 이걸 이용해 iframe에 띄우던가 그랬음
        full_url = full_url.replace("ix?doc=/", "", 1)
        response = self.request_helper.request_with_exception(full_url)
        return BeautifulSoup(response.text, 'html.parser')

    def do_entry_process(self, entry):
        time.sleep(0.5)
        response = self.request_helper.request_with_exception(entry.link)
        if response is None: return
        doc = BeautifulSoup(response.text, 'html.parser')
        try:
            time.sleep(0.5)
            doc = self.extract_8_k_doc(doc)
        except Exception as e:
            logging.error(e)
            self.request_helper.send_to_slack(str(e))
            return

        body_text = html_body_extractor(doc)
        groq_answer = self.check_signal_by_groq(body_text)
        contain_keyword = self.find_contain_keyword(body_text)

        msg = RequestHelper.generate_message_body(entry)
        if groq_answer is not None and not groq_answer.startswith('0'):
            msg = RequestHelper.add_message(msg, "groq_answer", groq_answer)
        if contain_keyword:
            msg = RequestHelper.add_message(msg, "keywords", str(contain_keyword))
        if msg == RequestHelper.generate_message_body(entry): return
        self.request_helper.send_to_slack(msg)

    def check_signal_by_groq(self, text):
        logging.info(text)
        return GroqHelper.ask_groq(text, self.groq_msg, self.groq_client, self.request_helper)


if __name__ == '__main__':
    logging.info("process start")
    request_helper = RequestHelper(get_slack_webhook_merge_url())
    eight_k_rss_url = 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=8-K&company=&dateb=&owner=include&start=0&count=40&output=atom'
    eight_k_bot = EightKBot(
        get_nasdaq_top_stocks(50, request_helper).union({'M&A', 'Acquisition', 'Merger', 'Takeover'}), eight_k_rss_url,
        request_helper, Groq(api_key=get_groq_api_key()))
    schedule.every(3).minutes.do(eight_k_bot.check_rss_feed)
    while True:
        schedule.run_pending()
        time.sleep(1)
