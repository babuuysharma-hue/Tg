import asyncio
import logging
import os
from threading import Thread
from flask import Flask
from telethon import TelegramClient
from telethon.sessions import StringSession
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Flask server to keep Render free web service alive
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    print("Keep-alive ping received!")
    return "Bot is running live!"

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

client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
app = None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Welcome to Info Bot!</b>\n\n"
        "Send any user link, username, or text, and I will forward it to the target bot.",
        parse_mode='HTML'
    )

async def handle_incoming_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    text_content = message.text.strip()
    if text_content.startswith("/"):
        return

    try:
        # Send the exact text/link received from the user directly to the target bot via Userbot
        await client.send_message(TARGET_BOT_USERNAME, text_content)
        
        # Wait for target bot to reply
        await asyncio.sleep(2.5)
        
        # Fetch the latest response from target bot and send back to the user
        async for msg in client.iter_messages(TARGET_BOT_USERNAME, limit=1):
            if msg and msg.text:
                await message.reply_text(msg.text)
                return

        await message.reply_text("⚠️ Target bot did not reply in time.")
            
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)[:100]}")

async def main():
    global app
    await client.start()
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_incoming_content))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    asyncio.run(main())















