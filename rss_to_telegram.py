import os
import feedparser
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# Load environment variables
RSS_FEED_URL = os.getenv('RSS_FEED_URL')
API_ID = int(os.getenv('TELEGRAM_API_ID'))
API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION_STRING = os.getenv('TELEGRAM_SESSION_STRING')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

# File to keep track of the last posted entry
LAST_POST_FILE = 'last_post.txt'

async def main():
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()

    while True:
        feed = feedparser.parse(RSS_FEED_URL)

        if feed.entries:
            latest_entry = feed.entries[0]

            # Get ID or unique link of the latest entry
            latest_entry_id = latest_entry.get('id', latest_entry.link)

            # Check if last_post.txt exists
            if not os.path.exists(LAST_POST_FILE):
                # First run, send ONLY latest post and save it
                await send_entry(client, latest_entry)
                with open(LAST_POST_FILE, 'w') as file:
                    file.write(latest_entry_id)
                print("✅ First run completed, latest post sent.")
            else:
                # Subsequent runs, check if there's a new entry
                with open(LAST_POST_FILE, 'r') as file:
                    last_posted_id = file.read().strip()

                if latest_entry_id != last_posted_id:
                    # New post found, send it
                    await send_entry(client, latest_entry)
                    with open(LAST_POST_FILE, 'w') as file:
                        file.write(latest_entry_id)
                    print("✅ New post detected and sent.")
                else:
                    print("ℹ️ No new posts found.")

        else:
            print("⚠️ RSS feed is empty or unavailable.")

        # Wait 1 hour (3600 seconds) before checking again
        await asyncio.sleep(3600)

async def send_entry(client, entry):
    # Extract content without links
    caption = entry.title.strip()

    # Check for images in RSS feed
    if 'media_content' in entry:
        image_url = entry.media_content[0]['url']
        await client.send_file(CHANNEL_ID, image_url, caption=caption)
    elif 'links' in entry and entry.links[0].type.startswith('image'):
        image_url = entry.links[0].href
        await client.send_file(CHANNEL_ID, image_url, caption=caption)
    else:
        # If no image, send just the caption
        await client.send_message(CHANNEL_ID, caption)

if __name__ == '__main__':
    asyncio.run(main())
