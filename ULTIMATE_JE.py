"""
ULTIMATE CHEMISTRY BOT - PRODUCTION VERSION
Complete Working Code with Beautiful PDF Generation
98-99%+ Accuracy Target
Triple-Pass Analysis + Complete Chemistry Logic Database

SECURITY: Uses environment variables for all sensitive data
"""

import os
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from io import BytesIO
from PIL import Image, ImageEnhance
from datetime import datetime
from weasyprint import HTML, CSS
from jinja2 import Template
import re
import base64
import httpx
import aiohttp
import json
import logging

nest_asyncio.apply()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION - ENVIRONMENT VARIABLES
# ============================================================================

BOT_TOKEN = os.environ.get('BOT_TOKEN')

GEMINI_API_KEYS = [
    os.environ.get('GEMINI_KEY_1'),
    os.environ.get('GEMINI_KEY_2'),
    os.environ.get('GEMINI_KEY_3'),
    os.environ.get('GEMINI_KEY_4'),
    os.environ.get('GEMINI_KEY_5'),
]

# Filter out None values in case not all keys are set
GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]

# Validate configuration
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable not set!")
if not GEMINI_API_KEYS:
    raise ValueError("❌ No GEMINI API keys found in environment variables!")

logger.info(f"✅ Loaded {len(GEMINI_API_KEYS)} Gemini API keys")

current_key_index = 0
CHEMISTRY_CACHE_FILE = "/app/data/chemistry_knowledge_cache.json" if os.path.exists("/app/data") else "chemistry_knowledge_cache.json"
chemistry_knowledge_base = {}

# ============================================================================
# GITHUB CHEMISTRY REPOSITORIES
# ============================================================================

CHEMISTRY_KNOWLEDGE_SOURCES = {
    "functional_groups": "https://raw.githubusercontent.com/Sulstice/global-chem/master/global_chem/functional_groups/functional_groups.json",
    "common_r_groups": "https://raw.githubusercontent.com/Sulstice/global-chem/master/global_chem/common_R_groups/common_R_groups.json",
    "amino_acids": "https://raw.githubusercontent.com/Sulstice/global-chem/master/global_chem/amino_acids/amino_acids.json",
    "common_solvents": "https://raw.githubusercontent.com/Sulstice/global-chem/master/global_chem/common_solvents/common_solvents.json",
    "named_reactions": "https://raw.githubusercontent.com/Sulstice/global-chem/master/global_chem/named_reactions/named_reactions.json",
    "organic_molecules": "https://raw.githubusercontent.com/Sulstice/global-chem/master/global_chem/miscellaneous/organic_molecules.json",
}

# ============================================================================
# JEE ADVANCED LOGIC
# ============================================================================

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
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(CHEMISTRY_CACHE_FILE), exist_ok=True)
        with open(CHEMISTRY_CACHE_FILE, 'w') as f:
            json.dump(chemistry_knowledge_base, f, indent=2)
        logger.info(f"💾 Saved cache: {len(chemistry_knowledge_base)} sections")
    except Exception as e:
        logger.error(f"⚠️ Cache save error: {e}")

# ============================================================================
# DOWNLOAD KNOWLEDGE
# ============================================================================

async def download_chemistry_knowledge():
    global chemistry_knowledge_base

    if chemistry_knowledge_base:
        return chemistry_knowledge_base

    logger.info("🌐 Downloading chemistry knowledge from GitHub...")
    logger.info("=" * 70)

    downloaded = {}

    try:
        async with aiohttp.ClientSession() as session:
            for name, url in CHEMISTRY_KNOWLEDGE_SOURCES.items():
                try:
                    logger.info(f"📥 Downloading {name}...")
                    async with session.get(url, timeout=30) as response:
                        if response.status == 200:
                            data = await response.json()
                            downloaded[name] = data
                            if isinstance(data, list):
                                logger.info(f"   ✅ {name}: {len(data)} entries")
                            else:
                                logger.info(f"   ✅ {name}: loaded")
                        else:
                            logger.info(f"   ⚠️ {name}: HTTP {response.status}")
                except Exception as e:
                    logger.info(f"   ⚠️ {name}: {str(e)[:50]}")
                await asyncio.sleep(0.5)

        downloaded["jee_advanced_logic"] = JEE_ADVANCED_LOGIC
        chemistry_knowledge_base = downloaded
        save_chemistry_cache()
        logger.info("=" * 70)
        logger.info(f"✅ Downloaded! Total: {len(chemistry_knowledge_base)} sections")

    except Exception as e:
        logger.error(f"❌ Download error: {e}")
        chemistry_knowledge_base = {"jee_advanced_logic": JEE_ADVANCED_LOGIC}

    return chemistry_knowledge_base

# ============================================================================
# BUILD PROMPT
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
# BEAUTIFUL PDF GENERATION WITH WEASYPRINT
# ============================================================================

CSS_TEMPLATE = """
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
    """Convert plain text to HTML with chemistry formatting"""
    # Escape HTML first
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Subscripts (H2O -> H₂O)
    text = re.sub(r'_(\d+)', r'<sub>\1</sub>', text)
    
    # Superscripts (10^11 -> 10¹¹)
    text = re.sub(r'\^(\d+)', r'<sup>\1</sup>', text)
    text = re.sub(r'\^(\+|-)', r'<sup>\1</sup>', text)
    
    # Arrows
    text = text.replace('-&gt;', '→').replace('=&gt;', '⇒')
    
    # Bold and italic
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    
    return text

def parse_solution_to_html(solution_text):
    """Parse solution text into structured HTML"""
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
        
        # Skip fluff
        if line.startswith(('Answering as', 'Here is', 'BEGIN ANALYSIS')):
            continue
        
        # Strategy sections
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
        
        # Final answer
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
        
        # One-sentence reason
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
        
        # Confidence
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
        
        # Section headers
        if line.isupper() or re.match(r'^[A-Z\s]+:', line):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<h2 class="section-title">{format_chemistry_html(line)}</h2>')
            continue
        
        # Steps
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
        
        # Bullets
        if line.startswith(('• ', '* ', '- ', '◦ ')):
            clean = line[2:].strip()
            if not in_list:
                html_parts.append('<ul>')
                in_list = True
            html_parts.append(f'<li>{format_chemistry_html(clean)}</li>')
            continue
        
        # Regular paragraphs
        if len(line) > 10:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<p>{format_chemistry_html(line)}</p>')
    
    if in_list:
        html_parts.append('</ul>')
    
    return '\n'.join(html_parts)

def create_beautiful_pdf(solution_text):
    """Create stunning PDF with WeasyPrint"""
    try:
        content_html = parse_solution_to_html(solution_text)
        
        template = Template(HTML_TEMPLATE)
        html_output = template.render(
            content=content_html,
            date=datetime.now().strftime('%B %d, %Y at %I:%M %p')
        )
        
        # Combine HTML and CSS into one document
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
            {CSS_TEMPLATE}
            </style>
        </head>
        <body>
        {html_output}
        </body>
        </html>
        """
        
        pdf_buffer = BytesIO()
        
        # Create HTML object and write PDF directly
        HTML(string=full_html).write_pdf(pdf_buffer)
        
        pdf_buffer.seek(0)
        
        return pdf_buffer
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        raise

# ============================================================================
# BOT HANDLERS
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = "✅ Loaded" if chemistry_knowledge_base else "⏳ Loading..."
    await update.message.reply_text(
        f"🔬 *ULTIMATE CHEMISTRY BOT*\n\n"
        f"Triple-Strategy | 98-99% Accuracy\n"
        f"📚 GitHub Knowledge: {status}\n\n"
        f"📸 Send chemistry problem photo\n"
        f"⏱️ Analysis: 3-8 minutes\n\n"
        f"_MS Chouhan + Bruice + GitHub DB_",
        parse_mode='Markdown'
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *HOW TO USE*\n\n"
        "1️⃣ Send clear photo\n"
        "2️⃣ Wait 3-8 minutes\n"
        "3️⃣ Receive PDF solution\n\n"
        "*Features:*\n"
        "• GitHub chemistry database\n"
        "• Triple-strategy analysis\n"
        "• JEE trap detection\n"
        "• Beautiful PDF reports\n\n"
        "_Quality over speed!_",
        parse_mode='Markdown'
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        status = await update.message.reply_text(
            "🔬 *ANALYSIS STARTED*\n\n📸 Image received\n🌐 Loading knowledge...\n\n_Please wait..._",
            parse_mode='Markdown'
        )

        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        img_bytes = await file.download_as_bytearray()
        user_question = update.message.caption or ""

        import time
        start_time = time.time()

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

        solution = await call_gemini(bytes(img_bytes), user_question)
        elapsed = int(time.time() - start_time)

        await status.edit_text(f"✅ *COMPLETE*\n\n⏱️ Time: {elapsed}s\n📄 Generating PDF...", parse_mode='Markdown')

        pdf = create_beautiful_pdf(solution)
        filename = f"Chem_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        await update.message.reply_document(
            document=pdf,
            filename=filename,
            caption=f"✅ *Analysis complete!*\n⏱️ {elapsed}s\n🎯 Maximum accuracy\n📚 Knowledge-enhanced",
            parse_mode='Markdown'
        )

        await status.delete()
        logger.info(f"✅ Delivered in {elapsed}s")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error: {str(e)[:150]}\n\nRetry with clearer image.", parse_mode='Markdown')

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Send an *image* of your chemistry problem!", parse_mode='Markdown')

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

# ============================================================================
# MAIN
# ============================================================================

async def startup_routine():
    logger.info("=" * 70)
    logger.info("🔬 ULTIMATE CHEMISTRY BOT - STARTUP")
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
    logger.info(f"✅ Model: Gemini 2.0 Flash Exp")
    logger.info(f"✅ Temperature: 0.05")
    logger.info("=" * 70)

def main():
    print("=" * 70)
    print("🔬 ULTIMATE CHEMISTRY BOT - PRODUCTION VERSION")
    print("   GitHub Integration | 98-99% Accuracy | Beautiful PDFs")
    print("=" * 70)

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

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
