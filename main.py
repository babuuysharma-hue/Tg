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
logger = logging.getLogger(__name__)

# Initialize userbot
userbot = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
bot_app = None

# Store user message to reply later
user_message_cache = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Welcome to Info Bot!</b>\n\n"
        "📌 <b>How to use:</b>\n"
        "1️⃣ Share any user's profile to this bot\n"
        "2️⃣ Forward any user's message\n\n"
        "⚡ I'll fetch info from target bot and send back!",
        parse_mode='HTML'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = update.effective_user.id
    
    if not message:
        return
    
    logger.info(f"===== NEW MESSAGE from {user_id} =====")
    logger.info(f"Message text: {message.text}")
    logger.info(f"Has forward_from: {message.forward_from}")
    
    # Store user message for response
    user_message_cache[user_id] = message
    
    # ==========================================
    # CASE 1: USER SHARED PROFILE (Forward)
    # ==========================================
    if message.forward_from:
        try:
            forwarded_user = message.forward_from
            logger.info(f"✅ Forwarded user: {forwarded_user.first_name} (ID: {forwarded_user.id})")
            
            # Send acknowledgement to user
            await message.reply_text("⏳ Processing... Forwarding to target bot...")
            
            # Get target bot entity
            target_bot = await userbot.get_entity(TARGET_BOT_USERNAME)
            logger.info(f"✅ Target bot entity: {target_bot.id}")
            
            # 🔥 CRITICAL: Forward the message to target bot using userbot
            await userbot.forward_messages(
                entity=target_bot,
                messages=message.id,
                from_peer=message.chat_id
            )
            logger.info("✅ Message forwarded to target bot")
            
            # Wait for target bot response
            await asyncio.sleep(4)
            
            # Get target bot's response
            async for response in userbot.iter_messages(TARGET_BOT_USERNAME, limit=1):
                if response and response.text:
                    logger.info(f"✅ Target bot response: {response.text[:100]}...")
                    await message.reply_text(
                        f"📊 <b>User Info:</b>\n\n{response.text}",
                        parse_mode='HTML'
                    )
                    return
            
            # If no response
            await message.reply_text("⚠️ Target bot did not respond. Try again.")
            return
            
        except Exception as e:
            logger.error(f"❌ Error in forward: {e}")
            await message.reply_text(f"❌ Error: {str(e)[:100]}")
            return
    
    # ==========================================
    # CASE 2: USER SENT TEXT (username/name)
    # ==========================================
    if message.text and not message.text.startswith("/"):
        text = message.text.strip()
        logger.info(f"📝 Processing text: {text}")
        
        # Try to find user
        try:
            found_user = None
            
            # Search by username
            if text.startswith("@"):
                username = text.replace("@", "")
                try:
                    found_user = await userbot.get_entity(text)
                    logger.info(f"✅ Found by username: {found_user.first_name}")
                except:
                    pass
            
            # If not found, search by name
            if not found_user:
                async for user in userbot.iter_participants(limit=100):
                    if user.first_name and text.lower() in user.first_name.lower():
                        found_user = user
                        logger.info(f"✅ Found by first name: {user.first_name}")
                        break
                    elif user.last_name and text.lower() in user.last_name.lower():
                        found_user = user
                        logger.info(f"✅ Found by last name: {user.last_name}")
                        break
            
            if found_user:
                await message.reply_text(f"⏳ Found user: {found_user.first_name}. Fetching info...")
                
                # Send to target bot
                target_bot = await userbot.get_entity(TARGET_BOT_USERNAME)
                
                # Send user info to target bot
                await userbot.send_message(
                    target_bot,
                    f"User: {found_user.first_name} {found_user.last_name or ''}\nID: {found_user.id}"
                )
                logger.info(f"✅ Sent user info to target bot: {found_user.id}")
                
                await asyncio.sleep(3)
                
                # Get response
                async for response in userbot.iter_messages(TARGET_BOT_USERNAME, limit=1):
                    if response and response.text:
                        await message.reply_text(
                            f"📊 <b>Info for {found_user.first_name}:</b>\n\n{response.text}",
                            parse_mode='HTML'
                        )
                        return
            else:
                await message.reply_text("⚠️ User not found. Please share their profile directly.")
                
        except Exception as e:
            logger.error(f"❌ Error in text processing: {e}")
            await message.reply_text(f"❌ Error: {str(e)[:100]}")
        return
    
    # ==========================================
    # CASE 3: FORWARD FROM CHAT/GROUP
    # ==========================================
    if message.forward_from_chat:
        try:
            logger.info("✅ Forwarded from chat")
            await message.reply_text("⏳ Processing forwarded message...")
            
            target_bot = await userbot.get_entity(TARGET_BOT_USERNAME)
            await userbot.forward_messages(
                entity=target_bot,
                messages=message.id,
                from_peer=message.chat_id
            )
            logger.info("✅ Forwarded to target bot")
            
            await asyncio.sleep(3)
            
            async for response in userbot.iter_messages(TARGET_BOT_USERNAME, limit=1):
                if response and response.text:
                    await message.reply_text(
                        f"📊 <b>Info:</b>\n\n{response.text}",
                        parse_mode='HTML'
                    )
                    return
                    
        except Exception as e:
            logger.error(f"❌ Error in chat forward: {e}")
            await message.reply_text(f"❌ Error: {str(e)[:100]}")
        return

# ==========================================
# 🔥 LISTEN TO TARGET BOT RESPONSES
# ==========================================
@userbot.on(events.NewMessage(chats=TARGET_BOT_USERNAME))
async def target_bot_listener(event):
    """Listen to target bot and forward response to user"""
    try:
        if not event.message.text:
            return
            
        logger.info(f"🎯 TARGET BOT RESPONSE: {event.message.text[:100]}...")
        
        # Find the user who requested
        if user_message_cache:
            # Get the last user who sent message
            last_user_id = list(user_message_cache.keys())[-1]
            user_message = user_message_cache[last_user_id]
            
            # Send response to user via official bot
            await bot_app.bot.send_message(
                chat_id=last_user_id,
                text=f"📊 <b>Target Bot Response:</b>\n\n{event.message.text}",
                parse_mode='HTML',
                reply_to_message_id=user_message.message_id
            )
            logger.info(f"✅ Response sent to user {last_user_id}")
            
            # Remove from cache after sending
            user_message_cache.pop(last_user_id, None)
            
    except Exception as e:
        logger.error(f"❌ Listener error: {e}")

async def main():
    global bot_app
    
    logger.info("🚀 Starting userbot...")
    await userbot.start()
    logger.info("✅ Userbot started!")
    
    # Start Flask
    Thread(target=run_flask).start()
    logger.info("✅ Flask started!")
    
    # Setup official bot
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start_command))
    bot_app.add_handler(MessageHandler(filters.ALL, handle_message))
    
    logger.info("🚀 Starting bot...")
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    
    logger.info("✅ Bot is running! Waiting for messages...")
    
    # Keep running
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())















