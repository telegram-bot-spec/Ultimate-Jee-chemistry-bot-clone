"""
ULTIMATE CHEMISTRY BOT - PHASE 1 COMPLETE & INTEGRATED
All features working: Text queries, Feedback, Dark mode, Admin tools

Author: @aryansmilezzz
Admin ID: 6298922725
Version: Phase 1 Final
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
from collections import defaultdict

# Import Phase 1 modules
from phase1_features import (
    handle_text_query,
    handle_detailed_request,
    collect_feedback_comment,
    get_user_preference,
    set_user_preference,
    check_rate_limit,
    is_spam_message,
    DARK_MODE_CSS
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
    notify_admin,
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
    bot_start_time
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
    raise ValueError("❌ BOT_TOKEN environment variable not set!")
if not GEMINI_API_KEYS:
    raise ValueError("❌ No GEMINI API keys found!")

logger.info(f"✅ Loaded {len(GEMINI_API_KEYS)} Gemini API keys")

current_key_index = 0
CHEMISTRY_CACHE_FILE = "/app/data/chemistry_knowledge_cache.json" if os.path.exists("/app/data") else "chemistry_knowledge_cache.json"
chemistry_knowledge_base = {}

# Donate QR (base64 embedded - you'll replace this with your actual QR)
DONATE_QR_BASE64 = None  # Set to None, will use file if available
DONATE_QR_PATH = "donate_qr.png"

# ============================================================================
# CHEMISTRY KNOWLEDGE SOURCES
# ============================================================================

CHEMISTRY_KNOWLEDGE_SOURCES = {
    "functional_groups": "https://raw.githubusercontent.com/Sulstice/global-chem/master/global_chem/functional_groups/functional_groups.json",
    "common_r_groups": "https://raw.githubusercontent.com/Sulstice/global-chem/master/global_chem/common_R_groups/common_R_groups.json",
    "amino_acids": "https://raw.githubusercontent.com/Sulstice/global-chem/master/global_chem/amino_acids/amino_acids.json",
    "common_solvents": "https://raw.githubusercontent.com/Sulstice/global-chem/master/global_chem/common_solvents/common_solvents.json",
    "named_reactions": "https://raw.githubusercontent.com/Sulstice/global-chem/master/global_chem/named_reactions/named_reactions.json",
    "organic_molecules": "https://raw.githubusercontent.com/Sulstice/global-chem/master/global_chem/miscellaneous/organic_molecules.json",
}

JEE_ADVANCED_LOGIC = {
    "mechanism_decision_trees": {
        "substitution": {
            "primary_substrate": "SN2 - Rate = k[Nu][RX], Inversion, 180° backside attack",
            "secondary_substrate": "Check NGP! π or n participation within 2-3 atoms gives 10^3-10^14 boost",
            "tertiary_substrate": "SN1 - Rate = k[RX], Racemization, NGP → 10^6-10^14 rate increase"
        }
    },
    "NGP_detection_rules": {
        "pi_participation": {
            "rate_boost": "10^6 to 10^14 times faster",
            "groups": ["C=C (allylic)", "benzene (benzylic)", "C≡C (propargylic)"]
        },
        "n_participation": {
            "rate_boost": "10^3 to 10^11 times faster",
            "groups": ["-OR", "-NR2", "-SR", "-OCOR"]
        }
    },
    "common_jee_traps": {
        "trap_1_NGP_missed": "Always check within 2-3 atoms for π-bonds or lone pairs",
        "trap_2_rate_magnitude": "Must know HOW MUCH faster (10^X)",
        "trap_3_acetal_definition": "R2C(OR')2 - TWO OR on SAME carbon only"
    }
}

# ============================================================================
# CACHE FUNCTIONS
# ============================================================================

def load_chemistry_cache():
    global chemistry_knowledge_base
    try:
        with open(CHEMISTRY_CACHE_FILE, 'r') as f:
            chemistry_knowledge_base = json.load(f)
        logger.info(f"📂 Loaded cache: {len(chemistry_knowledge_base)} sections")
        return True
    except:
        return False

def save_chemistry_cache():
    try:
        os.makedirs(os.path.dirname(CHEMISTRY_CACHE_FILE), exist_ok=True)
        with open(CHEMISTRY_CACHE_FILE, 'w') as f:
            json.dump(chemistry_knowledge_base, f, indent=2)
        logger.info(f"💾 Saved cache: {len(chemistry_knowledge_base)} sections")
    except Exception as e:
        logger.error(f"⚠️ Cache save error: {e}")

async def download_chemistry_knowledge():
    global chemistry_knowledge_base

    if chemistry_knowledge_base:
        return chemistry_knowledge_base

    logger.info("🌐 Downloading chemistry knowledge from GitHub...")
    downloaded = {}

    try:
        async with aiohttp.ClientSession() as session:
            for name, url in CHEMISTRY_KNOWLEDGE_SOURCES.items():
                try:
                    async with session.get(url, timeout=30) as response:
                        if response.status == 200:
                            data = await response.json()
                            downloaded[name] = data
                            if isinstance(data, list):
                                logger.info(f"✅ {name}: {len(data)} entries")
                        else:
                            logger.info(f"⚠️ {name}: HTTP {response.status}")
                except Exception as e:
                    logger.info(f"⚠️ {name}: {str(e)[:50]}")
                await asyncio.sleep(0.5)

        downloaded["jee_advanced_logic"] = JEE_ADVANCED_LOGIC
        chemistry_knowledge_base = downloaded
        save_chemistry_cache()
        logger.info(f"✅ Downloaded! Total: {len(chemistry_knowledge_base)} sections")

    except Exception as e:
        logger.error(f"❌ Download error: {e}")
        chemistry_knowledge_base = {"jee_advanced_logic": JEE_ADVANCED_LOGIC}

    return chemistry_knowledge_base

# ============================================================================
# PROMPT BUILDING
# ============================================================================

def build_enhanced_chemistry_prompt():
    knowledge_summary = ""

    if chemistry_knowledge_base:
        knowledge_summary = "\n🔬 INTEGRATED CHEMISTRY KNOWLEDGE BASE:\n"
        knowledge_summary += "═" * 70 + "\n"
        for section, data in chemistry_knowledge_base.items():
            if section != "jee_advanced_logic":
                if isinstance(data, list):
                    knowledge_summary += f"📚 {section}: {len(data)} entries\n"
        knowledge_summary += "═" * 70 + "\n"

    return f"""You are THE ULTIMATE CHEMISTRY EXPERT with complete chemical knowledge.

{knowledge_summary}

JEE ADVANCED LOGIC:
{json.dumps(JEE_ADVANCED_LOGIC, indent=2)}

CORE MECHANISMS:
1. SN1: R-X → R+ + X-, Rate = k[R-X], Racemization, NGP boost: 10^3-10^14×
2. SN2: Nu- + R-X → Nu-R + X-, Rate = k[Nu][R-X], Inversion, 180° attack
3. NGP: π-participation (10^6-10^14×), n-participation (10^3-10^11×)
4. E1/E2: Anti-periplanar, Zaitsev (or Hofmann with bulky base)

TRIPLE-STRATEGY ANALYSIS:

STRATEGY 1 - SYSTEMATIC:
Step 1: Observe image, list molecules, options
Step 2: Compare features (carbons, groups, leaving groups, NGP?)
Step 3: Test each option mechanism
Step 4: Eliminate impossible
Step 5: Deep analysis of remaining
Step 6: Verify against JEE traps
ANSWER: Option [?], Confidence: [?]%

STRATEGY 2 - MS CHOUHAN:
Find THE ONE KEY DIFFERENCE between molecules
Quantify rate effect: 10^X because [reason]
ANSWER: Option [?], Confidence: [?]%

STRATEGY 3 - PAULA BRUICE:
Orbital analysis, complete mechanism, Hammond postulate
ANSWER: Option [?], Confidence: [?]%

FINAL SYNTHESIS:
Agreement? [YES/NO]
JEE Trap Check: [verify]
ULTIMATE ANSWER: Option ([Letter])
ONE-SENTENCE REASON: [clear explanation]
FINAL CONFIDENCE: [90-100%]

FORMATTING: Use _X for subscripts, ^X for superscripts, -> for arrows
BEGIN ANALYSIS:"""

# ============================================================================
# IMAGE ENHANCEMENT
# ============================================================================

async def enhance_image(image_bytes):
    try:
        img = Image.open(BytesIO(image_bytes))
        if img.mode != 'RGB':
            if img.mode == 'RGBA':
                bg = Image.new('RGB', img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3])
                img = bg
            else:
                img = img.convert('RGB')

        if max(img.size) > 2048:
            ratio = 2048 / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        img = ImageEnhance.Contrast(img).enhance(1.3)
        img = ImageEnhance.Sharpness(img).enhance(1.2)
        img = ImageEnhance.Brightness(img).enhance(1.1)

        output = BytesIO()
        img.save(output, format='JPEG', quality=98)
        return output.getvalue()
    except Exception as e:
        logger.error(f"Enhancement failed: {e}")
        return image_bytes

# ============================================================================
# GEMINI API
# ============================================================================

async def call_gemini(image_bytes, user_question=""):
    global current_key_index

    image_bytes = await enhance_image(image_bytes)
    img = Image.open(BytesIO(image_bytes))
    if img.mode != 'RGB':
        img = img.convert('RGB')

    output = BytesIO()
    img.save(output, format='JPEG', quality=98)
    b64 = base64.b64encode(output.getvalue()).decode('utf-8')

    prompt = build_enhanced_chemistry_prompt()
    if user_question:
        prompt = f"Context: {user_question}\n\n" + prompt

    for attempt in range(len(GEMINI_API_KEYS)):
        try:
            api_key = GEMINI_API_KEYS[current_key_index]
            logger.info(f"Using API Key #{current_key_index + 1}")

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"

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
                    "maxOutputTokens": 8192,
                },
                "safetySettings": [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]
            }

            async with httpx.AsyncClient(timeout=300.0) as client:
                resp = await client.post(url, json=payload)

                if resp.status_code != 200:
                    raise Exception(f"API Error {resp.status_code}: {resp.text[:200]}")

                result = resp.json()
                solution = result['candidates'][0]['content']['parts'][0]['text']
                logger.info(f"✅ Solution generated ({len(solution)} chars)")
                return solution

        except Exception as e:
            logger.error(f"❌ Key #{current_key_index + 1} failed: {str(e)[:200]}")
            current_key_index = (current_key_index + 1) % len(GEMINI_API_KEYS)
            if attempt < len(GEMINI_API_KEYS) - 1:
                await asyncio.sleep(3)
                continue
            raise

# ============================================================================
# PDF GENERATION
# ============================================================================

LIGHT_MODE_CSS = """
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
    color: #1a1a1a;
    background: white;
}

.page {
    padding: 20px;
}

.header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
    opacity: 0.9;
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
    color: #667eea;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 3px solid #667eea;
}

.subsection-title {
    font-size: 12pt;
    font-weight: bold;
    color: #2c3e50;
    margin: 15px 0 10px 0;
    border-left: 4px solid #667eea;
    padding-left: 10px;
}

.strategy-box {
    background: #f8f9fa;
    border-left: 5px solid #667eea;
    padding: 20px;
    margin: 20px 0;
    border-radius: 6px;
    page-break-inside: avoid;
}

.strategy-header {
    font-size: 13pt;
    font-weight: bold;
    color: #667eea;
    margin-bottom: 12px;
}

.answer-box {
    background: #e7f3ff;
    border: 3px solid #2196F3;
    padding: 20px;
    border-radius: 10px;
    margin: 25px 0;
    page-break-inside: avoid;
}

.answer-label {
    font-size: 10pt;
    font-weight: bold;
    color: #1976D2;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}

.answer-content {
    font-size: 12pt;
    font-weight: bold;
    color: #0d47a1;
}

.confidence {
    display: inline-block;
    background: #4CAF50;
    color: white;
    padding: 4px 12px;
    border-radius: 15px;
    font-size: 9pt;
    font-weight: bold;
    margin-left: 8px;
}

.formula {
    font-family: 'Courier New', monospace;
    background: #f5f5f5;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 10pt;
}

.step {
    background: white;
    border: 2px solid #e0e0e0;
    padding: 15px;
    margin: 12px 0;
    border-radius: 6px;
    page-break-inside: avoid;
}

.success-box {
    background: #d4edda;
    border-left: 4px solid #28a745;
    padding: 12px 15px;
    margin: 12px 0;
    border-radius: 4px;
}

.footer {
    margin-top: 40px;
    padding-top: 15px;
    border-top: 2px solid #e0e0e0;
    text-align: center;
    font-size: 9pt;
    color: #666;
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
    color: #2c3e50;
}
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Chemistry Analysis Report</title>
</head>
<body>
    <div class="page">
        <div class="header">
            <h1>🔬 Ultimate Chemistry Analysis</h1>
            <div class="subtitle">Triple-Strategy Knowledge-Enhanced Solution</div>
            <div class="meta">
                <div>📅 {{ date }}</div>
                <div>⚡ Maximum Accuracy Mode</div>
            </div>
        </div>

        {{ content }}

        <div class="footer">
            <p>Generated by Ultimate Chemistry Bot | Powered by GitHub Knowledge Base + Gemini AI</p>
            <p>MS Chouhan Method • Paula Bruice Principles • JEE Advanced Logic</p>
        </div>
    </div>
</body>
</html>
"""

def format_chemistry_html(text):
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = re.sub(r'_(\d+)', r'<sub>\1</sub>', text)
    text = re.sub(r'\^(\d+)', r'<sup>\1</sup>', text)
    text = re.sub(r'\^(\+|-)', r'<sup>\1</sup>', text)
    text = text.replace('-&gt;', '→').replace('=&gt;', '⇒')
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    return text

def parse_solution_to_html(solution_text):
    lines = solution_text.split('\n')
    html_parts = []
    in_strategy = False
    strategy_content = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        
        if not line or line in ['***', '---', '═'*70, '━'*70]:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            continue
        
        if line.startswith(('Answering as', 'Here is', 'BEGIN ANALYSIS')):
            continue
        
        if 'STRATEGY' in line.upper():
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            if strategy_content:
                content = '\n'.join(strategy_content[1:])
                html_parts.append(
                    f'<div class="strategy-box">'
                    f'<div class="strategy-header">{format_chemistry_html(strategy_content[0])}</div>'
                    f'{content}'
                    f'</div>'
                )
                strategy_content = []
            in_strategy = True
            strategy_content.append(line)
            continue
        
        if in_strategy:
            if line.startswith('ANSWER:') or 'Confidence:' in line:
                formatted = format_chemistry_html(line)
                strategy_content.append(f'<p><strong>{formatted}</strong></p>')
                if 'Confidence:' in line:
                    in_strategy = False
                    content = '\n'.join(strategy_content[1:])
                    html_parts.append(
                        f'<div class="strategy-box">'
                        f'<div class="strategy-header">{format_chemistry_html(strategy_content[0])}</div>'
                        f'{content}'
                        f'</div>'
                    )
                    strategy_content = []
            else:
                strategy_content.append(f'<p>{format_chemistry_html(line)}</p>')
            continue
        
        if 'ULTIMATE ANSWER' in line or 'FINAL ANSWER' in line:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            answer_match = re.search(r'Option\s*\(([A-D])\)', line, re.IGNORECASE)
            if answer_match:
                option = answer_match.group(1)
                html_parts.append(
                    f'<div class="answer-box">'
                    f'<div class="answer-label">✅ Final Answer</div>'
                    f'<div class="answer-content">Option ({option})</div>'
                    f'</div>'
                )
            continue
        
        if 'ONE-SENTENCE REASON' in line:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            reason = line.split(':', 1)[1].strip() if ':' in line else line
            html_parts.append(
                f'<div class="success-box">'
                f'<strong>Explanation:</strong> {format_chemistry_html(reason)}'
                f'</div>'
            )
            continue
        
        if 'FINAL CONFIDENCE' in line or line.startswith('Confidence:'):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            conf_match = re.search(r'(\d+)%', line)
            if conf_match:
                confidence = conf_match.group(1)
                html_parts.append(
                    f'<p><strong>Confidence:</strong> '
                    f'<span class="confidence">{confidence}%</span></p>'
                )
            continue
        
        if line.isupper() or re.match(r'^[A-Z\s]+:', line):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<h2 class="section-title">{format_chemistry_html(line)}</h2>')
            continue
        
        if line.startswith('Step '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(
                f'<div class="step">'
                f'<strong>{format_chemistry_html(line)}</strong>'
                f'</div>'
            )
            continue
        
        if line.startswith(('• ', '* ', '- ', '◦ ')):
            clean = line[2:].strip()
            if not in_list:
                html_parts.append('<ul>')
                in_list = True
            html_parts.append(f'<li>{format_chemistry_html(clean)}</li>')
            continue
        
        if len(line) > 10:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<p>{format_chemistry_html(line)}</p>')
    
    if in_list:
        html_parts.append('</ul>')
    
    return '\n'.join(html_parts)

def get_pdf_css(mode='light'):
    """Get CSS based on mode"""
    if mode == 'dark':
        return DARK_MODE_CSS
    else:
        return LIGHT_MODE_CSS

def create_beautiful_pdf(solution_text, mode='light'):
    try:
        content_html = parse_solution_to_html(solution_text)
        
        template = Template(HTML_TEMPLATE)
        html_output = template.render(
            content=content_html,
            date=datetime.now().strftime('%B %d, %Y at %I:%M %p')
        )
        
        css = get_pdf_css(mode)
        
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
            {css}
            </style>
        </head>
        <body>
        {html_output}
        </body>
        </html>
        """
        
        pdf_buffer = BytesIO()
        html = HTML(string=full_html)
        html.write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
        return pdf_buffer
        
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        raise

# ============================================================================
# FEEDBACK HANDLERS
# ============================================================================

def create_feedback_keyboard():
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
    keyboard = create_feedback_keyboard()
    
    await update.message.reply_text(
        "⭐ *How was this solution?*\n\n"
        "Rate 1-10 so I can improve! 😊\n"
        "_Your feedback helps make me better!_",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def handle_rating_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    rating = query.data.replace("rate_", "")
    user = query.from_user
    username = user.username or "Unknown"
    user_id = user.id
    
    context.user_data['rating'] = rating
    context.user_data['awaiting_feedback_comment'] = True
    
    track_feedback(rating)
    
    await query.edit_message_text(
        f"✅ *You rated: {rating}/10*\n\n"
        f"Want to add a comment? (Optional)\n"
        f"Just type your feedback, or press /skip\n\n"
        f"_Thank you! 🙏_",
        parse_mode='Markdown'
    )
    
    # Notify admin
    await notify_feedback(user_id, username, rating, None, context)

async def handle_comment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['awaiting_feedback_comment'] = True
    
    await query.edit_message_text(
        "💬 *Please type your feedback:*\n\n"
        "Share your thoughts about the solution!\n"
        "Or press /skip to finish.\n\n"
        "_Your input helps me improve!_ 😊",
        parse_mode='Markdown'
    )

async def handle_skip_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "👍 *Thanks anyway!*\n\n"
        "Send me another problem anytime! 📸",
        parse_mode='Markdown'
    )

# ============================================================================
# PDF MODE HANDLERS
# ============================================================================

def create_mode_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("☀️ Light Mode", callback_data="mode_light"),
            InlineKeyboardButton("🌙 Dark Mode", callback_data="mode_dark"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def ask_pdf_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if get_user_preference(user_id, 'asked_mode', False):
        return get_user_preference(user_id, 'pdf_mode', 'light')
    
    keyboard = create_mode_keyboard()
    
    await update.message.reply_text(
        "🎨 *Choose PDF Style:*\n\n"
        "☀️ *Light Mode* - Classic white background\n"
        "🌙 *Dark Mode* - Easy on eyes for night study\n\n"
        "_You can change this anytime with /settings_",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    
    return None

async def handle_mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# ============================================================================
# BOT COMMAND HANDLERS
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    # Check maintenance
    if await check_maintenance(update, context):
        return
    
    # Check ban
    if is_banned(user_id):
        await update.message.reply_text(
            "⛔ You have been banned from using this bot.\n"
            "Contact admin if you think this is a mistake."
        )
        return
    
    # Track new user
    is_new = track_new_user(user_id, username)
    if is_new:
        await notify_new_user(user_id, username, context)
    
    status = "✅ Loaded" if chemistry_knowledge_base else "⏳ Loading..."
    await update.message.reply_text(
        f"🔬 *ULTIMATE CHEMISTRY BOT*\n\n"
        f"Triple-Strategy | 98-99% Accuracy\n"
        f"📚 GitHub Knowledge: {status}\n\n"
        f"📸 Send chemistry problem photo\n"
        f"💬 Ask text questions too!\n"
        f"⏱️ Analysis: 3-8 minutes\n\n"
        f"*Commands:*\n"
        f"/help - How to use\n"
        f"/settings - PDF mode & more\n"
        f"/donate - Support the bot ❤️\n\n"
        f"_MS Chouhan + Bruice + GitHub DB_",
        parse_mode='Markdown'
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *HOW TO USE*\n\n"
        "*For Problem Solving:*\n"
        "1️⃣ Send clear photo 📸\n"
        "2️⃣ Wait 3-8 minutes ⏱️\n"
        "3️⃣ Receive PDF solution 📄\n\n"
        "*For Quick Questions:*\n"
        "💬 Just type your question!\n"
        "Example: \"What is SN1?\"\n"
        "Get instant 2-3 line answers!\n\n"
        "*Features:*\n"
        "• GitHub chemistry database\n"
        "• Triple-strategy analysis\n"
        "• JEE trap detection\n"
        "• Beautiful PDF reports\n"
        "• Dark mode support 🌙\n\n"
        "*Commands:*\n"
        "/settings - Change PDF style\n"
        "/donate - Support development\n\n"
        "_Quality over speed!_",
        parse_mode='Markdown'
    )

async def about_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime = datetime.now() - bot_start_time
    
    await update.message.reply_text(
        f"ℹ️ *ABOUT THIS BOT*\n\n"
        f"🔬 *Ultimate Chemistry Bot*\n"
        f"AI-powered JEE chemistry solver\n\n"
        f"📊 *Stats:*\n"
        f"• Users: {len(all_users)}\n"
        f"• Problems solved: {total_problems_solved}\n"
        f"• Uptime: {uptime.days}d {uptime.seconds//3600}h\n\n"
        f"✨ *Features:*\n"
        f"• Triple-strategy analysis\n"
        f"• 98-99% accuracy target\n"
        f"• Text queries supported\n"
        f"• Dark mode PDFs\n"
        f"• GitHub knowledge base\n\n"
        f"👨‍💻 *Developer:* {ADMIN_USERNAME}\n"
        f"📅 *Version:* Phase 1\n\n"
        f"_Made with ❤️ for JEE aspirants_",
        parse_mode='Markdown'
    )

async def donate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Try to send QR image file
        if os.path.exists(DONATE_QR_PATH):
            with open(DONATE_QR_PATH, 'rb') as qr_file:
                await update.message.reply_photo(
                    photo=qr_file,
                    caption=(
                        "💖 *Support the Bot!*\n\n"
                        f"Scan the QR code to donate via UPI\n\n"
                        f"Your support helps keep this bot:\n"
                        f"• Free for everyone ✅\n"
                        f"• Running 24/7 ⚡\n"
                        f"• Getting better features 🚀\n\n"
                        f"_Every contribution matters! 🙏_\n\n"
                        f"Thank you for your support!\n"
                        f"- {ADMIN_USERNAME}"
                    ),
                    parse_mode='Markdown'
                )
        elif DONATE_QR_BASE64:
            # Try base64 if file not found
            qr_bytes = base64.b64decode(DONATE_QR_BASE64)
            await update.message.reply_photo(
                photo=BytesIO(qr_bytes),
                caption=(
                    "💖 *Support the Bot!*\n\n"
                    f"Scan the QR code to donate via UPI\n\n"
                    f"Your support helps keep this bot:\n"
                    f"• Free for everyone ✅\n"
                    f"• Running 24/7 ⚡\n"
                    f"• Getting better features 🚀\n\n"
                    f"_Every contribution matters! 🙏_\n\n"
                    f"Thank you for your support!\n"
                    f"- {ADMIN_USERNAME}"
                ),
                parse_mode='Markdown'
            )
        else:
            # Fallback message
            await update.message.reply_text(
                "💖 *Support the Bot!*\n\n"
                "Thank you for wanting to support!\n"
                f"Contact: {ADMIN_USERNAME}\n\n"
                "_QR code coming soon!_",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Donate command error: {e}")
        await update.message.reply_text(
            "💖 *Support the Bot!*\n\n"
            "Thank you for your interest!\n"
            f"Contact: {ADMIN_USERNAME}",
            parse_mode='Markdown'
        )

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not chemistry_knowledge_base:
        await update.message.reply_text("⏳ Not loaded yet. Send a problem first!")
        return

    stats = "📊 *KNOWLEDGE BASE*\n\n"
    for section, data in chemistry_knowledge_base.items():
        if section == "jee_advanced_logic":
            stats += "🎯 JEE Logic: ✅\n"
        elif isinstance(data, list):
            stats += f"📚 {section}: {len(data)} entries\n"
    stats += f"\n✅ Fully operational"
    await update.message.reply_text(stats, parse_mode='Markdown')

async def skip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /skip command"""
    if context.user_data.get('awaiting_feedback_comment'):
        context.user_data['awaiting_feedback_comment'] = False
        await update.message.reply_text(
            "👍 *Feedback skipped!*\n\nSend me another problem anytime! 📸",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "Nothing to skip right now!",
            parse_mode='Markdown'
        )

# ============================================================================
# PHOTO HANDLER
# ============================================================================

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    # Check maintenance
    if await check_maintenance(update, context):
        return
    
    # Check ban
    if is_banned(user_id):
        await update.message.reply_text("⛔ You are banned from using this bot.")
        return
    
    try:
        # Ask for PDF mode on first use
        pdf_mode = get_user_preference(user_id, 'pdf_mode')
        if not pdf_mode or not get_user_preference(user_id, 'asked_mode', False):
            result = await ask_pdf_mode(update, context)
            if result is None:
                return  # Waiting for user to choose mode
            pdf_mode = result
        
        status = await update.message.reply_text(
            "🔬 *ANALYSIS STARTED*\n\n📸 Image received\n🌐 Loading knowledge...\n\n_Please wait..._",
            parse_mode='Markdown'
        )

        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        img_bytes = await file.download_as_bytearray()
        user_question = update.message.caption or ""

        start_time = time.time()

        # Download knowledge if needed
        if not chemistry_knowledge_base:
            await status.edit_text(
                "🔬 *ANALYSIS STARTED*\n\n📥 Downloading knowledge base...\n⏱️ 30-60 seconds first time\n\n_Building logic..._",
                parse_mode='Markdown'
            )
            await download_chemistry_knowledge()

        await status.edit_text(
            "🔬 *ANALYSIS IN PROGRESS*\n\n✅ Knowledge loaded\n🧠 Running triple-strategy...\n⏱️ 2-5 min remaining\n\n_Analyzing..._",
            parse_mode='Markdown'
        )

        # Call Gemini
        solution = await call_gemini(bytes(img_bytes), user_question)
        elapsed = int(time.time() - start_time)

        await status.edit_text(
            f"✅ *COMPLETE*\n\n⏱️ Time: {elapsed}s\n📄 Generating PDF...",
            parse_mode='Markdown'
        )

        # Generate PDF with user's preferred mode
        pdf_mode = get_user_preference(user_id, 'pdf_mode', 'light')
        pdf = create_beautiful_pdf(solution, pdf_mode)
        filename = f"Chem_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        # Send PDF
        await update.message.reply_document(
            document=pdf,
            filename=filename,
            caption=f"✅ *Analysis complete!*\n⏱️ {elapsed}s\n🎯 Maximum accuracy\n📚 Knowledge-enhanced",
            parse_mode='Markdown'
        )

        await status.delete()
        
        # Track problem solved
        track_problem_solved(user_id)
        
        # Request feedback
        await request_feedback(update, context)
        
        # Notify admin
        await notify_problem_solved(user_id, username, elapsed, context, BytesIO(img_bytes))
        
        logger.info(f"✅ Delivered in {elapsed}s to {username}")

    except Exception as e:
        logger.error(f"Error in handle_photo: {e}", exc_info=True)
        await notify_error(str(e), context)
        await update.message.reply_text(
            f"❌ Error: {str(e)[:150]}\n\nRetry with clearer image.",
            parse_mode='Markdown'
        )

# ============================================================================
# TEXT HANDLER
# ============================================================================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    text = update.message.text
    
    # Check maintenance
    if await check_maintenance(update, context):
        return
    
    # Check ban
    if is_banned(user_id):
        return
    
    # Check if awaiting feedback comment
    if context.user_data.get('awaiting_feedback_comment'):
        feedback_data = await collect_feedback_comment(text, update, context)
        if feedback_data:
            # Notify admin with comment
            await notify_feedback(
                feedback_data['user_id'],
                feedback_data['username'],
                feedback_data['rating'],
                feedback_data['comment'],
                context
            )
        return
    
    # Check if awaiting detailed explanation
    handled = await handle_detailed_request(text, update, context)
    if handled:
        return
    
    # Handle text query
    result = await handle_text_query(text, update, context)
    
    if result == "spam_detected":
        # Detect spam
        is_spam, spam_type, count = detect_spam(user_id, text)
        if is_spam:
            recent_msgs = [msg for ts, msg in __import__('phase1_admin').user_message_history[user_id][-10:]]
            await notify_spam_detected(user_id, username, spam_type, count, recent_msgs, context)
    
    elif result == "answered":
        # Track text query
        track_text_query(user_id)
        # Notification already sent in handle_text_query
    
    elif result == "rate_limited":
        # Already handled in handle_text_query
        pass
    
    elif result == "unknown":
        # Unknown query - already handled
        pass

# ============================================================================
# STARTUP ROUTINE
# ============================================================================

async def startup_routine():
    logger.info("=" * 70)
    logger.info("🔬 ULTIMATE CHEMISTRY BOT - PHASE 1 STARTUP")
    logger.info("=" * 70)
    logger.info("📂 Checking cache...")

    if not load_chemistry_cache():
        logger.info("🌐 Downloading from GitHub...")
        await download_chemistry_knowledge()
    else:
        logger.info("✅ Using cached knowledge")

    logger.info("=" * 70)
    logger.info(f"✅ Sections: {len(chemistry_knowledge_base)}")
    logger.info(f"✅ API Keys: {len(GEMINI_API_KEYS)}")
    logger.info(f"✅ Admin ID: {ADMIN_ID}")
    logger.info(f"✅ Admin Username: {ADMIN_USERNAME}")
    logger.info(f"✅ Model: Gemini 2.0 Flash Exp")
    logger.info("=" * 70)

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("🔬 ULTIMATE CHEMISTRY BOT - PHASE 1")
    print("   Text Queries | Feedback | Dark Mode | Admin Tools")
    print("=" * 70)

    app = Application.builder().token(BOT_TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("about", about_cmd))
    app.add_handler(CommandHandler("donate", donate_cmd))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("skip", skip_cmd))
    
    # Admin commands
    app.add_handler(CommandHandler("admin_ban", admin_ban_command))
    app.add_handler(CommandHandler("admin_unban", admin_unban_command))
    app.add_handler(CommandHandler("admin_stats", admin_stats_command))
    app.add_handler(CommandHandler("admin_maintenance", admin_maintenance_command))
    app.add_handler(CommandHandler("admin_broadcast", admin_broadcast_command))
    app.add_handler(CommandHandler("admin_users", admin_users_command))
    app.add_handler(CommandHandler("admin_warn", admin_warn_command))
    app.add_handler(CommandHandler("admin_ignore", admin_ignore_command))
    app.add_handler(CommandHandler("admin_help", admin_help_command))
    
    # Callback query handlers
    app.add_handler(CallbackQueryHandler(handle_rating_callback, pattern="^rate_"))
    app.add_handler(CallbackQueryHandler(handle_comment_callback, pattern="^add_comment$"))
    app.add_handler(CallbackQueryHandler(handle_skip_callback, pattern="^skip_feedback$"))
    app.add_handler(CallbackQueryHandler(handle_mode_callback, pattern="^mode_"))
    
    # Message handlers
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Run startup
    loop = asyncio.get_event_loop()
    loop.run_until_complete(startup_routine())

    print("✅ Bot ready!")
    print("=" * 70)
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Stopped")
        print("💾 Knowledge cached!")
    except Exception as e:
        logger.error(f"\n🚨 FATAL: {e}", exc_info=True)
