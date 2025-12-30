"""
Script to get file IDs directly from your bot by having it receive files from the channel.

This script will:
1. Use your bot to forward messages from the channel to itself
2. Extract the bot's own file IDs from those messages
3. Create a CSV with bot-compatible file IDs
"""
import asyncio
import pandas as pd
from telegram import Bot
from telegram.error import TelegramError

# Configuration
BOT_TOKEN = '8365146329:AAFbijjTj7pJoprQLee6rBDUTC-SrDeeogQ'
CHANNEL_USERNAME = '@examlanka'  # Your channel
CHAT_ID = None  # Will be set to bot's chat with itself or a private chat

async def get_bot_file_ids():
    """Get file IDs by having the bot access files from the channel."""
    bot = Bot(token=BOT_TOKEN)
    
    # Get bot info
    bot_info = await bot.get_me()
    print(f"Bot: @{bot_info.username} ({bot_info.first_name})")
    
    # For a bot to get file IDs, it needs to receive the files
    # Option 1: Forward messages from channel to bot's private chat
    # Option 2: Use getUpdates to get messages the bot receives
    
    print("\n⚠️  This approach requires the bot to receive the files.")
    print("Options:")
    print("1. Forward files from channel to your bot")
    print("2. Add bot as admin to channel and use getUpdates")
    print("\nAlternatively, use the fix_index.py script but ensure:")
    print("- Your bot is added to the @examlanka channel")
    print("- The bot has access to view/download files")
    
    # Try to get recent updates
    try:
        updates = await bot.get_updates(limit=10)
        print(f"\nFound {len(updates)} recent updates")
        
        file_data = []
        for update in updates:
            if update.message and update.message.document:
                doc = update.message.document
                file_id = doc.file_id
                file_name = doc.file_name or f"file_{doc.file_unique_id}"
                file_data.append({
                    "File Name": file_name,
                    "File ID": file_id
                })
                print(f"✓ Found: {file_name} -> {file_id[:30]}...")
        
        if file_data:
            df = pd.DataFrame(file_data)
            df.to_csv('bot_file_ids.csv', index=False)
            print(f"\n✅ Saved {len(file_data)} file IDs to bot_file_ids.csv")
        else:
            print("\n⚠️  No files found in recent updates.")
            print("Forward some files from the channel to your bot and try again.")
            
    except TelegramError as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(get_bot_file_ids())

