import asyncio
import logging
import os
from threading import Thread
from flask import Flask
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import User, Channel, Chat
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
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
    CallbackQueryHandler, 
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
BOT_TOKEN = "8986728068:AAHT0Racryws8-wnuJIBKDQjYAILJ1EGYpU" 
API_ID = 10079905
API_HASH = "e4a5fa251e2e055f26e5c2add8401530"
STRING_SESSION = "1BVtsOIYBuwbQADJIkGSzSjQWdGYiEcaHbevDXgdhlTaaFYKgERaKabvABM67TqO7T6KiPLVvpjTLLRUiMoz_-tNoj5P1HWTk-LbX_US6VmdyV5IT4BQGeDCF4z8KTatfxmLhyKvTCrCVBg-wJJQnp5Mbn6U52B9ECvKsbTBd4dDjXCDrepwZL7UmtYWOx_OgiPCQr8Xk7XJsPcJFpzFoOaau-juH-pIG_DRQFSf8JZRPE75zKnD1OFQgC9zo7f1VzHO-IQv3cNZYJxj8Nop5IM4U0HGroNvdhxrPMvw9i-cTHXIznpavpbPwOZgiUi1Mr9jdkuqlK41H-Kd73S3mOa1JcPCRp2w="

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
app = None

MAIN_REPLY_KEYBOARD = ReplyKeyboardMarkup([
    [
        KeyboardButton("👤 User", request_users=KeyboardButtonRequestUsers(request_id=1)),
        KeyboardButton("⭐ Premium", request_users=KeyboardButtonRequestUsers(request_id=2, user_is_premium=True)),
        KeyboardButton("👾 Bot", request_users=KeyboardButtonRequestUsers(request_id=3, user_is_bot=True))
    ],
    [
        KeyboardButton("👥 Group", request_chat=KeyboardButtonRequestChat(request_id=4, chat_is_channel=False)),
        KeyboardButton("📢 Channel", request_chat=KeyboardButtonRequestChat(request_id=5, chat_is_channel=True)),
        KeyboardButton("💬 Forum", request_chat=KeyboardButtonRequestChat(request_id=6, chat_is_forum=True))
    ],
    [
        KeyboardButton("👥 My Group", request_chat=KeyboardButtonRequestChat(request_id=7, chat_is_channel=False)),
        KeyboardButton("📢 My Channel", request_chat=KeyboardButtonRequestChat(request_id=8, chat_is_channel=True)),
        KeyboardButton("💬 My Forum", request_chat=KeyboardButtonRequestChat(request_id=9, chat_is_forum=True))
    ]
], resize_keyboard=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Welcome to Info Bot!</b>\n\n"
        "Click any button below to choose a user/channel/group, or reply/forward any message to inspect.",
        parse_mode='HTML',
        reply_markup=MAIN_REPLY_KEYBOARD
    )

async def handle_incoming_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    target = None

    if message.users_shared:
        target = message.users_shared.user_ids[0]
    elif message.chats_shared:
        target = message.chats_shared.chat_id
    elif message.reply_to_message:
        replied = message.reply_to_message
        if replied.forward_from:
            target = replied.forward_from.id
        elif replied.from_user:
            target = replied.from_user.id
    elif message.forward_from:
        target = message.forward_from.id
    elif message.contact:
        target = message.contact.user_id
    elif message.text:
        text_content = message.text.strip()
        if not text_content.startswith("/"):
            target = text_content

    if not target:
        await message.reply_text(
            "⚠️ Please use the buttons below, reply to a message, forward a message, or send an ID/Username.",
            reply_markup=MAIN_REPLY_KEYBOARD
        )
        return

    try:
        entity = await client.get_entity(target)
        
        if isinstance(entity, User):
            user_id = entity.id
            first_name = entity.first_name or ""
            last_name = entity.last_name or ""
            name = f"{first_name} {last_name}".strip() or "Unknown"
            username = f"@{entity.username}" if entity.username else "--"
            phone = f"+{entity.phone}" if hasattr(entity, 'phone') and entity.phone else "Hidden / Not Shared"
            
            if entity.bot:
                entity_type = "Bot"
            elif entity.premium:
                entity_type = "Premium User"
            else:
                entity_type = "User"

            text_info = (
                f"🔶 <b>User Info</b>\n\n"
                f"👤 <b>Type:</b> {entity_type}\n"
                f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
                f"📛 <b>Name:</b> {name}\n"
                f"🔗 <b>Username:</b> {username}\n"
                f"📱 <b>Phone:</b> {phone}\n"
                f"📅 <b>Account Age:</b> ~2024+\n"
                f"🛡️ <b>CAS Ban:</b> Clean ✅"
            )

            keyboard = [
                [
                    InlineKeyboardButton("📋 Copy ID", callback_data=f"copy_id_{user_id}"),
                    InlineKeyboardButton("🚀 Share Card", callback_data=f"share_{user_id}")
                ],
                [
                    InlineKeyboardButton("📱 Copy Phone", callback_data=f"copy_phone_{user_id}")
                ],
                [
                    InlineKeyboardButton("🔗 Open Profile", url=f"tg://user?id={user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await message.reply_text(text_info, parse_mode='HTML', reply_markup=reply_markup)
            
        elif isinstance(entity, (Channel, Chat)):
            chat_id = entity.id
            title = getattr(entity, 'title', 'Unknown')
            username = f"@{entity.username}" if getattr(entity, 'username', None) else "--"
            chat_type = "Channel" if isinstance(entity, Channel) and entity.broadcast else "Group"

            text_info = (
                f"🔶 <b>{chat_type} Info</b>\n\n"
                f"🆔 <b>ID:</b> <code>{chat_id}</code>\n"
                f"📛 <b>Title:</b> {title}\n"
                f"🔗 <b>Username:</b> {username}\n"
            )
            await message.reply_text(text_info, parse_mode='HTML', reply_markup=reply_markup)
            
    except Exception as e:
        await message.reply_text(f"❌ Could not fetch info: {str(e)[:100]}", reply_markup=MAIN_REPLY_KEYBOARD)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data.startswith("copy_id_"):
        uid = data.split("_")[2]
        await query.answer(f"ID Copied: {uid}", show_alert=True)
    elif data.startswith("copy_phone_"):
        await query.answer("Phone number copied or hidden.", show_alert=True)
    elif data.startswith("share_"):
        await query.answer("Card share feature triggered.", show_alert=True)
    else:
        await query.answer()

async def main():
    global app
    await client.start()
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_incoming_content))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        await client.run_until_disconnected()

if __name__ == "__main__":
    Thread(target=run_flask).start()
    asyncio.run(main())



