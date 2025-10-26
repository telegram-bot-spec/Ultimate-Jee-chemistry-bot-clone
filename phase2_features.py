"""
PHASE 2 FEATURES MODULE
Hints System, Flashcard Generator, PDF Themes

Author: @aryansmilezzz
Admin ID: 6298922725
Phase: 2
"""

import random
import time
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# HINTS SYSTEM (5 Progressive Levels)
# ============================================================================

HINT_LEVELS = {
    1: "🔍 Hint 1: Identify the key structural features",
    2: "🔍 Hint 2: Consider the mechanism type (SN1, SN2, E1, E2)",
    3: "🔍 Hint 3: Check for NGP within 2-3 atoms",
    4: "🔍 Hint 4: Calculate the rate effect (10^X)",
    5: "🔍 Hint 5: Review stereochemistry and orbital overlap"
}

# Context-aware hints for different topics
TOPIC_HINTS = {
    "SN1": [
        "🔍 Hint 1: What type of substrate? (1°, 2°, 3°)",
        "🔍 Hint 2: SN1 forms carbocation - check stability!",
        "🔍 Hint 3: Look for NGP within 2-3 atoms (π or n)",
        "🔍 Hint 4: NGP gives 10³-10¹⁴× rate boost!",
        "🔍 Hint 5: SN1 → Racemization (unless NGP locks stereochem)"
    ],
    "SN2": [
        "🔍 Hint 1: Check substrate accessibility (1° best, 3° impossible)",
        "🔍 Hint 2: SN2 needs backside attack at 180°",
        "🔍 Hint 3: Rate = k[Nu][RX] - both matter!",
        "🔍 Hint 4: Inversion of stereochemistry (Walden inversion)",
        "🔍 Hint 5: Strong nucleophile + primary substrate = fast SN2"
    ],
    "NGP": [
        "🔍 Hint 1: Check within 2-3 atoms for π-bonds or lone pairs",
        "🔍 Hint 2: π-participation (C=C, benzene) = 10⁶-10¹⁴× boost",
        "🔍 Hint 3: n-participation (O, N, S) = 10³-10¹¹× boost",
        "🔍 Hint 4: NGP stabilizes transition state via orbital overlap",
        "🔍 Hint 5: THIS IS THE #1 JEE TRAP - rate magnitude!"
    ],
    "E1": [
        "🔍 Hint 1: E1 forms carbocation first (like SN1)",
        "🔍 Hint 2: Base removes β-hydrogen AFTER carbocation forms",
        "🔍 Hint 3: Follows Zaitsev's rule (more substituted alkene)",
        "🔍 Hint 4: Competes with SN1 - heat favors elimination",
        "🔍 Hint 5: Rate = k[substrate] only"
    ],
    "E2": [
        "🔍 Hint 1: Requires anti-periplanar geometry (180°)",
        "🔍 Hint 2: One-step: base removes H while X leaves",
        "🔍 Hint 3: Strong base + heat = E2 favored",
        "🔍 Hint 4: Zaitsev (strong base) vs Hofmann (bulky base)",
        "🔍 Hint 5: Rate = k[base][substrate]"
    ]
}

# Store user hint progress
user_hint_progress = {}  # {user_id: {"topic": "SN1", "level": 3, "context": "..."}}

def get_next_hint(user_id, topic=None, context=None):
    """
    Get next progressive hint for user
    Returns: (hint_text, level, can_continue)
    """
    if user_id not in user_hint_progress:
        user_hint_progress[user_id] = {"topic": topic, "level": 0, "context": context}
    
    progress = user_hint_progress[user_id]
    
    # Update context if provided
    if topic:
        progress["topic"] = topic
    if context:
        progress["context"] = context
    
    # Increment level
    progress["level"] += 1
    current_level = progress["level"]
    
    # Get hint based on topic or generic
    if progress["topic"] and progress["topic"].upper() in TOPIC_HINTS:
        hints = TOPIC_HINTS[progress["topic"].upper()]
        if current_level <= len(hints):
            hint = hints[current_level - 1]
        else:
            hint = "💡 All hints given! Try solving now."
            current_level = len(hints)
    else:
        # Generic hints
        if current_level in HINT_LEVELS:
            hint = HINT_LEVELS[current_level]
        else:
            hint = "💡 All hints given! Try solving now."
            current_level = 5
    
    can_continue = current_level < 5
    
    return hint, current_level, can_continue

def reset_hints(user_id):
    """Reset hint progress for user"""
    if user_id in user_hint_progress:
        del user_hint_progress[user_id]

def create_hint_keyboard(can_continue):
    """Create keyboard for hint system"""
    if can_continue:
        keyboard = [
            [
                InlineKeyboardButton("💡 Next Hint", callback_data="hint_next"),
                InlineKeyboardButton("🚫 Stop Hints", callback_data="hint_stop")
            ]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🔄 Start Over", callback_data="hint_reset")]
        ]
    return InlineKeyboardMarkup(keyboard)

# ============================================================================
# FLASHCARD GENERATOR (AI-Designed, Colorful)
# ============================================================================

FLASHCARD_TEMPLATES = {
    "neon": {
        "bg_colors": [(255, 0, 128), (0, 255, 255), (255, 255, 0)],
        "text_color": (255, 255, 255),
        "border_color": (255, 0, 255),
        "style": "bold"
    },
    "pastel": {
        "bg_colors": [(255, 182, 193), (173, 216, 230), (255, 218, 185)],
        "text_color": (50, 50, 50),
        "border_color": (200, 150, 200),
        "style": "normal"
    },
    "dark": {
        "bg_colors": [(30, 30, 30), (50, 50, 80), (60, 40, 60)],
        "text_color": (240, 240, 240),
        "border_color": (100, 200, 255),
        "style": "bold"
    },
    "handwritten": {
        "bg_colors": [(255, 250, 240), (240, 255, 240), (255, 240, 245)],
        "text_color": (40, 40, 40),
        "border_color": (100, 100, 100),
        "style": "handwritten"
    }
}

def generate_flashcard(front_text, back_text, template="pastel"):
    """
    Generate beautiful flashcard image
    Returns: (front_image_bytes, back_image_bytes)
    """
    # Card dimensions
    width, height = 800, 500
    
    # Get template
    theme = FLASHCARD_TEMPLATES.get(template, FLASHCARD_TEMPLATES["pastel"])
    
    # Generate front card
    front_img = create_card_side(front_text, "QUESTION", width, height, theme)
    front_bytes = BytesIO()
    front_img.save(front_bytes, format='PNG')
    front_bytes.seek(0)
    
    # Generate back card
    back_img = create_card_side(back_text, "ANSWER", width, height, theme)
    back_bytes = BytesIO()
    back_img.save(back_bytes, format='PNG')
    back_bytes.seek(0)
    
    return front_bytes, back_bytes

def create_card_side(text, label, width, height, theme):
    """Create one side of flashcard"""
    # Create image
    bg_color = random.choice(theme["bg_colors"])
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Add gradient effect (simple)
    for i in range(height):
        alpha = int(30 * (i / height))
        overlay = Image.new('RGB', (width, 1), (0, 0, 0))
        img.paste(overlay, (0, i), mask=None)
    
    # Border
    border_width = 10
    draw.rectangle(
        [(border_width, border_width), (width - border_width, height - border_width)],
        outline=theme["border_color"],
        width=border_width
    )
    
    # Try to load custom font, fallback to default
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
    
    # Draw label (QUESTION/ANSWER)
    label_bbox = draw.textbbox((0, 0), label, font=title_font)
    label_width = label_bbox[2] - label_bbox[0]
    label_height = label_bbox[3] - label_bbox[1]
    label_x = (width - label_width) // 2
    label_y = 50
    
    # Label background
    draw.rectangle(
        [(label_x - 20, label_y - 10), (label_x + label_width + 20, label_y + label_height + 10)],
        fill=theme["border_color"]
    )
    draw.text((label_x, label_y), label, fill=(255, 255, 255), font=title_font)
    
    # Draw main text (wrapped)
    wrapped_text = wrap_text(text, text_font, width - 100)
    text_y = 150
    
    for line in wrapped_text:
        bbox = draw.textbbox((0, 0), line, font=text_font)
        line_width = bbox[2] - bbox[0]
        line_x = (width - line_width) // 2
        draw.text((line_x, text_y), line, fill=theme["text_color"], font=text_font)
        text_y += bbox[3] - bbox[1] + 15
    
    # Add decorative elements
    if theme["style"] == "handwritten":
        # Add slight rotation/wobble effect
        img = img.rotate(random.uniform(-1, 1), expand=False)
    
    return img

def wrap_text(text, font, max_width):
    """Wrap text to fit within max_width"""
    lines = []
    words = text.split()
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

# Sample flashcard content
SAMPLE_FLASHCARDS = {
    "SN1": [
        {
            "front": "What is the rate law for SN1 reaction?",
            "back": "Rate = k[RX]\nUnimolecular - only substrate concentration matters!"
        },
        {
            "front": "SN1 carbocation stability order?",
            "back": "3° > 2° > 1° > methyl\nMore substituted = more stable (hyperconjugation)"
        }
    ],
    "NGP": [
        {
            "front": "NGP π-participation rate boost?",
            "back": "10⁶ to 10¹⁴ times faster!\nC=C, benzene, C≡C within 2-3 atoms"
        },
        {
            "front": "NGP n-participation rate boost?",
            "back": "10³ to 10¹¹ times faster!\nLone pairs from O, N, S atoms"
        }
    ]
}

# ============================================================================
# PDF THEMES (Neon, Minimal, Notebook)
# ============================================================================

THEME_NEON_CSS = """
@page { size: A4; margin: 2cm; }
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: 'Arial', sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #00ff00;
    background: #0a0a0a;
}

.header {
    background: linear-gradient(135deg, #ff00ff 0%, #00ffff 100%);
    color: #000;
    padding: 30px;
    border-radius: 15px;
    margin-bottom: 30px;
    box-shadow: 0 0 30px #ff00ff;
}

.header h1 {
    font-size: 28pt;
    font-weight: bold;
    text-shadow: 0 0 10px #fff;
}

.section-title {
    font-size: 16pt;
    font-weight: bold;
    color: #ff00ff;
    text-shadow: 0 0 10px #ff00ff;
    border-bottom: 3px solid #00ffff;
    margin: 20px 0;
}

.answer-box {
    background: #1a001a;
    border: 3px solid #ff00ff;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 0 20px #ff00ff;
}

.answer-content {
    color: #00ffff;
    font-size: 14pt;
    font-weight: bold;
    text-shadow: 0 0 5px #00ffff;
}

strong { color: #ffff00; text-shadow: 0 0 5px #ffff00; }
"""

THEME_MINIMAL_CSS = """
@page { size: A4; margin: 3cm; }
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: 'Georgia', serif;
    font-size: 10pt;
    line-height: 1.8;
    color: #333;
    background: #fff;
}

.header {
    border-bottom: 2px solid #333;
    padding-bottom: 20px;
    margin-bottom: 40px;
}

.header h1 {
    font-size: 22pt;
    font-weight: normal;
    color: #000;
}

.section-title {
    font-size: 14pt;
    font-weight: normal;
    color: #000;
    border-left: 3px solid #000;
    padding-left: 15px;
    margin: 30px 0 15px 0;
}

.answer-box {
    border: 1px solid #333;
    padding: 20px;
    margin: 20px 0;
}

.answer-content {
    font-size: 12pt;
    color: #000;
}

strong { font-weight: 600; }
"""

THEME_NOTEBOOK_CSS = """
@page { size: A4; margin: 2cm; }
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: 'Comic Sans MS', 'Marker Felt', cursive;
    font-size: 11pt;
    line-height: 1.7;
    color: #2c3e50;
    background: #fffef0;
    background-image: repeating-linear-gradient(
        transparent,
        transparent 30px,
        #aaa 30px,
        #aaa 31px
    );
}

.header {
    background: #fff9e6;
    border: 2px dashed #8b7355;
    padding: 25px;
    margin-bottom: 30px;
    transform: rotate(-0.5deg);
}

.header h1 {
    font-size: 24pt;
    color: #8b4513;
    transform: rotate(0.5deg);
}

.section-title {
    font-size: 15pt;
    color: #d2691e;
    border-bottom: 2px dotted #d2691e;
    margin: 25px 0 15px 0;
    transform: rotate(-0.3deg);
}

.answer-box {
    background: #fff;
    border: 2px solid #ffb347;
    padding: 20px;
    margin: 20px 0;
    transform: rotate(0.3deg);
    box-shadow: 3px 3px 5px rgba(0,0,0,0.2);
}

.answer-content {
    font-size: 13pt;
    color: #1e90ff;
    font-weight: bold;
}

strong { color: #ff6347; }
"""

def get_theme_css(theme_name):
    """Get CSS for a specific theme"""
    themes = {
        "neon": THEME_NEON_CSS,
        "minimal": THEME_MINIMAL_CSS,
        "notebook": THEME_NOTEBOOK_CSS
    }
    return themes.get(theme_name, themes["minimal"])

# ============================================================================
# COMMAND HANDLERS
# ============================================================================

async def hint_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /hint command"""
    user_id = update.effective_user.id
    
    # Get context from user's last problem (if available)
    last_problem = context.user_data.get('last_problem_topic')
    
    hint, level, can_continue = get_next_hint(user_id, topic=last_problem)
    
    await update.message.reply_text(
        f"💡 *HINT SYSTEM*\n\n"
        f"Level {level}/5\n\n"
        f"{hint}\n\n"
        f"_{'More hints available!' if can_continue else 'All hints given - try solving!'}",
        reply_markup=create_hint_keyboard(can_continue),
        parse_mode='Markdown'
    )

async def flashcard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /flashcard command"""
    # Show flashcard topics
    keyboard = [
        [
            InlineKeyboardButton("🎯 SN1", callback_data="flashcard_SN1"),
            InlineKeyboardButton("🎯 SN2", callback_data="flashcard_SN2")
        ],
        [
            InlineKeyboardButton("⚡ NGP", callback_data="flashcard_NGP"),
            InlineKeyboardButton("🔄 E1/E2", callback_data="flashcard_E1")
        ]
    ]
    
    await update.message.reply_text(
        "🃏 *FLASHCARD GENERATOR*\n\n"
        "Select a topic to generate beautiful flashcards!\n\n"
        "*Features:*\n"
        "• AI-designed colorful cards\n"
        "• Handwritten-style available\n"
        "• Question on front, answer on back\n\n"
        "_Choose a topic:_",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def theme_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /theme command"""
    keyboard = [
        [
            InlineKeyboardButton("🌈 Neon", callback_data="theme_neon"),
            InlineKeyboardButton("📄 Minimal", callback_data="theme_minimal")
        ],
        [
            InlineKeyboardButton("📓 Notebook", callback_data="theme_notebook"),
            InlineKeyboardButton("☀️ Light", callback_data="theme_light")
        ],
        [
            InlineKeyboardButton("🌙 Dark", callback_data="theme_dark")
        ]
    ]
    
    await update.message.reply_text(
        "🎨 *PDF THEME SELECTOR*\n\n"
        "Choose your PDF style:\n\n"
        "🌈 *Neon* - Cyberpunk vibes\n"
        "📄 *Minimal* - Clean & elegant\n"
        "📓 *Notebook* - Handwritten look\n"
        "☀️ *Light* - Classic white\n"
        "🌙 *Dark* - Night mode\n\n"
        "_Select theme:_",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# ============================================================================
# CALLBACK HANDLERS
# ============================================================================

async def handle_hint_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle next hint button"""
    query = update.callback_query
    await query.answer("💡 Loading next hint...")
    
    user_id = query.from_user.id
    hint, level, can_continue = get_next_hint(user_id)
    
    await query.edit_message_text(
        f"💡 *HINT SYSTEM*\n\n"
        f"Level {level}/5\n\n"
        f"{hint}\n\n"
        f"_{'More hints available!' if can_continue else 'All hints given!'}",
        reply_markup=create_hint_keyboard(can_continue),
        parse_mode='Markdown'
    )

async def handle_hint_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle stop hints button"""
    query = update.callback_query
    await query.answer("Hints stopped!")
    
    user_id = query.from_user.id
    reset_hints(user_id)
    
    await query.edit_message_text(
        "🚫 *Hints Stopped*\n\n"
        "Good luck solving! 💪\n"
        "_Use /hint anytime for help_",
        parse_mode='Markdown'
    )

async def handle_hint_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle reset hints button"""
    query = update.callback_query
    await query.answer("Hints reset!")
    
    user_id = query.from_user.id
    reset_hints(user_id)
    
    await query.edit_message_text(
        "🔄 *Hints Reset*\n\n"
        "Use /hint to start over!",
        parse_mode='Markdown'
    )

async def handle_flashcard_topic(update: Update, context: ContextTypes.DEFAULT_TYPE, topic):
    """Generate and send flashcard for topic"""
    query = update.callback_query
    await query.answer("🃏 Generating flashcard...")
    
    # Get sample flashcard
    cards = SAMPLE_FLASHCARDS.get(topic, SAMPLE_FLASHCARDS["SN1"])
    card = random.choice(cards)
    
    # Generate images
    front_bytes, back_bytes = generate_flashcard(
        card["front"], 
        card["back"], 
        template="pastel"
    )
    
    # Send front
    await query.message.reply_photo(
        photo=front_bytes,
        caption=f"🃏 *Flashcard: {topic}*\n\n📝 QUESTION (Front)",
        parse_mode='Markdown'
    )
    
    # Send back
    await query.message.reply_photo(
        photo=back_bytes,
        caption=f"✅ ANSWER (Back)\n\n_Want more? Use /flashcard again!_",
        parse_mode='Markdown'
    )

async def handle_theme_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, theme):
    """Handle theme selection"""
    query = update.callback_query
    await query.answer(f"✅ Theme set to {theme}!")
    
    user_id = query.from_user.id
    context.user_data['pdf_theme'] = theme
    
    emoji_map = {
        "neon": "🌈",
        "minimal": "📄",
        "notebook": "📓",
        "light": "☀️",
        "dark": "🌙"
    }
    
    await query.edit_message_text(
        f"{emoji_map.get(theme, '🎨')} *Theme Set: {theme.title()}*\n\n"
        f"All PDFs will use {theme} theme!\n\n"
        f"_Change anytime with /theme_",
        parse_mode='Markdown'
    )
