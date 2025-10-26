"""
PHASE 1 ADMIN MODULE
Admin tools: Notifications, Ban system, Stats, Maintenance mode, Broadcast

Author: @aryansmilezzz
Admin ID: 6298922725
"""

import time
from datetime import datetime, timedelta
from collections import defaultdict
from telegram import Update, InputFile
from telegram.ext import ContextTypes
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# ADMIN CONFIGURATION
# ============================================================================

ADMIN_ID = 6298922725
ADMIN_USERNAME = "@aryansmilezzz"

# ============================================================================
# TRACKING & STORAGE
# ============================================================================

# User tracking
all_users = set()  # {user_id1, user_id2, ...}
user_first_seen = {}  # {user_id: timestamp}
user_problem_count = defaultdict(int)  # {user_id: count}
user_last_activity = {}  # {user_id: timestamp}

# Spam tracking
user_message_history = defaultdict(list)  # {user_id: [(timestamp, message), ...]}
spam_warnings = defaultdict(int)  # {user_id: warning_count}

# Ban list
banned_users = set()  # {user_id1, user_id2, ...}

# Stats
total_problems_solved = 0
total_text_queries = 0
total_feedback_received = 0
feedback_ratings = []  # [rating1, rating2, ...]

# Maintenance mode
maintenance_mode = False
maintenance_message = "🔧 Bot is under maintenance. Please try again later!"

# Bot start time
bot_start_time = datetime.now()

# ============================================================================
# USER TRACKING
# ============================================================================

def track_new_user(user_id, username):
    """Track new user"""
    if user_id not in all_users:
        all_users.add(user_id)
        user_first_seen[user_id] = datetime.now()
        logger.info(f"New user: {username} ({user_id})")
        return True
    return False

def track_user_activity(user_id):
    """Update user last activity"""
    user_last_activity[user_id] = datetime.now()

def track_problem_solved(user_id):
    """Track problem solved"""
    global total_problems_solved
    user_problem_count[user_id] += 1
    total_problems_solved += 1
    track_user_activity(user_id)

def track_text_query(user_id):
    """Track text query"""
    global total_text_queries
    total_text_queries += 1
    track_user_activity(user_id)

def track_feedback(rating):
    """Track feedback rating"""
    global total_feedback_received
    total_feedback_received += 1
    feedback_ratings.append(int(rating))

# ============================================================================
# SPAM DETECTION
# ============================================================================

def detect_spam(user_id, message):
    """
    Detect if user is spamming
    Returns: (is_spam, spam_type, count)
    """
    now = time.time()
    
    # Clean old messages (keep last 60 seconds)
    user_message_history[user_id] = [
        (ts, msg) for ts, msg in user_message_history[user_id]
        if now - ts < 60
    ]
    
    # Add current message
    user_message_history[user_id].append((now, message.lower().strip()))
    
    recent_messages = [msg for ts, msg in user_message_history[user_id]]
    
    # Check for repeated messages
    if len(recent_messages) >= 5:
        last_5 = recent_messages[-5:]
        if len(set(last_5)) == 1:  # All same message
            return True, "repeated_message", 5
    
    # Check for rapid fire (>10 messages in 30 seconds)
    last_30s = [ts for ts, msg in user_message_history[user_id] if now - ts < 30]
    if len(last_30s) > 10:
        return True, "rapid_fire", len(last_30s)
    
    # Check for spam patterns
    spam_words = ["hi", "hello", "test", "hey", "lol", "haha"]
    recent_spam = [msg for msg in recent_messages[-10:] if msg in spam_words]
    if len(recent_spam) >= 5:
        return True, "spam_words", len(recent_spam)
    
    return False, None, 0

# ============================================================================
# BAN SYSTEM
# ============================================================================

def ban_user(user_id):
    """Ban a user"""
    banned_users.add(user_id)
    logger.warning(f"User banned: {user_id}")

def unban_user(user_id):
    """Unban a user"""
    if user_id in banned_users:
        banned_users.remove(user_id)
        logger.info(f"User unbanned: {user_id}")
        return True
    return False

def is_banned(user_id):
    """Check if user is banned"""
    return user_id in banned_users

def add_spam_warning(user_id):
    """Add spam warning to user"""
    spam_warnings[user_id] += 1
    if spam_warnings[user_id] >= 3:
        ban_user(user_id)
        return True  # Auto-banned
    return False

# ============================================================================
# ADMIN NOTIFICATIONS
# ============================================================================

async def notify_admin(context: ContextTypes.DEFAULT_TYPE, message, image=None):
    """Send notification to admin"""
    try:
        if image:
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=image,
                caption=message,
                parse_mode='Markdown'
            )
        else:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=message,
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")

async def notify_new_user(user_id, username, context):
    """Notify admin of new user"""
    message = (
        f"📊 *NEW USER*\n\n"
        f"👤 User: @{username}\n"
        f"🆔 ID: `{user_id}`\n"
        f"📅 Time: {datetime.now().strftime('%I:%M %p')}\n"
        f"👥 Total users: {len(all_users)}"
    )
    await notify_admin(context, message)

async def notify_problem_solved(user_id, username, processing_time, context, image=None):
    """Notify admin of problem solved"""
    message = (
        f"🔬 *PROBLEM SOLVED*\n\n"
        f"👤 User: @{username}\n"
        f"🆔 ID: `{user_id}`\n"
        f"⏱️ Time: {processing_time}s\n"
        f"📊 Total by user: {user_problem_count[user_id]}\n"
        f"📈 Total today: {total_problems_solved}"
    )
    await notify_admin(context, message, image)

async def notify_text_query(user_id, username, query, answer, context):
    """Notify admin of text query"""
    message = (
        f"💬 *TEXT QUERY*\n\n"
        f"👤 User: @{username}\n"
        f"🆔 ID: `{user_id}`\n"
        f"❓ Query: _{query[:100]}_\n"
        f"✅ Answer: _{answer[:100]}_\n"
        f"📊 Total text queries: {total_text_queries}"
    )
    await notify_admin(context, message)

async def notify_feedback(user_id, username, rating, comment, context):
    """Notify admin of feedback received"""
    avg_rating = sum(feedback_ratings) / len(feedback_ratings) if feedback_ratings else 0
    
    message = (
        f"⭐ *FEEDBACK RECEIVED*\n\n"
        f"👤 User: @{username}\n"
        f"🆔 ID: `{user_id}`\n"
        f"⭐ Rating: *{rating}/10*\n"
    )
    
    if comment:
        message += f"💬 Comment: _{comment[:200]}_\n"
    
    message += (
        f"\n📊 *Statistics:*\n"
        f"Total feedback: {total_feedback_received}\n"
        f"Average rating: {avg_rating:.1f}/10"
    )
    
    await notify_admin(context, message)

async def notify_spam_detected(user_id, username, spam_type, count, messages, context):
    """Notify admin of spam detection"""
    warnings = spam_warnings[user_id]
    
    message = (
        f"⚠️ *SPAM ALERT*\n\n"
        f"👤 User: @{username}\n"
        f"🆔 ID: `{user_id}`\n"
        f"🚨 Type: {spam_type.replace('_', ' ').title()}\n"
        f"📊 Count: {count} messages\n"
        f"⚠️ Warnings: {warnings}/3\n\n"
        f"📝 Recent messages:\n_{', '.join(messages[-5:])}_\n\n"
        f"*Actions:*\n"
        f"/admin_ban {user_id} - Ban user\n"
        f"/admin_warn {user_id} - Just warn\n"
        f"/admin_ignore {user_id} - Ignore"
    )
    
    await notify_admin(context, message)

async def notify_error(error_msg, context):
    """Notify admin of errors"""
    message = (
        f"❌ *ERROR ALERT*\n\n"
        f"🕐 Time: {datetime.now().strftime('%I:%M %p')}\n"
        f"📝 Error: `{error_msg[:500]}`"
    )
    await notify_admin(context, message)

# ============================================================================
# ADMIN COMMANDS
# ============================================================================

async def admin_ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user - /admin_ban <user_id>"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "Usage: `/admin_ban <user_id>`",
            parse_mode='Markdown'
        )
        return
    
    try:
        user_id = int(context.args[0])
        ban_user(user_id)
        await update.message.reply_text(
            f"✅ *User Banned*\n\nID: `{user_id}`\n"
            f"They can no longer use the bot.",
            parse_mode='Markdown'
        )
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID!")

async def admin_unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user - /admin_unban <user_id>"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "Usage: `/admin_unban <user_id>`",
            parse_mode='Markdown'
        )
        return
    
    try:
        user_id = int(context.args[0])
        if unban_user(user_id):
            await update.message.reply_text(
                f"✅ *User Unbanned*\n\nID: `{user_id}`\n"
                f"They can use the bot again.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ User was not banned!")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID!")

async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics - /admin_stats"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    uptime = datetime.now() - bot_start_time
    avg_rating = sum(feedback_ratings) / len(feedback_ratings) if feedback_ratings else 0
    
    # Active users (last 24 hours)
    now = datetime.now()
    active_24h = sum(
        1 for uid, last_time in user_last_activity.items()
        if now - last_time < timedelta(hours=24)
    )
    
    # Top users
    top_users = sorted(user_problem_count.items(), key=lambda x: x[1], reverse=True)[:5]
    top_users_text = "\n".join([f"  • User {uid}: {count} problems" for uid, count in top_users])
    
    message = (
        f"📊 *BOT STATISTICS*\n\n"
        f"⏱️ *Uptime:* {uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m\n\n"
        f"👥 *Users:*\n"
        f"  • Total: {len(all_users)}\n"
        f"  • Active (24h): {active_24h}\n"
        f"  • Banned: {len(banned_users)}\n\n"
        f"🔬 *Problems Solved:*\n"
        f"  • Total: {total_problems_solved}\n"
        f"  • Average per user: {total_problems_solved/len(all_users) if all_users else 0:.1f}\n\n"
        f"💬 *Text Queries:* {total_text_queries}\n\n"
        f"⭐ *Feedback:*\n"
        f"  • Total received: {total_feedback_received}\n"
        f"  • Average rating: {avg_rating:.1f}/10\n\n"
        f"🏆 *Top Users:*\n{top_users_text if top_users_text else '  None yet'}\n\n"
        f"🔧 *Maintenance:* {'ON' if maintenance_mode else 'OFF'}"
    )
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def admin_maintenance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle maintenance mode - /admin_maintenance on/off"""
    global maintenance_mode, maintenance_message
    
    if update.effective_user.id != ADMIN_ID:
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            f"Usage: `/admin_maintenance on/off [message]`\n\n"
            f"Current: {'ON' if maintenance_mode else 'OFF'}",
            parse_mode='Markdown'
        )
        return
    
    mode = context.args[0].lower()
    
    if mode == 'on':
        maintenance_mode = True
        if len(context.args) > 1:
            maintenance_message = ' '.join(context.args[1:])
        await update.message.reply_text(
            f"🔧 *Maintenance Mode: ON*\n\n"
            f"Message: _{maintenance_message}_",
            parse_mode='Markdown'
        )
    elif mode == 'off':
        maintenance_mode = False
        await update.message.reply_text(
            "✅ *Maintenance Mode: OFF*\n\nBot is now accepting requests!",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Use 'on' or 'off'")

async def admin_broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all users - /admin_broadcast <message>"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "Usage: `/admin_broadcast <message>`",
            parse_mode='Markdown'
        )
        return
    
    message = ' '.join(context.args)
    
    await update.message.reply_text(
        f"📢 *Broadcasting to {len(all_users)} users...*",
        parse_mode='Markdown'
    )
    
    success = 0
    failed = 0
    
    for user_id in all_users:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📢 *Announcement*\n\n{message}",
                parse_mode='Markdown'
            )
            success += 1
        except Exception as e:
            failed += 1
            logger.error(f"Broadcast failed for {user_id}: {e}")
    
    await update.message.reply_text(
        f"✅ *Broadcast Complete*\n\n"
        f"Sent: {success}\nFailed: {failed}",
        parse_mode='Markdown'
    )

async def admin_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all users - /admin_users"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    user_list = []
    for user_id in list(all_users)[:20]:  # Show first 20
        problems = user_problem_count[user_id]
        first_seen = user_first_seen.get(user_id, datetime.now())
        days_ago = (datetime.now() - first_seen).days
        user_list.append(f"• {user_id}: {problems} problems ({days_ago}d ago)")
    
    message = (
        f"👥 *USER LIST* (First 20)\n\n"
        f"{chr(10).join(user_list)}\n\n"
        f"Total: {len(all_users)} users"
    )
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def admin_warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Warn user about spam - /admin_warn <user_id>"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "Usage: `/admin_warn <user_id>`",
            parse_mode='Markdown'
        )
        return
    
    try:
        user_id = int(context.args[0])
        auto_banned = add_spam_warning(user_id)
        
        if auto_banned:
            await update.message.reply_text(
                f"⛔ *User Auto-Banned*\n\n"
                f"ID: `{user_id}`\n"
                f"Reason: 3 spam warnings",
                parse_mode='Markdown'
            )
        else:
            warnings = spam_warnings[user_id]
            await update.message.reply_text(
                f"⚠️ *Warning Added*\n\n"
                f"ID: `{user_id}`\n"
                f"Warnings: {warnings}/3",
                parse_mode='Markdown'
            )
            
            # Send warning to user
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"⚠️ *Warning*\n\n"
                        f"Please avoid spam messages.\n"
                        f"Warnings: {warnings}/3\n\n"
                        f"_3 warnings = automatic ban_"
                    ),
                    parse_mode='Markdown'
                )
            except:
                pass
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID!")

async def admin_ignore_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ignore spam alert - /admin_ignore <user_id>"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "Usage: `/admin_ignore <user_id>`",
            parse_mode='Markdown'
        )
        return
    
    try:
        user_id = int(context.args[0])
        # Reset spam history
        user_message_history[user_id] = []
        await update.message.reply_text(
            f"✅ *Ignored*\n\nSpam alert for user `{user_id}` cleared.",
            parse_mode='Markdown'
        )
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID!")

# ============================================================================
# MAINTENANCE CHECK
# ============================================================================

async def check_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if bot is in maintenance mode"""
    if maintenance_mode and update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(
            maintenance_message,
            parse_mode='Markdown'
        )
        return True
    return False

# ============================================================================
# ADMIN HELP
# ============================================================================

async def admin_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin commands - /admin_help"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    message = (
        f"👑 *ADMIN COMMANDS*\n\n"
        f"*User Management:*\n"
        f"• `/admin_ban <id>` - Ban user\n"
        f"• `/admin_unban <id>` - Unban user\n"
        f"• `/admin_warn <id>` - Warn user\n"
        f"• `/admin_ignore <id>` - Ignore spam alert\n"
        f"• `/admin_users` - List all users\n\n"
        f"*Statistics:*\n"
        f"• `/admin_stats` - Full bot stats\n\n"
        f"*Bot Control:*\n"
        f"• `/admin_maintenance on/off` - Toggle maintenance\n"
        f"• `/admin_broadcast <msg>` - Send to all users\n\n"
        f"*Help:*\n"
        f"• `/admin_help` - This message\n\n"
        f"_All user actions auto-notify you!_"
    )
    
    await update.message.reply_text(message, parse_mode='Markdown')
