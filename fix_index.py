"""
Script to convert Telegram file IDs to Bot API compatible format.

IMPORTANT: This script requires a USER account (your phone number), NOT a bot token.
Bots cannot access channel message history due to Telegram API restrictions.

On first run, you'll be prompted to:
1. Enter your phone number
2. Enter the verification code sent to Telegram
3. Enter your 2FA password (if enabled)
"""
import os
import pandas as pd
import asyncio
from telethon import TelegramClient, utils

# --- CONFIGURATION ---
API_ID = 38232860 
API_HASH = '551f7b73f63908e8753aa13adc33559d'
# Note: This will use YOUR user account (phone number login), not a bot
# Option 1: Use channel username (EASIEST - recommended)
CHANNEL = '@examlanka'  # Channel username (with @)
# Option 2: Use channel ID (must be negative for channels)
# CHANNEL = -1002844545093  # Uncomment and use if username doesn't work
INPUT_CSV = 'master_index.csv'
OUTPUT_CSV = 'master_index_final.csv'

# Use a different session name to avoid bot token session
client = TelegramClient('user_session', API_ID, API_HASH)

async def main():
    print("=" * 60)
    print("IMPORTANT: Enter your PHONE NUMBER, NOT the bot token!")
    print("Format: +1234567890 (with country code)")
    print("=" * 60)
    
    # Start with user account (phone number), not bot token
    # This will prompt for phone number and code on first run
    if not await client.is_user_authorized():
        print("\n📱 You will be prompted to enter your phone number.")
        print("   DO NOT enter the bot token - enter your personal phone number!\n")
    
    await client.start()
    
    # Verify we're using a user account, not a bot
    me = await client.get_me()
    if me.bot:
        print("\n❌ ERROR: Detected bot account!")
        print("This script requires a USER account (your personal Telegram account).")
        print("\nTo fix this:")
        print("1. Close this script")
        print("2. Delete the session file: user_session.session")
        print("3. Run the script again")
        print("4. When prompted, enter your PHONE NUMBER (e.g., +94763815438)")
        print("   NOT the bot token!")
        await client.disconnect()
        return
    
    print(f"\n✓ Logged in as: {me.first_name} {me.last_name or ''} (@{me.username or 'no username'})")
    
    # Load your current CSV
    df = pd.read_csv(INPUT_CSV)
    new_data = []
    
    print("Connecting to channel...")
    try:
        # Try to get the channel entity (supports username or ID)
        entity = await client.get_entity(CHANNEL)
        channel_title = entity.title if hasattr(entity, 'title') else str(CHANNEL)
        print(f"✓ Connected to: {channel_title}")
        
        # Verify it's a channel/chat
        if not hasattr(entity, 'title'):
            print("⚠️  Warning: Entity doesn't appear to be a channel. Continuing anyway...")
            
    except ValueError as e:
        error_msg = str(e)
        print(f"❌ Error accessing channel: {error_msg}")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure you've JOINED the channel with your user account (@kaizishere)")
        print("   2. Check the channel username is correct (case-sensitive)")
        print("   3. If using ID, try the channel username instead (easier)")
        print(f"\n   Current CHANNEL setting: {CHANNEL}")
        print("\n   To find your channel username:")
        print("   - Open the channel in Telegram")
        print("   - The username is in the format: @channelname")
        return
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"\n   Current CHANNEL setting: {CHANNEL}")
        return
    
    print("Fetching Bot-API compatible IDs from your channel...")
    print("This may take a while if the channel has many messages...\n")
    
    # Load existing CSV to match filenames (optional - for verification)
    existing_files = set(df['File Name'].tolist()) if not df.empty else set()
    
    count = 0
    # We iterate through the channel messages to get the 'Bot API' version of the ID
    # Limit to 10000 messages to avoid timeout (adjust if needed)
    print(f"\n📥 Fetching messages from channel...")
    async for message in client.iter_messages(entity, limit=10000):
        if message.document:
            # This is the magic part: Telethon packs the ID into the Bot API format
            bot_api_id = utils.pack_bot_file_id(message.document)
            
            # Get the filename
            filename = message.file.name if message.file.name else f"file_{count}.pdf"
            
            new_data.append({"File Name": filename, "File ID": bot_api_id})
            count += 1
            
            # Show progress
            if count % 10 == 0:
                print(f"Processed {count} files...", end='\r')
            else:
                print(f"✓ {filename[:50]}...")
    
    print(f"\n\nProcessed {count} files total.")

    # Save the new compatible CSV
    if new_data:
        new_df = pd.DataFrame(new_data)
        new_df.to_csv(OUTPUT_CSV, index=False)
        print(f"\n✅ Success! Found {len(new_data)} files.")
        print(f"📁 New CSV saved as: '{OUTPUT_CSV}'")
        print(f"💡 Replace 'master_index.csv' with '{OUTPUT_CSV}' in your Streamlit app.")
    else:
        print("\n⚠️  No files found in the channel. Make sure:")
        print("   - The channel has messages with documents")
        print("   - Your bot has access to the channel")

with client:
    client.loop.run_until_complete(main())