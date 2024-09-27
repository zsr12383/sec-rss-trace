import pandas as pd
import logging

logger = logging.getLogger(__name__)

from request_helper import Request_Helper
from yahoo_keyword import get_yahoo_keywords

spare_data = {'Apple', 'Adobe', 'Intuit', 'Cisco', 'Honeywell', 'Texas Instrument', 'NVIDIA', 'Microsoft', 'Automatic',
              'Intuitive', 'Cintas', 'Amgen', 'Mondelez', 'Amazon', 'Vertex', 'ASML', 'Palo', 'Ryanair', 'Gilead',
              'Meta', 'Starbucks', 'Regeneron', 'Alphabet', 'Booking', 'Costco', 'Netflix', 'T-Mobile', 'Micron', 'Lam',
              'CME', 'Comcast', 'AMD', 'Advanced Micro Device,' 'AstraZeneca', 'Arm', 'Intel', 'KLA', 'Applied',
              'Sanofi', 'MercadoLibre', 'QUALCOMM', 'Analog', 'PepsiCo', 'Equinix', 'Broadcom', 'Airbnb', 'Linde',
              'PDD', 'Synopsys', 'Tesla', 'Google', 'Googl'}.union(get_yahoo_keywords())


def get_nasdaq_stocks(request_helper: Request_Helper):
    url = "https://api.nasdaq.com/api/screener/stocks"
    params = {
        "exchange": "NASDAQ",
        "download": "true"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = request_helper.request_with_exception(url, params=params, headers=headers)
    return response


def get_nasdaq_top_stocks(len, request_helper: Request_Helper):
    response = get_nasdaq_stocks(request_helper)
    if response is None:
        request_helper.send_to_slack(
            'Since we are unable to get NASDAQ data, we run the process using pre-prepared data.')
        logging.info('Since we are unable to get NASDAQ data, we run the process using pre-prepared data.')
        return spare_data
    nasdaq_stocks = response.json()['data']['rows']
    df = pd.DataFrame(nasdaq_stocks)
    # Convert market cap to numeric, replacing '-' with NaN
    df['marketCap'] = pd.to_numeric(df['marketCap'].replace('-', float('nan')), errors='coerce')
    # Sort by market cap (descending) and select top 50
    top_list = df.sort_values('marketCap', ascending=False).head(len)
    first_words = set([stock['name'].split()[0].split('.')[0] for stock in top_list.to_dict('records')])
    if "Advanced" in first_words:
        first_words.remove("Advanced")
        first_words.add("Advanced Micro Device")
        first_words.add("AMD")
    if "Texas" in first_words:
        first_words.remove("Texas")
        first_words.add("Texas Instrument")
    first_words.add("Googl")
    first_words.add("Google")
    first_words.union(get_yahoo_keywords())
    return first_words
