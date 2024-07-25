import pandas as pd
import logging

logger = logging.getLogger(__name__)

from request import request_with_exception, send_to_slack

spare_data = {'Apple', 'Adobe', 'Intuit', 'Cisco', 'Honeywell', 'Texas', 'NVIDIA', 'Microsoft', 'Automatic',
              'Intuitive', 'Cintas', 'Amgen', 'Mondelez', 'Amazon', 'Vertex', 'ASML', 'Palo', 'Ryanair', 'Gilead',
              'Meta', 'Starbucks', 'Regeneron', 'Alphabet', 'Booking', 'Costco', 'Netflix', 'T-Mobile', 'Micron', 'Lam',
              'CME', 'Comcast', 'Advanced', 'AstraZeneca', 'Arm', 'Intel', 'KLA', 'Applied', 'Sanofi', 'MercadoLibre',
              'QUALCOMM', 'Analog', 'PepsiCo', 'Equinix', 'Broadcom', 'Airbnb', 'Linde', 'PDD', 'Synopsys', 'Tesla'}


def get_nasdaq_stocks():
    url = "https://api.nasdaq.com/api/screener/stocks"
    params = {
        "exchange": "NASDAQ",
        "download": "true"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = request_with_exception(url, params=params, headers=headers)
    return response


def get_nasdaq_top_stocks(len=50):
    response = get_nasdaq_stocks()
    if response is None:
        send_to_slack('Since we are unable to get NASDAQ data, we run the process using pre-prepared data.')
        logging.info('Since we are unable to get NASDAQ data, we run the process using pre-prepared data.')
        return spare_data
    nasdaq_stocks = response.json()['data']['rows']
    df = pd.DataFrame(nasdaq_stocks)
    # Convert market cap to numeric, replacing '-' with NaN
    df['marketCap'] = pd.to_numeric(df['marketCap'].replace('-', float('nan')), errors='coerce')
    # Sort by market cap (descending) and select top 50
    top_list = df.sort_values('marketCap', ascending=False).head(len)
    first_words = set([stock['name'].split()[0].split('.')[0] for stock in top_list.to_dict('records')])
    return first_words
