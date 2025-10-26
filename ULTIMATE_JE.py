"""
ULTIMATE_PHASE2.py - COMPLETE INTEGRATION (SLIM VERSION)
All Phase 1 + Phase 2 + Core Features

Author: @aryansmilezzz
Admin ID: 6298922725
Version: Phase 2 Final
"""

import os
import asyncio
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from io import BytesIO
from PIL import Image, ImageEnhance
from datetime import datetime
from weasyprint import HTML
from jinja2 import Template
import re
import base64
import httpx
import aiohttp
import json
import logging
import time

# ============================================================================
# PHASE 1 IMPORTS
# ============================================================================
from phase1_features import (
    handle_text_query,
    handle_detailed_request,
    collect_feedback_comment,
    get_user_preference,
    set_user_preference,
    DARK_MODE_CSS,
    request_feedback,
    ask_pdf_mode
)

from phase1_admin import (
    ADMIN_ID,
    ADMIN_USERNAME,
    track_new_user,
    track_problem_solved,
    track_text_query,
    track_feedback,
    detect_spam,
    is_banned,
    check_maintenance,
    notify_new_user,
    notify_problem_solved,
    notify_text_query,
    notify_feedback,
    notify_spam_detected,
    notify_error,
    admin_ban_command,
    admin_unban_command,
    admin_stats_command,
    admin_maintenance_command,
    admin_broadcast_command,
    admin_users_command,
    admin_warn_command,
    admin_ignore_command,
    admin_help_command,
    all_users,
    total_problems_solved,
    bot_start_time,
    user_message_history
)

# ============================================================================
# PHASE 2 IMPORTS
# ============================================================================
from phase2_visualizer import (
    visualize_molecule_command,
    visualize_concept_map_command
)

from phase2_features import (
    hint_command as phase2_hint,
    flashcard_command as phase2_flashcard,
    theme_command as phase2_theme,
    handle_hint_next,
    handle_hint_stop,
    handle_hint_reset,
    handle_flashcard_topic,
    handle_theme_selection
)

from phase2_exam import (
    mock_test_command,
    start_mock_test_config,
    handle_question_count,
    handle_time_limit,
    handle_difficulty_selection,
    handle_answer,
    active_mock_tests
)

from phase2_predictors import (
    difficulty_command as phase2_difficulty,
    pka_command,
    jee_frequency_command,
    analyze_difficulty_text,
    analyze_pka_text,
    analyze_jee_frequency_text
)

nest_asyncio.apply()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

BOT_TOKEN = os.environ.get('BOT_TOKEN')

GEMINI_API_KEYS = [
    os.environ.get('GEMINI_KEY_1'),
    os.environ.get('GEMINI_KEY_2'),
    os.environ.get('GEMINI_KEY_3'),
    os.environ.get('GEMINI_KEY_4'),
    os.environ.get('GEMINI_KEY_5'),
]

GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not set!")
if not GEMINI_API_KEYS:
    raise ValueError("❌ No GEMINI keys!")

logger.info(f"✅ Loaded {len(GEMINI_API_KEYS)} API keys")

current_key_index = 0
CHEMISTRY_CACHE_FILE = "/app/data/chemistry_cache.json" if os.path.exists("/app/data") else "chemistry_cache.json"
chemistry_knowledge_base = {}

# ============================================================================
# CHEMISTRY KNOWLEDGE SOURCES
# ============================================================================

CHEMISTRY_SOURCES = {
    "functional_groups": "https://raw.githubusercontent.com/Sulstice/global-chem/master/global_chem/functional_groups/functional_groups.json",
    "common_r_groups": "https://raw.githubusercontent.com/Sulstice/global-chem/master/global_chem/common_R_groups/common_R_groups.json",
    "amino_acids": "https://raw.githubusercontent.com/Sulstice/global-chem/master/global_chem/amino_acids/amino_acids.json",
    "common_solvents": "https://raw.githubusercontent.com/Sulstice/global-chem/master/global_chem/common_solvents/common_solvents.json",
    "named_reactions": "https://raw.githubusercontent.com/Sulstice/global-chem/master/global_chem/named_reactions/named_reactions.json",
}

JEE_LOGIC = {
    "mechanism_trees": {
        "substitution": {
            "primary": "SN2 - Rate = k[Nu][RX], Inversion, 180°",
            "secondary": "Check NGP! π/n within 2-3 atoms = 10^3-10^14 boost",
            "tertiary": "SN1 - Rate = k[RX], Racemization, NGP = 10^6-10^14"
        }
    },
    "NGP_rules": {
        "pi": {"boost": "10^6-10^14×", "groups": ["C=C", "benzene", "C≡C"]},
        "n": {"boost": "10^3-10^11×", "groups": ["-OR", "-NR2", "-SR"]}
    },
    "jee_traps": {
        "trap1": "Check 2-3 atoms for π/n",
        "trap2": "Know rate magnitude (10^X)",
        "trap3": "Acetal = R2C(OR')2"
    }
}

# ============================================================================
# CACHE FUNCTIONS
# ============================================================================

def load_cache():
    global chemistry_knowledge_base
    try:
        with open(CHEMISTRY_CACHE_FILE, 'r') as f:
            chemistry_knowledge_base = json.load(f)
        logger.info(f"📂 Cache: {len(chemistry_knowledge_base)} sections")
        return True
    except:
        return False

def save_cache():
    try:
        os.makedirs(os.path.dirname(CHEMISTRY_CACHE_FILE), exist_ok=True)
        with open(CHEMISTRY_CACHE_FILE, 'w') as f:
            json.dump(chemistry_knowledge_base, f, indent=2)
        logger.info("💾 Cache saved")
    except Exception as e:
        logger.error(f"Cache error: {e}")

async def download_knowledge():
    global chemistry_knowledge_base
    if chemistry_knowledge_base:
        return chemistry_knowledge_base

    logger.info("🌐 Downloading knowledge...")
    downloaded = {}

    try:
        async with aiohttp.ClientSession() as session:
            for name, url in CHEMISTRY_SOURCES.items():
                try:
                    async with session.get(url, timeout=30) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            downloaded[name] = data
                            logger.info(f"✅ {name}: {len(data) if isinstance(data, list) else 'OK'}")
                except Exception as e:
                    logger.info(f"⚠️ {name}: {str(e)[:30]}")
                await asyncio.sleep(0.5)

        downloaded["jee_logic"] = JEE_LOGIC
        chemistry_knowledge_base = downloaded
        save_cache()
        logger.info(f"✅ Total: {len(chemistry_knowledge_base)} sections")

    except Exception as e:
        logger.error(f"Download error: {e}")
        chemistry_knowledge_base = {"jee_logic": JEE_LOGIC}

    return chemistry_knowledge_base

# ============================================================================
# PROMPT BUILDING
# ============================================================================

def build_prompt():
    summary = ""
    if chemistry_knowledge_base:
        summary = "\n🔬 KNOWLEDGE BASE:\n" + "="*70 + "\n"
        for sec, data in chemistry_knowledge_base.items():
            if sec != "jee_logic" and isinstance(data, list):
                summary += f"📚 {sec}: {len(data)} entries\n"
        summary += "="*70 + "\n"

    return f"""You are THE ULTIMATE CHEMISTRY EXPERT.

{summary}

JEE LOGIC: {json.dumps(JEE_LOGIC, indent=2)}

MECHANISMS:
1. SN1: Rate=k[RX], Racemization, NGP: 10^3-10^14×
2. SN2: Rate=k[Nu][RX], Inversion, 180°
3. NGP: π(10^6-10^14×), n(10^3-10^11×)
4. E1/E2: Anti-periplanar, Zaitsev/Hofmann

TRIPLE-STRATEGY:

STRATEGY 1 - SYSTEMATIC:
Step 1: List molecules, options
Step 2: Compare features
Step 3: Test mechanisms
Step 4: Eliminate wrong
Step 5: Deep analysis
Step 6: JEE trap check
ANSWER: Option [?], Confidence: [?]%

STRATEGY 2 - MS CHOUHAN:
Find KEY DIFFERENCE
Quantify: 10^X because [reason]
ANSWER: Option [?], Confidence: [?]%

STRATEGY 3 - BRUICE:
Orbital analysis, mechanism, Hammond
ANSWER: Option [?], Confidence: [?]%

FINAL:
Agreement? [YES/NO]
Trap Check: [verify]
ULTIMATE ANSWER: Option ([Letter])
ONE-SENTENCE: [explain]
CONFIDENCE: [90-100%]

FORMAT: _X=subscript, ^X=superscript, ->=arrow
BEGIN:"""

# ============================================================================
# IMAGE PROCESSING
# ============================================================================

async def enhance_image(img_bytes):
    try:
        img = Image.open(BytesIO(img_bytes))
        if img.mode == 'RGBA':
            bg = Image.new('RGB', img.size, (255,255,255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        if max(img.size) > 2048:
            ratio = 2048 / max(img.size)
            img = img.resize(tuple(int(d*ratio) for d in img.size), Image.Resampling.LANCZOS)

        img = ImageEnhance.Contrast(img).enhance(1.3)
        img = ImageEnhance.Sharpness(img).enhance(1.2)
        img = ImageEnhance.Brightness(img).enhance(1.1)

        out = BytesIO()
        img.save(out, format='JPEG', quality=98)
        return out.getvalue()
    except Exception as e:
        logger.error(f"Enhance error: {e}")
        return img_bytes

# ============================================================================
# GEMINI API
# ============================================================================

async def call_gemini(img_bytes, question=""):
    global current_key_index

    img_bytes = await enhance_image(img_bytes)
    img = Image.open(BytesIO(img_bytes))
    if img.mode != 'RGB':
        img = img.convert('RGB')

    out = BytesIO()
    img.save(out, format='JPEG', quality=98)
    b64 = base64.b64encode(out.getvalue()).decode()

    prompt = build_prompt()
    if question:
        prompt = f"Context: {question}\n\n{prompt}"

    for attempt in range(len(GEMINI_API_KEYS)):
        try:
            key = GEMINI_API_KEYS[current_key_index]
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={key}"

            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "image/jpeg", "data": b64}}
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.05,
                    "topP": 0.9,
                    "topK": 30,
                    "maxOutputTokens": 8192
                },
                "safetySettings": [
                    {"category": cat, "threshold": "BLOCK_NONE"}
                    for cat in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", 
                               "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]
                ]
            }

            async with httpx.AsyncClient(timeout=300.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    raise Exception(f"API {resp.status_code}: {resp.text[:100]}")
                
                result = resp.json()
                solution = result['candidates'][0]['content']['parts'][0]['text']
                logger.info(f"✅ Solution: {len(solution)} chars")
                return solution

        except Exception as e:
            logger.error(f"Key {current_key_index+1} failed: {str(e)[:100]}")
            current_key_index = (current_key_index + 1) % len(GEMINI_API_KEYS)
            if attempt < len(GEMINI_API_KEYS) - 1:
                await asyncio.sleep(3)
            else:
                raise

# ============================================================================
# PDF GENERATION (uses DARK_MODE_CSS from phase1_features)
# ============================================================================

LIGHT_CSS = """
@page { size: A4; margin: 2cm; }
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: Arial, sans-serif; font-size: 11pt; line-height: 1.6; color: #1a1a1a; }
.header { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; }
.header h1 { font-size: 24pt; font-weight: bold; }
.section-title { font-size: 15pt; font-weight: bold; color: #667eea; border-bottom: 3px solid #667eea; margin: 20px 0 10px; }
.strategy-box { background: #f8f9fa; border-left: 5px solid #667eea; padding: 20px; margin: 20px 0; border-radius: 6px; }
.answer-box { background: #e7f3ff; border: 3px solid #2196F3; padding: 20px; border-radius: 10px; margin: 25px 0; }
.answer-content { font-size: 12pt; font-weight: bold; color: #0d47a1; }
.confidence { background: #4CAF50; color: white; padding: 4px 12px; border-radius: 15px; font-size: 9pt; }
.footer { margin-top: 40px; padding-top: 15px; border-top: 2px solid #e0e0e0; text-align: center; font-size: 9pt; color: #666; }
p { margin: 8px 0; }
strong { font-weight: bold; color: #2c3e50; }
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Chemistry Report</title></head>
<body>
<div class="header">
<h1>🔬 Ultimate Chemistry Analysis</h1>
<div>📅 {{ date }}</div>
</div>
{{ content }}
<div class="footer">
<p>Ultimate Chemistry Bot | Phase 2 | GitHub + Gemini AI</p>
</div>
</body>
</html>"""

def format_html(text):
    text = text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    text = re.sub(r'_(\d+)', r'<sub>\1</sub>', text)
    text = re.sub(r'\^(\d+)', r'<sup>\1</sup>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    return text

def parse_to_html(solution):
    lines = solution.split('\n')
    parts = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith(('Answering', 'BEGIN')):
            continue
        
        if 'STRATEGY' in line.upper():
            parts.append(f'<div class="strategy-box"><strong>{format_html(line)}</strong>')
        elif 'ANSWER:' in line or 'Confidence:' in line:
            parts.append(f'<p><strong>{format_html(line)}</strong></p></div>')
        elif 'ULTIMATE ANSWER' in line or 'FINAL ANSWER' in line:
            match = re.search(r'Option\s*\(([A-D])\)', line, re.I)
            if match:
                parts.append(f'<div class="answer-box"><div class="answer-content">Option ({match.group(1)})</div></div>')
        elif len(line) > 10:
            parts.append(f'<p>{format_html(line)}</p>')
    
    return '\n'.join(parts)

def create_pdf(solution, mode='light'):
    try:
        content = parse_to_html(solution)
        template = Template(HTML_TEMPLATE)
        html_out = template.render(content=content, date=datetime.now().strftime('%B %d, %Y'))
        
        css = DARK_MODE_CSS if mode == 'dark' else LIGHT_CSS
        full_html = f"<!DOCTYPE html><html><head><style>{css}</style></head><body>{html_out}</body></html>"
        
        pdf_buf = BytesIO()
        HTML(string=full_html).write_pdf(pdf_buf)
        pdf_buf.seek(0)
        return pdf_buf
    except Exception as e:
        logger.error(f"PDF error: {e}")
        raise

# ============================================================================
# COMMAND HANDLERS
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    if await check_maintenance(update, context):
        return
    if is_banned(user_id):
        await update.message.reply_text("⛔ Banned. Contact admin.")
        return
    
    if track_new_user(user_id, username):
        await notify_new_user(user_id, username, context)
    
    status = "✅" if chemistry_knowledge_base else "⏳"
    await update.message.reply_text(
        f"🔬 *ULTIMATE CHEMISTRY BOT - PHASE 2*\n\n"
        f"📚 Knowledge: {status}\n\n"
        f"*CORE:*\n📸 Problem solving\n💬 Text queries\n🌙 Dark mode\n\n"
        f"*PHASE 2:*\n🧬 /molecule - 3D molecules\n🗺️ /conceptmap - Concept maps\n"
        f"💡 /hint - Progressive hints\n🃏 /flashcard - Flashcards\n"
        f"📝 /mocktest - Practice tests\n🎯 /difficulty - Predict level\n"
        f"🔢 /pka - pKa estimates\n📊 /jeefrequency - Topic stats\n\n"
        f"*INFO:*\n/help - Guide\n/settings - Preferences\n/about - Stats",
        parse_mode='Markdown'
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *HELP*\n\n"
        "*Problem Solving:*\n📸 Send clear photo → Wait 3-8 min → Get PDF\n\n"
        "*Quick Answers:*\n💬 Type question → Get 2-3 line answer\n\n"
        "*Phase 2 Tools:*\n"
        "/molecule CH4 - 3D molecule\n"
        "/conceptmap SN1 - Concept map\n"
        "/hint - Get progressive hints\n"
        "/flashcard - Study cards\n"
        "/mocktest - Practice exam\n"
        "/difficulty - Check problem level\n"
        "/pka CH3COOH - Estimate pKa\n"
        "/jeefrequency NGP - Topic stats\n\n"
        "/settings - Change PDF mode\n"
        "/about - Bot info",
        parse_mode='Markdown'
    )

async def about_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime = datetime.now() - bot_start_time
    await update.message.reply_text(
        f"ℹ️ *ABOUT*\n\n"
        f"🔬 Ultimate Chemistry Bot Phase 2\n"
        f"👥 Users: {len(all_users)}\n"
        f"📊 Solved: {total_problems_solved}\n"
        f"⏱️ Uptime: {uptime.days}d {uptime.seconds//3600}h\n\n"
        f"✨ Features: Triple-strategy, GitHub DB, Mock tests\n"
        f"👨‍💻 Dev: {ADMIN_USERNAME}",
        parse_mode='Markdown'
    )

async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    mode = get_user_preference(user_id, 'pdf_mode', 'light')
    
    keyboard = [
        [
            InlineKeyboardButton(f"{'✅' if mode=='light' else '◻️'} Light", callback_data="mode_light"),
            InlineKeyboardButton(f"{'✅' if mode=='dark' else '◻️'} Dark", callback_data="mode_dark")
        ]
    ]
    
    await update.message.reply_text(
        f"⚙️ *SETTINGS*\n\nPDF Mode: {'☀️ Light' if mode=='light' else '🌙 Dark'}\n\n_Tap to change:_",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not chemistry_knowledge_base:
        await update.message.reply_text("⏳ Not loaded yet!")
        return
    
    stats = "📊 *KNOWLEDGE*\n\n"
    for sec, data in chemistry_knowledge_base.items():
        if sec == "jee_logic":
            stats += "🎯 JEE Logic: ✅\n"
        elif isinstance(data, list):
            stats += f"📚 {sec}: {len(data)}\n"
    
    await update.message.reply_text(stats, parse_mode='Markdown')

async def skip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_feedback_comment'):
        context.user_data['awaiting_feedback_comment'] = False
        await update.message.reply_text("👍 Skipped! Send another problem 📸")
    else:
        await update.message.reply_text("Nothing to skip!")

# ============================================================================
# PHOTO HANDLER
# ============================================================================

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    if await check_maintenance(update, context):
        return
    if is_banned(user_id):
        await update.message.reply_text("⛔ Banned.")
        return
    
    try:
        # Check PDF mode
        pdf_mode = get_user_preference(user_id, 'pdf_mode')
        if not pdf_mode or not get_user_preference(user_id, 'asked_mode', False):
            result = await ask_pdf_mode(update, context)
            if result is None:
                return
            pdf_mode = result
        
        status = await update.message.reply_text(
            "🔬 *ANALYZING*\n\n📸 Image received\n⏳ Please wait...",
            parse_mode='Markdown'
        )

        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        img_bytes = await file.download_as_bytearray()
        question = update.message.caption or ""

        start = time.time()

        # Download knowledge if needed
        if not chemistry_knowledge_base:
            await status.edit_text("🔬 *ANALYZING*\n\n📥 Loading knowledge (30-60s first time)...")
            await download_knowledge()

        await status.edit_text("🔬 *ANALYZING*\n\n🧠 Running triple-strategy...\n⏱️ 2-5 min")

        # Call Gemini
        solution = await call_gemini(bytes(img_bytes), question)
        elapsed = int(time.time() - start)

        await status.edit_text(f"✅ *DONE*\n\n⏱️ {elapsed}s\n📄 Creating PDF...")

        # Generate PDF
        pdf_mode = get_user_preference(user_id, 'pdf_mode', 'light')
        pdf = create_pdf(solution, pdf_mode)
        filename = f"Chem_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        # Send PDF
        await update.message.reply_document(
            document=pdf,
            filename=filename,
            caption=f"✅ Complete! ⏱️ {elapsed}s\n🎯 Phase 2 Analysis",
            parse_mode='Markdown'
        )

        await status.delete()
        
        # Track & feedback
        track_problem_solved(user_id)
        await request_feedback(update, context)
        await notify_problem_solved(user_id, username, elapsed, context, BytesIO(img_bytes))
        
        logger.info(f"✅ {elapsed}s for {username}")

    except Exception as e:
        logger.error(f"Photo error: {e}", exc_info=True)
        await notify_error(str(e), context)
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}\n\nRetry with clearer image.")

# ============================================================================
# TEXT HANDLER
# ============================================================================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    text = update.message.text
    
    if await check_maintenance(update, context):
        return
    if is_banned(user_id):
        return
    
    # Check feedback comment
    if context.user_data.get('awaiting_feedback_comment'):
        feedback = await collect_feedback_comment(text, update, context)
        if feedback:
            await notify_feedback(feedback['user_id'], feedback['username'], 
                                 feedback['rating'], feedback['comment'], context)
        return
    
    # Check detailed request
    if await handle_detailed_request(text, update, context):
        return
    
    # Handle text query
    result = await handle_text_query(text, update, context)
    
    if result == "spam_detected":
        is_spam, spam_type, count = detect_spam(user_id, text)
        if is_spam:
            recent = [msg for ts, msg in user_message_history[user_id][-10:]]
            await notify_spam_detected(user_id, username, spam_type, count, recent, context)
    elif result == "answered":
        track_text_query(user_id)

# ============================================================================
# CALLBACK HANDLERS
# ============================================================================

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    # Feedback callbacks (Phase 1)
    if data.startswith('rate_'):
        await query.answer()
        rating = data.replace('rate_', '')
        user_id = query.from_user.id
        username = query.from_user.username or "Unknown"
        
        context.user_data['rating'] = rating
        context.user_data['awaiting_feedback_comment'] = True
        track_feedback(rating)
        
        await query.edit_message_text(
            f"✅ *Rated: {rating}/10*\n\nType comment or /skip\n\n_Thank you! 🙏_",
            parse_mode='Markdown'
        )
        await notify_feedback(user_id, username, rating, None, context)
    
    elif data == 'add_comment':
        await query.answer()
        context.user_data['awaiting_feedback_comment'] = True
        await query.edit_message_text(
            "💬 *Type your feedback:*\n\nOr /skip to finish.",
            parse_mode='Markdown'
        )
    
    elif data == 'skip_feedback':
        await query.answer()
        await query.edit_message_text("👍 Thanks! Send another problem 📸")
    
    # PDF mode callbacks
    elif data.startswith('mode_'):
        await query.answer()
        user_id = query.from_user.id
        mode = data.replace('mode_', '')
        
        set_user_preference(user_id, 'pdf_mode', mode)
        set_user_preference(user_id, 'asked_mode', True)
        
        emoji = '☀️' if mode == 'light' else '🌙'
        await query.edit_message_text(
            f"{emoji} *PDF Mode: {mode.title()}*\n\n_Change anytime with /settings_",
            parse_mode='Markdown'
        )
    
    # Phase 2 - Hint callbacks
    elif data.startswith('hint_'):
        if data == 'hint_next':
            await handle_hint_next(update, context)
        elif data == 'hint_stop':
            await handle_hint_stop(await handle_hint_stop(update, context)
        elif data == 'hint_reset':
            await handle_hint_reset(update, context)
    
    # Phase 2 - Flashcard callbacks
    elif data.startswith('flashcard_'):
        topic = data.replace('flashcard_', '')
        await handle_flashcard_topic(update, context, topic)
    
    # Phase 2 - Theme callbacks
    elif data.startswith('theme_'):
        theme = data.replace('theme_', '')
        await handle_theme_selection(update, context, theme)
    
    # Phase 2 - Mock test callbacks
    elif data == 'mock_config_start':
        await start_mock_test_config(update, context)
    
    elif data.startswith('mock_q_'):
        count = int(data.replace('mock_q_', ''))
        await handle_question_count(update, context, count)
    
    elif data.startswith('mock_t_'):
        time_key = data.replace('mock_t_', '')
        await handle_time_limit(update, context, time_key)
    
    elif data.startswith('mock_d_'):
        difficulty = data.replace('mock_d_', '')
        await handle_difficulty_selection(update, context, difficulty)
    
    elif data.startswith('mock_ans_'):
        parts = data.split('_')
        q_num = int(parts[2])
        answer = parts[3]
        await handle_answer(update, context, q_num, answer)

# ============================================================================
# PHASE 2 COMMAND WRAPPERS
# ============================================================================

async def molecule_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /molecule command"""
    if len(context.args) < 1:
        await update.message.reply_text(
            "🧬 *3D MOLECULE VIEWER*\n\n"
            "Usage: `/molecule <formula>`\n\n"
            "*Examples:*\n"
            "/molecule CH4\n"
            "/molecule C6H6\n"
            "/molecule CH3CH2OH\n\n"
            "_Interactive Three.js visualization!_",
            parse_mode='Markdown'
        )
        return
    
    formula = ''.join(context.args)
    await visualize_molecule_command(update, context, formula)

async def conceptmap_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /conceptmap command"""
    if len(context.args) < 1:
        await update.message.reply_text(
            "🗺️ *CONCEPT MAP*\n\n"
            "Usage: `/conceptmap <topic>`\n\n"
            "*Examples:*\n"
            "/conceptmap SN1\n"
            "/conceptmap NGP\n"
            "/conceptmap E2\n\n"
            "_Interactive D3.js mind map!_",
            parse_mode='Markdown'
        )
        return
    
    topic = ' '.join(context.args)
    await visualize_concept_map_command(update, context, topic)

async def difficulty_analyze_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input after /difficulty command"""
    if len(context.args) < 1:
        await phase2_difficulty(update, context)
    else:
        text = ' '.join(context.args)
        await analyze_difficulty_text(update, context, text)

async def pka_analyze_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /pka with molecule"""
    if len(context.args) < 1:
        await pka_command(update, context)
    else:
        molecule = ' '.join(context.args)
        await analyze_pka_text(update, context, molecule)

async def jeefreq_analyze_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /jeefrequency with topic"""
    if len(context.args) < 1:
        await jee_frequency_command(update, context)
    else:
        topic = ' '.join(context.args)
        await analyze_jee_frequency_text(update, context, topic)

# ============================================================================
# STARTUP
# ============================================================================

async def startup():
    logger.info("="*70)
    logger.info("🔬 ULTIMATE CHEMISTRY BOT - PHASE 2 STARTUP")
    logger.info("="*70)
    logger.info("📂 Checking cache...")

    if not load_cache():
        logger.info("🌐 Downloading from GitHub...")
        await download_knowledge()
    else:
        logger.info("✅ Using cached knowledge")

    logger.info("="*70)
    logger.info(f"✅ Sections: {len(chemistry_knowledge_base)}")
    logger.info(f"✅ API Keys: {len(GEMINI_API_KEYS)}")
    logger.info(f"✅ Admin: {ADMIN_USERNAME}")
    logger.info(f"✅ Phase: 2 (Complete)")
    logger.info("="*70)

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("="*70)
    print("🔬 ULTIMATE CHEMISTRY BOT - PHASE 2")
    print("   All Phase 1 + Phase 2 Features Integrated")
    print("="*70)

    app = Application.builder().token(BOT_TOKEN).build()
    
    # Core commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("about", about_cmd))
    app.add_handler(CommandHandler("settings", settings_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("skip", skip_cmd))
    
    # Phase 1 - Admin commands
    app.add_handler(CommandHandler("admin_ban", admin_ban_command))
    app.add_handler(CommandHandler("admin_unban", admin_unban_command))
    app.add_handler(CommandHandler("admin_stats", admin_stats_command))
    app.add_handler(CommandHandler("admin_maintenance", admin_maintenance_command))
    app.add_handler(CommandHandler("admin_broadcast", admin_broadcast_command))
    app.add_handler(CommandHandler("admin_users", admin_users_command))
    app.add_handler(CommandHandler("admin_warn", admin_warn_command))
    app.add_handler(CommandHandler("admin_ignore", admin_ignore_command))
    app.add_handler(CommandHandler("admin_help", admin_help_command))
    
    # Phase 2 - Visualization commands
    app.add_handler(CommandHandler("molecule", molecule_cmd))
    app.add_handler(CommandHandler("conceptmap", conceptmap_cmd))
    
    # Phase 2 - Learning tools
    app.add_handler(CommandHandler("hint", phase2_hint))
    app.add_handler(CommandHandler("flashcard", phase2_flashcard))
    app.add_handler(CommandHandler("theme", phase2_theme))
    
    # Phase 2 - Exam tools
    app.add_handler(CommandHandler("mocktest", mock_test_command))
    app.add_handler(CommandHandler("difficulty", difficulty_analyze_cmd))
    app.add_handler(CommandHandler("pka", pka_analyze_cmd))
    app.add_handler(CommandHandler("jeefrequency", jeefreq_analyze_cmd))
    
    # Unified callback handler
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    
    # Message handlers
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Run startup
    loop = asyncio.get_event_loop()
    loop.run_until_complete(startup())

    print("✅ Bot ready with Phase 2 features!")
    print("="*70)
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Stopped")
        print("💾 Knowledge cached!")
    except Exception as e:
        logger.error(f"\n🚨 FATAL: {e}", exc_info=True)
```
