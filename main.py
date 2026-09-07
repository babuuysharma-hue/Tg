import asyncio
import logging
import os
from threading import Thread
from flask import Flask
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl import types
from telethon.tl.types import User
from telegram import (
    Update, 
    ReplyKeyboardMarkup, 
    KeyboardButton,
    KeyboardButtonRequestUsers,
    KeyboardButtonRequestChat
)
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    CommandHandler, 
    MessageHandler, 
    filters
)

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

MAIN_REPLY_KEYBOARD = ReplyKeyboardMarkup([
    [
        KeyboardButton("👤 My Profile")
    ],
    [
        KeyboardButton("👤 User", request_users=KeyboardButtonRequestUsers(request_id=1)),
        KeyboardButton("⭐ Premium", request_users=KeyboardButtonRequestUsers(request_id=2, user_is_premium=True)),
        KeyboardButton("👾 Bot", request_users=KeyboardButtonRequestUsers(request_id=3, user_is_bot=True))
    ],
    [
        KeyboardButton("👥 Group", request_chat=KeyboardButtonRequestChat(request_id=4, chat_is_channel=False)),
        KeyboardButton("📢 Channel", request_chat=KeyboardButtonRequestChat(request_id=5, chat_is_channel=True))
    ]
], resize_keyboard=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Welcome to Info Bot!</b>\n\n"
        "Click buttons to inspect users through the target bot.",
        parse_mode='HTML',
        reply_markup=MAIN_REPLY_KEYBOARD
    )

async def handle_incoming_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    target_payload = None

    # Check what user sent or shared
    if message.text == "👤 My Profile":
        target_payload = f"tg://user?id={message.from_user.id}"
    elif message.users_shared:
        user_id = message.users_shared.user_ids[0]
        target_payload = f"tg://user?id={user_id}"
    elif message.chats_shared:
        chat_id = message.chats_shared.chat_id
        target_payload = str(chat_id)
    elif message.reply_to_message:
        replied = message.reply_to_message
        if replied.forward_from:
            target_payload = f"tg://user?id={replied.forward_from.id}"
        elif replied.from_user:
            target_payload = f"tg://user?id={replied.from_user.id}"
        elif replied.text:
            target_payload = replied.text.strip()
    elif message.forward_from:
        target_payload = f"tg://user?id={message.forward_from.id}"
    elif message.contact:
        target_payload = f"tg://user?id={message.contact.user_id}"
    elif message.text:
        text_content = message.text.strip()
        if not text_content.startswith("/"):
            if text_content.isdigit():
                target_payload = f"tg://user?id={text_content}"
            else:
                target_payload = text_content

    if not target_payload:
        await message.reply_text(
            "⚠️ Please use the buttons below or send an ID/Username/Link.",
            reply_markup=MAIN_REPLY_KEYBOARD
        )
        return

    try:
        # Send the exact link/payload format directly to the target bot via Userbot session
        await client.send_message(TARGET_BOT_USERNAME, target_payload)
        
        # Wait for target bot to reply
        await asyncio.sleep(2.5)
        
        # Fetch the latest response from target bot and send back to the user in official bot
        async for msg in client.iter_messages(TARGET_BOT_USERNAME, limit=1):
            if msg and msg.text:
                await message.reply_text(msg.text, reply_markup=MAIN_REPLY_KEYBOARD)
                return

        await message.reply_text("⚠️ Target bot did not reply in time.", reply_markup=MAIN_REPLY_KEYBOARD)
            
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)[:100]}", reply_markup=MAIN_REPLY_KEYBOARD)

async def main():
    global app
    await client.start()
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_incoming_content))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    asyncio.run(main())














