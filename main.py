import asyncio
import logging
import os
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Flask server
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

# ==========================================
# 🔑 CREDENTIALS
# ==========================================
BOT_TOKEN = "8947053031:AAEE42KqJFLQKX1NPFps5QqZM1uGWh06898" 
API_ID = 10079905
API_HASH = "e4a5fa251e2e055f26e5c2add8401530"
STRING_SESSION = "1BVtsOIwBu5M1JD_6qhpYIDzzEWfAswiucDVlxbxINPBlR6WOnqCUkSv6K99W2yXeGK-NAGLklagM43oUgOeJj4h0Fkky659-x0Q8k8FJgB2ZXa8o4D_IENbulHdPshh40WRp9q_XuawdwJ0dkEzwL7ibm0h0GSzSo2jq1Nqr95O4VLQENaFuglJ5gFK6l4DBOTHMyDEhr70iNJDi3S-FyzeICmQiytFUE7YwHVaALDXEkrPEPoDc861DdpaxCyYFJ7u30QXp88AIllTohT6khw1dk1cbr2nBulFbQc1iP4_SsFH27i0IqDh4r1tcgT1k_s4j986ns2-r9e12jYd4YUmf7gnxJgg="

TARGET_BOT_USERNAME = "@ExposeInfo_Bot"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize userbot client
userbot = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
bot_app = None

# Store user message IDs to reply later
user_messages = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Welcome to Info Bot!</b>\n\n"
        "📌 <b>How to use:</b>\n"
        "1️⃣ Share any user's profile to this bot\n"
        "2️⃣ Send username (e.g., @username)\n"
        "3️⃣ Send user ID\n"
        "4️⃣ Forward any message\n\n"
        "⚡ I'll fetch info from target bot and send back!",
        parse_mode='HTML'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = update.effective_user.id
    
    if not message:
        return
    
    # Save user's message ID to reply later
    user_messages[user_id] = message.message_id
    
    # CASE 1: Forwarded user profile
    if message.forward_from:
        try:
            forwarded_user = message.forward_from
            user_info = None
            
            # Try to get username first
            if forwarded_user.username:
                user_info = f"@{forwarded_user.username}"
            else:
                # If no username, use ID
                user_info = str(forwarded_user.id)
            
            logging.info(f"Forwarded user: {user_info}")
            
            # Send to target bot using userbot
            await userbot.send_message(TARGET_BOT_USERNAME, user_info)
            
            # Wait for response
            await asyncio.sleep(3)
            
            # Get target bot's latest response
            async for msg in userbot.iter_messages(TARGET_BOT_USERNAME, limit=1):
                if msg and msg.text and not msg.text.startswith("/"):
                    # Send response back to user
                    await message.reply_text(
                        f"📊 <b>User Info:</b>\n\n{msg.text}",
                        parse_mode='HTML'
                    )
                    return
            
            await message.reply_text("⚠️ Target bot did not respond. Try again.")
            return
            
        except Exception as e:
            logging.error(f"Error in forward_from: {e}")
            await message.reply_text(f"❌ Error: {str(e)[:100]}")
            return
    
    # CASE 2: Text message with username or link
    if message.text and not message.text.startswith("/"):
        text = message.text.strip()
        
        # Check if it's a username or Telegram link
        if text.startswith("@") or "t.me/" in text or text.isdigit():
            try:
                await userbot.send_message(TARGET_BOT_USERNAME, text)
                await asyncio.sleep(3)
                
                async for msg in userbot.iter_messages(TARGET_BOT_USERNAME, limit=1):
                    if msg and msg.text and not msg.text.startswith("/"):
                        await message.reply_text(
                            f"📊 <b>Info for {text}:</b>\n\n{msg.text}",
                            parse_mode='HTML'
                        )
                        return
                
                await message.reply_text("⚠️ Target bot did not respond.")
                return
                
            except Exception as e:
                logging.error(f"Error in text message: {e}")
                await message.reply_text(f"❌ Error: {str(e)[:100]}")
                return
        
        # CASE 3: Plain text - forward as-is
        try:
            await userbot.send_message(TARGET_BOT_USERNAME, text)
            await asyncio.sleep(3)
            
            async for msg in userbot.iter_messages(TARGET_BOT_USERNAME, limit=1):
                if msg and msg.text and not msg.text.startswith("/"):
                    await message.reply_text(msg.text)
                    return
            
            await message.reply_text("⚠️ Target bot did not respond.")
            
        except Exception as e:
            logging.error(f"Error in plain text: {e}")
            await message.reply_text(f"❌ Error: {str(e)[:100]}")
        return
    
    # CASE 4: Any other message (like media, etc.)
    if message.forward_from_chat:
        await message.reply_text("⚠️ Please share individual user profiles or send username/ID.")

# ==========================================
# 🔄 Background listener for target bot responses
# ==========================================
@userbot.on(events.NewMessage(chats=TARGET_BOT_USERNAME))
async def target_bot_response_handler(event):
    """Listen to target bot responses and forward to user"""
    try:
        if not event.message.text or event.message.text.startswith("/"):
            return
        
        # Get the last user who requested
        if user_messages:
            last_user_id = list(user_messages.keys())[-1]
            msg_id = user_messages[last_user_id]
            
            # Send response to user via official bot
            await bot_app.bot.send_message(
                chat_id=last_user_id,
                text=f"📊 <b>Response from target bot:</b>\n\n{event.message.text}",
                parse_mode='HTML',
                reply_to_message_id=msg_id
            )
            
            # Clear after sending
            user_messages.pop(last_user_id, None)
            
    except Exception as e:
        logging.error(f"Error in response handler: {e}")

async def main():
    global bot_app
    
    # Start userbot
    await userbot.start()
    logging.info("✅ Userbot started!")
    
    # Start Flask
    Thread(target=run_flask).start()
    
    # Setup official bot
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start_command))
    bot_app.add_handler(MessageHandler(
        filters.TEXT | filters.FORWARDED, 
        handle_message
    ))
    
    # Start bot
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    
    logging.info("✅ Bot is running!")
    
    # Keep running
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())















