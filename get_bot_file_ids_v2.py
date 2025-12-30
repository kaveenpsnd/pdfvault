"""
Get file IDs from your bot's perspective by forwarding channel messages to the bot.

Steps:
1. Add your bot to @examlanka channel (as admin or member)
2. Forward messages from channel to your bot (or use this script if bot is admin)
3. This script will extract the bot's file IDs from those messages
"""
import asyncio
import pandas as pd
from telegram import Bot
from telegram.error import TelegramError

# Configuration
BOT_TOKEN = '8365146329:AAFbijjTj7pJoprQLee6rBDUTC-SrDeeogQ'
CHANNEL_USERNAME = '@examlanka'

async def get_file_ids_from_bot():
    """Get file IDs by having bot access channel messages."""
    bot = Bot(token=BOT_TOKEN)
    
    bot_info = await bot.get_me()
    print(f"Bot: @{bot_info.username}")
    
    # Get the channel chat
    try:
        # Try to get channel info (bot must be in channel)
        channel = await bot.get_chat(CHANNEL_USERNAME)
        print(f"Channel: {channel.title}")
    except TelegramError as e:
        print(f"❌ Cannot access channel: {e}")
        print("\n💡 Make sure:")
        print("   1. Your bot is added to @examlanka channel")
        print("   2. Bot has permission to read messages")
        return
    
    # Get recent messages from channel
    # Note: Bots can't directly get channel history, but we can use getUpdates
    # if the bot has received forwarded messages
    
    print("\n📥 Checking for messages the bot has received...")
    print("(Forward some files from channel to your bot first)")
    
    updates = await bot.get_updates(limit=100, allowed_updates=['message'])
    
    file_data = []
    seen_files = set()
    
    for update in updates:
        msg = update.message
        if msg and msg.document:
            doc = msg.document
            file_id = doc.file_id
            file_name = doc.file_name or f"document_{doc.file_unique_id}"
            
            # Avoid duplicates
            if file_id not in seen_files:
                seen_files.add(file_id)
                file_data.append({
                    "File Name": file_name,
                    "File ID": file_id
                })
                print(f"✓ {file_name[:50]}... -> {file_id[:30]}...")
    
    if file_data:
        df = pd.DataFrame(file_data)
        output_file = 'bot_file_ids.csv'
        df.to_csv(output_file, index=False)
        print(f"\n✅ Saved {len(file_data)} file IDs to {output_file}")
        print(f"💡 Replace master_index.csv with this file")
    else:
        print("\n⚠️  No files found!")
        print("\nTo get file IDs:")
        print("1. Add bot to @examlanka channel")
        print("2. Forward files from channel to your bot")
        print("3. Run this script again")

if __name__ == "__main__":
    asyncio.run(get_file_ids_from_bot())

