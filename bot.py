import telebot
import requests
from telebot import types

# --- CONFIGURATION ---
TOKEN = "8574435830:AAE0kbggvVYU_mnQpOcbwZaSKoQE8Nd02bw"
API_URL = "https://tg2num-owner-api.vercel.app?userid="
c = "@Unkonwn_BMT"

bot = telebot.TeleBot(TOKEN)

# Main Menu Keyboard (Pro look)
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🔍 Search User ID")
    btn2 = types.KeyboardButton("📢 Channel")
    btn3 = types.KeyboardButton("ℹ️ Help")
    markup.add(btn1)
    markup.add(btn2, btn3)
    return markup

# /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message, 
        f"👋 Welcome {message.from_user.first_name}!\n\nUser ID pathan phone number ber korar jonno.", 
        reply_markup=main_menu()
    )

# Message handler
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = message.chat.id
    text = message.text

    if text == "🔍 Search User ID":
        bot.send_message(chat_id, "🔢 Please send the **Numeric User ID**.")
    
    elif text == "📢 Channel":
        bot.send_message(chat_id, "🔗 Join: @AbdulBotzOfficial")

    elif text == "ℹ️ Help":
        bot.send_message(chat_id, "Shudhu numeric ID dilei bot details nibe.\n\nContact: {c}")

    # Jodi user numeric ID pathay
    elif text.isdigit():
        wait_msg = bot.send_message(chat_id, "⚡ Searching in Database...")
        
        try:
            # API Request
            response = requests.get(f"{API_URL}{text}")
            data = response.json()

            if data.get("status") == "success" and data["data"]["found"]:
                info = data["data"]
                result = (
                    f"✅ **Match Found!**\n\n"
                    f"🆔 **User ID:** `{data['searched_userid']}`\n"
                    f"📞 **Number:** `{info['number']}`\n"
                    f"🌍 **Country:** {info['country']}\n"
                    f"⚡ **Response:** {data['response_time']}\n\n"
                    f"💳 Credit: {c}"
                )
                bot.edit_message_text(result, chat_id, wait_msg.message_id, parse_mode="Markdown")
            else:
                bot.edit_message_text("❌ No data found for this ID.", chat_id, wait_msg.message_id)
        
        except Exception as e:
            bot.edit_message_text(f"⚠️ Error: API issue!", chat_id, wait_msg.message_id)

    else:
        bot.send_message(chat_id, "❌ Invalid Input! Use numeric ID.")

print("✅ Bot is running on Pydroid...")
bot.infinity_polling()
