import os
import requests
import feedparser
import schedule
import time
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Slack setup
slack_token = os.getenv('SLACK_API_TOKEN')
slack_channel = os.getenv('SLACK_CHANNEL_ID')
client = WebClient(token=slack_token)

# List of RSS feed URLs
rss_feed_urls = [
    'https://data.sec.gov/rss?cik=320193&type=3,4,5&count=40',
    # Add more RSS feed URLs here
]

# Dictionary to store the last seen entry id for each feed
last_seen_entry_ids = {url: None for url in rss_feed_urls}

# User-Agent header
headers = {'User-Agent': 'Mozilla/5.0 (compatible; MyRSSBot/1.0; +http://mywebsite.com/bot)'}


def fetch_feed(url):
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return feedparser.parse(response.content)


def send_slack_message(message):
    try:
        response = client.chat_postMessage(
            channel=slack_channel,
            text=message
        )
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")


def check_rss_updates():
    global last_seen_entry_ids
    for rss_feed_url in rss_feed_urls:
        feed = fetch_feed(rss_feed_url)

        new_entries = []
        for entry in feed.entries:
            entry_id = entry.id
            if last_seen_entry_ids[rss_feed_url] is None or entry_id > last_seen_entry_ids[rss_feed_url]:
                new_entries.append(entry)

        if new_entries:
            new_entries.sort(key=lambda x: x.id)  # Sort entries by ID
            for entry in new_entries:
                message = (
                    f"New entry in {feed.feed.title}:\n"
                    f"*Title:* {entry.title}\n"
                    f"*Link:* {entry.link}\n"
                    f"*Published:* {entry.updated}"
                )
                send_slack_message(message)
                last_seen_entry_ids[rss_feed_url] = entry.id


def daily_summary():
    summary = "Daily RSS Summary:\n"
    for rss_feed_url in rss_feed_urls:
        feed = fetch_feed(rss_feed_url)
        for entry in feed.entries:
            summary += (
                f"Title: {entry.title}\n"
                f"Link: {entry.link}\n"
                f"Published: {entry.updated}\n\n"
            )
    send_slack_message(summary)


# Schedule tasks
schedule.every(10).minutes.do(check_rss_updates)
schedule.every().day.at("09:00").do(daily_summary)

# Main loop
while True:
    schedule.run_pending()
    time.sleep(1)
