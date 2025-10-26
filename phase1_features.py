"""
PHASE 1 FEATURES MODULE
User-facing features: Text queries, Feedback system, Dark mode PDFs

Author: @aryansmilezzz
Phase: 1 (Text + Feedback + Dark Mode)
"""

import re
import time
from datetime import datetime, timedelta
from collections import defaultdict
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# RATE LIMITING
# ============================================================================

user_text_queries = defaultdict(list)  # {user_id: [timestamp1, timestamp2, ...]}
TEXT_QUERY_LIMIT = 10  # queries per minute
TEXT_QUERY_WINDOW = 60  # seconds

def check_rate_limit(user_id):
    """Check if user has exceeded text query rate limit"""
    now = time.time()
    
    # Clean old timestamps
    user_text_queries[user_id] = [
        ts for ts in user_text_queries[user_id] 
        if now - ts < TEXT_QUERY_WINDOW
    ]
    
    # Check limit
    if len(user_text_queries[user_id]) >= TEXT_QUERY_LIMIT:
        return False, TEXT_QUERY_LIMIT - len(user_text_queries[user_id])
    
    # Add new timestamp
    user_text_queries[user_id].append(now)
    return True, TEXT_QUERY_LIMIT - len(user_text_queries[user_id])

# ============================================================================
# CHEMISTRY KNOWLEDGE BASE (Quick Answers)
# ============================================================================

CHEMISTRY_QUICK_ANSWERS = {
    # SN reactions
    "sn1": "SN1 is unimolecular substitution where leaving group departs first forming carbocation (Rate = k[RX]). Racemization occurs, and NGP can boost rate 10³-10¹⁴×!",
    "sn2": "SN2 is bimolecular substitution with backside attack at 180° (Rate = k[Nu][RX]). Inversion of configuration occurs. Works best with primary substrates!",
    
    # Elimination
    "e1": "E1 is unimolecular elimination forming carbocation first, then base removes β-H. Follows Zaitsev's rule (more substituted alkene preferred).",
    "e2": "E2 is bimolecular elimination requiring anti-periplanar geometry. Strong base removes β-H while leaving group departs simultaneously!",
    
    # NGP
    "ngp": "Neighboring Group Participation (NGP) is when nearby π-bonds or lone pairs help stabilize transition state. Rate boost: π = 10⁶-10¹⁴×, n = 10³-10¹¹×!",
    
    # Carbocations
    "carbocation": "Carbocations are positively charged carbon species. Stability: 3° > 2° > 1° > methyl. Stabilized by hyperconjugation, resonance, and NGP!",
    
    # Mechanisms
    "mechanism": "Reaction mechanisms show step-by-step bond breaking/forming with electron flow arrows. Key: identify rate-determining step and intermediates!",
    
    # Stereochemistry
    "stereochemistry": "Stereochemistry studies 3D arrangement of atoms. SN2 gives inversion, SN1 gives racemization, E2 needs anti-periplanar geometry!",
    
    # Common groups
    "leaving group": "Good leaving groups are weak bases (I⁻ > Br⁻ > Cl⁻ > F⁻). Better leaving group = faster reaction!",
    "nucleophile": "Nucleophiles are electron-rich species that attack electron-deficient carbons. Stronger nucleophile = faster SN2!",
    
    # Acidity/Basicity
    "pka": "pKa measures acidity. Lower pKa = stronger acid. Important for predicting reaction mechanisms and equilibria!",
    
    # General
    "jee": "JEE Advanced tests deep understanding of mechanisms, stereochemistry, and rate effects. Watch for NGP traps and rate magnitude questions!",
}

def get_quick_answer(query):
    """Get quick answer from knowledge base"""
    query_lower = query.lower()
    
    # Check for exact matches
    for key, answer in CHEMISTRY_QUICK_ANSWERS.items():
        if key in query_lower:
            return answer
    
    # Check for common patterns
    if any(word in query_lower for word in ["what is", "define", "explain"]):
        # Extract the term
        for key in CHEMISTRY_QUICK_ANSWERS.keys():
            if key in query_lower:
                return CHEMISTRY_QUICK_ANSWERS[key]
    
    return None

def is_spam_message(text):
    """Detect spam/casual messages"""
    spam_patterns = [
        r'^hi+$', r'^hello+$', r'^hey+$', r'^test+$',
        r'^ok+$', r'^yes+$', r'^no+$', r'^lol+$',
        r'^haha+$', r'^hmm+$', r'^uh+$', r'^um+$'
    ]
    
    text_clean = text.lower().strip()
    return any(re.match(pattern, text_clean) for pattern in spam_patterns)

# ============================================================================
# TEXT QUERY HANDLER
# ============================================================================

async def handle_text_query(text, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle text questions with friendly responses
    Mode: Hybrid (quick answer + offer detailed)
    """
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    # Check spam
    if is_spam_message(text):
        return "spam_detected"
    
    # Check rate limit
    allowed, remaining = check_rate_limit(user_id)
    if not allowed:
        await update.message.reply_text(
            f"⏳ *Rate limit reached!*\n\n"
            f"You can ask {TEXT_QUERY_LIMIT} text questions per minute.\n"
            f"Please wait a moment before asking again!\n\n"
            f"_For unlimited solving, send images! 📸_",
            parse_mode='Markdown'
        )
        return "rate_limited"
    
    # Get quick answer
    quick_answer = get_quick_answer(text)
    
    if quick_answer:
        # Send short answer with option for detailed
        response = (
            f"💡 *Quick Answer:*\n\n"
            f"{quick_answer}\n\n"
            f"_Want a detailed explanation? Reply:_\n"
            f"*YES* - Get full explanation\n"
            f"*NO* - That's enough\n\n"
            f"📊 Remaining queries: {remaining}/{TEXT_QUERY_LIMIT} per minute"
        )
        
        # Store context for follow-up
        context.user_data['last_query'] = text
        context.user_data['awaiting_detailed'] = True
        
        await update.message.reply_text(response, parse_mode='Markdown')
        return "answered"
    else:
        # Unknown query - suggest image
        await update.message.reply_text(
            f"🤔 Hmm, I'm not sure about that!\n\n"
            f"*Try:*\n"
            f"• Send a photo of your problem 📸\n"
            f"• Rephrase your question\n"
            f"• Use keywords like: SN1, SN2, NGP, E1, E2\n\n"
            f"_I'm best at solving problems from images!_",
            parse_mode='Markdown'
        )
        return "unknown"

async def handle_detailed_request(text, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle YES/NO response for detailed explanation"""
    if not context.user_data.get('awaiting_detailed'):
        return False
    
    text_lower = text.lower().strip()
    
    if text_lower in ['yes', 'y', 'yeah', 'yep', 'sure']:
        last_query = context.user_data.get('last_query', '')
        
        await update.message.reply_text(
            f"📚 *Detailed Explanation Coming!*\n\n"
            f"For comprehensive analysis with mechanisms, "
            f"orbital diagrams, and JEE insights:\n\n"
            f"*Please send an image* of a related problem or "
            f"the specific concept you want explained.\n\n"
            f"I'll give you a beautiful PDF with triple-strategy analysis! 📄",
            parse_mode='Markdown'
        )
        
        context.user_data['awaiting_detailed'] = False
        return True
    
    elif text_lower in ['no', 'n', 'nope', 'nah']:
        await update.message.reply_text(
            "👍 Got it! Ask me anything else or send a problem image! 📸"
        )
        context.user_data['awaiting_detailed'] = False
        return True
    
    return False

# ============================================================================
# FEEDBACK SYSTEM
# ============================================================================

def create_feedback_keyboard():
    """Create inline keyboard for rating 1-10"""
    keyboard = [
        [
            InlineKeyboardButton("⭐ 1", callback_data="rate_1"),
            InlineKeyboardButton("⭐ 2", callback_data="rate_2"),
            InlineKeyboardButton("⭐ 3", callback_data="rate_3"),
            InlineKeyboardButton("⭐ 4", callback_data="rate_4"),
            InlineKeyboardButton("⭐ 5", callback_data="rate_5"),
        ],
        [
            InlineKeyboardButton("⭐ 6", callback_data="rate_6"),
            InlineKeyboardButton("⭐ 7", callback_data="rate_7"),
            InlineKeyboardButton("⭐ 8", callback_data="rate_8"),
            InlineKeyboardButton("⭐ 9", callback_data="rate_9"),
            InlineKeyboardButton("⭐ 10", callback_data="rate_10"),
        ],
        [
            InlineKeyboardButton("💬 Add Comment", callback_data="add_comment"),
            InlineKeyboardButton("❌ Skip", callback_data="skip_feedback"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def request_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Request feedback after sending PDF"""
    keyboard = create_feedback_keyboard()
    
    await update.message.reply_text(
        "⭐ *How was this solution?*\n\n"
        "Rate 1-10 so I can improve! 😊\n"
        "_Your feedback helps make me better!_",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def handle_rating_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle rating button press"""
    query = update.callback_query
    await query.answer()
    
    rating = query.data.replace("rate_", "")
    user = query.from_user
    username = user.username or "Unknown"
    user_id = user.id
    
    # Store rating
    context.user_data['rating'] = rating
    
    # Ask for optional comment
    await query.edit_message_text(
        f"✅ *You rated: {rating}/10*\n\n"
        f"Want to add a comment? (Optional)\n"
        f"Just type your feedback, or press /skip\n\n"
        f"_Thank you! 🙏_",
        parse_mode='Markdown'
    )
    
    # Mark awaiting comment
    context.user_data['awaiting_feedback_comment'] = True
    
    # Return rating for admin notification
    return int(rating), username, user_id

async def handle_comment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Add Comment' button"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "💬 *Please type your feedback:*\n\n"
        "Share your thoughts about the solution!\n"
        "Or press /skip to finish.\n\n"
        "_Your input helps me improve!_ 😊",
        parse_mode='Markdown'
    )
    
    context.user_data['awaiting_feedback_comment'] = True

async def handle_skip_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Skip' button"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "👍 *Thanks anyway!*\n\n"
        "Send me another problem anytime! 📸",
        parse_mode='Markdown'
    )

async def collect_feedback_comment(text, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collect text comment after rating"""
    if not context.user_data.get('awaiting_feedback_comment'):
        return None
    
    rating = context.user_data.get('rating', 'N/A')
    user = update.effective_user
    username = user.username or "Unknown"
    user_id = user.id
    
    context.user_data['awaiting_feedback_comment'] = False
    context.user_data['rating'] = None
    
    await update.message.reply_text(
        "🙏 *Thank you so much!*\n\n"
        "Your feedback has been recorded.\n"
        "Keep solving! 📸✨",
        parse_mode='Markdown'
    )
    
    return {
        'rating': rating,
        'comment': text,
        'username': username,
        'user_id': user_id,
        'timestamp': datetime.now()
    }

# ============================================================================
# USER SETTINGS
# ============================================================================

user_preferences = {}  # {user_id: {'pdf_mode': 'light/dark'}}

def get_user_preference(user_id, key, default='light'):
    """Get user preference"""
    if user_id not in user_preferences:
        user_preferences[user_id] = {}
    return user_preferences[user_id].get(key, default)

def set_user_preference(user_id, key, value):
    """Set user preference"""
    if user_id not in user_preferences:
        user_preferences[user_id] = {}
    user_preferences[user_id][key] = value

async def ask_pdf_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask user for PDF mode preference on first use"""
    user_id = update.effective_user.id
    
    # Check if already asked
    if get_user_preference(user_id, 'asked_mode', False):
        return get_user_preference(user_id, 'pdf_mode', 'light')
    
    keyboard = [
        [
            InlineKeyboardButton("☀️ Light Mode", callback_data="mode_light"),
            InlineKeyboardButton("🌙 Dark Mode", callback_data="mode_dark"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎨 *Choose PDF Style:*\n\n"
        "☀️ *Light Mode* - Classic white background\n"
        "🌙 *Dark Mode* - Easy on eyes for night study\n\n"
        "_You can change this anytime with /settings_",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return None  # Will be set by callback

async def handle_mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PDF mode selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    mode = query.data.replace("mode_", "")
    
    set_user_preference(user_id, 'pdf_mode', mode)
    set_user_preference(user_id, 'asked_mode', True)
    
    emoji = "☀️" if mode == "light" else "🌙"
    await query.edit_message_text(
        f"{emoji} *PDF Mode Set: {mode.title()}*\n\n"
        f"All PDFs will now use {mode} mode!\n"
        f"_Change anytime with /settings_",
        parse_mode='Markdown'
    )
    
    return mode

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command"""
    user_id = update.effective_user.id
    current_mode = get_user_preference(user_id, 'pdf_mode', 'light')
    
    keyboard = [
        [
            InlineKeyboardButton(
                f"{'✅' if current_mode == 'light' else '◻️'} Light Mode", 
                callback_data="mode_light"
            ),
            InlineKeyboardButton(
                f"{'✅' if current_mode == 'dark' else '◻️'} Dark Mode", 
                callback_data="mode_dark"
            ),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    emoji = "☀️" if current_mode == "light" else "🌙"
    
    await update.message.reply_text(
        f"⚙️ *Settings*\n\n"
        f"*PDF Mode:* {emoji} {current_mode.title()}\n"
        f"*Response Style:* Concise (2-3 lines)\n\n"
        f"_Tap to change PDF mode:_",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ============================================================================
# DARK MODE PDF CSS
# ============================================================================

DARK_MODE_CSS = """
@page {
    size: A4;
    margin: 2cm;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Helvetica', 'Arial', sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #e8e8e8;
    background: #1a1a1a;
}

.page {
    padding: 20px;
}

.header {
    background: linear-gradient(135deg, #4a9eff 0%, #00d9ff 100%);
    color: white;
    padding: 30px;
    border-radius: 12px;
    margin-bottom: 30px;
}

.header h1 {
    font-size: 24pt;
    font-weight: bold;
    margin-bottom: 8px;
}

.header .subtitle {
    font-size: 11pt;
    opacity: 0.95;
}

.header .meta {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid rgba(255,255,255,0.3);
    font-size: 9pt;
}

.section {
    margin: 25px 0;
    page-break-inside: avoid;
}

.section-title {
    font-size: 15pt;
    font-weight: bold;
    color: #4a9eff;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 3px solid #4a9eff;
}

.subsection-title {
    font-size: 12pt;
    font-weight: bold;
    color: #00d9ff;
    margin: 15px 0 10px 0;
    border-left: 4px solid #00d9ff;
    padding-left: 10px;
}

.strategy-box {
    background: #2a2a2a;
    border-left: 5px solid #4a9eff;
    padding: 20px;
    margin: 20px 0;
    border-radius: 6px;
    page-break-inside: avoid;
}

.strategy-header {
    font-size: 13pt;
    font-weight: bold;
    color: #4a9eff;
    margin-bottom: 12px;
}

.answer-box {
    background: #1e3a5f;
    border: 3px solid #4a9eff;
    padding: 20px;
    border-radius: 10px;
    margin: 25px 0;
    page-break-inside: avoid;
}

.answer-label {
    font-size: 10pt;
    font-weight: bold;
    color: #00d9ff;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}

.answer-content {
    font-size: 12pt;
    font-weight: bold;
    color: #4a9eff;
}

.confidence {
    display: inline-block;
    background: #00d9ff;
    color: #1a1a1a;
    padding: 4px 12px;
    border-radius: 15px;
    font-size: 9pt;
    font-weight: bold;
    margin-left: 8px;
}

.formula {
    font-family: 'Courier New', monospace;
    background: #2a2a2a;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 10pt;
    color: #00d9ff;
}

.step {
    background: #252525;
    border: 2px solid #3a3a3a;
    padding: 15px;
    margin: 12px 0;
    border-radius: 6px;
    page-break-inside: avoid;
}

.success-box {
    background: #1e3a1e;
    border-left: 4px solid #00d9ff;
    padding: 12px 15px;
    margin: 12px 0;
    border-radius: 4px;
}

.footer {
    margin-top: 40px;
    padding-top: 15px;
    border-top: 2px solid #3a3a3a;
    text-align: center;
    font-size: 9pt;
    color: #888;
    font-style: italic;
}

p {
    margin: 8px 0;
}

ul, ol {
    margin: 12px 0;
    padding-left: 25px;
}

li {
    margin: 6px 0;
}

strong {
    font-weight: bold;
    color: #00d9ff;
}
"""

def get_pdf_css(mode='light'):
    """Get appropriate CSS based on mode"""
    if mode == 'dark':
        return DARK_MODE_CSS
    else:
        # Return existing light mode CSS
        from ULTIMATE_JE import CSS_TEMPLATE
        return CSS_TEMPLATE
