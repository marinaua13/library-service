import telebot
from django.conf import settings

TELEGRAM_BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID = settings.TELEGRAM_CHAT_ID

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


def send_telegram_message(text):
    try:
        bot.send_message(TELEGRAM_CHAT_ID, text)
        return {"success": True, "message": "Message sent successfully"}
    except Exception as e:
        return {"success": False, "message": f"Failed to send message: {str(e)}"}
