"""
PHASE 2 FEATURES MODULE - ENHANCED
Dynamic Flashcards from GitHub + PDF Generation, Hints, Themes

Author: @aryansmilezzz
Admin ID: 6298922725
Phase: 2 - Enhanced
"""

import random
import time
from datetime import datetime
from io import BytesIO
from weasyprint import HTML
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# HINTS SYSTEM (Keep existing - Progressive 5 levels)
# ============================================================================

HINT_LEVELS = {
    1: "🔍 Hint 1: Identify the key structural features",
    2: "🔍 Hint 2: Consider the mechanism type (SN1, SN2, E1, E2)",
    3: "🔍 Hint 3: Check for NGP within 2-3 atoms",
    4: "🔍 Hint 4: Calculate the rate effect (10^X)",
    5: "🔍 Hint 5: Review stereochemistry and orbital overlap"
}

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

user_hint_progress = {}

def get_next_hint(user_id, topic=None, context=None):
    if user_id not in user_hint_progress:
        user_hint_progress[user_id] = {"topic": topic, "level": 0, "context": context}
    
    progress = user_hint_progress[user_id]
    if topic:
        progress["topic"] = topic
    if context:
        progress["context"] = context
    
    progress["level"] += 1
    current_level = progress["level"]
    
    if progress["topic"] and progress["topic"].upper() in TOPIC_HINTS:
        hints = TOPIC_HINTS[progress["topic"].upper()]
        if current_level <= len(hints):
            hint = hints[current_level - 1]
        else:
            hint = "💡 All hints given! Try solving now."
            current_level = len(hints)
    else:
        if current_level in HINT_LEVELS:
            hint = HINT_LEVELS[current_level]
        else:
            hint = "💡 All hints given! Try solving now."
            current_level = 5
    
    can_continue = current_level < 5
    return hint, current_level, can_continue

def reset_hints(user_id):
    if user_id in user_hint_progress:
        del user_hint_progress[user_id]

def create_hint_keyboard(can_continue):
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
# 🔥 DYNAMIC FLASHCARD SYSTEM - PDF GENERATION 🔥
# ============================================================================

def get_flashcards_from_knowledge(topic, chemistry_knowledge_base):
    """
    Get flashcards from GitHub knowledge base
    Falls back to local data if GitHub source not available
    """
    topic_upper = topic.upper()
    
    # Try to get from knowledge base (GitHub)
    if "flashcards" in chemistry_knowledge_base:
        flashcards_data = chemistry_knowledge_base["flashcards"]
        
        # Match topic
        for key in flashcards_data.keys():
            if topic_upper in key.upper() or key.upper() in topic_upper:
                topic_cards = flashcards_data[key]
                
                # Flatten all categories
                all_cards = []
                if isinstance(topic_cards, dict):
                    for category, cards in topic_cards.items():
                        if isinstance(cards, list):
                            all_cards.extend(cards)
                
                if all_cards:
                    logger.info(f"✅ Loaded {len(all_cards)} flashcards for {topic} from knowledge base")
                    return all_cards
    
    # Fallback: return empty (will use fallback data in main file)
    logger.info(f"⚠️ No flashcards found for {topic}, using fallback")
    return []

def generate_flashcard_pdf(topic, cards, mode='light'):
    """
    Generate beautiful PDF with all flashcards for a topic
    Each card shows FRONT and BACK on same page
    """
    
    # CSS for flashcard PDF
    css = """
    @page {
        size: A4;
        margin: 1.5cm;
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
        background: #ffffff;
    }
    
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 25px;
        border-radius: 12px;
        margin-bottom: 30px;
        text-align: center;
    }
    
    .header h1 {
        font-size: 26pt;
        font-weight: bold;
        margin-bottom: 8px;
    }
    
    .header .subtitle {
        font-size: 12pt;
        opacity: 0.95;
    }
    
    .card-container {
        page-break-inside: avoid;
        margin-bottom: 30px;
        border: 2px solid #667eea;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .card-number {
        background: #667eea;
        color: white;
        padding: 8px 15px;
        font-weight: bold;
        font-size: 10pt;
    }
    
    .card-side {
        padding: 20px;
        min-height: 120px;
    }
    
    .card-front {
        background: #f8f9ff;
        border-bottom: 2px dashed #667eea;
    }
    
    .card-back {
        background: #ffffff;
    }
    
    .card-label {
        font-size: 9pt;
        font-weight: bold;
        color: #667eea;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 10px;
    }
    
    .card-content {
        font-size: 11pt;
        line-height: 1.6;
        color: #2c3e50;
    }
    
    .card-content strong {
        color: #667eea;
        font-weight: bold;
    }
    
    .footer {
        margin-top: 40px;
        padding-top: 15px;
        border-top: 2px solid #e0e0e0;
        text-align: center;
        font-size: 9pt;
        color: #666;
    }
    
    .category-header {
        background: #764ba2;
        color: white;
        padding: 15px;
        margin: 30px 0 20px 0;
        border-radius: 8px;
        font-size: 14pt;
        font-weight: bold;
    }
    """
    
    # Dark mode CSS
    if mode == 'dark':
        css = """
        @page {
            size: A4;
            margin: 1.5cm;
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
        
        .header {
            background: linear-gradient(135deg, #4a9eff 0%, #00d9ff 100%);
            color: white;
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 26pt;
            font-weight: bold;
            margin-bottom: 8px;
        }
        
        .header .subtitle {
            font-size: 12pt;
            opacity: 0.95;
        }
        
        .card-container {
            page-break-inside: avoid;
            margin-bottom: 30px;
            border: 2px solid #4a9eff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        
        .card-number {
            background: #4a9eff;
            color: white;
            padding: 8px 15px;
            font-weight: bold;
            font-size: 10pt;
        }
        
        .card-side {
            padding: 20px;
            min-height: 120px;
        }
        
        .card-front {
            background: #2a2a2a;
            border-bottom: 2px dashed #4a9eff;
        }
        
        .card-back {
            background: #1e1e1e;
        }
        
        .card-label {
            font-size: 9pt;
            font-weight: bold;
            color: #4a9eff;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }
        
        .card-content {
            font-size: 11pt;
            line-height: 1.6;
            color: #e8e8e8;
        }
        
        .card-content strong {
            color: #00d9ff;
            font-weight: bold;
        }
        
        .footer {
            margin-top: 40px;
            padding-top: 15px;
            border-top: 2px solid #3a3a3a;
            text-align: center;
            font-size: 9pt;
            color: #888;
        }
        
        .category-header {
            background: #00d9ff;
            color: #1a1a1a;
            padding: 15px;
            margin: 30px 0 20px 0;
            border-radius: 8px;
            font-size: 14pt;
            font-weight: bold;
        }
        """
    
    # Build HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Flashcards: {topic}</title>
        <style>{css}</style>
    </head>
    <body>
        <div class="header">
            <h1>🃏 {topic.upper()} FLASHCARDS</h1>
            <div class="subtitle">Study Guide | {len(cards)} Cards</div>
            <div class="subtitle" style="margin-top: 10px;">Generated on {datetime.now().strftime('%B %d, %Y')}</div>
        </div>
    """
    
    # Add cards
    for i, card in enumerate(cards, 1):
        front = card.get('front', 'No question')
        back = card.get('back', 'No answer')
        
        # Format text (preserve line breaks, bold)
        front = front.replace('\n', '<br>')
        back = back.replace('\n', '<br>')
        
        html_content += f"""
        <div class="card-container">
            <div class="card-number">Card #{i}</div>
            
            <div class="card-side card-front">
                <div class="card-label">📝 Question</div>
                <div class="card-content">{front}</div>
            </div>
            
            <div class="card-side card-back">
                <div class="card-label">✅ Answer</div>
                <div class="card-content">{back}</div>
            </div>
        </div>
        """
    
    # Footer
    html_content += f"""
        <div class="footer">
            <p>Ultimate Chemistry Bot | Phase 2 Enhanced</p>
            <p>🃏 {len(cards)} flashcards for mastering {topic}</p>
        </div>
    </body>
    </html>
    """
    
    # Generate PDF
    try:
        pdf_buffer = BytesIO()
        HTML(string=html_content).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
        return pdf_buffer
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        raise

# ============================================================================
# PDF THEMES (Keep existing)
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
    user_id = update.effective_user.id
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
    """Show flashcard topic selection"""
    keyboard = [
        [
            InlineKeyboardButton("🎯 SN1", callback_data="flashcard_SN1"),
            InlineKeyboardButton("🎯 SN2", callback_data="flashcard_SN2")
        ],
        [
            InlineKeyboardButton("⚡ NGP", callback_data="flashcard_NGP"),
            InlineKeyboardButton("🔄 E1", callback_data="flashcard_E1")
        ],
        [
            InlineKeyboardButton("🔄 E2", callback_data="flashcard_E2"),
            InlineKeyboardButton("⚛️ Carbocation", callback_data="flashcard_Carbocation")
        ],
        [
            InlineKeyboardButton("🧬 Stereochemistry", callback_data="flashcard_Stereochemistry")
        ]
    ]
    
    await update.message.reply_text(
        "🃏 *FLASHCARD GENERATOR*\n\n"
        "Select a topic to get comprehensive flashcards!\n\n"
        "*Features:*\n"
        "• All cards in beautiful PDF\n"
        "• Front: Question | Back: Answer\n"
        "• Sourced from GitHub database\n"
        "• 50-100+ cards per topic\n\n"
        "_Choose a topic:_",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def theme_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    """Generate and send flashcard PDF for topic"""
    query = update.callback_query
    await query.answer("🃏 Generating flashcard PDF...")
    
    await query.edit_message_text(
        f"🃏 *Generating {topic} Flashcards...*\n\n"
        f"📚 Compiling from knowledge base\n"
        f"📄 Creating PDF...\n\n"
        f"_This may take 10-20 seconds_",
        parse_mode='Markdown'
    )
    
    try:
        # Get flashcards from knowledge base
        from ULTIMATE_JE import chemistry_knowledge_base
        cards = get_flashcards_from_knowledge(topic, chemistry_knowledge_base)
        
        # If no cards from GitHub, use fallback
        if not cards:
            logger.info(f"Using fallback flashcards for {topic}")
            # Import fallback from main file
            from ULTIMATE_JE import FALLBACK_FLASHCARDS
            topic_data = FALLBACK_FLASHCARDS.get(topic, {})
            
            # Flatten all categories
            cards = []
            for category, category_cards in topic_data.items():
                if isinstance(category_cards, list):
                    cards.extend(category_cards)
        
        if not cards:
            await query.edit_message_text(
                f"❌ *No flashcards found for {topic}*\n\n"
                f"Try another topic!",
                parse_mode='Markdown'
            )
            return
        
        # Get user preference for PDF mode
        user_id = query.from_user.id
        from phase1_features import get_user_preference
        pdf_mode = get_user_preference(user_id, 'pdf_mode', 'light')
        
        # Generate PDF
        pdf_buffer = generate_flashcard_pdf(topic, cards, mode=pdf_mode)
        
        # Send PDF
        filename = f"Flashcards_{topic}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        await query.message.reply_document(
            document=pdf_buffer,
            filename=filename,
            caption=(
                f"🃏 *{topic} Flashcards*\n\n"
                f"📚 {len(cards)} cards generated\n"
                f"✅ Ready to study!\n\n"
                f"_Each card has question + answer on same page_"
            ),
            parse_mode='Markdown'
        )
        
        await query.edit_message_text(
            f"✅ *Flashcards Sent!*\n\n"
            f"📄 {len(cards)} cards for {topic}\n"
            f"Check the PDF above!\n\n"
            f"_Want more? Use /flashcard again_",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Flashcard generation error: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ *Error generating flashcards*\n\n"
            f"{str(e)[:100]}\n\n"
            f"Try another topic or contact admin.",
            parse_mode='Markdown'
        )

async def handle_theme_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, theme):
    query = update.callback_query
    await query.answer(f"✅ Theme set to {theme}!")
    
    user_id = query.from_user.id
    from phase1_features import set_user_preference
    set_user_preference(user_id, 'pdf_theme', theme)
    
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
