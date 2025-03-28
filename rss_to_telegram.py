import os
import time
import feedparser
import html
import re
import json
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram API credentials and session string from environment variables
API_ID = int(os.getenv('TELEGRAM_API_ID'))
API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION_STRING = os.getenv('TELEGRAM_SESSION_STRING')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

# RSS Feed URL
RSS_FEED_URL = 'https://rss.app/feeds/GlIhLfO4znFdKbiW.xml'

# File to store processed post IDs
PROCESSED_POSTS_FILE = 'processed_posts.json'

# Optional: Affiliate link or any specific link you want to include
AFFILIATE_LINK = 'https://your-affiliate-link.com'

def load_processed_posts():
    """Load the set of processed post IDs from file."""
    if os.path.exists(PROCESSED_POSTS_FILE):
        with open(PROCESSED_POSTS_FILE, 'r') as file:
            return set(json.load(file))
    return set()

def save_processed_post(post_id):
    """Save a new processed post ID to file."""
    processed_posts = load_processed_posts()
    processed_posts.add(post_id)
    with open(PROCESSED_POSTS_FILE, 'w') as file:
        json.dump(list(processed_posts), file)

def extract_image_url(entry):
    """Extract image URL from the RSS entry."""
    # Check for media:content
    media_content = entry.get('media_content', [])
    if media_content:
        return media_content[0]['url']
    
    # Check for image in the description
    if 'description' in entry:
        description = html.unescape(entry.description)
        img_match = re.search(r'<img.*?src="(.*?)".*?>', description)
        if img_match:
            return img_match.group(1)
    
    return None

def main():
    """Main function to monitor RSS feed and send new posts to Telegram."""
    # Initialize Telegram client with session string
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    client.start()
    
    processed_posts = load_processed_posts()
    
    while True:
        feed = feedparser.parse(RSS_FEED_URL)
        new_entries = []

        for entry in feed.entries:
            post_id = entry.id if 'id' in entry else entry.link
            if post_id not in processed_posts:
                new_entries.append(entry)
            else:
                break  # Assumes entries are in reverse chronological order

        # Process new entries in reverse order to maintain chronological sequence
        for entry in reversed(new_entries):
            post_id = entry.id if 'id' in entry else entry.link
            title = entry.title
            image_url = extract_image_url(entry)
            
            # Construct the message without any links
            caption = f"{title}"
            
            # Optional: Append the affiliate link if specified
            if AFFILIATE_LINK:
                caption += f"\n\nMore details: {AFFILIATE_LINK}"

            if image_url:
                client.send_file(CHANNEL_ID, image_url, caption=caption)
            else:
                client.send_message(CHANNEL_ID, caption)

            save_processed_post(post_id)
            print(f"Processed post: {title}")

        print("Waiting for 30 minutes before checking for new posts...")
        time.sleep(1800)  # Wait for 30 minutes

if __name__ == "__main__":
    main()
