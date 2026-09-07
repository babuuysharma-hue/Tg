import asyncio
import logging
import os
from threading import Thread
from flask import Flask
from telethon import TelegramClient
from telethon.sessions import StringSession
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, KeyboardButtonRequestUser, KeyboardButtonRequestChat
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Flask server for Render keep-alive
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
    # Creating interactive request buttons so Telegram sends proper user/chat ID data
    keyboard = [
        [
            KeyboardButton("👤 Select User", request_user=KeyboardButtonRequestUser(request_id=1, user_is_bot=False)),
            KeyboardButton("🤖 Select Bot", request_user=KeyboardButtonRequestUser(request_id=2, user_is_bot=True))
        ],
        [
            KeyboardButton("📢 Select Channel", request_chat=KeyboardButtonRequestChat(request_id=3, chat_is_channel=True)),
            KeyboardButton("👥 Select Group", request_chat=KeyboardButtonRequestChat(request_id=4, chat_is_channel=False))
        ]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "👋 <b>Welcome to Info Bot!</b>\n\n"
        "📌 <b>How to use:</b>\n"
        "1️⃣ Tap any button below to share a profile safely.\n"
        "⚡ Session account will instantly fetch info from the target bot!",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    
    if not message:
        return
        
    target_uid = None
    user_name = "User"
    
    # 1. Capture user ID from interactive request buttons
    if message.user_shared:
        target_uid = message.user_shared.user_id
        user_name = f"User_{target_uid}"
        logger.info(f"✅ Captured via user_shared: {target_uid}")
        
    # 2. Capture chat/channel ID from interactive request buttons
    elif message.chat_shared:
        target_uid = message.chat_shared.chat_id
        user_name = f"Chat_{target_uid}"
        logger.info(f"✅ Captured via chat_shared: {target_uid}")
        
    # 3. Fallback for text input / user ID
    elif message.text and not message.text.startswith("/"):
        text = message.text.strip()
        if text.isdigit():
            target_uid = int(text)
        user_name = text

    if not target_uid:
        await message.reply_text("⚠️ Please select a profile using the keyboard buttons below.")
        return
        
    logger.info(f"Extracted Target ID: {target_uid}, Name: {user_name}")
    await message.reply_text("⏳ Processing command through session account...")
    
    try:
        # Format as /tg <user_id> and send to the target bot via session
        command_text = f"/tg {target_uid}"
        await userbot.send_message(TARGET_BOT_USERNAME, command_text)
        logger.info(f"Sent command {command_text} to target bot")
        
        # Wait for target bot response
        await asyncio.sleep(5)
        
        async for response in userbot.iter_messages(TARGET_BOT_USERNAME, limit=1):
            if response and response.text and response.text != command_text:
                logger.info(f"Got response: {response.text[:100]}...")
                await message.reply_text(
                    f"📊 <b>User Info for {user_name}:</b>\n\n{response.text}",
                    parse_mode='HTML'
                )
                return
        
        await message.reply_text("⚠️ No response from target bot. Make sure session account has started @ExposeInfo_Bot once.")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await message.reply_text(f"❌ Error: {str(e)[:100]}")

async def main():
    global bot_app
    
    logger.info("Starting userbot session...")
    await userbot.start()
    logger.info("Userbot session started successfully!")
    
    # Start Flask server thread
    Thread(target=run_flask).start()
    
    # Setup official telegram bot
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start_command))
    bot_app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    
    logger.info("Starting official bot polling...")
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    
    logger.info("Everything is running smoothly!")
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())




















