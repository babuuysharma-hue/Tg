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
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize userbot
userbot = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
bot_app = None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Welcome to Info Bot!</b>\n\n"
        "📌 <b>How to use:</b>\n"
        "1️⃣ Share any user's profile to this bot\n\n"
        "⚡ I'll fetch info and send back!",
        parse_mode='HTML'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = update.effective_user.id
    
    if not message:
        return
    
    logger.info(f"📩 Message from {user_id}")
    logger.info(f"Text: '{message.text}'")
    logger.info(f"Message ID: {message.message_id}")
    logger.info(f"Chat ID: {message.chat_id}")
    logger.info(f"Forward from: {message.forward_from}")
    logger.info(f"Entities: {message.entities}")
    
    # ==========================================
    # 🔥🔥🔥 PROFILE SHARE - FORWARD TO TARGET BOT
    # ==========================================
    if message.text and not message.text.startswith("/"):
        text = message.text.strip()
        
        # Send acknowledgment
        await message.reply_text("⏳ Processing...")
        
        try:
            # 🔥 STEP 1: Target bot entity lo
            target_bot = await userbot.get_entity(TARGET_BOT_USERNAME)
            logger.info(f"✅ Target bot found: {target_bot.id}")
            
            # 🔥 STEP 2: Profile message AS-IS forward karo userbot se
            # YEHI WOH MAGIC HAI - Profile share message forward ho raha hai!
            result = await userbot.forward_messages(
                entity=target_bot,
                messages=message.message_id,
                from_peer=message.chat_id
            )
            logger.info(f"✅ Profile message forwarded to target bot! Result: {result}")
            
            # 🔥 STEP 3: Target bot se response lo
            await asyncio.sleep(5)
            
            async for response in userbot.iter_messages(TARGET_BOT_USERNAME, limit=1):
                if response and response.text:
                    logger.info(f"✅ Got response: {response.text[:100]}...")
                    await message.reply_text(
                        f"📊 <b>User Info:</b>\n\n{response.text}",
                        parse_mode='HTML'
                    )
                    return
            
            await message.reply_text("⚠️ No response from target bot")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}", exc_info=True)
            await message.reply_text(f"❌ Error: {str(e)[:100]}")
        return
    
    # ==========================================
    # FORWARDED USER (Direct forward)
    # ==========================================
    if message.forward_from:
        try:
            forwarded_user = message.forward_from
            logger.info(f"🔄 Forwarded user: {forwarded_user.first_name}")
            
            await message.reply_text("⏳ Processing...")
            
            target_bot = await userbot.get_entity(TARGET_BOT_USERNAME)
            
            await userbot.forward_messages(
                entity=target_bot,
                messages=message.message_id,
                from_peer=message.chat_id
            )
            logger.info("✅ Forwarded to target bot!")
            
            await asyncio.sleep(4)
            
            async for response in userbot.iter_messages(TARGET_BOT_USERNAME, limit=1):
                if response and response.text:
                    await message.reply_text(
                        f"📊 <b>User Info:</b>\n\n{response.text}",
                        parse_mode='HTML'
                    )
                    return
                    
            await message.reply_text("⚠️ No response from target bot")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            await message.reply_text(f"❌ Error: {str(e)[:100]}")
        return
    
    await message.reply_text("⚠️ Please share a profile")

async def main():
    global bot_app
    
    logger.info("🚀 Starting userbot...")
    await userbot.start()
    logger.info("✅ Userbot started!")
    
    # Start Flask
    Thread(target=run_flask).start()
    
    # Setup official bot
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start_command))
    bot_app.add_handler(MessageHandler(filters.ALL, handle_message))
    
    logger.info("🚀 Starting bot...")
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    
    logger.info("✅ Bot is running!")
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())















