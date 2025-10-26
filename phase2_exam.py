"""
PHASE 2 EXAM MODULE
Mock Tests, MCQ System, Timer, Difficulty Predictor

Author: @aryansmilezzz
Admin ID: 6298922725
Phase: 2
"""

import json
import random
import time
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# MOCK TEST CONFIGURATION
# ============================================================================

DIFFICULTY_LEVELS = {
    "easy": {
        "name": "Easy",
        "emoji": "🟢",
        "topics": ["Basic SN1/SN2", "Simple E1/E2", "Carbocation Stability"]
    },
    "medium": {
        "name": "Medium", 
        "emoji": "🟡",
        "topics": ["NGP Detection", "Rearrangements", "Rate Comparisons"]
    },
    "hard": {
        "name": "Hard",
        "emoji": "🔴",
        "topics": ["Complex NGP", "Multiple Mechanisms", "JEE Advanced Traps"]
    },
    "mixed": {
        "name": "Mixed",
        "emoji": "🌈",
        "topics": ["All Topics - Exam Simulation"]
    }
}

TIME_LIMITS = {
    "30min": 1800,
    "1hr": 3600,
    "2hr": 7200,
    "3hr": 10800
}

QUESTION_COUNTS = [10, 20, 30, 50]

# Sample question bank (you can expand this!)
QUESTION_BANK = {
    "easy": [
        {
            "question": "Which substrate reacts fastest in SN1 reaction?",
            "options": {
                "A": "CH₃CH₂Br (Primary)",
                "B": "(CH₃)₂CHBr (Secondary)",
                "C": "(CH₃)₃CBr (Tertiary)",
                "D": "CH₃Br (Methyl)"
            },
            "answer": "C",
            "explanation": "Tertiary carbocations are most stable (3° > 2° > 1° > methyl) due to hyperconjugation. SN1 forms carbocation intermediate, so stability = reactivity."
        },
        {
            "question": "SN2 reaction shows which stereochemical outcome?",
            "options": {
                "A": "Retention",
                "B": "Inversion",
                "C": "Racemization",
                "D": "No change"
            },
            "answer": "B",
            "explanation": "SN2 = backside attack at 180°, causing Walden inversion. One-step mechanism means complete stereochemical inversion."
        }
    ],
    "medium": [
        {
            "question": "NGP from π-participation gives rate boost of:",
            "options": {
                "A": "10² to 10³ times",
                "B": "10⁶ to 10¹⁴ times",
                "C": "10 to 10² times",
                "D": "No significant boost"
            },
            "answer": "B",
            "explanation": "π-participation (C=C, benzene, C≡C) within 2-3 atoms gives MASSIVE rate boost: 10⁶ to 10¹⁴ times faster!"
        }
    ],
    "hard": [
        {
            "question": "Which factor MOST increases SN1 rate in NGP systems?",
            "options": {
                "A": "Temperature increase",
                "B": "Better leaving group",
                "C": "π-participation within 2 atoms",
                "D": "Polar protic solvent"
            },
            "answer": "C",
            "explanation": "NGP with π-participation gives 10⁶-10¹⁴× boost - WAY more than any other factor! This is THE JEE trap."
        }
    ]
}

# ============================================================================
# DIFFICULTY PREDICTOR
# ============================================================================

def predict_difficulty(problem_text):
    """
    Predict problem difficulty based on keywords and complexity
    Returns: ("easy"/"medium"/"hard", confidence%, explanation)
    """
    text_lower = problem_text.lower()
    
    # Difficulty indicators
    hard_keywords = [
        "ngp", "neighboring group", "participation", "rate boost", "10^",
        "rearrangement", "complex mechanism", "multi-step"
    ]
    
    medium_keywords = [
        "sn1", "sn2", "e1", "e2", "carbocation", "stereochemistry",
        "zaitsev", "hofmann", "anti-periplanar"
    ]
    
    easy_keywords = [
        "primary", "secondary", "tertiary", "stability", "basic"
    ]
    
    # Count matches
    hard_count = sum(1 for kw in hard_keywords if kw in text_lower)
    medium_count = sum(1 for kw in medium_keywords if kw in text_lower)
    easy_count = sum(1 for kw in easy_keywords if kw in text_lower)
    
    # Determine difficulty
    if hard_count >= 2:
        difficulty = "hard"
        confidence = min(70 + (hard_count * 5), 95)
        explanation = f"Contains {hard_count} advanced concepts (NGP, rate effects, rearrangements)"
    elif medium_count >= 2 or hard_count == 1:
        difficulty = "medium"
        confidence = min(65 + (medium_count * 5), 90)
        explanation = f"Involves mechanism comparison and stereochemistry"
    else:
        difficulty = "easy"
        confidence = min(60 + (easy_count * 5), 85)
        explanation = "Basic concept or straightforward mechanism"
    
    return difficulty, confidence, explanation

# ============================================================================
# MOCK TEST CONFIGURATION UI
# ============================================================================

def create_config_keyboard():
    """Create configuration keyboard for mock test"""
    keyboard = [
        [InlineKeyboardButton("📝 Configure Test", callback_data="mock_config_start")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_question_count_keyboard():
    """Select number of questions"""
    keyboard = []
    row = []
    for count in QUESTION_COUNTS:
        row.append(InlineKeyboardButton(f"{count} Q", callback_data=f"mock_q_{count}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def create_time_keyboard():
    """Select time limit"""
    keyboard = [
        [
            InlineKeyboardButton("⏱️ 30 min", callback_data="mock_t_30min"),
            InlineKeyboardButton("⏱️ 1 hr", callback_data="mock_t_1hr")
        ],
        [
            InlineKeyboardButton("⏱️ 2 hr", callback_data="mock_t_2hr"),
            InlineKeyboardButton("⏱️ 3 hr", callback_data="mock_t_3hr")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_difficulty_keyboard():
    """Select difficulty level"""
    keyboard = []
    for key, diff in DIFFICULTY_LEVELS.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{diff['emoji']} {diff['name']}", 
                callback_data=f"mock_d_{key}"
            )
        ])
    return InlineKeyboardMarkup(keyboard)

# ============================================================================
# MOCK TEST SESSION
# ============================================================================

class MockTestSession:
    """Manages a mock test session"""
    
    def __init__(self, user_id, num_questions, time_limit, difficulty):
        self.user_id = user_id
        self.num_questions = num_questions
        self.time_limit = time_limit  # seconds
        self.difficulty = difficulty
        self.start_time = None
        self.end_time = None
        self.current_question = 0
        self.answers = {}  # {question_num: selected_option}
        self.score = 0
        self.questions = []
        
    def generate_questions(self):
        """Generate questions based on difficulty"""
        if self.difficulty == "mixed":
            # Mix from all difficulties
            easy_q = random.sample(QUESTION_BANK.get("easy", []), 
                                  min(self.num_questions // 3, len(QUESTION_BANK.get("easy", []))))
            medium_q = random.sample(QUESTION_BANK.get("medium", []), 
                                    min(self.num_questions // 3, len(QUESTION_BANK.get("medium", []))))
            hard_q = random.sample(QUESTION_BANK.get("hard", []), 
                                  min(self.num_questions // 3, len(QUESTION_BANK.get("hard", []))))
            self.questions = easy_q + medium_q + hard_q
        else:
            bank = QUESTION_BANK.get(self.difficulty, [])
            self.questions = random.sample(bank, min(self.num_questions, len(bank)))
        
        random.shuffle(self.questions)
        
    def start(self):
        """Start the test"""
        self.start_time = time.time()
        self.generate_questions()
        
    def get_time_remaining(self):
        """Get remaining time in seconds"""
        if not self.start_time:
            return self.time_limit
        elapsed = time.time() - self.start_time
        remaining = max(0, self.time_limit - elapsed)
        return int(remaining)
    
    def is_time_up(self):
        """Check if time is up"""
        return self.get_time_remaining() <= 0
    
    def format_time_remaining(self):
        """Format time as HH:MM:SS"""
        seconds = self.get_time_remaining()
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def submit_answer(self, question_num, answer):
        """Submit answer for a question"""
        self.answers[question_num] = answer
        
    def calculate_score(self):
        """Calculate final score"""
        correct = 0
        for i, q in enumerate(self.questions):
            if self.answers.get(i) == q["answer"]:
                correct += 1
        self.score = correct
        self.end_time = time.time()
        return correct, len(self.questions)
    
    def get_accuracy(self):
        """Get accuracy percentage"""
        if not self.questions:
            return 0
        return int((self.score / len(self.questions)) * 100)

# Store active mock test sessions
active_mock_tests = {}  # {user_id: MockTestSession}

# ============================================================================
# MOCK TEST HANDLERS
# ============================================================================

async def start_mock_test_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start mock test configuration"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📝 *MOCK TEST CONFIGURATION*\n\n"
        "Step 1/3: Select number of questions\n\n"
        "_Configure your custom test:_",
        reply_markup=create_question_count_keyboard(),
        parse_mode='Markdown'
    )

async def handle_question_count(update: Update, context: ContextTypes.DEFAULT_TYPE, count):
    """Handle question count selection"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['mock_questions'] = count
    
    await query.edit_message_text(
        f"📝 *MOCK TEST CONFIGURATION*\n\n"
        f"✅ Questions: {count}\n"
        f"Step 2/3: Select time limit\n\n"
        f"_How long do you need?_",
        reply_markup=create_time_keyboard(),
        parse_mode='Markdown'
    )

async def handle_time_limit(update: Update, context: ContextTypes.DEFAULT_TYPE, time_key):
    """Handle time limit selection"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['mock_time'] = time_key
    questions = context.user_data.get('mock_questions', 20)
    
    await query.edit_message_text(
        f"📝 *MOCK TEST CONFIGURATION*\n\n"
        f"✅ Questions: {questions}\n"
        f"✅ Time: {time_key}\n"
        f"Step 3/3: Select difficulty\n\n"
        f"_Choose your challenge level:_",
        reply_markup=create_difficulty_keyboard(),
        parse_mode='Markdown'
    )

async def handle_difficulty_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, difficulty):
    """Handle difficulty selection and start test"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    questions = context.user_data.get('mock_questions', 20)
    time_key = context.user_data.get('mock_time', '1hr')
    time_seconds = TIME_LIMITS[time_key]
    
    # Create session
    session = MockTestSession(user_id, questions, time_seconds, difficulty)
    session.start()
    active_mock_tests[user_id] = session
    
    diff_info = DIFFICULTY_LEVELS[difficulty]
    
    await query.edit_message_text(
        f"🎯 *MOCK TEST READY*\n\n"
        f"📝 Questions: {questions}\n"
        f"⏱️ Time: {time_key}\n"
        f"{diff_info['emoji']} Difficulty: {diff_info['name']}\n\n"
        f"*Topics:*\n"
        f"{chr(10).join('• ' + t for t in diff_info['topics'])}\n\n"
        f"✅ *Test will start now!*\n"
        f"_You can answer at your own pace_",
        parse_mode='Markdown'
    )
    
    # Start first question
    await asyncio.sleep(2)
    await show_question(query.message, context, user_id, 0)

async def show_question(message, context: ContextTypes.DEFAULT_TYPE, user_id, question_num):
    """Show a question"""
    session = active_mock_tests.get(user_id)
    if not session or question_num >= len(session.questions):
        return
    
    question = session.questions[question_num]
    
    # Create answer keyboard
    keyboard = []
    for opt_key, opt_text in question["options"].items():
        keyboard.append([
            InlineKeyboardButton(
                f"{opt_key}) {opt_text[:40]}...",
                callback_data=f"mock_ans_{question_num}_{opt_key}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("⏭️ Skip", callback_data=f"mock_skip_{question_num}")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    time_left = session.format_time_remaining()
    progress = f"{question_num + 1}/{len(session.questions)}"
    
    await message.reply_text(
        f"📝 *Question {question_num + 1}*\n"
        f"⏱️ Time: {time_left} | Progress: {progress}\n\n"
        f"{question['question']}\n\n"
        f"*Options:*\n"
        f"{chr(10).join(f'{k}) {v}' for k, v in question['options'].items())}\n\n"
        f"_Select your answer:_",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, question_num, answer):
    """Handle answer submission"""
    query = update.callback_query
    await query.answer("✅ Answer recorded!")
    
    user_id = query.from_user.id
    session = active_mock_tests.get(user_id)
    
    if not session:
        await query.edit_message_text("❌ Session expired. Start a new test with /mock_test")
        return
    
    # Record answer
    session.submit_answer(question_num, answer)
    
    # Check if time up
    if session.is_time_up():
        await end_mock_test(query.message, context, user_id)
        return
    
    # Move to next question
    next_q = question_num + 1
    if next_q < len(session.questions):
        await query.edit_message_text(
            f"✅ Answer recorded: {answer}\n\n_Loading next question..._",
            parse_mode='Markdown'
        )
        await show_question(query.message, context, user_id, next_q)
    else:
        # Test complete
        await end_mock_test(query.message, context, user_id)

async def end_mock_test(message, context: ContextTypes.DEFAULT_TYPE, user_id):
    """End mock test and show results"""
    session = active_mock_tests.get(user_id)
    if not session:
        return
    
    correct, total = session.calculate_score()
    accuracy = session.get_accuracy()
    time_taken = int(session.end_time - session.start_time)
    time_taken_str = f"{time_taken // 60}m {time_taken % 60}s"
    
    # Determine performance
    if accuracy >= 90:
        performance = "🏆 Excellent!"
        emoji = "🎉"
    elif accuracy >= 75:
        performance = "🌟 Great!"
        emoji = "👏"
    elif accuracy >= 60:
        performance = "👍 Good"
        emoji = "💪"
    else:
        performance = "📚 Keep Practicing"
        emoji = "🔥"
    
    result_text = (
        f"{emoji} *MOCK TEST COMPLETE!*\n\n"
        f"📊 *Results:*\n"
        f"✅ Correct: {correct}/{total}\n"
        f"📈 Accuracy: {accuracy}%\n"
        f"⏱️ Time: {time_taken_str}\n"
        f"🎯 Performance: {performance}\n\n"
        f"*Detailed Analysis:*\n"
    )
    
    # Show wrong answers
    wrong_count = 0
    for i, q in enumerate(session.questions):
        user_ans = session.answers.get(i, "Not answered")
        if user_ans != q["answer"]:
            wrong_count += 1
            if wrong_count <= 5:  # Show first 5 wrong answers
                result_text += (
                    f"\n❌ Q{i+1}: {q['question'][:60]}...\n"
                    f"Your: {user_ans} | Correct: {q['answer']}\n"
                )
    
    if wrong_count > 5:
        result_text += f"\n_...and {wrong_count - 5} more mistakes_\n"
    
    result_text += "\n💡 Review explanations and try again!"
    
    await message.reply_text(result_text, parse_mode='Markdown')
    
    # Clean up session
    del active_mock_tests[user_id]

# ============================================================================
# COMMAND HANDLERS
# ============================================================================

async def mock_test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mock_test command"""
    await update.message.reply_text(
        "📝 *MOCK TEST SIMULATOR*\n\n"
        "Practice with real JEE-style MCQs!\n\n"
        "*Features:*\n"
        "• Customizable (questions, time, difficulty)\n"
        "• Timer with live countdown\n"
        "• Instant scoring & analysis\n"
        "• Detailed explanations\n\n"
        "_Configure your test:_",
        reply_markup=create_config_keyboard(),
        parse_mode='Markdown'
    )

async def difficulty_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /difficulty command - predict problem difficulty"""
    await update.message.reply_text(
        "🎯 *DIFFICULTY PREDICTOR*\n\n"
        "Send me a chemistry problem (text or image)\n"
        "and I'll predict its difficulty!\n\n"
        "*Levels:*\n"
        "🟢 Easy - Basic concepts\n"
        "🟡 Medium - Mechanism comparisons\n"
        "🔴 Hard - JEE Advanced level\n\n"
        "_Send a problem now!_",
        parse_mode='Markdown'
    )
