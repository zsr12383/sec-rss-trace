from urllib.parse import urljoin
import time
import pytz
import schedule
from datetime import datetime, timedelta
from get_env import get_slack_webhook_merge_url
from nasdaq import get_nasdaq_top_stocks
from bs4 import BeautifulSoup
import logging
from request_helper import Request_Helper
from sc13.sc13_bot import SC13_bot

logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class EightK_bot(SC13_bot):
    def __init__(self, keywords, rss_url, request: Request_Helper):
        super(EightK_bot, self).__init__(keywords, rss_url, request)
        self.eastern = pytz.timezone('US/Eastern')
        self.last_updated = (datetime.now(self.eastern) - timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%S-04:00')
        self.base_url = 'https://www.sec.gov'

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
        response = self.request.request_with_exception(full_url)
        return BeautifulSoup(response.text, 'html.parser')

    def do_entry_process(self, entry):
        time.sleep(0.4)
        response = self.request.request_with_exception(entry.link)
        if response is None: return
        doc = BeautifulSoup(response.text, 'html.parser')
        try:
            time.sleep(0.4)
            doc = self.extract_8K_doc(doc)
        except Exception as e:
            logging.error(e)
            self.request.send_to_slack(str(e))
            return
        contain_keyword = self.find_contain_keyword(doc)
        if not contain_keyword: return
        self.send_to_slack_keyword(entry, contain_keyword)


if __name__ == '__main__':
    logging.info("process start")
    request_helper = Request_Helper(get_slack_webhook_merge_url())
    eightk_rss_url = 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=8-K&company=&dateb=&owner=include&start=0&count=40&output=atom'
    eightk_bot = EightK_bot(
        get_nasdaq_top_stocks(50, request_helper).union({'M&A', 'Acquisition', 'Merger', 'Takeover'}), eightk_rss_url,
        request_helper)
    schedule.every(2).minutes.do(eightk_bot.check_rss_feed)
    while True:
        schedule.run_pending()
        time.sleep(1)
