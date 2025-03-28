import os
import feedparser
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

# Environment variables
RSS_FEED_URL = os.getenv('RSS_FEED_URL')
API_ID = int(os.getenv('TELEGRAM_API_ID'))
API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION_STRING = os.getenv('TELEGRAM_SESSION_STRING')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

# State tracking
LAST_POST_FILE = 'last_post.txt'

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ RSS Telegram Bot is Running!"

async def rss_worker():
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()

    while True:
        feed = feedparser.parse(RSS_FEED_URL)

        if feed.entries:
            latest_entry = feed.entries[0]
            latest_entry_id = latest_entry.get('id', latest_entry.link)

            if not os.path.exists(LAST_POST_FILE):
                await send_entry(client, latest_entry)
                with open(LAST_POST_FILE, 'w') as file:
                    file.write(latest_entry_id)
                print("✅ First run, sent latest post.")
            else:
                with open(LAST_POST_FILE, 'r') as file:
                    last_posted_id = file.read().strip()

                if latest_entry_id != last_posted_id:
                    await send_entry(client, latest_entry)
                    with open(LAST_POST_FILE, 'w') as file:
                        file.write(latest_entry_id)
                    print("✅ New post sent.")
                else:
                    print("ℹ️ No new posts found.")

        else:
            print("⚠️ RSS feed empty/unavailable.")

        # Check RSS every hour
        await asyncio.sleep(3600)

async def send_entry(client, entry):
    caption = entry.title.strip()

    if 'media_content' in entry:
        image_url = entry.media_content[0]['url']
        await client.send_file(CHANNEL_ID, image_url, caption=caption)
    elif 'links' in entry and entry.links[0].type.startswith('image'):
        image_url = entry.links[0].href
        await client.send_file(CHANNEL_ID, image_url, caption=caption)
    else:
        await client.send_message(CHANNEL_ID, caption)

def run_asyncio_loop():
    asyncio.run(rss_worker())

if __name__ == '__main__':
    # Run RSS Telegram worker in a separate thread
    thread = Thread(target=run_asyncio_loop)
    thread.start()

    # Run Flask web server on Render's expected port
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
