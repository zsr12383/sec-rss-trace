import requests
import pandas as pd


def get_nasdaq_stocks():
    url = "https://api.nasdaq.com/api/screener/stocks"
    params = {
        "exchange": "NASDAQ",
        "download": "true"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(url, params=params, headers=headers)
    data = response.json()['data']['rows']

    return data


def get_nasdaq_top_stocks(len=50):
    # Get the list of Nasdaq stocks
    nasdaq_stocks = get_nasdaq_stocks()
    # Convert to DataFrame
    df = pd.DataFrame(nasdaq_stocks)
    # Convert market cap to numeric, replacing '-' with NaN
    df['marketCap'] = pd.to_numeric(df['marketCap'].replace('-', float('nan')), errors='coerce')
    # Sort by market cap (descending) and select top 50
    top_list = df.sort_values('marketCap', ascending=False).head(len)
    first_words = set([stock['name'].split()[0].split('.')[0] for stock in top_list.to_dict('records')])
    return first_words
