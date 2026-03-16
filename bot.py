import aiohttp
import aiosqlite
import asyncio
import logging
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- CONFIG ---
TOKEN = "8659832644:AAGG8M0i6zWRas4e_j80FLYWFraaQu8vZ7k"
ADMIN_ID = 7276206449
FORCE_CHANNEL = "@mbtcyber"
LOG_CHANNEL = -1002740128760
API_URL = "https://bmttts.wuaze.com/subapi.php?chat_id="

# --- MENUS ---
main_menu = ReplyKeyboardMarkup([["🔎 Search", "📊 My Stats"], ["👥 Refer", "ℹ️ Help"]], resize_keyboard=True)
back_menu = ReplyKeyboardMarkup([["🔙 Back"]], resize_keyboard=True)

# --- DB INIT ---
async def init_db():
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS users
            (user_id INTEGER PRIMARY KEY, credits INTEGER DEFAULT 2, ref_by INTEGER, searches INTEGER DEFAULT 0)""")
        await db.commit()

# --- FUNCTIONS ---
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(FORCE_CHANNEL, update.effective_user.id)
        if member.status in ["member", "administrator", "creator"]:
            return True
    except:
        pass
    await update.message.reply_text(f"⚠️ Prothome channel-e join koro: {FORCE_CHANNEL}")
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_join(update, context): return
    
    user_id = update.effective_user.id
    ref_id = int(context.args[0]) if context.args and context.args[0].isdigit() else None

    async with aiosqlite.connect("bot.db") as db:
        cur = await db.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
        if not await cur.fetchone():
            await db.execute("INSERT INTO users(user_id, ref_by) VALUES(?,?)", (user_id, ref_id))
            if ref_id and ref_id != user_id:
                await db.execute("UPDATE users SET credits = credits + 2 WHERE user_id=?", (ref_id,))
            await db.commit()
            await update.message.reply_text("🎁 Welcome! 2 credits bonus peyechho.", reply_markup=main_menu)
        else:
            await update.message.reply_text("Ki obostha mama? Abaro shagoto!", reply_markup=main_menu)

async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "🔙 Back":
        context.user_data.clear()
        return await update.message.reply_text("Main Menu-te firiye ana holo.", reply_markup=main_menu)

    if text == "📊 My Stats":
        async with aiosqlite.connect("bot.db") as db:
            cur = await db.execute("SELECT credits, searches FROM users WHERE user_id=?", (user_id,))
            data = await cur.fetchone()
            if data:
                return await update.message.reply_text(f"📊 Stats:\n💳 Credits: {data[0]}\n🔎 Searches: {data[1]}")

    if text == "👥 Refer":
        link = f"https://t.me/{(await context.bot.get_me()).username}?start={user_id}"
        return await update.message.reply_text(f"👥 Refer kore income koro:\n{link}")

    if text == "🔎 Search":
        context.user_data["mode"] = "search"
        return await update.message.reply_text("Chat ID-ta dao mama:", reply_markup=back_menu)

    # Search Logic
    if context.user_data.get("mode") == "search":
        async with aiosqlite.connect("bot.db") as db:
            cur = await db.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
            res = await cur.fetchone()
            if not res or res[0] < 1:
                return await update.message.reply_text("❌ Credit sesh! Refer koro.")

            wait = await update.message.reply_text("⏳ Wait, khujchhi...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL + text) as r:
                    data = await r.json() if r.status == 200 else None

            if data and data.get("data", {}).get("found"):
                info = data["data"]
                msg = f"✅ Result:\n📞 Number: {info['number']}\n🌍 Country: {info['country']}"
                await db.execute("UPDATE users SET credits=credits-1, searches=searches+1 WHERE user_id=?", (user_id,))
                await db.commit()
            else:
                msg = "❌ Kichu pawa jayni!"
            
            await wait.edit_text(msg)
            await context.bot.send_message(LOG_CHANNEL, f"Log: {user_id} searched {text}")

# --- RUNNER ---
def main():
    # Database initialize korar jonno ekbar loop run kora
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())

    # Application build
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))

    print("Bot is alive!")
    app.run_polling(close_loop=False) # Pydroid-er loop close hobe na

if __name__ == "__main__":
    main()
