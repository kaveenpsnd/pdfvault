"""
Extract file IDs from your bot's perspective.

This script requires:
1. Your bot added to @examlanka channel
2. Forward messages from channel to your bot (or run bot as admin)

Then run this script to extract the bot's file IDs.
"""
import asyncio
import pandas as pd
from telegram import Bot

BOT_TOKEN = '8365146329:AAFbijjTj7pJoprQLee6rBDUTC-SrDeeogQ'

async def extract_bot_file_ids():
    bot = Bot(token=BOT_TOKEN)
    bot_info = await bot.get_me()
    print(f"Bot: @{bot_info.username}\n")
    
    print("📥 Getting messages the bot has received...")
    updates = await bot.get_updates(limit=1000, allowed_updates=['message'])
    
    file_data = []
    seen_file_ids = set()
    
    for update in updates:
        msg = update.message
        if msg and msg.document:
            doc = msg.document
            file_id = doc.file_id
            file_name = doc.file_name or f"file_{doc.file_unique_id}.pdf"
            
            if file_id not in seen_file_ids:
                seen_file_ids.add(file_id)
                file_data.append({
                    "File Name": file_name,
                    "File ID": file_id
                })
                print(f"✓ {file_name[:60]}")
    
    if file_data:
        df = pd.DataFrame(file_data)
        output = 'master_index_bot_ids.csv'
        df.to_csv(output, index=False)
        print(f"\n✅ Extracted {len(file_data)} file IDs")
        print(f"📁 Saved to: {output}")
        print(f"💡 Replace master_index.csv with this file")
    else:
        print("\n⚠️  No files found!")
        print("\nTo get file IDs:")
        print("1. Add your bot to @examlanka channel")
        print("2. Forward files from channel to your bot")
        print("   (You can forward multiple at once)")
        print("3. Run this script again")

if __name__ == "__main__":
    asyncio.run(extract_bot_file_ids())

