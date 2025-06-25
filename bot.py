# bot.py
import logging
import os # <-- Import the 'os' module
import random
import datetime
from pymongo import MongoClient
from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from telegram.error import BadRequest, Unauthorized

# --- CONFIGURATION (from Environment Variables) ---
# We will set these in the Koyeb dashboard later
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGO_URI = os.environ.get("MONGO_URI")
DATABASE_NAME = os.environ.get("DATABASE_NAME")
SOURCE_CHANNEL_ID = int(os.environ.get("SOURCE_CHANNEL_ID"))
# Admin IDs will be a comma-separated string like "1111,2222"
ADMIN_IDS_STR = os.environ.get("ADMIN_IDS", "")
ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(',') if admin_id.strip()]

# --- GAMEPLAY CONSTANTS ---
DAILY_VIDEO_LIMIT = 50
POINTS_PER_VIDEO = 1
POINTS_PER_REFERRAL = 25

# --- DATABASE SETUP ---
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
users_collection = db.users

# --- LOGGING ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- All your other functions (get_or_create_user, start, button_handler, etc.) go here ---
# (Copy and paste all the functions from the previous response. They do not need to be changed.)

def get_or_create_user(user_id, first_name, referred_by_id=None):
    """Gets user from DB or creates a new one, handling referrals."""
    user = users_collection.find_one({"_id": user_id})
    if not user:
        new_user = {
            "_id": user_id,
            "first_name": first_name,
            "is_premium": False,
            "daily_video_count": 0,
            "last_access_date": datetime.date.today().isoformat(),
            "points": 0,
            "referral_count": 0,
            "referred_by": referred_by_id
        }
        users_collection.insert_one(new_user)
        if referred_by_id:
            try:
                users_collection.update_one(
                    {"_id": referred_by_id},
                    {"$inc": {"referral_count": 1, "points": POINTS_PER_REFERRAL}}
                )
                logger.info(f"User {referred_by_id} referred {user_id} and got {POINTS_PER_REFERRAL} points.")
            except Exception as e:
                logger.error(f"Error crediting referrer {referred_by_id}: {e}")
        return new_user
    return user

def check_and_reset_limit(user):
    """Checks if the daily limit needs to be reset."""
    today = datetime.date.today().isoformat()
    if user.get("last_access_date") != today:
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"daily_video_count": 0, "last_access_date": today}}
        )
        user["daily_video_count"] = 0
    return user

def start(update: Update, context: CallbackContext) -> None:
    """Handles the /start command, including referrals."""
    user = update.effective_user
    referrer_id = None
    if context.args:
        try:
            referrer_id = int(context.args[0])
            if referrer_id == user.id: referrer_id = None
        except (ValueError, IndexError):
            referrer_id = None
    get_or_create_user(user.id, user.first_name, referrer_id)
    welcome_text = (
        f"🔥 **Ooh, {user.first_name}~**\n\n"
        f"Welcome To **Pyasi Angel Bot** 🎉\n\n"
        f"I'm here to send you exclusive adult /video and /photo from various categories!\n\n"
        f"⚠️ **Disclaimer:** For users 18+ 🔞. This service is strictly for adults. By continuing, you confirm you are 18+\n\n"
        f"💡 Enjoy responsibly and have fun!"
    )
    keyboard = [
        [InlineKeyboardButton("VIDEO 🥵", callback_data="send_video"), InlineKeyboardButton("PHOTO 📸", callback_data="send_photo")],
        [InlineKeyboardButton("POINTS 🏅", callback_data="show_points"), InlineKeyboardButton("REFER & EARN 🔗", callback_data="show_refer")],
        [InlineKeyboardButton("🏆 Leaderboard 🏆", callback_data="show_leaderboard")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

def send_random_content(chat_id, context: CallbackContext, content_type: str) -> None:
    """Sends a random video or photo and handles points/limits."""
    user = users_collection.find_one({"_id": chat_id})
    if content_type == 'video':
        if not user.get('is_premium', False):
            user = check_and_reset_limit(user)
            if user.get('daily_video_count', 0) >= DAILY_VIDEO_LIMIT:
                context.bot.send_message(chat_id, "🚫 You have reached your daily limit of 50 videos. Upgrade to premium for unlimited access!")
                return
            users_collection.update_one({"_id": chat_id}, {"$inc": {"daily_video_count": 1}})
    try:
        total_messages = context.bot.get_chat(SOURCE_CHANNEL_ID).total_count
        if not total_messages:
            context.bot.send_message(chat_id, "Sorry, the content library is currently empty.")
            return
        for _ in range(10):
            random_msg_id = random.randint(1, total_messages)
            try:
                context.bot.copy_message(chat_id=chat_id, from_chat_id=SOURCE_CHANNEL_ID, message_id=random_msg_id)
                if content_type == 'video':
                    users_collection.update_one({"_id": chat_id}, {"$inc": {"points": POINTS_PER_VIDEO}})
                return
            except (BadRequest, Unauthorized):
                continue
        context.bot.send_message(chat_id, "Couldn't find any content right now, please try again in a moment.")
    except Exception as e:
        logger.error(f"Error sending content to {chat_id}: {e}")
        context.bot.send_message(chat_id, "An error occurred. The admin has been notified.")

def button_handler(update: Update, context: CallbackContext) -> None:
    """Handles all inline button clicks."""
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    data = query.data
    if data == 'send_video': send_random_content(user_id, context, 'video')
    elif data == 'send_photo': send_random_content(user_id, context, 'photo')
    elif data == 'show_points':
        user_data = users_collection.find_one({"_id": user_id})
        points = user_data.get('points', 0)
        referrals = user_data.get('referral_count', 0)
        text = (f"🏅 **Your Stats** 🏅\n\nYou currently have: **{points} points**\nYou have successfully referred: **{referrals} users**\n\nKeep watching videos and referring friends to earn more!")
        query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    elif data == 'show_refer':
        bot_username = context.bot.get_me().username
        referral_link = f"https://t.me/{bot_username}?start={user_id}"
        text = (f"🔗 **Refer & Earn Points!** 🔗\n\nShare your unique link with friends. When a new user starts the bot through your link, you'll earn **{POINTS_PER_REFERRAL} points** and climb the leaderboard!\n\nYour personal referral link is:\n`{referral_link}`")
        query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    elif data == 'show_leaderboard':
        leaderboard_text = "🏆 **Referral Leaderboard** 🏆\n\n*Top 10 users with the most referrals:*\n\n"
        top_users = users_collection.find({"referral_count": {"$gt": 0}}).sort("referral_count", -1).limit(10)
        rank_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}
        found_users = False
        for i, user in enumerate(top_users, 1):
            found_users = True
            rank = rank_emojis.get(i, f"**{i}.**")
            user_name = user['first_name'].replace("<", "<").replace(">", ">")
            leaderboard_text += f"{rank} {user_name} - **{user['referral_count']}** referrals\n"
        if not found_users:
            leaderboard_text += "The leaderboard is empty. Start referring people to get on top!"
        query.message.reply_text(leaderboard_text, parse_mode=ParseMode.MARKDOWN)

def broadcast(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id not in ADMIN_IDS: return
    message_to_broadcast = update.message.text.split('/broadcast ', 1)
    if len(message_to_broadcast) < 2 or not message_to_broadcast[1]:
        update.message.reply_text("Usage: /broadcast <your message>")
        return
    message_text = message_to_broadcast[1]
    all_users = users_collection.find({}, {"_id": 1})
    user_ids = [user["_id"] for user in all_users]
    success_count, fail_count = 0, 0
    update.message.reply_text(f"📢 Starting broadcast to {len(user_ids)} users...")
    for uid in user_ids:
        try:
            context.bot.send_message(chat_id=uid, text=message_text)
            success_count += 1
        except (Unauthorized, BadRequest):
            fail_count += 1
    update.message.reply_text(f"✅ Broadcast finished!\nSent: {success_count}, Failed: {fail_count}")

def add_premium(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id not in ADMIN_IDS: return
    try:
        user_id_to_add = int(context.args[0])
        result = users_collection.update_one({"_id": user_id_to_add}, {"$set": {"is_premium": True}})
        if result.matched_count == 0: update.message.reply_text(f"User {user_id_to_add} not found.")
        else: update.message.reply_text(f"✅ User {user_id_to_add} is now Premium!")
    except (IndexError, ValueError): update.message.reply_text("Usage: /addpremium <user_id>")

def remove_premium(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id not in ADMIN_IDS: return
    try:
        user_id_to_remove = int(context.args[0])
        users_collection.update_one({"_id": user_id_to_remove}, {"$set": {"is_premium": False}})
        update.message.reply_text(f"✅ User {user_id_to_remove} is now a normal user.")
    except (IndexError, ValueError): update.message.reply_text("Usage: /removepremium <user_id>")

# --- MAIN FUNCTION ---
def main() -> None:
    """Start the bot."""
    # Ensure all environment variables are set
    if not all([BOT_TOKEN, MONGO_URI, DATABASE_NAME, SOURCE_CHANNEL_ID, ADMIN_IDS]):
        logger.error("FATAL: One or more environment variables are missing!")
        return

    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    dispatcher.add_handler(CommandHandler("broadcast", broadcast))
    dispatcher.add_handler(CommandHandler("addpremium", add_premium))
    dispatcher.add_handler(CommandHandler("removepremium", remove_premium))
    updater.start_polling()
    logger.info("Bot started successfully!")
    updater.idle()

if __name__ == '__main__':
    main()