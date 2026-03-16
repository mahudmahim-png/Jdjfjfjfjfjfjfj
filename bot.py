import aiohttp
import aiosqlite
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8659832644:AAGG8M0i6zWRas4e_j80FLYWFraaQu8vZ7k"
ADMIN_ID = 7276206449

FORCE_CHANNEL = "@mbtcyber"
LOG_CHANNEL = -1002740128760

API = "https://bmttts.wuaze.com/subapi.php?chat_id="

main_menu = ReplyKeyboardMarkup(
[
["🔎 Search","📊 My Stats"],
["👥 Refer","ℹ️ Help"]
],
resize_keyboard=True
)

back_menu = ReplyKeyboardMarkup(
[
["🔙 Back"]
],
resize_keyboard=True
)

# ---------------- DATABASE ----------------

async def init_db():
    async with aiosqlite.connect("bot.db") as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        credits INTEGER DEFAULT 2,
        ref_by INTEGER,
        searches INTEGER DEFAULT 0
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS settings(
        status INTEGER
        )
        """)

        row = await db.execute("SELECT * FROM settings")

        if await row.fetchone() is None:
            await db.execute("INSERT INTO settings VALUES(1)")

        await db.commit()

# ---------------- FORCE JOIN ----------------

async def check_join(bot,user):

    try:
        member = await bot.get_chat_member(FORCE_CHANNEL,user)
        return member.status in ["member","administrator","creator"]
    except:
        return False

# ---------------- START ----------------

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if not await check_join(context.bot,user):

        await update.message.reply_text(
        f"⚠️ Join channel first:\nhttps://t.me/{FORCE_CHANNEL.replace('@','')}"
        )
        return

    ref=None

    if context.args:
        ref=int(context.args[0])

    async with aiosqlite.connect("bot.db") as db:

        cur = await db.execute("SELECT * FROM users WHERE user_id=?",(user,))
        data = await cur.fetchone()

        if not data:

            await db.execute(
            "INSERT INTO users(user_id,ref_by) VALUES(?,?)",(user,ref)
            )

            if ref and ref!=user:
                await db.execute(
                "UPDATE users SET credits=credits+2 WHERE user_id=?",(ref,)
                )

            await db.commit()

    await update.message.reply_text(
    "🎉 Welcome!\nYou received 2 credits.",
    reply_markup=main_menu
    )

# ---------------- STATS ----------------

async def stats(update:Update):

    user = update.effective_user.id

    async with aiosqlite.connect("bot.db") as db:

        cur = await db.execute(
        "SELECT credits,searches FROM users WHERE user_id=?",(user,)
        )

        data = await cur.fetchone()

    msg=f"""
📊 Your Stats

💳 Credits : {data[0]}
🔎 Searches : {data[1]}
"""

    await update.message.reply_text(msg,reply_markup=main_menu)

# ---------------- REFER ----------------

async def refer(update:Update,context):

    user = update.effective_user.id
    link=f"https://t.me/{context.bot.username}?start={user}"

    msg=f"""
👥 Referral System

Invite friends and earn 2 credits.

🔗 Your link:
{link}
"""

    await update.message.reply_text(msg,reply_markup=main_menu)

# ---------------- SEARCH MODE ----------------

async def search(update:Update,context):

    context.user_data["mode"]="search"

    await update.message.reply_text(
    "Send chat id to search",
    reply_markup=back_menu
    )

# ---------------- API CALL ----------------

async def api_call(uid):

    async with aiohttp.ClientSession() as s:
        async with s.get(API+str(uid)) as r:
            return await r.json()

# ---------------- MESSAGE HANDLER ----------------

async def messages(update:Update,context:ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    user = update.effective_user.id

    if text=="🔙 Back":
        context.user_data.clear()
        await update.message.reply_text("Back",reply_markup=main_menu)
        return

    if text=="🔎 Search":
        await search(update,context)
        return

    if text=="📊 My Stats":
        await stats(update)
        return

    if text=="👥 Refer":
        await refer(update,context)
        return

    if context.user_data.get("mode")!="search":
        return

    async with aiosqlite.connect("bot.db") as db:

        cur = await db.execute(
        "SELECT credits FROM users WHERE user_id=?",(user,)
        )

        credit=(await cur.fetchone())[0]

        if credit<=0:
            await update.message.reply_text("❌ No credits left")
            return

        await update.message.reply_text("⏳ Searching...")

        data = await api_call(text)

        if data["data"]["found"]:

            msg=f"""
✅ Result Found

📱 Number : {data['data']['number']}
🌍 Country : {data['data']['country']}
💬 {data['data']['message']}
⏱ {data['response_time']}

{data['credit']}
"""

        else:
            msg="❌ Not Found"

        await db.execute(
        "UPDATE users SET credits=credits-1,searches=searches+1 WHERE user_id=?",(user,)
        )

        await db.commit()

    await update.message.reply_text(msg)

    await context.bot.send_message(
    LOG_CHANNEL,
    f"User {user} searched {text}"
    )

# ---------------- ADMIN ----------------

async def admin(update:Update):

    if update.effective_user.id!=ADMIN_ID:
        return

    async with aiosqlite.connect("bot.db") as db:

        cur=await db.execute("SELECT COUNT(*) FROM users")
        users=(await cur.fetchone())[0]

    await update.message.reply_text(
    f"""
👮 Admin Panel

👤 Total Users : {users}

Commands:

/addcredit USERID AMOUNT
/removecredit USERID AMOUNT
/botoff
/boton
/userdata USERID
"""
    )

# ---------------- CREDIT CONTROL ----------------

async def addcredit(update:Update,context):

    if update.effective_user.id!=ADMIN_ID:
        return

    uid=int(context.args[0])
    amt=int(context.args[1])

    async with aiosqlite.connect("bot.db") as db:

        await db.execute(
        "UPDATE users SET credits=credits+? WHERE user_id=?",(amt,uid)
        )

        await db.commit()

    await update.message.reply_text("✅ Credit Added")

async def removecredit(update:Update,context):

    if update.effective_user.id!=ADMIN_ID:
        return

    uid=int(context.args[0])
    amt=int(context.args[1])

    async with aiosqlite.connect("bot.db") as db:

        await db.execute(
        "UPDATE users SET credits=credits-? WHERE user_id=?",(amt,uid)
        )

        await db.commit()

    await update.message.reply_text("✅ Credit Removed")

# ---------------- USER DATA ----------------

async def userdata(update:Update,context):

    if update.effective_user.id!=ADMIN_ID:
        return

    uid=int(context.args[0])

    async with aiosqlite.connect("bot.db") as db:

        cur=await db.execute(
        "SELECT * FROM users WHERE user_id=?",(uid,)
        )

        data=await cur.fetchone()

    await update.message.reply_text(
    f"""
User : {uid}
Credits : {data[1]}
Searches : {data[3]}
"""
    )

# ---------------- RUN BOT ----------------

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("admin",admin))
    app.add_handler(CommandHandler("addcredit",addcredit))
    app.add_handler(CommandHandler("removecredit",removecredit))
    app.add_handler(CommandHandler("userdata",userdata))

    app.add_handler(MessageHandler(filters.TEXT,messages))

    app.run_polling()

if __name__ == "__main__":

    import asyncio
    asyncio.run(init_db())

    main()
