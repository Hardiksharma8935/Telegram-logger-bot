import os
import re
import telebot
import time
from telebot import apihelper
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import requests
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID") 

if LOG_CHANNEL_ID:
    LOG_CHANNEL_ID = int(LOG_CHANNEL_ID)

session = requests.Session()
retry_strategy = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

apihelper.CUSTOM_REQUEST_SENDER = lambda method, url, **kwargs: session.request(method, url, **kwargs)
apihelper.CONNECT_TIMEOUT = 30
apihelper.READ_TIMEOUT = 30

bot = telebot.TeleBot(BOT_TOKEN)
USER_DATABASE_FILE = "group_members.txt"
USELESS_WORDS = ["hi", "hello", "ok", "okay", "nice", "thanks", "thank you", "gm", "gn", "bye", "good", "wow"]

if not os.path.exists(USER_DATABASE_FILE):
    with open(USER_DATABASE_FILE, "w") as f:
        pass

print("=== DATA LOGGER BOT INITIALIZED ===", flush=True)

@bot.message_handler(content_types=['new_chat_members'])
def backup_member(message):
    for member in message.new_chat_members:
        if not member.is_bot:
            user_id = str(member.id)
            with open(USER_DATABASE_FILE, "r") as f:
                saved_ids = f.read().splitlines()
                
            if user_id not in saved_ids:
                with open(USER_DATABASE_FILE, "a") as f:
                    f.write(user_id + "\n")
                
                if LOG_CHANNEL_ID:
                    try:
                        bot.send_message(LOG_CHANNEL_ID, f"👤 **Naya Member Joined:**\nNaam: {member.first_name}\nID: `{member.id}`")
                    except Exception as e:
                        print(f"[ERROR] Channel logging failed: {e}", flush=True)

@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'voice'])
def log_everything(message):
    if not LOG_CHANNEL_ID or message.chat.id == LOG_CHANNEL_ID:
        return

    if message.text:
        clean_text = message.text.strip().lower()
        word_count = len(clean_text.split())
        
        if word_count <= 2 and clean_text in USELESS_WORDS:
            return
            
        urls = re.findall(r'(https?://\S+|www\.\S+)', message.text)
        if not urls and word_count <= 2:
            return

        if urls:
            user_info = f"👤 **From:** {message.from_user.first_name} (ID: `{message.from_user.id}`)\n"
            log_text = user_info + f"📝 Full Message: {message.text}"
            try:
                bot.send_message(LOG_CHANNEL_ID, log_text)
                print("[SUCCESS] Message logged to channel", flush=True)
            except Exception as e:
                print(f"[ERROR] Message sending failed: {e}", flush=True)

    elif message.content_type in ['photo', 'video', 'document']:
        user_info = f"👤 **From:** {message.from_user.first_name} (ID: `{message.from_user.id}`)\n"
        try:
            if message.content_type == 'photo':
                caption = f"{user_info}🖼️ **Photo Shared**\nCaption: {message.caption or 'No caption'}"
                bot.send_photo(LOG_CHANNEL_ID, message.photo[-1].file_id, caption=caption)
            elif message.content_type == 'video':
                caption = f"{user_info}📹 **Video Shared**\nCaption: {message.caption or 'No caption'}"
                bot.send_video(LOG_CHANNEL_ID, message.video.file_id, caption=caption)
            elif message.content_type == 'document':
                caption = f"{user_info}📂 **File/Document Shared**\nCaption: {message.caption or 'No caption'}"
                bot.send_document(LOG_CHANNEL_ID, message.document.file_id, caption=caption)
            print(f"[SUCCESS] {message.content_type.capitalize()} logged to channel", flush=True)
        except Exception as e:
            print(f"[ERROR] {message.content_type.capitalize()} sending failed: {e}", flush=True)

@bot.message_handler(commands=['getbackup'])
def send_backup(message):
    if message.from_user.id == OWNER_ID:
        if os.path.getsize(USER_DATABASE_FILE) > 0:
            with open(USER_DATABASE_FILE, "rb") as f:
                bot.send_document(message.chat.id, f, caption="📂 Members ID Backup File.")
        else:
            bot.reply_to(message, "❌ Database khali hai.")

if __name__ == "__main__":
    print("[POLLING] Bot started successfully on Koyeb...", flush=True)
    while True:
        try:
            bot.polling(non_stop=True, timeout=40)
        except Exception as e:
            print(f"[POLLING ERROR] Retry in 5s: {e}", flush=True)
            time.sleep(5)
                                                                             
