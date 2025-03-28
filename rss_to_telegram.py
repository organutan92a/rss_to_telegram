import os
import asyncio
import feedparser
import requests
from io import BytesIO
from telethon import TelegramClient
from telethon.sessions import StringSession

# Environment vars are already set correctly
RSS_FEED_URL = os.getenv('RSS_FEED_URL')
CHANNEL_ID = int(os.getenv('TELEGRAM_CHANNEL_ID'))
SESSION_STRING = os.getenv('TELEGRAM_SESSION_STRING')
API_ID = int(os.getenv('TELEGRAM_API_ID'))
API_HASH = os.getenv('TELEGRAM_API_HASH')
LAST_POST_FILE = 'last_post.txt'

async def send_image(client, entry):
    caption = entry.title.strip()

    image_url = None
    if 'media_content' in entry:
        image_url = entry.media_content[0]['url']
    elif 'links' in entry and entry.links[0].type.startswith('image'):
        image_url = entry.links[0].href

    if image_url:
        response = requests.get(image_url)
        img_bytes = BytesIO(response.content)
        img_bytes.name = 'image.jpg'

        await client.send_file(
            CHANNEL_ID,
            file=img_bytes,
            caption=caption,
            force_document=False
        )
    else:
        await client.send_message(CHANNEL_ID, caption)

async def rss_worker():
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()

    posted_ids = set()

    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE, 'r') as file:
            posted_ids = set(file.read().splitlines())

    while True:
        feed = feedparser.parse(RSS_FEED_URL)

        if feed.entries:
            latest_entry = feed.entries[0]
            latest_entry_id = latest_entry.get('id', latest_entry.link)

            if latest_entry_id not in posted_ids:
                await send_image(client, latest_entry)
                posted_ids.add(latest_entry_id)

                with open(LAST_POST_FILE, 'w') as file:
                    file.write('\n'.join(posted_ids))

                print(f"✅ Posted new entry: {latest_entry_id}")
            else:
                print("ℹ️ No new post detected. Skipping.")
        else:
            print("⚠️ RSS feed is empty or unavailable.")

        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(rss_worker())


