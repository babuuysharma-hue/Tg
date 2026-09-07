import asyncio
import logging
import os
from threading import Thread
from flask import Flask
from telethon import TelegramClient
from telethon.sessions import StringSession
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Flask server for keeping the app alive on hosting platforms
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
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize userbot session client
userbot = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
bot_app = None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Welcome to Info Bot!</b>\n\n"
        "📌 <b>How to use:</b>\n"
        "1️⃣ Share any profile mention to this bot\n\n"
        "⚡ Session account will convert it into a profile link and fetch info!",
        parse_mode='HTML'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = update.effective_user.id
    
    if not message:
        return
        
    profile_link = None
    user_name = "User"
    
    # Extract profile link and user name from message entities (mention / text_link)
    if message.entities:
        for entity in message.entities:
            if entity.type == "text_mention":
                uid = entity.user.id
                user_name = entity.user.first_name
                profile_link = f"tg://user?id={uid}"
                break
            elif entity.type == "text_link":
                profile_link = entity.url
                user_name = message.text[entity.offset:entity.offset+entity.length] if message.text else "User"
                break
            elif entity.type == "url":
                offset = entity.offset
                length = entity.length
                profile_link = message.text[offset:offset+length]
                user_name = profile_link
                break
                
    # Check if a contact card is shared
    if not profile_link and message.contact:
        if message.contact.user_id:
            profile_link = f"tg://user?id={message.contact.user_id}"
            user_name = message.contact.first_name
            
    # Check if a message is forwarded
    if not profile_link and message.forward_from:
        user_name = message.forward_from.first_name or "User"
        if message.forward_from.username:
            profile_link = f"https://t.me/{message.forward_from.username}"
        elif message.forward_from.id:
            profile_link = f"tg://user?id={message.forward_from.id}"
            
    # Fallback to plain text if no entity found
    if not profile_link and message.text and not message.text.startswith("/"):
        text = message.text.strip()
        user_name = text
        if text.startswith("@"):
            profile_link = f"https://t.me/{text.lstrip('@')}"
        elif "t.me/" in text:
            profile_link = text if text.startswith("http") else f"https://{text}"
        else:
            if text.isdigit():
                profile_link = f"tg://user?id={text}"
            else:
                profile_link = f"https://t.me/{text.lstrip('@')}"
                
    if not profile_link:
        await message.reply_text("⚠️ Please share a valid profile mention or link.")
        return
        
    logger.info(f"📩 Extracted Name: {user_name}, Profile Link: {profile_link}")
    await message.reply_text("⏳ Processing profile link through session account...")
    
    try:
        target_bot = await userbot.get_entity(TARGET_BOT_USERNAME)
        logger.info(f"✅ Target bot found: {target_bot.id}")
        
        # Send the extracted profile link directly via userbot to target bot
        await userbot.send_message(target_bot, profile_link)
        logger.info(f"✅ Sent profile link to target bot: {profile_link}")
        
        # Wait for target bot response
        await asyncio.sleep(5)
        
        async for response in userbot.iter_messages(TARGET_BOT_USERNAME, limit=1):
            if response and response.text and response.text != profile_link:
                logger.info(f"✅ Got response from target bot: {response.text[:100]}...")
                await message.reply_text(
                    f"📊 <b>User Info for {user_name}:</b>\n\n{response.text}",
                    parse_mode='HTML'
                )
                return
        
        await message.reply_text("⚠️ No response from target bot.")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        await message.reply_text(f"❌ Error: {str(e)[:100]}")

async def main():
    global bot_app
    
    logger.info("🚀 Starting userbot session...")
    await userbot.start()
    logger.info("✅ Userbot session started successfully!")
    
    # Start Flask server thread
    Thread(target=run_flask).start()
    
    # Setup official telegram bot
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start_command))
    bot_app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    
    logger.info("🚀 Starting official bot polling...")
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    
    logger.info("✅ Everything is running smoothly!")
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
















