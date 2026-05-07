import asyncio
import hashlib
import hmac
import json
import logging
import math
import os
import random
import secrets
import sqlite3
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    User,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

# ============================================================
# КОНФИГУРАЦИЯ
# ============================================================

# Telegram Bot Token
BOT_TOKEN = 8183582932:AAEIas0VlMxWSDvOLap_y6cTsZ9yqicmhYc

# Администраторы (через запятую)
ADMIN_IDS = 1170970828

# Валюта
CURRENCY_NAME=Коин
CURRENCY_SYMBOL=🪙

# Экономика
STARTING_BALANCE=500
DAILY_BONUS=100
REFERRAL_BONUS=50
QUIZ_BASE_REWARD=10
MIN_BET=10
MAX_BET=10000
DAILY_WIN_LIMIT=50000
DAILY_LOSS_LIMIT=20000
CARD_RAKE=0.04

# Кулдауны (секунды)
MINIGAME_COOLDOWN=300
QUIZ_COOLDOWN=60
CARD_TURN_TIMEOUT=45

# RTP казино (0.85 - 0.99)
SLOTS_RTP=0.90
ROULETTE_RTP=0.973
BLACKJACK_RTP=0.995
CRASH_RTP=0.95
DICE_RTP=0.98
# Пути
DATA_DIR = Path("/app/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "bot.db"

# ============================================================
# ЛОГИРОВАНИЕ
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "msg": "%(message)s"}',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(DATA_DIR / "bot.log"),
    ]
)
logger = logging.getLogger(__name__)

# ============================================================
# БАЗА ДАННЫХ - ИНИЦИАЛИЗАЦИЯ
# ============================================================

def init_db():
    """Инициализация SQLite базы данных с полной схемой."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    
    # Таблица пользователей
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            language TEXT DEFAULT 'ru',
            referral_by INTEGER,
            is_banned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица балансов
    conn.execute('''
        CREATE TABLE IF NOT EXISTS balances (
            user_id INTEGER PRIMARY KEY,
            amount INTEGER DEFAULT 0,
            total_earned INTEGER DEFAULT 0,
            total_spent INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Таблица транзакций
    conn.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            balance_after INTEGER,
            checksum TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Дневные лимиты
    conn.execute('''
        CREATE TABLE IF NOT EXISTS daily_limits (
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            won INTEGER DEFAULT 0,
            lost INTEGER DEFAULT 0,
            minigames_played INTEGER DEFAULT 0,
            quizzes_played INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, date),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Кулдауны
    conn.execute('''
        CREATE TABLE IF NOT EXISTS cooldowns (
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            PRIMARY KEY (user_id, action),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Сессии мини-игр
    conn.execute('''
        CREATE TABLE IF NOT EXISTS minigame_sessions (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            game_type TEXT NOT NULL,
            state TEXT NOT NULL,
            data TEXT,
            bet INTEGER DEFAULT 0,
            multiplier REAL DEFAULT 1.0,
            message_id INTEGER,
            chat_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Ставки казино
    conn.execute('''
        CREATE TABLE IF NOT EXISTS casino_bets (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            game_type TEXT NOT NULL,
            bet INTEGER NOT NULL,
            result TEXT,
            win_amount INTEGER DEFAULT 0,
            seed TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Карточные сессии
    conn.execute('''
        CREATE TABLE IF NOT EXISTS card_sessions (
            id TEXT PRIMARY KEY,
            state TEXT NOT NULL,
            pot INTEGER DEFAULT 0,
            current_bet INTEGER DEFAULT 0,
            community_cards TEXT DEFAULT '[]',
            deck TEXT DEFAULT '[]',
            stage TEXT DEFAULT 'waiting',
            current_turn INTEGER,
            rake INTEGER DEFAULT 0,
            seed TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    ''')
    
    # Игроки в карточных сессиях
    conn.execute('''
        CREATE TABLE IF NOT EXISTS card_players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            hole_cards TEXT DEFAULT '[]',
            chips INTEGER DEFAULT 0,
            bet_amount INTEGER DEFAULT 0,
            total_bet INTEGER DEFAULT 0,
            status TEXT DEFAULT 'waiting',
            position INTEGER DEFAULT 0,
            message_id INTEGER,
            FOREIGN KEY (session_id) REFERENCES card_sessions(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Викторины
    conn.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            difficulty INTEGER DEFAULT 1,
            question TEXT NOT NULL,
            options TEXT NOT NULL,
            correct_index INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Статистика игрока
    conn.execute('''
        CREATE TABLE IF NOT EXISTS player_stats (
            user_id INTEGER PRIMARY KEY,
            games_played INTEGER DEFAULT 0,
            games_won INTEGER DEFAULT 0,
            casino_bets INTEGER DEFAULT 0,
            casino_won INTEGER DEFAULT 0,
            casino_lost INTEGER DEFAULT 0,
            cards_played INTEGER DEFAULT 0,
            cards_won INTEGER DEFAULT 0,
            quizzes_answered INTEGER DEFAULT 0,
            quizzes_correct INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Достижения
    conn.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_key TEXT NOT NULL,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, achievement_key),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Очередь на карточные игры
    conn.execute('''
        CREATE TABLE IF NOT EXISTS card_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            bet INTEGER NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    
    # Заполнение викторины начальными вопросами
    _seed_quizzes(conn)
    
    conn.close()
    logger.info(f"База данных инициализирована: {DB_PATH}")


def _seed_quizzes(conn):
    """Заполнение базы начальными вопросами для викторины."""
    count = conn.execute("SELECT COUNT(*) FROM quizzes").fetchone()[0]
    if count > 0:
        return
    
    questions = [
        # Категория: География, сложность 1
        ("geography", 1, "Какая страна самая большая по площади?",
         '["США", "Китай", "Россия", "Канада"]', 2),
        ("geography", 1, "Столица Франции?",
         '["Берлин", "Лондон", "Париж", "Рим"]', 2),
        ("geography", 2, "Какая река самая длинная в мире?",
         '["Амазонка", "Нил", "Янцзы", "Миссисипи"]', 1),
        ("geography", 2, "В какой стране находится Мачу-Пикчу?",
         '["Бразилия", "Колумбия", "Перу", "Чили"]', 2),
        ("geography", 3, "Какой океан самый маленький?",
         '["Атлантический", "Индийский", "Северный Ледовитый", "Тихий"]', 2),
        # Категория: Наука, сложность 1-3
        ("science", 1, "Сколько планет в Солнечной системе?",
         '["7", "8", "9", "10"]', 1),
        ("science", 1, "Что является символом воды в химии?",
         '["CO2", "H2O", "O2", "H2"]', 1),
        ("science", 2, "Кто открыл закон всемирного тяготения?",
         '["Эйнштейн", "Дарвин", "Ньютон", "Галилей"]', 2),
        ("science", 2, "Скорость света примерно равна?",
         '["100 000 км/с", "200 000 км/с", "300 000 км/с", "400 000 км/с"]', 2),
        ("science", 3, "Какой элемент имеет символ Au?",
         '["Серебро", "Золото", "Алюминий", "Аргон"]', 1),
        # Категория: История, сложность 1-3
        ("history", 1, "В каком году закончилась Вторая мировая война?",
         '["1943", "1944", "1945", "1946"]', 2),
        ("history", 1, "Кто был первым президентом США?",
         '["Линкольн", "Вашингтон", "Джефферсон", "Адамс"]', 1),
        ("history", 2, "В каком веке произошла Французская революция?",
         '["XVII", "XVIII", "XIX", "XX"]', 1),
        ("history", 3, "Как называлась операция по высадке союзников в Нормандии?",
         '["Барбаросса", "Оверлорд", "Торч", "Маркет-гарден"]', 1),
        # Категория: Математика
        ("math", 1, "Сколько будет 7 × 8?",
         '["54", "56", "58", "64"]', 1),
        ("math", 2, "Что такое число Пи (приближённо)?",
         '["2.71", "3.14", "1.41", "1.73"]', 1),
        ("math", 3, "Чему равен квадратный корень из 144?",
         '["11", "12", "13", "14"]', 1),
        # Категория: Спорт
        ("sport", 1, "Сколько игроков в футбольной команде?",
         '["9", "10", "11", "12"]', 2),
        ("sport", 2, "В какой стране возникли Олимпийские игры?",
         '["Риме", "Греции", "Египте", "Персии"]', 1),
        ("sport", 3, "Какой вид спорта называют 'игрой в кегли'?",
         '["Боулинг", "Бильярд", "Гольф", "Крикет"]', 0),
    ]
    
    conn.executemany(
        "INSERT INTO quizzes (category, difficulty, question, options, correct_index) VALUES (?,?,?,?,?)",
        questions
    )
    conn.commit()
    logger.info(f"Добавлено {len(questions)} вопросов викторины")


def get_db():
    """Получить соединение с БД."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ - ПОЛЬЗОВАТЕЛИ И БАЛАНС
# ============================================================

def ensure_user(user_id: int, username: str = None, first_name: str = None,
                referral_by: int = None) -> bool:
    """Создать пользователя если не существует. Возвращает True если новый."""
    with get_db() as conn:
        existing = conn.execute("SELECT id FROM users WHERE id=?", (user_id,)).fetchone()
        if existing:
            conn.execute(
                "UPDATE users SET last_active=CURRENT_TIMESTAMP, username=? WHERE id=?",
                (username, user_id)
            )
            conn.commit()
            return False
        
        conn.execute(
            "INSERT INTO users (id, username, first_name, referral_by) VALUES (?,?,?,?)",
            (user_id, username, first_name, referral_by)
        )
        conn.execute(
            "INSERT INTO balances (user_id, amount) VALUES (?,?)",
            (user_id, STARTING_BALANCE)
        )
        conn.execute(
            "INSERT INTO player_stats (user_id) VALUES (?)",
            (user_id,)
        )
        # Реферальный бонус
        if referral_by and referral_by != user_id:
            _credit_balance(conn, referral_by, REFERRAL_BONUS, "referral_bonus", 
                          f"Реферал: {user_id}")
        conn.commit()
        
        # Стартовая транзакция
        _record_transaction(conn, user_id, STARTING_BALANCE, "starting_bonus", 
                          "Стартовый бонус", STARTING_BALANCE)
        conn.commit()
        return True


def get_balance(user_id: int) -> int:
    """Получить баланс пользователя."""
    with get_db() as conn:
        row = conn.execute("SELECT amount FROM balances WHERE user_id=?", (user_id,)).fetchone()
        return row["amount"] if row else 0


def _credit_balance(conn, user_id: int, amount: int, tx_type: str, 
                   description: str = "") -> Tuple[bool, int]:
    """Начислить коины (атомарно, внутри транзакции)."""
    row = conn.execute(
        "SELECT amount FROM balances WHERE user_id=?", (user_id,)
    ).fetchone()
    if not row:
        return False, 0
    
    new_balance = row["amount"] + amount
    conn.execute(
        "UPDATE balances SET amount=?, total_earned=total_earned+? WHERE user_id=?",
        (new_balance, amount, user_id)
    )
    _record_transaction(conn, user_id, amount, tx_type, description, new_balance)
    return True, new_balance


def _debit_balance(conn, user_id: int, amount: int, tx_type: str,
                  description: str = "") -> Tuple[bool, int]:
    """Списать коины (атомарно, с проверкой баланса)."""
    row = conn.execute(
        "SELECT amount FROM balances WHERE user_id=?", (user_id,)
    ).fetchone()
    if not row or row["amount"] < amount:
        return False, row["amount"] if row else 0
    
    new_balance = row["amount"] - amount
    conn.execute(
        "UPDATE balances SET amount=?, total_spent=total_spent+? WHERE user_id=?",
        (new_balance, amount, user_id)
    )
    _record_transaction(conn, user_id, -amount, tx_type, description, new_balance)
    return True, new_balance


def _record_transaction(conn, user_id: int, amount: int, tx_type: str,
                        description: str, balance_after: int):
    """Записать транзакцию с контрольной суммой."""
    tx_id = str(uuid.uuid4())
    data = f"{tx_id}:{user_id}:{amount}:{tx_type}:{int(time.time())}"
    checksum = hashlib.sha256(data.encode()).hexdigest()[:16]
    
    conn.execute(
        """INSERT INTO transactions 
           (id, user_id, amount, type, description, balance_after, checksum)
           VALUES (?,?,?,?,?,?,?)""",
        (tx_id, user_id, amount, tx_type, description, balance_after, checksum)
    )


def credit_user(user_id: int, amount: int, tx_type: str, description: str = "") -> Tuple[bool, int]:
    """Публичный метод начисления коинов."""
    with get_db() as conn:
        result = _credit_balance(conn, user_id, amount, tx_type, description)
        conn.commit()
        return result


def debit_user(user_id: int, amount: int, tx_type: str, description: str = "") -> Tuple[bool, int]:
    """Публичный метод списания коинов."""
    with get_db() as conn:
        result = _debit_balance(conn, user_id, amount, tx_type, description)
        conn.commit()
        return result

# ============================================================
# КУЛДАУНЫ И ДНЕВНЫЕ ЛИМИТЫ
# ============================================================

def check_cooldown(user_id: int, action: str) -> Optional[int]:
    """Проверить кулдаун. Возвращает секунды до конца или None если свободен."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT expires_at FROM cooldowns WHERE user_id=? AND action=?",
            (user_id, action)
        ).fetchone()
        if not row:
            return None
        
        expires = datetime.fromisoformat(row["expires_at"])
        now = datetime.now()
        if expires <= now:
            conn.execute(
                "DELETE FROM cooldowns WHERE user_id=? AND action=?",
                (user_id, action)
            )
            conn.commit()
            return None
        
        return int((expires - now).total_seconds())


def set_cooldown(user_id: int, action: str, seconds: int):
    """Установить кулдаун."""
    expires = datetime.now() + timedelta(seconds=seconds)
    with get_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO cooldowns (user_id, action, expires_at)
               VALUES (?,?,?)""",
            (user_id, action, expires.isoformat())
        )
        conn.commit()


def check_daily_limit(user_id: int, limit_type: str, limit_value: int) -> Tuple[bool, int]:
    """Проверить дневной лимит. Возвращает (можно, остаток)."""
    today = datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        row = conn.execute(
            "SELECT won, lost FROM daily_limits WHERE user_id=? AND date=?",
            (user_id, today)
        ).fetchone()
        
        current = 0
        if row:
            current = row["won"] if limit_type == "won" else row["lost"]
        
        remaining = limit_value - current
        return remaining > 0, remaining


def update_daily_limit(user_id: int, limit_type: str, amount: int):
    """Обновить дневной счётчик."""
    today = datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        conn.execute(
            """INSERT INTO daily_limits (user_id, date) VALUES (?,?)
               ON CONFLICT(user_id, date) DO NOTHING""",
            (user_id, today)
        )
        if limit_type == "won":
            conn.execute(
                "UPDATE daily_limits SET won=won+? WHERE user_id=? AND date=?",
                (amount, user_id, today)
            )
        elif limit_type == "lost":
            conn.execute(
                "UPDATE daily_limits SET lost=lost+? WHERE user_id=? AND date=?",
                (amount, user_id, today)
            )
        elif limit_type == "minigames":
            conn.execute(
                "UPDATE daily_limits SET minigames_played=minigames_played+1 WHERE user_id=? AND date=?",
                (user_id, today)
            )
        conn.commit()

# ============================================================
# КЛАВИАТУРЫ
# ============================================================

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 Заработок", callback_data="menu_earn"),
        InlineKeyboardButton(text="🎰 Казино", callback_data="menu_casino")
    )
    builder.row(
        InlineKeyboardButton(text="🃏 Карточные дуэли", callback_data="menu_cards"),
        InlineKeyboardButton(text="👤 Профиль", callback_data="menu_profile")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="menu_stats"),
        InlineKeyboardButton(text="📋 Правила", callback_data="menu_rules")
    )
    return builder.as_markup()


def earn_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню заработка."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Викторина", callback_data="earn_quiz"),
        InlineKeyboardButton(text="🎁 Дневной бонус", callback_data="earn_daily")
    )
    builder.row(
        InlineKeyboardButton(text="💣 Сапёр", callback_data="game_minesweeper"),
        InlineKeyboardButton(text="⚡ Реакция", callback_data="game_reaction")
    )
    builder.row(
        InlineKeyboardButton(text="🧠 Память", callback_data="game_memory"),
        InlineKeyboardButton(text="🔗 Реферал", callback_data="earn_referral")
    )
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder.as_markup()


def casino_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню казино."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎰 Слоты", callback_data="casino_slots"),
        InlineKeyboardButton(text="🎡 Рулетка", callback_data="casino_roulette")
    )
    builder.row(
        InlineKeyboardButton(text="🃏 Блэкджек", callback_data="casino_blackjack"),
        InlineKeyboardButton(text="🚀 Краш", callback_data="casino_crash")
    )
    builder.row(
        InlineKeyboardButton(text="🎲 Дайс", callback_data="casino_dice")
    )
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder.as_markup()


def bet_keyboard(game: str, bets: List[int] = None) -> InlineKeyboardMarkup:
    """Клавиатура выбора ставки."""
    if bets is None:
        bets = [50, 100, 250, 500, 1000, 2500]
    
    builder = InlineKeyboardBuilder()
    row = []
    for bet in bets:
        row.append(InlineKeyboardButton(
            text=f"{CURRENCY_SYMBOL}{bet}",
            callback_data=f"bet_{game}_{bet}"
        ))
        if len(row) == 3:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="menu_casino"))
    return builder.as_markup()


def back_to_main() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder.as_markup()

# ============================================================
# СОСТОЯНИЯ FSM
# ============================================================

class QuizStates(StatesGroup):
    answering = State()


class BlackjackStates(StatesGroup):
    betting = State()
    playing = State()


class RouletteSates(StatesGroup):
    betting = State()
    selecting_number = State()


class CardStates(StatesGroup):
    in_game = State()


class MinesweeperStates(StatesGroup):
    playing = State()


class ReactionStates(StatesGroup):
    waiting = State()


class MemoryStates(StatesGroup):
    playing = State()

# ============================================================
# РОУТЕРЫ
# ============================================================

router = Router()

# ============================================================
# БАЗОВЫЕ КОМАНДЫ
# ============================================================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Команда /start с обработкой рефералов."""
    user = message.from_user
    args = message.text.split()
    referral_by = None
    
    if len(args) > 1:
        try:
            referral_by = int(args[1].replace("ref_", ""))
        except ValueError:
            pass
    
    is_new = ensure_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        referral_by=referral_by
    )
    
    await state.clear()
    
    if is_new:
        text = (
            f"👋 Добро пожаловать, <b>{user.first_name}</b>!\n\n"
            f"🎉 Ты получил стартовый бонус: <b>{STARTING_BALANCE} {CURRENCY_SYMBOL}</b>\n\n"
            f"⚠️ <i>Валюта бота является виртуальной, не имеет реальной ценности "
            f"и не подлежит обмену или выводу.</i>\n\n"
            f"Используй /help для ознакомления с правилами."
        )
    else:
        balance = get_balance(user.id)
        text = (
            f"👋 С возвращением, <b>{user.first_name}</b>!\n\n"
            f"💰 Твой баланс: <b>{balance} {CURRENCY_SYMBOL}</b>"
        )
    
    await message.answer(text, reply_markup=main_menu_keyboard(), parse_mode=ParseMode.HTML)


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await state.clear()
    balance = get_balance(message.from_user.id)
    await message.answer(
        f"🏠 Главное меню\n💰 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>",
        reply_markup=main_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )


@router.message(Command("balance"))
async def cmd_balance(message: Message):
    ensure_user(message.from_user.id, message.from_user.username)
    balance = get_balance(message.from_user.id)
    await message.answer(
        f"💰 Твой баланс: <b>{balance} {CURRENCY_SYMBOL}</b>",
        parse_mode=ParseMode.HTML
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 <b>Справка по боту</b>\n\n"
        "💰 <b>Заработок:</b>\n"
        "• /quiz — викторина с наградой\n"
        "• /daily — ежедневный бонус\n"
        "• /minesweeper — игра сапёр\n"
        "• /reaction — игра на реакцию\n"
        "• /memory — игра на память\n\n"
        "🎰 <b>Казино:</b>\n"
        "• /slots — игровые автоматы\n"
        "• /roulette — рулетка\n"
        "• /blackjack — блэкджек\n"
        "• /crash — краш\n"
        "• /dice — дайс\n\n"
        "🃏 <b>Карточные дуэли:</b>\n"
        "• /playcards [ставка] — найти соперника\n\n"
        "👤 <b>Профиль:</b>\n"
        "• /balance — баланс\n"
        "• /stats — статистика\n"
        "• /referral — реферальная ссылка\n\n"
        "⚠️ <i>Все игры используют виртуальную валюту без реальной ценности.</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(Command("terms"))
async def cmd_terms(message: Message):
    text = (
        "📋 <b>Правила и условия</b>\n\n"
        "⚠️ <b>ВАЖНО:</b> Все игры в данном боте используют исключительно "
        "виртуальную игровую валюту.\n\n"
        "1. Виртуальная валюта <b>не имеет реальной денежной ценности</b>\n"
        "2. Валюта <b>не подлежит обмену</b> на реальные деньги или товары\n"
        "3. Все игровые результаты генерируются случайным образом на сервере\n"
        "4. Бот предназначен для развлечения лиц 18+ лет\n"
        "5. Администрация вправе ограничить доступ за нарушение правил\n"
        "6. Все транзакции логируются для обеспечения честности игры\n\n"
        "Используя бота, вы соглашаетесь с данными условиями."
    )
    await message.answer(text, parse_mode=ParseMode.HTML)

# ============================================================
# НАВИГАЦИЯ ЧЕРЕЗ CALLBACK
# ============================================================

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    balance = get_balance(callback.from_user.id)
    try:
        await callback.message.edit_text(
            f"🏠 Главное меню\n💰 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>",
            reply_markup=main_menu_keyboard(),
            parse_mode=ParseMode.HTML
        )
    except Exception:
        await callback.message.answer(
            f"🏠 Главное меню\n💰 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>",
            reply_markup=main_menu_keyboard(),
            parse_mode=ParseMode.HTML
        )
    await callback.answer()


@router.callback_query(F.data == "menu_earn")
async def cb_menu_earn(callback: CallbackQuery):
    balance = get_balance(callback.from_user.id)
    try:
        await callback.message.edit_text(
            f"💰 <b>Заработок</b>\nТвой баланс: <b>{balance} {CURRENCY_SYMBOL}</b>\n\nВыбери активность:",
            reply_markup=earn_menu_keyboard(),
            parse_mode=ParseMode.HTML
        )
    except Exception:
        await callback.message.answer(
            f"💰 <b>Заработок</b>\nТвой баланс: <b>{balance} {CURRENCY_SYMBOL}</b>\n\nВыбери активность:",
            reply_markup=earn_menu_keyboard(),
            parse_mode=ParseMode.HTML
        )
    await callback.answer()


@router.callback_query(F.data == "menu_casino")
async def cb_menu_casino(callback: CallbackQuery):
    balance = get_balance(callback.from_user.id)
    try:
        await callback.message.edit_text(
            f"🎰 <b>Казино</b>\nТвой баланс: <b>{balance} {CURRENCY_SYMBOL}</b>\n\n"
            f"Выбери игру:\n"
            f"⚠️ Минимальная ставка: {MIN_BET} {CURRENCY_SYMBOL}",
            reply_markup=casino_menu_keyboard(),
            parse_mode=ParseMode.HTML
        )
    except Exception:
        await callback.message.answer(
            f"🎰 <b>Казино</b>\nТвой баланс: <b>{balance} {CURRENCY_SYMBOL}</b>",
            reply_markup=casino_menu_keyboard(),
            parse_mode=ParseMode.HTML
        )
    await callback.answer()


@router.callback_query(F.data == "menu_profile")
async def cb_menu_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    balance = get_balance(user_id)
    
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        stats = conn.execute("SELECT * FROM player_stats WHERE user_id=?", (user_id,)).fetchone()
        tx = conn.execute(
            "SELECT COUNT(*) as cnt, SUM(CASE WHEN amount>0 THEN amount ELSE 0 END) as earned "
            "FROM transactions WHERE user_id=?",
            (user_id,)
        ).fetchone()
    
    wr = 0
    if stats and stats["games_played"] > 0:
        wr = round(stats["games_won"] / stats["games_played"] * 100, 1)
    
    text = (
        f"👤 <b>Профиль</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"👤 Имя: {callback.from_user.first_name}\n"
        f"💰 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"🎮 Игр сыграно: {stats['games_played'] if stats else 0}\n"
        f"🏆 Побед: {stats['games_won'] if stats else 0} ({wr}%)\n"
        f"🎰 Ставок в казино: {stats['casino_bets'] if stats else 0}\n"
        f"🃏 Карточных игр: {stats['cards_played'] if stats else 0}\n"
        f"📝 Вопросов отвечено: {stats['quizzes_answered'] if stats else 0}\n"
        f"✅ Правильных ответов: {stats['quizzes_correct'] if stats else 0}\n\n"
        f"📅 Зарегистрирован: {user['created_at'][:10] if user else 'N/A'}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔗 Реферальная ссылка", callback_data="earn_referral"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    
    try:
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    except Exception:
        await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await callback.answer()


@router.callback_query(F.data == "menu_stats")
async def cb_menu_stats(callback: CallbackQuery):
    """Топ игроков."""
    with get_db() as conn:
        top = conn.execute(
            """SELECT u.first_name, u.username, b.amount 
               FROM balances b JOIN users u ON b.user_id=u.id
               ORDER BY b.amount DESC LIMIT 10"""
        ).fetchall()
    
    lines = ["🏆 <b>Топ-10 игроков</b>\n"]
    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    for i, row in enumerate(top):
        name = row["first_name"] or row["username"] or "Аноним"
        lines.append(f"{medals[i]} {name}: <b>{row['amount']} {CURRENCY_SYMBOL}</b>")
    
    try:
        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=back_to_main(),
            parse_mode=ParseMode.HTML
        )
    except Exception:
        await callback.message.answer(
            "\n".join(lines),
            reply_markup=back_to_main(),
            parse_mode=ParseMode.HTML
        )
    await callback.answer()


@router.callback_query(F.data == "menu_rules")
async def cb_menu_rules(callback: CallbackQuery):
    text = (
        "📋 <b>Правила игры</b>\n\n"
        "⚠️ Валюта является виртуальной и не имеет реальной ценности.\n\n"
        "💰 <b>Лимиты:</b>\n"
        f"• Мин. ставка: {MIN_BET} {CURRENCY_SYMBOL}\n"
        f"• Макс. ставка: {MAX_BET} {CURRENCY_SYMBOL}\n"
        f"• Дневной лимит выигрыша: {DAILY_WIN_LIMIT} {CURRENCY_SYMBOL}\n"
        f"• Дневной лимит проигрыша: {DAILY_LOSS_LIMIT} {CURRENCY_SYMBOL}\n\n"
        "⏱ <b>Кулдауны:</b>\n"
        f"• Мини-игры: {MINIGAME_COOLDOWN//60} мин\n"
        f"• Викторина: {QUIZ_COOLDOWN} сек\n"
        f"• Дневной бонус: 24 часа\n\n"
        "🎰 <b>RTP казино:</b>\n"
        f"• Слоты: {int(SLOTS_RTP*100)}%\n"
        f"• Рулетка: {ROULETTE_RTP*100:.1f}%\n"
        f"• Блэкджек: {BLACKJACK_RTP*100:.1f}%\n"
        f"• Краш: {int(CRASH_RTP*100)}%\n"
        f"• Дайс: {int(DICE_RTP*100)}%\n"
        f"• Карточные дуэли: комиссия {int(CARD_RAKE*100)}%"
    )
    try:
        await callback.message.edit_text(text, reply_markup=back_to_main(), parse_mode=ParseMode.HTML)
    except Exception:
        await callback.message.answer(text, reply_markup=back_to_main(), parse_mode=ParseMode.HTML)
    await callback.answer()

# ============================================================
# ЕЖЕДНЕВНЫЙ БОНУС
# ============================================================

@router.callback_query(F.data == "earn_daily")
@router.message(Command("daily"))
async def earn_daily(event, **kwargs):
    """Ежедневный бонус."""
    if isinstance(event, CallbackQuery):
        user = event.from_user
        answer = event.answer
        send = event.message.answer
    else:
        user = event.from_user
        answer = None
        send = event.answer
    
    ensure_user(user.id, user.username)
    
    cd = check_cooldown(user.id, "daily_bonus")
    if cd:
        hours = cd // 3600
        mins = (cd % 3600) // 60
        msg = f"⏳ Следующий бонус через: <b>{hours}ч {mins}м</b>"
        await send(msg, parse_mode=ParseMode.HTML)
        if answer:
            await answer()
        return
    
    # Streak бонус
    with get_db() as conn:
        last = conn.execute(
            "SELECT created_at FROM transactions WHERE user_id=? AND type='daily_bonus' "
            "ORDER BY created_at DESC LIMIT 1",
            (user.id,)
        ).fetchone()
    
    bonus = DAILY_BONUS
    streak_text = ""
    
    credit_user(user.id, bonus, "daily_bonus", f"Ежедневный бонус")
    set_cooldown(user.id, "daily_bonus", DAILY_BONUS_COOLDOWN)
    
    balance = get_balance(user.id)
    msg = (
        f"🎁 <b>Ежедневный бонус получен!</b>\n\n"
        f"💰 Начислено: <b>+{bonus} {CURRENCY_SYMBOL}</b>\n"
        f"💼 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>\n\n"
        f"Приходи завтра за новым бонусом!"
    )
    await send(msg, reply_markup=back_to_main(), parse_mode=ParseMode.HTML)
    if answer:
        await answer("🎁 Бонус получен!")


@router.callback_query(F.data == "earn_referral")
async def earn_referral(callback: CallbackQuery):
    """Реферальная ссылка."""
    bot_info = await callback.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{callback.from_user.id}"
    
    with get_db() as conn:
        ref_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM users WHERE referral_by=?",
            (callback.from_user.id,)
        ).fetchone()
    
    text = (
        f"🔗 <b>Реферальная программа</b>\n\n"
        f"За каждого приглашённого друга ты получаешь "
        f"<b>{REFERRAL_BONUS} {CURRENCY_SYMBOL}</b>!\n\n"
        f"Твоих рефералов: <b>{ref_count['cnt']}</b>\n\n"
        f"Твоя ссылка:\n<code>{ref_link}</code>"
    )
    try:
        await callback.message.edit_text(text, reply_markup=back_to_main(), parse_mode=ParseMode.HTML)
    except Exception:
        await callback.message.answer(text, reply_markup=back_to_main(), parse_mode=ParseMode.HTML)
    await callback.answer()

# ============================================================
# ВИКТОРИНА
# ============================================================

def get_random_quiz(category: str = None) -> Optional[Dict]:
    """Получить случайный вопрос."""
    with get_db() as conn:
        if category:
            row = conn.execute(
                "SELECT * FROM quizzes WHERE category=? ORDER BY RANDOM() LIMIT 1",
                (category,)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM quizzes ORDER BY RANDOM() LIMIT 1"
            ).fetchone()
        
        if not row:
            return None
        
        options = json.loads(row["options"])
        shuffled = list(enumerate(options))
        random.shuffle(shuffled)
        
        return {
            "id": row["id"],
            "question": row["question"],
            "options": [opt for _, opt in shuffled],
            "correct_idx": next(i for i, (orig_i, _) in enumerate(shuffled) 
                               if orig_i == row["correct_index"]),
            "difficulty": row["difficulty"],
            "category": row["category"],
            "asked_at": time.time()
        }


def quiz_category_keyboard() -> InlineKeyboardMarkup:
    """Выбор категории викторины."""
    builder = InlineKeyboardBuilder()
    categories = [
        ("🌍 География", "quiz_cat_geography"),
        ("🔬 Наука", "quiz_cat_science"),
        ("📜 История", "quiz_cat_history"),
        ("➕ Математика", "quiz_cat_math"),
        ("⚽ Спорт", "quiz_cat_sport"),
        ("🎲 Случайно", "quiz_cat_random"),
    ]
    for text, data in categories:
        builder.row(InlineKeyboardButton(text=text, callback_data=data))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="menu_earn"))
    return builder.as_markup()


@router.callback_query(F.data == "earn_quiz")
@router.message(Command("quiz"))
async def start_quiz(event, state: FSMContext, **kwargs):
    """Начать викторину."""
    if isinstance(event, CallbackQuery):
        user = event.from_user
        send = event.message.answer
        edit = event.message.edit_text
        answer = event.answer
    else:
        user = event.from_user
        send = event.answer
        edit = None
        answer = None
    
    ensure_user(user.id, user.username)
    
    cd = check_cooldown(user.id, "quiz")
    if cd:
        msg = f"⏳ Следующий вопрос через: <b>{cd} сек</b>"
        await send(msg, parse_mode=ParseMode.HTML)
        if answer:
            await answer()
        return
    
    text = "📝 <b>Викторина</b>\n\nВыбери категорию:"
    try:
        if edit:
            await edit(text, reply_markup=quiz_category_keyboard(), parse_mode=ParseMode.HTML)
        else:
            await send(text, reply_markup=quiz_category_keyboard(), parse_mode=ParseMode.HTML)
    except Exception:
        await send(text, reply_markup=quiz_category_keyboard(), parse_mode=ParseMode.HTML)
    
    if answer:
        await answer()


@router.callback_query(F.data.startswith("quiz_cat_"))
async def quiz_category_selected(callback: CallbackQuery, state: FSMContext):
    """Показать вопрос по категории."""
    category = callback.data.replace("quiz_cat_", "")
    if category == "random":
        category = None
    
    quiz = get_random_quiz(category)
    if not quiz:
        await callback.message.edit_text(
            "😔 Вопросы не найдены. Попробуй другую категорию.",
            reply_markup=quiz_category_keyboard()
        )
        await callback.answer()
        return
    
    # Сохраняем состояние
    await state.set_state(QuizStates.answering)
    await state.update_data(quiz=quiz)
    
    diff_stars = "⭐" * quiz["difficulty"]
    reward = QUIZ_BASE_REWARD * quiz["difficulty"]
    
    options_text = "\n".join([
        f"{chr(65+i)}. {opt}" for i, opt in enumerate(quiz["options"])
    ])
    
    text = (
        f"📝 <b>Вопрос ({diff_stars})</b>\n"
        f"💰 Награда: <b>{reward} {CURRENCY_SYMBOL}</b>\n"
        f"⏱ Время: <b>20 секунд</b>\n\n"
        f"❓ {quiz['question']}\n\n"
        f"{options_text}"
    )
    
    builder = InlineKeyboardBuilder()
    for i, opt in enumerate(quiz["options"]):
        builder.row(InlineKeyboardButton(
            text=f"{chr(65+i)}. {opt}",
            callback_data=f"quiz_answer_{i}"
        ))
    builder.row(InlineKeyboardButton(text="❌ Пропустить", callback_data="quiz_skip"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await callback.answer()


@router.callback_query(F.data.startswith("quiz_answer_"), QuizStates.answering)
async def quiz_answer(callback: CallbackQuery, state: FSMContext):
    """Обработка ответа на викторину."""
    data = await state.get_data()
    quiz = data.get("quiz")
    
    if not quiz:
        await state.clear()
        await callback.answer("Время истекло!")
        return
    
    selected = int(callback.data.replace("quiz_answer_", ""))
    elapsed = time.time() - quiz["asked_at"]
    
    if elapsed > 25:  # Буфер 5 сек
        await state.clear()
        await callback.message.edit_text(
            "⏰ Время вышло! Вопрос аннулирован.",
            reply_markup=earn_menu_keyboard()
        )
        await callback.answer("Время вышло!")
        return
    
    is_correct = selected == quiz["correct_idx"]
    reward = QUIZ_BASE_REWARD * quiz["difficulty"]
    
    # Бонус за скорость (до 5 сек = максимум)
    if is_correct and elapsed < 5:
        reward = int(reward * 1.5)
        speed_bonus = " ⚡ +50% за скорость!"
    else:
        speed_bonus = ""
    
    if is_correct:
        can_win, remaining = check_daily_limit(callback.from_user.id, "won", DAILY_WIN_LIMIT)
        if can_win:
            credit_user(callback.from_user.id, reward, "quiz_reward", 
                       f"Викторина: {quiz['question'][:30]}")
            update_daily_limit(callback.from_user.id, "won", reward)
        else:
            reward = 0
    
    set_cooldown(callback.from_user.id, "quiz", QUIZ_COOLDOWN)
    
    # Обновляем статистику
    with get_db() as conn:
        conn.execute(
            """UPDATE player_stats SET 
               quizzes_answered=quizzes_answered+1,
               quizzes_correct=quizzes_correct+?
               WHERE user_id=?""",
            (1 if is_correct else 0, callback.from_user.id)
        )
        conn.commit()
    
    correct_opt = quiz["options"][quiz["correct_idx"]]
    balance = get_balance(callback.from_user.id)
    
    if is_correct:
        text = (
            f"✅ <b>Правильно!</b>{speed_bonus}\n\n"
            f"💰 Получено: <b>+{reward} {CURRENCY_SYMBOL}</b>\n"
            f"💼 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>"
        )
    else:
        text = (
            f"❌ <b>Неверно!</b>\n\n"
            f"Правильный ответ: <b>{correct_opt}</b>\n"
            f"💼 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>"
        )
    
    await state.clear()
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Ещё вопрос", callback_data="earn_quiz"),
        InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
    )
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await callback.answer("✅ Правильно!" if is_correct else "❌ Неверно!")


@router.callback_query(F.data == "quiz_skip")
async def quiz_skip(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "⏭ Вопрос пропущен.",
        reply_markup=earn_menu_keyboard()
    )
    await callback.answer()

# ============================================================
# МИНИ-ИГРА: САПЁР
# ============================================================

MINESWEEPER_ROWS = 5
MINESWEEPER_COLS = 5
MINE_CONFIGS = {
    "easy": 3,
    "medium": 5,
    "hard": 8
}
MINE_MULTIPLIERS = {
    "easy": 1.15,
    "medium": 1.25,
    "hard": 1.45
}


def create_minesweeper_grid(mines: int) -> Dict:
    """Создать поле сапёра."""
    all_cells = [(r, c) for r in range(MINESWEEPER_ROWS) for c in range(MINESWEEPER_COLS)]
    mine_positions = set(map(tuple, random.sample(all_cells, mines)))
    
    return {
        "mines": [list(m) for m in mine_positions],
        "revealed": [],
        "multiplier": 1.0,
        "status": "playing"
    }


def minesweeper_keyboard(session_data: Dict, session_id: str) -> InlineKeyboardMarkup:
    """Клавиатура поля сапёра."""
    builder = InlineKeyboardBuilder()
    grid_data = json.loads(session_data["data"])
    revealed = set(map(tuple, grid_data["revealed"]))
    mines = set(map(tuple, grid_data["mines"]))
    
    for row in range(MINESWEEPER_ROWS):
        row_buttons = []
        for col in range(MINESWEEPER_COLS):
            cell = (row, col)
            if cell in revealed:
                if cell in mines:
                    text = "💥"
                else:
                    text = "✅"
            else:
                text = "⬜"
            
            row_buttons.append(InlineKeyboardButton(
                text=text,
                callback_data=f"ms_{session_id}_{row}_{col}"
            ))
        builder.row(*row_buttons)
    
    multiplier = grid_data["multiplier"]
    bet = session_data["bet"]
    potential = int(bet * multiplier)
    
    builder.row(
        InlineKeyboardButton(
            text=f"💰 Забрать {potential} {CURRENCY_SYMBOL} (×{multiplier:.2f})",
            callback_data=f"ms_cashout_{session_id}"
        )
    )
    return builder.as_markup()


@router.callback_query(F.data == "game_minesweeper")
@router.message(Command("minesweeper"))
async def start_minesweeper(event, state: FSMContext, **kwargs):
    """Запуск сапёра - выбор ставки."""
    if isinstance(event, CallbackQuery):
        user = event.from_user
        send = event.message.answer
        answer = event.answer
    else:
        user = event.from_user
        send = event.answer
        answer = None
    
    ensure_user(user.id, user.username)
    
    cd = check_cooldown(user.id, "minesweeper")
    if cd:
        mins = cd // 60
        secs = cd % 60
        await send(
            f"⏳ Сапёр доступен через: <b>{mins}м {secs}с</b>",
            parse_mode=ParseMode.HTML
        )
        if answer:
            await answer()
        return
    
    balance = get_balance(user.id)
    text = (
        f"💣 <b>Сапёр</b>\n\n"
        f"💼 Твой баланс: <b>{balance} {CURRENCY_SYMBOL}</b>\n\n"
        f"Открывай ячейки и забирай выигрыш!\n"
        f"Наступишь на мину — потеряешь ставку.\n\n"
        f"Выбери ставку:"
    )
    await send(text, reply_markup=bet_keyboard("ms", [50, 100, 200, 500, 1000]), parse_mode=ParseMode.HTML)
    if answer:
        await answer()


@router.callback_query(F.data.startswith("bet_ms_"))
async def minesweeper_bet_selected(callback: CallbackQuery, state: FSMContext):
    """Выбор ставки — выбор сложности."""
    bet = int(callback.data.replace("bet_ms_", ""))
    
    balance = get_balance(callback.from_user.id)
    if balance < bet:
        await callback.answer(f"❌ Недостаточно средств! Баланс: {balance} {CURRENCY_SYMBOL}", show_alert=True)
        return
    
    await state.update_data(ms_bet=bet)
    
    builder = InlineKeyboardBuilder()
    configs_text = {
        "easy": f"🟢 Лёгкий ({MINE_CONFIGS['easy']} мины, ×{MINE_MULTIPLIERS['easy']})",
        "medium": f"🟡 Средний ({MINE_CONFIGS['medium']} мин, ×{MINE_MULTIPLIERS['medium']})",
        "hard": f"🔴 Сложный ({MINE_CONFIGS['hard']} мин, ×{MINE_MULTIPLIERS['hard']})",
    }
    for key, text in configs_text.items():
        builder.row(InlineKeyboardButton(text=text, callback_data=f"ms_diff_{key}"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="game_minesweeper"))
    
    await callback.message.edit_text(
        f"💣 <b>Сапёр</b>\nСтавка: <b>{bet} {CURRENCY_SYMBOL}</b>\n\nВыбери сложность:",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ms_diff_"))
async def minesweeper_difficulty(callback: CallbackQuery, state: FSMContext):
    """Создать игру сапёра."""
    difficulty = callback.data.replace("ms_diff_", "")
    data = await state.get_data()
    bet = data.get("ms_bet", MIN_BET)
    
    # Списываем ставку
    ok, new_balance = debit_user(callback.from_user.id, bet, "minesweeper_bet", "Ставка сапёр")
    if not ok:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    mines_count = MINE_CONFIGS[difficulty]
    grid = create_minesweeper_grid(mines_count)
    grid["base_multiplier"] = MINE_MULTIPLIERS[difficulty]
    
    session_id = str(uuid.uuid4())[:8]
    expires = (datetime.now() + timedelta(minutes=30)).isoformat()
    
    with get_db() as conn:
        conn.execute(
            """INSERT INTO minigame_sessions 
               (id, user_id, game_type, state, data, bet, multiplier, message_id, chat_id, expires_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (session_id, callback.from_user.id, "minesweeper", "playing",
             json.dumps(grid), bet, 1.0, callback.message.message_id,
             callback.message.chat.id, expires)
        )
        conn.commit()
    
    await state.set_state(MinesweeperStates.playing)
    await state.update_data(ms_session=session_id)
    
    set_cooldown(callback.from_user.id, "minesweeper", MINIGAME_COOLDOWN)
    update_daily_limit(callback.from_user.id, "minigames", 1)
    
    with get_db() as conn:
        session = conn.execute(
            "SELECT * FROM minigame_sessions WHERE id=?", (session_id,)
        ).fetchone()
        session_dict = dict(session)
    
    text = (
        f"💣 <b>Сапёр</b> [{difficulty.upper()}]\n"
        f"💰 Ставка: <b>{bet} {CURRENCY_SYMBOL}</b>\n"
        f"💥 Мин: <b>{mines_count}</b> | Множитель: <b>×1.00</b>\n\n"
        f"Нажимай на ячейки. Удачи!"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=minesweeper_keyboard(session_dict, session_id),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ms_") & ~F.data.startswith("ms_diff_") & ~F.data.startswith("ms_cashout_"))
async def minesweeper_cell_click(callback: CallbackQuery, state: FSMContext):
    """Клик по ячейке сапёра."""
    parts = callback.data.split("_")
    if len(parts) != 4:
        await callback.answer()
        return
    
    _, session_id, row, col = parts
    row, col = int(row), int(col)
    
    with get_db() as conn:
        session = conn.execute(
            "SELECT * FROM minigame_sessions WHERE id=? AND user_id=?",
            (session_id, callback.from_user.id)
        ).fetchone()
        
        if not session or session["state"] != "playing":
            await callback.answer("Игра не найдена или завершена!", show_alert=True)
            return
        
        grid = json.loads(session["data"])
        revealed = [list(r) for r in grid["revealed"]]
        mines = [list(m) for m in grid["mines"]]
        
        if [row, col] in revealed:
            await callback.answer("Ячейка уже открыта!")
            return
        
        revealed.append([row, col])
        
        is_mine = [row, col] in mines
        
        if is_mine:
            grid["revealed"] = revealed
            grid["status"] = "lost"
            conn.execute(
                "UPDATE minigame_sessions SET state='finished', data=? WHERE id=?",
                (json.dumps(grid), session_id)
            )
            conn.commit()
            
            update_daily_limit(callback.from_user.id, "lost", session["bet"])
            
            with get_db() as conn2:
                conn2.execute(
                    "UPDATE player_stats SET games_played=games_played+1 WHERE user_id=?",
                    (callback.from_user.id,)
                )
                conn2.commit()
            
            balance = get_balance(callback.from_user.id)
            
            # Показываем все мины
            for mine in mines:
                if mine not in revealed:
                    revealed.append(mine)
            grid["revealed"] = revealed
            
            session_dict = dict(session)
            session_dict["data"] = json.dumps(grid)
            
            await callback.message.edit_text(
                f"💥 <b>Бум! Ты попал на мину!</b>\n\n"
                f"💸 Потеряно: <b>-{session['bet']} {CURRENCY_SYMBOL}</b>\n"
                f"💼 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="🔄 Сыграть снова", callback_data="game_minesweeper"),
                    InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
                ]]),
                parse_mode=ParseMode.HTML
            )
            await callback.answer("💥 Мина!")
        else:
            # Безопасная ячейка
            safe_count = len([c for c in revealed if c not in mines])
            base_mult = grid.get("base_multiplier", 1.25)
            new_multiplier = round(1.0 + (safe_count * (base_mult - 1.0)), 2)
            
            grid["revealed"] = revealed
            grid["multiplier"] = new_multiplier
            grid["status"] = "playing"
            
            conn.execute(
                "UPDATE minigame_sessions SET data=?, multiplier=? WHERE id=?",
                (json.dumps(grid), new_multiplier, session_id)
            )
            conn.commit()
            
            session_dict = dict(session)
            session_dict["data"] = json.dumps(grid)
            
            potential = int(session["bet"] * new_multiplier)
            
            text = (
                f"💣 <b>Сапёр</b>\n"
                f"💰 Ставка: <b>{session['bet']} {CURRENCY_SYMBOL}</b>\n"
                f"✅ Открыто: <b>{safe_count}</b> ячеек\n"
                f"💎 Множитель: <b>×{new_multiplier:.2f}</b>\n"
                f"💰 Потенциал: <b>{potential} {CURRENCY_SYMBOL}</b>\n\n"
                f"Продолжай или забери выигрыш!"
            )
            
            await callback.message.edit_text(
                text,
                reply_markup=minesweeper_keyboard(session_dict, session_id),
                parse_mode=ParseMode.HTML
            )
            await callback.answer(f"✅ Безопасно! ×{new_multiplier:.2f}")


@router.callback_query(F.data.startswith("ms_cashout_"))
async def minesweeper_cashout(callback: CallbackQuery, state: FSMContext):
    """Забрать выигрыш в сапёре."""
    session_id = callback.data.replace("ms_cashout_", "")
    
    with get_db() as conn:
        session = conn.execute(
            "SELECT * FROM minigame_sessions WHERE id=? AND user_id=? AND state='playing'",
            (session_id, callback.from_user.id)
        ).fetchone()
        
        if not session:
            await callback.answer("Игра не найдена!", show_alert=True)
            return
        
        grid = json.loads(session["data"])
        safe_count = len([c for c in grid["revealed"] if c not in grid["mines"]])
        
        if safe_count == 0:
            await callback.answer("Сначала открой хотя бы одну ячейку!", show_alert=True)
            return
        
        multiplier = grid["multiplier"]
        win_amount = int(session["bet"] * multiplier)
        
        conn.execute(
            "UPDATE minigame_sessions SET state='finished' WHERE id=?",
            (session_id,)
        )
        conn.commit()
    
    can_win, remaining = check_daily_limit(callback.from_user.id, "won", DAILY_WIN_LIMIT)
    if can_win:
        actual_win = min(win_amount, session["bet"] + remaining)
        credit_user(callback.from_user.id, actual_win, "minesweeper_win", 
                   f"Выигрыш в сапёре ×{multiplier:.2f}")
        update_daily_limit(callback.from_user.id, "won", actual_win - session["bet"])
    else:
        actual_win = session["bet"]
        credit_user(callback.from_user.id, actual_win, "minesweeper_return",
                   "Возврат ставки (лимит)")
    
    with get_db() as conn:
        conn.execute(
            "UPDATE player_stats SET games_played=games_played+1, games_won=games_won+1 WHERE user_id=?",
            (callback.from_user.id,)
        )
        conn.commit()
    
    balance = get_balance(callback.from_user.id)
    profit = actual_win - session["bet"]
    
    await callback.message.edit_text(
        f"💰 <b>Выигрыш забран!</b>\n\n"
        f"🎰 Множитель: <b>×{multiplier:.2f}</b>\n"
        f"💎 Получено: <b>+{actual_win} {CURRENCY_SYMBOL}</b>\n"
        f"📈 Профит: <b>+{profit} {CURRENCY_SYMBOL}</b>\n"
        f"💼 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔄 Сыграть снова", callback_data="game_minesweeper"),
            InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
        ]]),
        parse_mode=ParseMode.HTML
    )
    await state.clear()
    await callback.answer(f"💰 Получено {actual_win} {CURRENCY_SYMBOL}!")

# ============================================================
# МИНИ-ИГРА: РЕАКЦИЯ
# ============================================================

@router.callback_query(F.data == "game_reaction")
@router.message(Command("reaction"))
async def start_reaction(event, state: FSMContext, **kwargs):
    """Игра на реакцию."""
    if isinstance(event, CallbackQuery):
        user = event.from_user
        send = event.message.answer
        answer = event.answer
    else:
        user = event.from_user
        send = event.answer
        answer = None
    
    ensure_user(user.id, user.username)
    
    cd = check_cooldown(user.id, "reaction")
    if cd:
        await send(f"⏳ Реакция доступна через: <b>{cd} сек</b>", parse_mode=ParseMode.HTML)
        if answer:
            await answer()
        return
    
    # Случайная задержка
    delay = random.uniform(1.5, 4.0)
    
    await state.set_state(ReactionStates.waiting)
    await state.update_data(
        reaction_delay=delay,
        reaction_start=time.time() + delay,
        reaction_ready=False
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="⏳ Жди... не нажимай!",
        callback_data="reaction_early"
    ))
    
    msg = await send(
        "⚡ <b>Игра на реакцию</b>\n\nЖди сигнала... НЕ НАЖИМАЙ СЕЙЧАС!\n\n"
        f"Сигнал появится через <b>{delay:.1f}</b> сек",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    
    if answer:
        await answer()
    
    # Ждём и обновляем кнопку
    await asyncio.sleep(delay)
    
    start_time = time.time()
    await state.update_data(reaction_ready=True, reaction_start=start_time)
    
    builder2 = InlineKeyboardBuilder()
    builder2.row(InlineKeyboardButton(
        text="🟢 ЖМИ СЕЙЧАС!!! 🟢",
        callback_data="reaction_hit"
    ))
    
    try:
        if isinstance(event, CallbackQuery):
            await event.message.edit_reply_markup(reply_markup=builder2.as_markup())
        elif msg:
            await msg.edit_reply_markup(reply_markup=builder2.as_markup())
    except Exception:
        pass


@router.callback_query(F.data == "reaction_early", ReactionStates.waiting)
async def reaction_early(callback: CallbackQuery, state: FSMContext):
    """Нажали слишком рано."""
    await state.clear()
    set_cooldown(callback.from_user.id, "reaction", 30)
    
    await callback.message.edit_text(
        "❌ <b>Слишком рано!</b>\n\nПопробуй снова через 30 секунд.",
        reply_markup=back_to_main(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer("❌ Рано!")


@router.callback_query(F.data == "reaction_hit", ReactionStates.waiting)
async def reaction_hit(callback: CallbackQuery, state: FSMContext):
    """Нажали в нужный момент."""
    data = await state.get_data()
    
    if not data.get("reaction_ready"):
        await reaction_early(callback, state)
        return
    
    reaction_time = (time.time() - data["reaction_start"]) * 1000  # мс
    await state.clear()
    
    set_cooldown(callback.from_user.id, "reaction", MINIGAME_COOLDOWN)
    
    # Расчёт награды по скорости реакции
    if reaction_time < 200:
        reward = 150
        grade = "⚡ МОЛНИЕНОСНО!"
        emoji = "🥇"
    elif reaction_time < 400:
        reward = 100
        grade = "🟢 Отлично!"
        emoji = "🥈"
    elif reaction_time < 700:
        reward = 60
        grade = "🟡 Хорошо"
        emoji = "🥉"
    elif reaction_time < 1000:
        reward = 30
        grade = "🟠 Нормально"
        emoji = "🎖"
    else:
        reward = 10
        grade = "🔴 Медленно"
        emoji = "😴"
    
    can_win, _ = check_daily_limit(callback.from_user.id, "won", DAILY_WIN_LIMIT)
    if can_win:
        credit_user(callback.from_user.id, reward, "reaction_reward", 
                   f"Реакция: {reaction_time:.0f}мс")
        update_daily_limit(callback.from_user.id, "won", reward)
    else:
        reward = 0
    
    balance = get_balance(callback.from_user.id)
    
    await callback.message.edit_text(
        f"{emoji} <b>Результат: {reaction_time:.0f} мс</b>\n"
        f"Оценка: {grade}\n\n"
        f"💰 Награда: <b>+{reward} {CURRENCY_SYMBOL}</b>\n"
        f"💼 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔄 Ещё раз", callback_data="game_reaction"),
            InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
        ]]),
        parse_mode=ParseMode.HTML
    )
    await callback.answer(f"⚡ {reaction_time:.0f} мс!")


# ============================================================
# МИНИ-ИГРА: ПАМЯТЬ
# ============================================================

MEMORY_EMOJIS = ["🎮", "🎯", "🎲", "🎪", "🎨", "🎭", "🎬", "🎤"]


def create_memory_grid() -> Dict:
    """Создать сетку для игры на память."""
    pairs = MEMORY_EMOJIS * 2  # 16 карточек = 8 пар
    random.shuffle(pairs)
    
    return {
        "cards": pairs,
        "revealed": [],
        "matched": [],
        "attempts": 0,
        "selected": None,
        "pairs_found": 0
    }


def memory_keyboard(grid: Dict, session_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для игры на память."""
    builder = InlineKeyboardBuilder()
    cards = grid["cards"]
    revealed = set(grid["revealed"])
    matched = set(grid["matched"])
    selected = grid.get("selected")
    
    for i in range(4):
        row_btns = []
        for j in range(4):
            idx = i * 4 + j
            if idx in matched:
                text = "✅"
            elif idx in revealed or idx == selected:
                text = cards[idx]
            else:
                text = "🔲"
            
            row_btns.append(InlineKeyboardButton(
                text=text,
                callback_data=f"mem_{session_id}_{idx}"
            ))
        builder.row(*row_btns)
    
    pairs = grid["pairs_found"]
    attempts = grid["attempts"]
    builder.row(InlineKeyboardButton(
        text=f"Пар: {pairs}/8 | Попыток: {attempts}",
        callback_data="noop"
    ))
    return builder.as_markup()


@router.callback_query(F.data == "game_memory")
@router.message(Command("memory"))
async def start_memory(event, state: FSMContext, **kwargs):
    """Запуск игры на память."""
    if isinstance(event, CallbackQuery):
        user = event.from_user
        send = event.message.answer
        answer = event.answer
    else:
        user = event.from_user
        send = event.answer
        answer = None
    
    ensure_user(user.id, user.username)
    
    cd = check_cooldown(user.id, "memory")
    if cd:
        await send(f"⏳ Доступно через: <b>{cd // 60}м {cd % 60}с</b>", parse_mode=ParseMode.HTML)
        if answer:
            await answer()
        return
    
    grid = create_memory_grid()
    session_id = str(uuid.uuid4())[:8]
    expires = (datetime.now() + timedelta(minutes=15)).isoformat()
    
    with get_db() as conn:
        conn.execute(
            """INSERT INTO minigame_sessions 
               (id, user_id, game_type, state, data, bet, expires_at)
               VALUES (?,?,?,?,?,?,?)""",
            (session_id, user.id, "memory", "playing", json.dumps(grid), 0, expires)
        )
        conn.commit()
    
    await state.set_state(MemoryStates.playing)
    await state.update_data(memory_session=session_id)
    
    set_cooldown(user.id, "memory", MINIGAME_COOLDOWN)
    
    text = (
        "🧠 <b>Игра на память</b>\n\n"
        "Открывай карточки и найди все пары!\n"
        "Награда зависит от числа найденных пар."
    )
    
    await send(text, reply_markup=memory_keyboard(grid, session_id), parse_mode=ParseMode.HTML)
    if answer:
        await answer()


@router.callback_query(F.data.startswith("mem_") & ~F.data.startswith("mem_cashout"))
async def memory_card_click(callback: CallbackQuery, state: FSMContext):
    """Клик по карточке в игре на память."""
    parts = callback.data.split("_")
    if len(parts) != 3:
        await callback.answer()
        return
    
    _, session_id, idx_str = parts
    idx = int(idx_str)
    
    with get_db() as conn:
        session = conn.execute(
            "SELECT * FROM minigame_sessions WHERE id=? AND user_id=? AND state='playing'",
            (session_id, callback.from_user.id)
        ).fetchone()
        
        if not session:
            await callback.answer("Игра не найдена!")
            return
        
        grid = json.loads(session["data"])
        
        if idx in grid["matched"] or idx == grid.get("selected"):
            await callback.answer("Эта карточка уже открыта!")
            return
        
        if grid.get("selected") is None:
            # Первая карточка
            grid["selected"] = idx
            conn.execute(
                "UPDATE minigame_sessions SET data=? WHERE id=?",
                (json.dumps(grid), session_id)
            )
            conn.commit()
            
            await callback.message.edit_reply_markup(
                reply_markup=memory_keyboard(grid, session_id)
            )
            await callback.answer(f"Выбрано: {grid['cards'][idx]}")
        else:
            # Вторая карточка
            first_idx = grid["selected"]
            grid["selected"] = None
            grid["attempts"] += 1
            grid["revealed"].append(idx)
            grid["revealed"].append(first_idx)
            
            if grid["cards"][idx] == grid["cards"][first_idx] and idx != first_idx:
                # Пара найдена
                grid["matched"].extend([idx, first_idx])
                grid["pairs_found"] += 1
                grid["revealed"] = [r for r in grid["revealed"] 
                                    if r not in grid["matched"]]
                
                # Проверка завершения
                if grid["pairs_found"] == 8:
                    conn.execute(
                        "UPDATE minigame_sessions SET state='finished', data=? WHERE id=?",
                        (json.dumps(grid), session_id)
                    )
                    conn.commit()
                    
                    reward = 200
                    can_win, _ = check_daily_limit(callback.from_user.id, "won", DAILY_WIN_LIMIT)
                    if can_win:
                        credit_user(callback.from_user.id, reward, "memory_win", 
                                   f"Память: все пары найдены")
                    balance = get_balance(callback.from_user.id)
                    
                    await callback.message.edit_text(
                        f"🎉 <b>Все пары найдены!</b>\n\n"
                        f"Попыток: <b>{grid['attempts']}</b>\n"
                        f"💰 Награда: <b>+{reward} {CURRENCY_SYMBOL}</b>\n"
                        f"💼 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                            InlineKeyboardButton(text="🔄 Снова", callback_data="game_memory"),
                            InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
                        ]]),
                        parse_mode=ParseMode.HTML
                    )
                    await state.clear()
                    await callback.answer("🎉 Победа!")
                    return
                
                conn.execute(
                    "UPDATE minigame_sessions SET data=? WHERE id=?",
                    (json.dumps(grid), session_id)
                )
                conn.commit()
                
                await callback.message.edit_reply_markup(
                    reply_markup=memory_keyboard(grid, session_id)
                )
                await callback.answer(f"✅ Пара найдена! {grid['cards'][idx]}")
            else:
                # Не совпало
                conn.execute(
                    "UPDATE minigame_sessions SET data=? WHERE id=?",
                    (json.dumps(grid), session_id)
                )
                conn.commit()
                
                await callback.message.edit_reply_markup(
                    reply_markup=memory_keyboard(grid, session_id)
                )
                await callback.answer("❌ Не совпало")
                
                await asyncio.sleep(1.5)
                
                # Скрываем карточки
                grid["revealed"] = [r for r in grid["revealed"] 
                                    if r not in [idx, first_idx] and r not in grid["matched"]]
                
                with get_db() as conn2:
                    conn2.execute(
                        "UPDATE minigame_sessions SET data=? WHERE id=?",
                        (json.dumps(grid), session_id)
                    )
                    conn2.commit()
                
                try:
                    await callback.message.edit_reply_markup(
                        reply_markup=memory_keyboard(grid, session_id)
                    )
                except Exception:
                    pass


# ============================================================
# КАЗИНО: СЛОТЫ
# ============================================================

SLOT_SYMBOLS = ["🍒", "🍋", "🍊", "🍇", "💎", "🎰"]
SLOT_WEIGHTS = [30, 25, 20, 15, 7, 3]  # Веса символов

SLOT_PAYOUTS = {
    ("🍒", "🍒", "🍒"): 3,
    ("🍋", "🍋", "🍋"): 4,
    ("🍊", "🍊", "🍊"): 6,
    ("🍇", "🍇", "🍇"): 8,
    ("💎", "💎", "💎"): 20,
    ("🎰", "🎰", "🎰"): 50,
    ("🍒", "🍒", None): 1.5,
    ("🍋", "🍋", None): 1.5,
}


def spin_slots(seed: str = None) -> Tuple[List[str], float]:
    """Крутим барабаны слотов."""
    if seed:
        random.seed(seed)
    
    result = random.choices(SLOT_SYMBOLS, weights=SLOT_WEIGHTS, k=3)
    
    multiplier = 0
    result_tuple = tuple(result)
    
    if result_tuple in SLOT_PAYOUTS:
        multiplier = SLOT_PAYOUTS[result_tuple]
    elif result[0] == result[1]:
        key = (result[0], result[0], None)
        multiplier = SLOT_PAYOUTS.get(key, 0)
    
    # House edge
    if multiplier > 0:
        multiplier *= SLOTS_RTP
    
    return result, multiplier


@router.callback_query(F.data == "casino_slots")
@router.message(Command("slots"))
async def casino_slots(event, **kwargs):
    """Слоты - выбор ставки."""
    if isinstance(event, CallbackQuery):
        user = event.from_user
        send = event.message.answer
        edit = event.message.edit_text
        answer = event.answer
    else:
        user = event.from_user
        send = event.answer
        edit = None
        answer = None
    
    ensure_user(user.id, user.username)
    balance = get_balance(user.id)
    
    text = (
        f"🎰 <b>Слоты</b>\n\n"
        f"💼 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>\n\n"
        f"🎯 Комбинации:\n"
        f"🍒🍒🍒 = ×3 | 🍋🍋🍋 = ×4\n"
        f"🍊🍊🍊 = ×6 | 🍇🍇🍇 = ×8\n"
        f"💎💎💎 = ×20 | 🎰🎰🎰 = ×50\n\n"
        f"Выбери ставку:"
    )
    
    try:
        if edit:
            await edit(text, reply_markup=bet_keyboard("slots"), parse_mode=ParseMode.HTML)
        else:
            await send(text, reply_markup=bet_keyboard("slots"), parse_mode=ParseMode.HTML)
    except Exception:
        await send(text, reply_markup=bet_keyboard("slots"), parse_mode=ParseMode.HTML)
    
    if answer:
        await answer()


@router.callback_query(F.data.startswith("bet_slots_"))
async def slots_spin(callback: CallbackQuery):
    """Крутим слоты."""
    bet = int(callback.data.replace("bet_slots_", ""))
    user_id = callback.from_user.id
    
    balance = get_balance(user_id)
    if balance < bet:
        await callback.answer(f"❌ Недостаточно средств!", show_alert=True)
        return
    
    if bet < MIN_BET or bet > MAX_BET:
        await callback.answer(f"❌ Ставка должна быть от {MIN_BET} до {MAX_BET}", show_alert=True)
        return
    
    # Списываем ставку
    ok, _ = debit_user(user_id, bet, "slots_bet", f"Ставка слоты: {bet}")
    if not ok:
        await callback.answer("❌ Ошибка списания!", show_alert=True)
        return
    
    seed = secrets.token_hex(8)
    result, multiplier = spin_slots(seed)
    
    win_amount = int(bet * multiplier) if multiplier > 0 else 0
    
    # Проверка дневного лимита
    if win_amount > 0:
        can_win, remaining = check_daily_limit(user_id, "won", DAILY_WIN_LIMIT)
        if can_win:
            actual_win = min(win_amount, bet + remaining)
            credit_user(user_id, actual_win, "slots_win", f"Слоты: {' '.join(result)}")
            update_daily_limit(user_id, "won", actual_win - bet)
        else:
            actual_win = 0
    else:
        actual_win = 0
        update_daily_limit(user_id, "lost", bet)
    
    # Логируем ставку
    with get_db() as conn:
        conn.execute(
            """INSERT INTO casino_bets (id, user_id, game_type, bet, result, win_amount, seed, details)
               VALUES (?,?,?,?,?,?,?,?)""",
            (str(uuid.uuid4()), user_id, "slots", bet,
             json.dumps(result), actual_win, seed, json.dumps({"multiplier": multiplier}))
        )
        conn.execute(
            "UPDATE player_stats SET casino_bets=casino_bets+1, "
            "casino_won=casino_won+?, casino_lost=casino_lost+? WHERE user_id=?",
            (actual_win, bet if actual_win == 0 else 0, user_id)
        )
        conn.commit()
    
    balance = get_balance(user_id)
    
    reel = " | ".join(result)
    if win_amount > 0:
        result_text = f"🎉 <b>ВЫИГРЫШ!</b>\n💰 Получено: <b>+{actual_win} {CURRENCY_SYMBOL}</b> (×{multiplier:.1f})"
    else:
        result_text = "😔 <b>Не повезло...</b>"
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔄 Ещё раз", callback_data=f"bet_slots_{bet}"))
    builder.row(
        InlineKeyboardButton(text="💰 Другая ставка", callback_data="casino_slots"),
        InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
    )
    
    text = (
        f"🎰 <b>Слоты</b>\n\n"
        f"[ {reel} ]\n\n"
        f"{result_text}\n"
        f"💼 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>"
    )
    
    try:
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    except Exception:
        await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    
    await callback.answer()

# ============================================================
# КАЗИНО: РУЛЕТКА
# ============================================================

ROULETTE_RED = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
ROULETTE_BLACK = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}


def spin_roulette(seed: str = None) -> int:
    """Крутим рулетку."""
    if seed:
        random.seed(seed)
    return random.randint(0, 36)


def calculate_roulette_win(bet_type: str, bet_value: str, number: int, bet_amount: int) -> int:
    """Рассчитать выигрыш рулетки."""
    if bet_type == "number":
        if int(bet_value) == number:
            return int(bet_amount * 35 * ROULETTE_RTP)
    elif bet_type == "color":
        if bet_value == "red" and number in ROULETTE_RED:
            return int(bet_amount * 2 * ROULETTE_RTP)
        elif bet_value == "black" and number in ROULETTE_BLACK:
            return int(bet_amount * 2 * ROULETTE_RTP)
    elif bet_type == "parity":
        if number != 0:
            if bet_value == "even" and number % 2 == 0:
                return int(bet_amount * 2 * ROULETTE_RTP)
            elif bet_value == "odd" and number % 2 == 1:
                return int(bet_amount * 2 * ROULETTE_RTP)
    elif bet_type == "dozen":
        dozen = int(bet_value)
        if dozen == 1 and 1 <= number <= 12:
            return int(bet_amount * 3 * ROULETTE_RTP)
        elif dozen == 2 and 13 <= number <= 24:
            return int(bet_amount * 3 * ROULETTE_RTP)
        elif dozen == 3 and 25 <= number <= 36:
            return int(bet_amount * 3 * ROULETTE_RTP)
    return 0


@router.callback_query(F.data == "casino_roulette")
@router.message(Command("roulette"))
async def casino_roulette(event, **kwargs):
    """Рулетка - меню ставок."""
    if isinstance(event, CallbackQuery):
        user = event.from_user
        send = event.message.answer
        edit = event.message.edit_text
        answer = event.answer
    else:
        user = event.from_user
        send = event.answer
        edit = None
        answer = None
    
    ensure_user(user.id, user.username)
    balance = get_balance(user.id)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔴 Красное", callback_data="rl_type_color_red"),
        InlineKeyboardButton(text="⚫ Чёрное", callback_data="rl_type_color_black")
    )
    builder.row(
        InlineKeyboardButton(text="Чётное", callback_data="rl_type_parity_even"),
        InlineKeyboardButton(text="Нечётное", callback_data="rl_type_parity_odd")
    )
    builder.row(
        InlineKeyboardButton(text="1-12", callback_data="rl_type_dozen_1"),
        InlineKeyboardButton(text="13-24", callback_data="rl_type_dozen_2"),
        InlineKeyboardButton(text="25-36", callback_data="rl_type_dozen_3")
    )
    builder.row(InlineKeyboardButton(text="🔢 Число (×35)", callback_data="rl_type_number_0"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="menu_casino"))
    
    text = (
        f"🎡 <b>Рулетка (Европейская)</b>\n\n"
        f"💼 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>\n\n"
        f"Выбери тип ставки:"
    )
    
    try:
        if edit:
            await edit(text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
        else:
            await send(text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    except Exception:
        await send(text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    
    if answer:
        await answer()


@router.callback_query(F.data.startswith("rl_type_"))
async def roulette_type_selected(callback: CallbackQuery, state: FSMContext):
    """Выбор типа ставки рулетки."""
    parts = callback.data.replace("rl_type_", "").split("_", 1)
    bet_type = parts[0]
    bet_value = parts[1] if len(parts) > 1 else "0"
    
    if bet_type == "number":
        # Показываем числа
        builder = InlineKeyboardBuilder()
        buttons = []
        for i in range(37):
            if i in ROULETTE_RED:
                emoji = "🔴"
            elif i in ROULETTE_BLACK:
                emoji = "⚫"
            else:
                emoji = "🟢"
            buttons.append(InlineKeyboardButton(
                text=f"{emoji}{i}",
                callback_data=f"rl_num_{i}"
            ))
        
        for i in range(0, len(buttons), 6):
            builder.row(*buttons[i:i+6])
        builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="casino_roulette"))
        
        await callback.message.edit_text(
            "🎡 <b>Рулетка</b>\n\nВыбери число для ставки:",
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )
        await callback.answer()
        return
    
    # Для остальных типов — выбор суммы
    await state.update_data(rl_type=bet_type, rl_value=bet_value)
    
    type_names = {
        "color": {"red": "🔴 Красное", "black": "⚫ Чёрное"},
        "parity": {"even": "Чётное", "odd": "Нечётное"},
        "dozen": {"1": "1-12", "2": "13-24", "3": "25-36"}
    }
    
    bet_name = type_names.get(bet_type, {}).get(bet_value, bet_value)
    
    await callback.message.edit_text(
        f"🎡 <b>Рулетка</b>\nСтавка: <b>{bet_name}</b>\n\nВыбери сумму:",
        reply_markup=bet_keyboard("roulette"),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rl_num_"))
async def roulette_number_selected(callback: CallbackQuery, state: FSMContext):
    """Выбор числа рулетки."""
    number = int(callback.data.replace("rl_num_", ""))
    await state.update_data(rl_type="number", rl_value=str(number))
    
    await callback.message.edit_text(
        f"🎡 <b>Рулетка</b>\nСтавка на число: <b>{number}</b> (×35)\n\nВыбери сумму:",
        reply_markup=bet_keyboard("roulette"),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data.startswith("bet_roulette_"))
async def roulette_spin(callback: CallbackQuery, state: FSMContext):
    """Вращение рулетки."""
    bet = int(callback.data.replace("bet_roulette_", ""))
    user_id = callback.from_user.id
    
    data = await state.get_data()
    bet_type = data.get("rl_type", "color")
    bet_value = data.get("rl_value", "red")
    
    balance = get_balance(user_id)
    if balance < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    ok, _ = debit_user(user_id, bet, "roulette_bet", f"Рулетка: {bet_type}/{bet_value}")
    if not ok:
        await callback.answer("❌ Ошибка!", show_alert=True)
        return
    
    seed = secrets.token_hex(8)
    number = spin_roulette(seed)
    win = calculate_roulette_win(bet_type, bet_value, number, bet)
    
    if win > 0:
        can_win, remaining = check_daily_limit(user_id, "won", DAILY_WIN_LIMIT)
        if can_win:
            actual_win = min(win, bet + remaining)
            credit_user(user_id, actual_win, "roulette_win", f"Рулетка №{number}")
            update_daily_limit(user_id, "won", actual_win - bet)
        else:
            actual_win = 0
    else:
        actual_win = 0
        update_daily_limit(user_id, "lost", bet)
    
    with get_db() as conn:
        conn.execute(
            """INSERT INTO casino_bets (id, user_id, game_type, bet, result, win_amount, seed, details)
               VALUES (?,?,?,?,?,?,?,?)""",
            (str(uuid.uuid4()), user_id, "roulette", bet, str(number), actual_win, seed,
             json.dumps({"type": bet_type, "value": bet_value}))
        )
        conn.execute(
            "UPDATE player_stats SET casino_bets=casino_bets+1 WHERE user_id=?", (user_id,)
        )
        conn.commit()
    
    balance = get_balance(user_id)
    
    if number in ROULETTE_RED:
        num_emoji = f"🔴{number}"
    elif number in ROULETTE_BLACK:
        num_emoji = f"⚫{number}"
    else:
        num_emoji = f"🟢{number}"
    
    result_text = f"🎉 +{actual_win} {CURRENCY_SYMBOL}!" if win > 0 else "😔 Не повезло"
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Ещё раз", callback_data=f"rl_type_{bet_type}_{bet_value}"),
        InlineKeyboardButton(text="🎡 Меню", callback_data="casino_roulette")
    )
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    
    await callback.message.edit_text(
        f"🎡 <b>Рулетка</b>\n\n"
        f"Выпало: <b>{num_emoji}</b>\n"
        f"Ставка: {bet_type}/{bet_value}\n\n"
        f"{result_text}\n"
        f"💼 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

# ============================================================
# КАЗИНО: БЛЭКДЖЕК
# ============================================================

CARD_VALUES = {
    'A': 11, '2': 2, '3': 3, '4': 4, '5': 5,
    '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10
}

CARD_SUITS = ['♠️', '♥️', '♦️', '♣️']
CARD_RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']


def create_deck() -> List[str]:
    """Создать колоду."""
    deck = [f"{rank}{suit}" for suit in CARD_SUITS for rank in CARD_RANKS]
    random.shuffle(deck)
    return deck


def card_value(card: str) -> int:
    """Значение карты."""
    rank = card[:-2] if card[-2] in ['♠', '♥', '♦', '♣'] else card[0]
    # Убираем эмодзи суиты
    for suit in CARD_SUITS:
        rank = card.replace(suit, "")
    return CARD_VALUES.get(rank.strip(), 10)


def hand_value(hand: List[str]) -> int:
    """Считаем сумму руки."""
    total = 0
    aces = 0
    
    for card in hand:
        # Извлекаем ранг
        for suit in CARD_SUITS:
            card = card.replace(suit, "")
        card = card.strip()
        
        if card == 'A':
            aces += 1
            total += 11
        else:
            total += CARD_VALUES.get(card, 10)
    
    while total > 21 and aces:
        total -= 10
        aces -= 1
    
    return total


def format_hand(hand: List[str]) -> str:
    """Форматировать руку."""
    return " ".join(hand)


@router.callback_query(F.data == "casino_blackjack")
@router.message(Command("blackjack"))
async def casino_blackjack(event, state: FSMContext, **kwargs):
    """Блэкджек - выбор ставки."""
    if isinstance(event, CallbackQuery):
        user = event.from_user
        send = event.message.answer
        edit = event.message.edit_text
        answer = event.answer
    else:
        user = event.from_user
        send = event.answer
        edit = None
        answer = None
    
    ensure_user(user.id, user.username)
    balance = get_balance(user.id)
    
    text = (
        f"🃏 <b>Блэкджек</b>\n\n"
        f"💼 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>\n\n"
        f"Цель: набрать 21 или ближе к 21, чем дилер.\n"
        f"Блэкджек = А + 10-карта = ×2.5\n\n"
        f"Выбери ставку:"
    )
    
    try:
        if edit:
            await edit(text, reply_markup=bet_keyboard("bj"), parse_mode=ParseMode.HTML)
        else:
            await send(text, reply_markup=bet_keyboard("bj"), parse_mode=ParseMode.HTML)
    except Exception:
        await send(text, reply_markup=bet_keyboard("bj"), parse_mode=ParseMode.HTML)
    
    if answer:
        await answer()


@router.callback_query(F.data.startswith("bet_bj_"))
async def blackjack_start(callback: CallbackQuery, state: FSMContext):
    """Начать партию блэкджека."""
    bet = int(callback.data.replace("bet_bj_", ""))
    user_id = callback.from_user.id
    
    balance = get_balance(user_id)
    if balance < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    ok, _ = debit_user(user_id, bet, "blackjack_bet", f"Блэкджек ставка: {bet}")
    if not ok:
        await callback.answer("❌ Ошибка!", show_alert=True)
        return
    
    deck = create_deck()
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    
    session_data = {
        "bet": bet,
        "player_hand": player_hand,
        "dealer_hand": dealer_hand,
        "deck": deck,
        "status": "playing"
    }
    
    await state.set_state(BlackjackStates.playing)
    await state.update_data(bj=session_data)
    
    player_val = hand_value(player_hand)
    
    # Проверка блэкджека
    if player_val == 21:
        win = int(bet * 2.5 * BLACKJACK_RTP)
        credit_user(user_id, win, "blackjack_win", "Блэкджек!")
        update_daily_limit(user_id, "won", win - bet)
        
        balance = get_balance(user_id)
        await state.clear()
        
        await callback.message.edit_text(
            f"🃏 <b>БЛЭКДЖЕК!</b> 🎉\n\n"
            f"Твоя рука: {format_hand(player_hand)} = <b>{player_val}</b>\n\n"
            f"💰 Выигрыш: <b>+{win} {CURRENCY_SYMBOL}</b>\n"
            f"💼 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔄 Снова", callback_data="casino_blackjack"),
                InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
            ]]),
            parse_mode=ParseMode.HTML
        )
        await callback.answer("🃏 БЛЭКДЖЕК!")
        return
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🃏 Взять", callback_data="bj_hit"),
        InlineKeyboardButton(text="✋ Стоп", callback_data="bj_stand")
    )
    if balance >= bet:
        builder.row(InlineKeyboardButton(text="⬆️ Удвоить", callback_data="bj_double"))
    
    dealer_card = dealer_hand[0]
    
    await callback.message.edit_text(
        f"🃏 <b>Блэкджек</b>\n\n"
        f"🤖 Дилер: {dealer_card} 🎴 = ?\n"
        f"👤 Ты: {format_hand(player_hand)} = <b>{player_val}</b>\n\n"
        f"💰 Ставка: <b>{bet} {CURRENCY_SYMBOL}</b>",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data == "bj_hit", BlackjackStates.playing)
async def blackjack_hit(callback: CallbackQuery, state: FSMContext):
    """Взять карту."""
    data = await state.get_data()
    bj = data["bj"]
    
    bj["player_hand"].append(bj["deck"].pop())
    player_val = hand_value(bj["player_hand"])
    
    if player_val > 21:
        # Перебор
        update_daily_limit(callback.from_user.id, "lost", bj["bet"])
        with get_db() as conn:
            conn.execute(
                "UPDATE player_stats SET casino_bets=casino_bets+1, "
                "casino_lost=casino_lost+? WHERE user_id=?",
                (bj["bet"], callback.from_user.id)
            )
            conn.commit()
        
        await state.clear()
        balance = get_balance(callback.from_user.id)
        
        await callback.message.edit_text(
            f"🃏 <b>Перебор!</b>\n\n"
            f"Твоя рука: {format_hand(bj['player_hand'])} = <b>{player_val}</b>\n\n"
            f"💸 Потеряно: <b>-{bj['bet']} {CURRENCY_SYMBOL}</b>\n"
            f"💼 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔄 Снова", callback_data="casino_blackjack"),
                InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
            ]]),
            parse_mode=ParseMode.HTML
        )
        await callback.answer("💥 Перебор!")
        return
    
    await state.update_data(bj=bj)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🃏 Взять", callback_data="bj_hit"),
        InlineKeyboardButton(text="✋ Стоп", callback_data="bj_stand")
    )
    
    await callback.message.edit_text(
        f"🃏 <b>Блэкджек</b>\n\n"
        f"🤖 Дилер: {bj['dealer_hand'][0]} 🎴 = ?\n"
        f"👤 Ты: {format_hand(bj['player_hand'])} = <b>{player_val}</b>\n\n"
        f"💰 Ставка: <b>{bj['bet']} {CURRENCY_SYMBOL}</b>",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer(f"Карта! Сумма: {player_val}")


@router.callback_query(F.data == "bj_stand", BlackjackStates.playing)
async def blackjack_stand(callback: CallbackQuery, state: FSMContext):
    """Стоп — играем за дилера."""
    data = await state.get_data()
    bj = data["bj"]
    
    player_val = hand_value(bj["player_hand"])
    
    # Дилер добирает до 17
    while hand_value(bj["dealer_hand"]) < 17:
        bj["dealer_hand"].append(bj["deck"].pop())
    
    dealer_val = hand_value(bj["dealer_hand"])
    bet = bj["bet"]
    
    # Определяем победителя
    if dealer_val > 21 or player_val > dealer_val:
        win = int(bet * 2 * BLACKJACK_RTP)
        credit_user(callback.from_user.id, win, "blackjack_win", 
                   f"Блэкджек победа: {player_val} vs {dealer_val}")
        update_daily_limit(callback.from_user.id, "won", win - bet)
        result_text = f"🏆 <b>Победа!</b>\n💰 Выигрыш: <b>+{win} {CURRENCY_SYMBOL}</b>"
    elif player_val == dealer_val:
        credit_user(callback.from_user.id, bet, "blackjack_push", "Блэкджек ничья")
        result_text = f"🤝 <b>Ничья!</b>\n💰 Ставка возвращена: <b>{bet} {CURRENCY_SYMBOL}</b>"
    else:
        update_daily_limit(callback.from_user.id, "lost", bet)
        result_text = f"😔 <b>Проигрыш!</b>\n💸 Потеряно: <b>-{bet} {CURRENCY_SYMBOL}</b>"
    
    with get_db() as conn:
        conn.execute(
            "UPDATE player_stats SET casino_bets=casino_bets+1 WHERE user_id=?",
            (callback.from_user.id,)
        )
        conn.commit()
    
    await state.clear()
    balance = get_balance(callback.from_user.id)
    
    await callback.message.edit_text(
        f"🃏 <b>Блэкджек — Итог</b>\n\n"
        f"🤖 Дилер: {format_hand(bj['dealer_hand'])} = <b>{dealer_val}</b>\n"
        f"👤 Ты: {format_hand(bj['player_hand'])} = <b>{player_val}</b>\n\n"
        f"{result_text}\n"
        f"💼 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔄 Снова", callback_data="casino_blackjack"),
            InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
        ]]),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data == "bj_double", BlackjackStates.playing)
async def blackjack_double(callback: CallbackQuery, state: FSMContext):
    """Удвоить ставку."""
    data = await state.get_data()
    bj = data["bj"]
    bet = bj["bet"]
    
    ok, _ = debit_user(callback.from_user.id, bet, "blackjack_double", "Удвоение")
    if not ok:
        await callback.answer("❌ Недостаточно средств для удвоения!", show_alert=True)
        return
    
    bj["bet"] = bet * 2
    bj["player_hand"].append(bj["deck"].pop())
    
    await state.update_data(bj=bj)
    
    # Принудительный стоп после удвоения
    await blackjack_stand(callback, state)

# ============================================================
# КАЗИНО: КРАШ
# ============================================================

def generate_crash_point(seed: str, house_edge: float = 0.05) -> float:
    """Генерация точки краша через HMAC-SHA256."""
    h = hmac.new(seed.encode(), b"crash", hashlib.sha256).hexdigest()
    
    # Конвертируем в число 0-1
    val = int(h[:8], 16) / 0xFFFFFFFF
    
    # Формула краша
    if val < house_edge:
        return 1.0
    
    crash = (1 - house_edge) / (1 - val)
    return max(1.0, round(crash, 2))


@router.callback_query(F.data == "casino_crash")
@router.message(Command("crash"))
async def casino_crash(event, state: FSMContext, **kwargs):
    """Краш - выбор ставки."""
    if isinstance(event, CallbackQuery):
        user = event.from_user
        send = event.message.answer
        edit = event.message.edit_text
        answer = event.answer
    else:
        user = event.from_user
        send = event.answer
        edit = None
        answer = None
    
    ensure_user(user.id, user.username)
    balance = get_balance(user.id)
    
    text = (
        f"🚀 <b>Краш</b>\n\n"
        f"💼 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>\n\n"
        f"Ракета взлетает и множитель растёт.\n"
        f"Заберите выигрыш до краша!\n"
        f"Выбери ставку и порог авто-вывода:"
    )
    
    try:
        if edit:
            await edit(text, reply_markup=bet_keyboard("crash"), parse_mode=ParseMode.HTML)
        else:
            await send(text, reply_markup=bet_keyboard("crash"), parse_mode=ParseMode.HTML)
    except Exception:
        await send(text, reply_markup=bet_keyboard("crash"), parse_mode=ParseMode.HTML)
    
    if answer:
        await answer()


@router.callback_query(F.data.startswith("bet_crash_"))
async def crash_bet(callback: CallbackQuery, state: FSMContext):
    """Ставка в краше — выбор порога."""
    bet = int(callback.data.replace("bet_crash_", ""))
    await state.update_data(crash_bet=bet)
    
    builder = InlineKeyboardBuilder()
    thresholds = [1.5, 2.0, 3.0, 5.0, 10.0]
    for t in thresholds:
        builder.row(InlineKeyboardButton(
            text=f"×{t} авто-вывод",
            callback_data=f"crash_play_{bet}_{int(t*10)}"
        ))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="casino_crash"))
    
    await callback.message.edit_text(
        f"🚀 <b>Краш</b>\nСтавка: <b>{bet} {CURRENCY_SYMBOL}</b>\n\nВыбери порог авто-вывода:",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data.startswith("crash_play_"))
async def crash_play(callback: CallbackQuery, state: FSMContext):
    """Запуск краша."""
    parts = callback.data.replace("crash_play_", "").split("_")
    bet = int(parts[0])
    threshold = int(parts[1]) / 10
    user_id = callback.from_user.id
    
    balance = get_balance(user_id)
    if balance < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    ok, _ = debit_user(user_id, bet, "crash_bet", f"Краш: {bet}")
    if not ok:
        await callback.answer("❌ Ошибка!", show_alert=True)
        return
    
    seed = secrets.token_hex(16)
    crash_point = generate_crash_point(seed)
    
    # Симуляция полёта
    await callback.message.edit_text(
        f"🚀 <b>Краш — Взлёт!</b>\n\n"
        f"💰 Ставка: <b>{bet} {CURRENCY_SYMBOL}</b>\n"
        f"🎯 Авто-вывод: ×{threshold}\n\n"
        f"⏳ Ракета взлетает...",
        parse_mode=ParseMode.HTML
    )
    
    # Анимация
    current = 1.0
    step = 0.1
    crashed = False
    cashed_out = False
    cash_mult = 0
    
    animation_steps = []
    while current <= crash_point and current < 20.0:
        animation_steps.append(round(current, 2))
        if current >= threshold:
            cashed_out = True
            cash_mult = current
            break
        current = round(current + step, 2)
        if current > 2.0:
            step = 0.2
        if current > 5.0:
            step = 0.5
    
    if not cashed_out:
        crashed = True
    
    # Показываем несколько ключевых кадров
    display_points = animation_steps[::max(1, len(animation_steps)//5)]
    
    for mult in display_points[:3]:
        try:
            await callback.message.edit_text(
                f"🚀 <b>Краш — Взлёт!</b>\n\n"
                f"📈 Множитель: <b>×{mult:.2f}</b>\n"
                f"💰 Ставка: <b>{bet} {CURRENCY_SYMBOL}</b>\n"
                f"🎯 Авто-вывод: ×{threshold}",
                parse_mode=ParseMode.HTML
            )
            await asyncio.sleep(0.5)
        except Exception:
            pass
    
    if cashed_out:
        win = int(bet * cash_mult * CRASH_RTP)
        can_win, remaining = check_daily_limit(user_id, "won", DAILY_WIN_LIMIT)
        if can_win:
            actual_win = min(win, bet + remaining)
            credit_user(user_id, actual_win, "crash_win", f"Краш ×{cash_mult:.2f}")
            update_daily_limit(user_id, "won", actual_win - bet)
        else:
            actual_win = bet
            credit_user(user_id, actual_win, "crash_return", "Краш - возврат")
        
        result_text = (
            f"✅ <b>Авто-вывод при ×{cash_mult:.2f}!</b>\n"
            f"💰 Получено: <b>+{actual_win} {CURRENCY_SYMBOL}</b>\n"
            f"💥 Краш был при ×{crash_point:.2f}"
        )
    else:
        update_daily_limit(user_id, "lost", bet)
        actual_win = 0
        result_text = f"💥 <b>КРАШ при ×{crash_point:.2f}!</b>\n💸 Потеряно: <b>-{bet} {CURRENCY_SYMBOL}</b>"
    
    with get_db() as conn:
        conn.execute(
            """INSERT INTO casino_bets (id, user_id, game_type, bet, result, win_amount, seed, details)
               VALUES (?,?,?,?,?,?,?,?)""",
            (str(uuid.uuid4()), user_id, "crash", bet,
             f"crash_{crash_point}", actual_win, seed,
             json.dumps({"threshold": threshold, "cashed_out": cashed_out, "crash_point": crash_point}))
        )
        conn.execute(
            "UPDATE player_stats SET casino_bets=casino_bets+1 WHERE user_id=?", (user_id,)
        )
        conn.commit()
    
    balance = get_balance(user_id)
    
    await callback.message.edit_text(
        f"🚀 <b>Краш — Результат</b>\n\n"
        f"{result_text}\n"
        f"💼 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>\n\n"
        f"🔑 Seed: <code>{seed[:16]}</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔄 Снова", callback_data="casino_crash"),
            InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
        ]]),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

# ============================================================
# КАЗИНО: ДАЙС
# ============================================================

@router.callback_query(F.data == "casino_dice")
@router.message(Command("dice"))
async def casino_dice(event, state: FSMContext, **kwargs):
    """Дайс — выбор ставки."""
    if isinstance(event, CallbackQuery):
        user = event.from_user
        send = event.message.answer
        edit = event.message.edit_text
        answer = event.answer
    else:
        user = event.from_user
        send = event.answer
        edit = None
        answer = None
    
    ensure_user(user.id, user.username)
    balance = get_balance(user.id)
    
    text = (
        f"🎲 <b>Дайс</b>\n\n"
        f"💼 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>\n\n"
        f"Угадай число от 1 до 6!\n"
        f"Выигрыш при угадывании: ×5\n\n"
        f"Выбери ставку:"
    )
    
    try:
        if edit:
            await edit(text, reply_markup=bet_keyboard("dice"), parse_mode=ParseMode.HTML)
        else:
            await send(text, reply_markup=bet_keyboard("dice"), parse_mode=ParseMode.HTML)
    except Exception:
        await send(text, reply_markup=bet_keyboard("dice"), parse_mode=ParseMode.HTML)
    
    if answer:
        await answer()


@router.callback_query(F.data.startswith("bet_dice_"))
async def dice_choose_number(callback: CallbackQuery, state: FSMContext):
    """Выбор числа дайса."""
    bet = int(callback.data.replace("bet_dice_", ""))
    await state.update_data(dice_bet=bet)
    
    builder = InlineKeyboardBuilder()
    dice_faces = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    for i, face in enumerate(dice_faces):
        builder.row(InlineKeyboardButton(
            text=f"{face} {i+1}",
            callback_data=f"dice_roll_{bet}_{i+1}"
        ))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="casino_dice"))
    
    await callback.message.edit_text(
        f"🎲 <b>Дайс</b>\nСтавка: <b>{bet} {CURRENCY_SYMBOL}</b>\n\nВыбери число:",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dice_roll_"))
async def dice_roll(callback: CallbackQuery, state: FSMContext):
    """Бросок дайса."""
    parts = callback.data.replace("dice_roll_", "").split("_")
    bet = int(parts[0])
    chosen = int(parts[1])
    user_id = callback.from_user.id
    
    balance = get_balance(user_id)
    if balance < bet:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    ok, _ = debit_user(user_id, bet, "dice_bet", f"Дайс: {bet}")
    if not ok:
        await callback.answer("❌ Ошибка!", show_alert=True)
        return
    
    seed = secrets.token_hex(8)
    random.seed(seed)
    result = random.randint(1, 6)
    
    dice_faces = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    
    if result == chosen:
        win = int(bet * 5 * DICE_RTP)
        can_win, remaining = check_daily_limit(user_id, "won", DAILY_WIN_LIMIT)
        if can_win:
            credit_user(user_id, win, "dice_win", f"Дайс: выпало {result}")
            update_daily_limit(user_id, "won", win - bet)
        else:
            win = bet
            credit_user(user_id, win, "dice_return", "Дайс - возврат")
        result_text = f"🎉 <b>Попал!</b>\n💰 Выигрыш: <b>+{win} {CURRENCY_SYMBOL}</b>"
    else:
        update_daily_limit(user_id, "lost", bet)
        win = 0
        result_text = f"😔 <b>Не угадал</b>\n💸 Потеряно: <b>-{bet} {CURRENCY_SYMBOL}</b>"
    
    with get_db() as conn:
        conn.execute(
            """INSERT INTO casino_bets (id, user_id, game_type, bet, result, win_amount, seed)
               VALUES (?,?,?,?,?,?,?)""",
            (str(uuid.uuid4()), user_id, "dice", bet, str(result), win, seed)
        )
        conn.execute(
            "UPDATE player_stats SET casino_bets=casino_bets+1 WHERE user_id=?", (user_id,)
        )
        conn.commit()
    
    balance = get_balance(user_id)
    
    await callback.message.edit_text(
        f"🎲 <b>Дайс</b>\n\n"
        f"Выбрал: <b>{dice_faces[chosen-1]} {chosen}</b>\n"
        f"Выпало: <b>{dice_faces[result-1]} {result}</b>\n\n"
        f"{result_text}\n"
        f"💼 Баланс: <b>{balance} {CURRENCY_SYMBOL}</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔄 Снова", callback_data="casino_dice"),
            InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
        ]]),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

# ============================================================
# КАРТОЧНЫЕ ДУЭЛИ — УПРОЩЁННЫЙ БЛЭКДЖЕК-ДУЭЛЬ
# ============================================================

class CardGameStage(Enum):
    WAITING = "waiting"
    PLAYER1_TURN = "player1_turn"
    PLAYER2_TURN = "player2_turn"
    FINISHED = "finished"


def cards_game_keyboard(session_id: str, player_pos: int, 
                        can_take: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для карточной игры."""
    builder = InlineKeyboardBuilder()
    if can_take:
        builder.row(
            InlineKeyboardButton(text="🃏 Взять карту", callback_data=f"card_hit_{session_id}_{player_pos}"),
            InlineKeyboardButton(text="✋ Стоп", callback_data=f"card_stand_{session_id}_{player_pos}")
        )
    builder.row(
        InlineKeyboardButton(text="📊 Статус", callback_data=f"card_status_{session_id}_{player_pos}")
    )
    return builder.as_markup()


def format_card_state(session: Dict, player: Dict, is_opponent: bool = False) -> str:
    """Форматировать состояние карточной игры."""
    hand = json.loads(player["hole_cards"])
    val = hand_value(hand)
    
    if is_opponent:
        cards_str = f"🎴 × {len(hand)}"  # Скрываем карты соперника
    else:
        cards_str = format_hand(hand)
    
    return cards_str, val if not is_opponent else "?"


async def send_card_state(bot: Bot, session_id: str, notify_user_id: int = None):
    """Отправить/обновить состояние карточной игры игрокам."""
    with get_db() as conn:
        session = conn.execute(
            "SELECT * FROM card_sessions WHERE id=?", (session_id,)
        ).fetchone()
        if not session:
            return
        
        players = conn.execute(
            "SELECT * FROM card_players WHERE session_id=? ORDER BY position",
            (session_id,)
        ).fetchall()
        
        if len(players) < 2:
            return
        
        p1 = dict(players[0])
        p2 = dict(players[1])
        
        stage = session["stage"]
        pot = session["pot"]
        
        for i, player in enumerate([p1, p2]):
            opponent = p2 if i == 0 else p1
            
            if notify_user_id and player["user_id"] != notify_user_id:
                continue
            
            if not player["message_id"]:
                continue
            
            hand = json.loads(player["hole_cards"])
            opp_hand = json.loads(opponent["hole_cards"])
            
            val = hand_value(hand) if hand else 0
            opp_count = len(opp_hand)
            
            is_my_turn = (
                (stage == "player1_turn" and player["position"] == 0) or
                (stage == "player2_turn" and player["position"] == 1)
            )
            
            stage_text = {
                "player1_turn": "Ход игрока 1",
                "player2_turn": "Ход игрока 2",
                "finished": "🏁 Игра завершена",
                "waiting": "⏳ Ожидание"
            }.get(stage, stage)
            
            my_turn_text = "⚡ <b>Твой ход!</b>" if is_my_turn else "⏳ Ход соперника..."
            
            text = (
                f"🃏 <b>Карточная дуэль</b>\n"
                f"🎰 Банк: <b>{pot} {CURRENCY_SYMBOL}</b>\n"
                f"📍 {stage_text}\n\n"
                f"{my_turn_text}\n\n"
                f"👤 Твои карты: {format_hand(hand)} = <b>{val}</b>\n"
                f"🎴 Соперник: {opp_count} карт\n\n"
                f"{'✅ Ты остановился' if player['status'] == 'standing' else ''}"
            )
            
            keyboard = None
            if is_my_turn and player["status"] == "playing" and stage != "finished":
                keyboard = cards_game_keyboard(session_id, player["position"])
            
            try:
                await bot.edit_message_text(
                    text,
                    chat_id=player["user_id"],
                    message_id=player["message_id"],
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                logger.error(f"Ошибка обновления карточной игры: {e}")


@router.message(Command("playcards"))
async def playcards_command(message: Message, state: FSMContext, bot: Bot):
    """Поиск соперника для карточной дуэли."""
    user_id = message.from_user.id
    ensure_user(user_id, message.from_user.username, message.from_user.first_name)
    
    args = message.text.split()
    bet = MIN_BET
    if len(args) > 1:
        try:
            bet = int(args[1])
        except ValueError:
            pass
    
    bet = max(MIN_BET, min(bet, MAX_BET))
    
    balance = get_balance(user_id)
    if balance < bet:
        await message.answer(
            f"❌ Недостаточно средств!\n"
            f"Нужно: <b>{bet} {CURRENCY_SYMBOL}</b>\n"
            f"У тебя: <b>{balance} {CURRENCY_SYMBOL}</b>",
            parse_mode=ParseMode.HTML
        )
        return
    
    with get_db() as conn:
        # Проверяем очередь
        queue_player = conn.execute(
            "SELECT * FROM card_queue WHERE user_id != ? ORDER BY joined_at LIMIT 1",
            (user_id,)
        ).fetchone()
        
        if queue_player:
            # Нашли соперника
            opponent_id = queue_player["user_id"]
            opp_bet = queue_player["bet"]
            
            # Убираем соперника из очереди
            conn.execute("DELETE FROM card_queue WHERE user_id=?", (opponent_id,))
            
            # Согласуем ставку (минимум из двух)
            actual_bet = min(bet, opp_bet)
            
            # Создаём сессию
            session_id = str(uuid.uuid4())[:12]
            deck = create_deck()
            
            # Раздаём карты
            p1_hand = [deck.pop(), deck.pop()]
            p2_hand = [deck.pop(), deck.pop()]
            
            expires = (datetime.now() + timedelta(minutes=30)).isoformat()
            
            conn.execute(
                """INSERT INTO card_sessions 
                   (id, state, pot, current_bet, deck, stage, expires_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (session_id, "active", actual_bet * 2, actual_bet,
                 json.dumps(deck), "player1_turn", expires)
            )
            
            conn.execute(
                """INSERT INTO card_players 
                   (session_id, user_id, hole_cards, chips, bet_amount, status, position)
                   VALUES (?,?,?,?,?,?,?)""",
                (session_id, user_id, json.dumps(p1_hand), 
                 balance - actual_bet, actual_bet, "playing", 0)
            )
            conn.execute(
                """INSERT INTO card_players 
                   (session_id, user_id, hole_cards, chips, bet_amount, status, position)
                   VALUES (?,?,?,?,?,?,?)""",
                (session_id, opponent_id, json.dumps(p2_hand),
                 get_balance(opponent_id) - actual_bet, actual_bet, "playing", 1)
            )
            conn.commit()
            
            # Списываем ставки
            debit_user(user_id, actual_bet, "card_bet", f"Карточная дуэль: {session_id}")
            debit_user(opponent_id, actual_bet, "card_bet", f"Карточная дуэль: {session_id}")
            
            # Отправляем ЛС обоим игрокам
            p1_val = hand_value(p1_hand)
            
            p1_text = (
                f"🃏 <b>Карточная дуэль начата!</b>\n\n"
                f"🎰 Банк: <b>{actual_bet * 2} {CURRENCY_SYMBOL}</b>\n"
                f"💰 Ставка: <b>{actual_bet} {CURRENCY_SYMBOL}</b>\n\n"
                f"👤 Твои карты: {format_hand(p1_hand)} = <b>{p1_val}</b>\n"
                f"🎴 Соперник: 2 карты\n\n"
                f"⚡ <b>Твой ход!</b>\n"
                f"Цель: набрать 21 или больше соперника, не превышая 21."
            )
            
            try:
                msg1 = await bot.send_message(
                    user_id, p1_text,
                    reply_markup=cards_game_keyboard(session_id, 0),
                    parse_mode=ParseMode.HTML
                )
                
                with get_db() as conn2:
                    conn2.execute(
                        "UPDATE card_players SET message_id=? WHERE session_id=? AND user_id=?",
                        (msg1.message_id, session_id, user_id)
                    )
                    conn2.commit()
            except Exception as e:
                logger.error(f"Не могу отправить ЛС игроку {user_id}: {e}")
            
            p2_val = hand_value(p2_hand)
            p2_text = (
                f"🃏 <b>Карточная дуэль начата!</b>\n\n"
                f"🎰 Банк: <b>{actual_bet * 2} {CURRENCY_SYMBOL}</b>\n"
                f"💰 Ставка: <b>{actual_bet} {CURRENCY_SYMBOL}</b>\n\n"
                f"👤 Твои карты: {format_hand(p2_hand)} = <b>{p2_val}</b>\n"
                f"🎴 Соперник: 2 карты\n\n"
                f"⏳ Ход соперника (Игрок 1)..."
            )
            
            try:
                msg2 = await bot.send_message(
                    opponent_id, p2_text,
                    parse_mode=ParseMode.HTML
                )
                
                with get_db() as conn2:
                    conn2.execute(
                        "UPDATE card_players SET message_id=? WHERE session_id=? AND user_id=?",
                        (msg2.message_id, session_id, opponent_id)
                    )
                    conn2.commit()
            except Exception as e:
                logger.error(f"Не могу отправить ЛС игроку {opponent_id}: {e}")
            
            await message.answer(
                f"✅ Соперник найден! Проверь личные сообщения для игры.\n"
                f"Сессия: <code>{session_id}</code>",
                parse_mode=ParseMode.HTML
            )
        
        else:
            # Добавляем в очередь
            conn.execute(
                "INSERT OR REPLACE INTO card_queue (user_id, bet) VALUES (?,?)",
                (user_id, bet)
            )
            conn.commit()
            
            await message.answer(
                f"⏳ <b>Ищем соперника...</b>\n\n"
                f"Ставка: <b>{bet} {CURRENCY_SYMBOL}</b>\n\n"
                f"Когда найдём соперника, ты получишь сообщение в личку.\n"
                f"Используй /cancel_queue для отмены поиска.",
                parse_mode=ParseMode.HTML
            )


@router.message(Command("cancel_queue"))
async def cancel_queue(message: Message):
    """Отмена поиска игры."""
    with get_db() as conn:
        conn.execute("DELETE FROM card_queue WHERE user_id=?", (message.from_user.id,))
        conn.commit()
    
    await message.answer("✅ Поиск игры отменён.")


@router.callback_query(F.data.startswith("card_hit_"))
async def card_hit(callback: CallbackQuery, bot: Bot):
    """Взять карту в дуэли."""
    parts = callback.data.replace("card_hit_", "").split("_")
    if len(parts) != 2:
        await callback.answer()
        return
    
    session_id = parts[0]
    player_pos = int(parts[1])
    user_id = callback.from_user.id
    
    with get_db() as conn:
        session = conn.execute(
            "SELECT * FROM card_sessions WHERE id=? AND state='active'",
            (session_id,)
        ).fetchone()
        
        if not session:
            await callback.answer("Игра не найдена или завершена!", show_alert=True)
            return
        
        # Проверяем право хода
        expected_stage = f"player{player_pos + 1}_turn"
        if session["stage"] != expected_stage:
            await callback.answer("Сейчас не твой ход!", show_alert=True)
            return
        
        player = conn.execute(
            "SELECT * FROM card_players WHERE session_id=? AND user_id=?",
            (session_id, user_id)
        ).fetchone()
        
        if not player or player["status"] != "playing":
            await callback.answer("Ты уже остановился!", show_alert=True)
            return
        
        deck = json.loads(session["deck"])
        if not deck:
            await callback.answer("Колода пуста!", show_alert=True)
            return
        
        hand = json.loads(player["hole_cards"])
        new_card = deck.pop()
        hand.append(new_card)
        
        val = hand_value(hand)
        
        conn.execute(
            "UPDATE card_players SET hole_cards=? WHERE session_id=? AND user_id=?",
            (json.dumps(hand), session_id, user_id)
        )
        conn.execute(
            "UPDATE card_sessions SET deck=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(deck), session_id)
        )
        conn.commit()
        
        if val > 21:
            # Перебор — проигрыш
            conn.execute(
                "UPDATE card_players SET status='busted' WHERE session_id=? AND user_id=?",
                (session_id, user_id)
            )
            conn.execute(
                "UPDATE card_sessions SET stage='finished', state='finished' WHERE id=?",
                (session_id,)
            )
            conn.commit()
            
            # Получаем соперника
            opponent = conn.execute(
                "SELECT * FROM card_players WHERE session_id=? AND user_id!=?",
                (session_id, user_id)
            ).fetchone()
            
            await _finish_card_game(bot, session_id, conn, loser_id=user_id)
            
            await callback.answer(f"💥 Перебор! {val}")
            return
    
    await send_card_state(bot, session_id)
    await callback.answer(f"🃏 +{new_card} = {val}")


@router.callback_query(F.data.startswith("card_stand_"))
async def card_stand(callback: CallbackQuery, bot: Bot):
    """Остановиться в дуэли."""
    parts = callback.data.replace("card_stand_", "").split("_")
    session_id = parts[0]
    player_pos = int(parts[1])
    user_id = callback.from_user.id
    
    with get_db() as conn:
        session = conn.execute(
            "SELECT * FROM card_sessions WHERE id=? AND state='active'",
            (session_id,)
        ).fetchone()
        
        if not session:
            await callback.answer("Игра не найдена!", show_alert=True)
            return
        
        expected_stage = f"player{player_pos + 1}_turn"
        if session["stage"] != expected_stage:
            await callback.answer("Не твой ход!", show_alert=True)
            return
        
        conn.execute(
            "UPDATE card_players SET status='standing' WHERE session_id=? AND user_id=?",
            (session_id, user_id)
        )
        
        # Переключаем ход
        if player_pos == 0:
            next_stage = "player2_turn"
        else:
            # Оба остановились — финиш
            next_stage = "finished"
        
        conn.execute(
            "UPDATE card_sessions SET stage=? WHERE id=?",
            (next_stage, session_id)
        )
        conn.commit()
        
        if next_stage == "finished":
            conn.execute(
                "UPDATE card_sessions SET state='finished' WHERE id=?",
                (session_id,)
            )
            conn.commit()
            await _finish_card_game(bot, session_id, conn)
            await callback.answer("✋ Стоп!")
            return
    
    await send_card_state(bot, session_id)
    await callback.answer("✋ Ты остановился, ход соперника")


@router.callback_query(F.data.startswith("card_status_"))
async def card_status(callback: CallbackQuery, bot: Bot):
    """Показать текущий статус игры."""
    parts = callback.data.replace("card_status_", "").split("_")
    session_id = parts[0]
    player_pos = int(parts[1])
    
    await send_card_state(bot, session_id, notify_user_id=callback.from_user.id)
    await callback.answer("Статус обновлён")


async def _finish_card_game(bot: Bot, session_id: str, conn, loser_id: int = None):
    """Завершить карточную игру и выплатить выигрыш."""
    players = conn.execute(
        "SELECT * FROM card_players WHERE session_id=? ORDER BY position",
        (session_id,)
    ).fetchall()
    
    session = conn.execute(
        "SELECT * FROM card_sessions WHERE id=?", (session_id,)
    ).fetchone()
    
    if len(players) < 2:
        return
    
    p1 = dict(players[0])
    p2 = dict(players[1])
    pot = session["pot"]
    
    p1_hand = json.loads(p1["hole_cards"])
    p2_hand = json.loads(p2["hole_cards"])
    p1_val = hand_value(p1_hand)
    p2_val = hand_value(p2_hand)
    
    # Определяем победителя
    if loser_id == p1["user_id"] or (p1["status"] == "busted"):
        winner = p2
        loser = p1
        win_reason = "Соперник перебрал"
    elif loser_id == p2["user_id"] or (p2["status"] == "busted"):
        winner = p1
        loser = p2
        win_reason = "Соперник перебрал"
    elif p1_val > p2_val:
        winner = p1
        loser = p2
        win_reason = f"{p1_val} > {p2_val}"
    elif p2_val > p1_val:
        winner = p2
        loser = p1
        win_reason = f"{p2_val} > {p1_val}"
    else:
        # Ничья — возврат
        with get_db() as conn2:
            credit_user(p1["user_id"], session["current_bet"], "card_tie", "Ничья в дуэли")
            credit_user(p2["user_id"], session["current_bet"], "card_tie", "Ничья в дуэли")
        
        # Уведомляем обоих
        for p in [p1, p2]:
            if p["message_id"]:
                try:
                    await bot.edit_message_text(
                        f"🤝 <b>Ничья!</b>\n\n"
                        f"Ты: {format_hand(json.loads(p['hole_cards']))} = <b>{hand_value(json.loads(p['hole_cards']))}</b>\n"
                        f"Соперник: {format_hand(p2_hand if p['position']==0 else p1_hand)} = "
                        f"<b>{p2_val if p['position']==0 else p1_val}</b>\n\n"
                        f"💰 Ставка возвращена",
                        chat_id=p["user_id"],
                        message_id=p["message_id"],
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass
        return
    
    # Рассчитываем выигрыш с учётом рейка
    rake = int(pot * CARD_RAKE)
    win_amount = pot - rake
    
    credit_user(winner["user_id"], win_amount, "card_win",
               f"Победа в дуэли: {win_reason}")
    
    with get_db() as conn2:
        conn2.execute(
            "UPDATE player_stats SET cards_played=cards_played+1, cards_won=cards_won+1 WHERE user_id=?",
            (winner["user_id"],)
        )
        conn2.execute(
            "UPDATE player_stats SET cards_played=cards_played+1 WHERE user_id=?",
            (loser["user_id"],)
        )
        conn2.commit()
    
    winner_balance = get_balance(winner["user_id"])
    loser_balance = get_balance(loser["user_id"])
    
    # Финальные сообщения
    for p in [p1, p2]:
        if not p["message_id"]:
            continue
        
        is_winner = p["user_id"] == winner["user_id"]
        p_hand = json.loads(p["hole_cards"])
        opp_hand = p2_hand if p["position"] == 0 else p1_hand
        opp_val = p2_val if p["position"] == 0 else p1_val
        my_val = hand_value(p_hand)
        my_balance = winner_balance if is_winner else loser_balance
        
        if is_winner:
            result = f"🏆 <b>Победа!</b>\n💰 Выигрыш: <b>+{win_amount} {CURRENCY_SYMBOL}</b>"
        else:
            result = f"😔 <b>Поражение...</b>\n💸 Потеряно: <b>-{session['current_bet']} {CURRENCY_SYMBOL}</b>"
        
        try:
            await bot.edit_message_text(
                f"🃏 <b>Дуэль завершена!</b>\n\n"
                f"Твои карты: {format_hand(p_hand)} = <b>{my_val}</b>\n"
                f"Соперник: {format_hand(opp_hand)} = <b>{opp_val}</b>\n\n"
                f"{result}\n"
                f"🎰 Банк: {pot} | Рейк: {rake}\n"
                f"💼 Баланс: <b>{my_balance} {CURRENCY_SYMBOL}</b>",
                chat_id=p["user_id"],
                message_id=p["message_id"],
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text="🔄 Новая игра",
                        callback_data="start_playcards"
                    )
                ]]),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Ошибка отправки финала: {e}")


@router.callback_query(F.data == "start_playcards")
async def cb_start_playcards(callback: CallbackQuery):
    """Начать поиск новой карточной игры."""
    await callback.message.answer(
        f"🃏 <b>Карточные дуэли</b>\n\n"
        f"Используй: <code>/playcards [ставка]</code>\n"
        f"Например: <code>/playcards 100</code>\n\n"
        f"Минимальная ставка: {MIN_BET} {CURRENCY_SYMBOL}",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data == "menu_cards")
async def cb_menu_cards(callback: CallbackQuery):
    """Меню карточных дуэлей."""
    with get_db() as conn:
        queue_count = conn.execute("SELECT COUNT(*) as cnt FROM card_queue").fetchone()
    
    text = (
        f"🃏 <b>Карточные дуэли</b>\n\n"
        f"Игроков в очереди: <b>{queue_count['cnt']}</b>\n\n"
        f"Используй команду:\n"
        f"<code>/playcards [ставка]</code>\n\n"
        f"Карточная дуэль — упрощённый блэкджек.\n"
        f"Цель: набрать 21 или ближе к 21 без перебора.\n"
        f"Рейк: {int(CARD_RAKE*100)}% от банка.\n\n"
        f"Минимальная ставка: <b>{MIN_BET} {CURRENCY_SYMBOL}</b>"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⚔️ Найти игру", callback_data="start_playcards"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    
    try:
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    except Exception:
        await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await callback.answer()

# ============================================================
# КОМАНДЫ СТАТИСТИКИ
# ============================================================

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Статистика игрока."""
    user_id = message.from_user.id
    ensure_user(user_id, message.from_user.username)
    
    with get_db() as conn:
        stats = conn.execute(
            "SELECT * FROM player_stats WHERE user_id=?", (user_id,)
        ).fetchone()
        
        balance_row = conn.execute(
            "SELECT amount, total_earned, total_spent FROM balances WHERE user_id=?",
            (user_id,)
        ).fetchone()
    
    if not stats or not balance_row:
        await message.answer("Статистика не найдена. Используй /start")
        return
    
    wr = 0
    if stats["games_played"] > 0:
        wr = round(stats["games_won"] / stats["games_played"] * 100, 1)
    
    quiz_acc = 0
    if stats["quizzes_answered"] > 0:
        quiz_acc = round(stats["quizzes_correct"] / stats["quizzes_answered"] * 100, 1)
    
    text = (
        f"📊 <b>Твоя статистика</b>\n\n"
        f"💰 Баланс: <b>{balance_row['amount']} {CURRENCY_SYMBOL}</b>\n"
        f"📈 Всего заработано: <b>{balance_row['total_earned']} {CURRENCY_SYMBOL}</b>\n"
        f"📉 Всего потрачено: <b>{balance_row['total_spent']} {CURRENCY_SYMBOL}</b>\n\n"
        f"🎮 <b>Мини-игры:</b>\n"
        f"Сыграно: {stats['games_played']} | Побед: {stats['games_won']} ({wr}%)\n\n"
        f"🎰 <b>Казино:</b>\n"
        f"Ставок: {stats['casino_bets']}\n"
        f"Выиграно: {stats['casino_won']} {CURRENCY_SYMBOL}\n"
        f"Проиграно: {stats['casino_lost']} {CURRENCY_SYMBOL}\n\n"
        f"🃏 <b>Карточные дуэли:</b>\n"
        f"Игр: {stats['cards_played']} | Побед: {stats['cards_won']}\n\n"
        f"📝 <b>Викторина:</b>\n"
        f"Ответов: {stats['quizzes_answered']} | "
        f"Правильных: {stats['quizzes_correct']} ({quiz_acc}%)"
    )
    
    await message.answer(text, parse_mode=ParseMode.HTML)

# ============================================================
# РЕФЕРАЛЬНАЯ КОМАНДА
# ============================================================

@router.message(Command("referral"))
async def cmd_referral(message: Message, bot: Bot):
    """Реферальная ссылка."""
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{message.from_user.id}"
    
    with get_db() as conn:
        ref_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM users WHERE referral_by=?",
            (message.from_user.id,)
        ).fetchone()
    
    await message.answer(
        f"🔗 <b>Реферальная программа</b>\n\n"
        f"Рефералов: <b>{ref_count['cnt']}</b>\n"
        f"Бонус за реферала: <b>{REFERRAL_BONUS} {CURRENCY_SYMBOL}</b>\n\n"
        f"Твоя ссылка:\n<code>{ref_link}</code>",
        parse_mode=ParseMode.HTML
    )

# ============================================================
# АДМИН-ПАНЕЛЬ
# ============================================================

def admin_only(func):
    """Декоратор для проверки прав администратора."""
    async def wrapper(message: Message, *args, **kwargs):
        if message.from_user.id not in ADMIN_IDS:
            await message.answer("❌ Нет доступа.")
            return
        return await func(message, *args, **kwargs)
    return wrapper


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Панель администратора."""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
        InlineKeyboardButton(text="💰 Финансы", callback_data="admin_finance")
    )
    builder.row(
        InlineKeyboardButton(text="🎮 Активные игры", callback_data="admin_games"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
    )
    builder.row(InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast"))
    
    with get_db() as conn:
        users_count = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
        bets_count = conn.execute("SELECT COUNT(*) as cnt FROM casino_bets WHERE date(created_at)=date('now')").fetchone()
        active_cards = conn.execute("SELECT COUNT(*) as cnt FROM card_sessions WHERE state='active'").fetchone()
    
    await message.answer(
        f"⚙️ <b>Панель администратора</b>\n\n"
        f"👥 Пользователей: <b>{users_count['cnt']}</b>\n"
        f"🎰 Ставок сегодня: <b>{bets_count['cnt']}</b>\n"
        f"🃏 Активных игр: <b>{active_cards['cnt']}</b>",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )


@router.message(Command("give_coins"))
async def admin_give_coins(message: Message):
    """Выдать монеты игроку. /give_coins user_id amount"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    args = message.text.split()
    if len(args) != 3:
        await message.answer("Использование: /give_coins [user_id] [amount]")
        return
    
    try:
        target_id = int(args[1])
        amount = int(args[2])
    except ValueError:
        await message.answer("❌ Неверный формат")
        return
    
    ok, new_balance = credit_user(target_id, amount, "admin_grant", 
                                   f"Выдано администратором")
    if ok:
        await message.answer(
            f"✅ Выдано <b>{amount} {CURRENCY_SYMBOL}</b> пользователю {target_id}\n"
            f"Новый баланс: <b>{new_balance} {CURRENCY_SYMBOL}</b>",
            parse_mode=ParseMode.HTML
        )
        try:
            await message.bot.send_message(
                target_id,
                f"🎁 Администратор выдал вам <b>{amount} {CURRENCY_SYMBOL}</b>!\n"
                f"Баланс: <b>{new_balance} {CURRENCY_SYMBOL}</b>",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass
    else:
        await message.answer("❌ Ошибка выдачи монет")


@router.message(Command("ban"))
async def admin_ban(message: Message):
    """Забанить пользователя."""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /ban [user_id]")
        return
    
    try:
        target_id = int(args[1])
    except ValueError:
        await message.answer("❌ Неверный ID")
        return
    
    with get_db() as conn:
        conn.execute("UPDATE users SET is_banned=1 WHERE id=?", (target_id,))
        conn.commit()
    
    await message.answer(f"🔨 Пользователь {target_id} заблокирован")


@router.message(Command("cancel_game"))
async def admin_cancel_game(message: Message):
    """Отменить карточную игру."""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /cancel_game [session_id]")
        return
    
    session_id = args[1]
    
    with get_db() as conn:
        session = conn.execute(
            "SELECT * FROM card_sessions WHERE id=?", (session_id,)
        ).fetchone()
        
        if not session:
            await message.answer("❌ Сессия не найдена")
            return
        
        players = conn.execute(
            "SELECT * FROM card_players WHERE session_id=?", (session_id,)
        ).fetchall()
        
        # Возвращаем ставки
        for p in players:
            credit_user(p["user_id"], session["current_bet"], "admin_refund",
                       f"Возврат: отмена игры {session_id}")
        
        conn.execute(
            "UPDATE card_sessions SET state='cancelled' WHERE id=?",
            (session_id,)
        )
        conn.commit()
    
    await message.answer(f"✅ Игра {session_id} отменена, ставки возвращены")

# ============================================================
# ЗАЩИТА ОТ СПАМА И ПРОВЕРКА БАНА
# ============================================================

# Хранилище rate-limit (в памяти)
user_request_times: Dict[int, List[float]] = {}
RATE_LIMIT = 5  # запросов
RATE_WINDOW = 10  # секунд


async def check_rate_limit(user_id: int) -> bool:
    """Проверить rate limit. True = разрешено."""
    now = time.time()
    times = user_request_times.get(user_id, [])
    times = [t for t in times if now - t < RATE_WINDOW]
    
    if len(times) >= RATE_LIMIT:
        return False
    
    times.append(now)
    user_request_times[user_id] = times
    return True


@router.message()
async def catch_all_messages(message: Message):
    """Обработчик всех необработанных сообщений."""
    if not message.from_user:
        return
    
    user_id = message.from_user.id
    
    # Проверка бана
    with get_db() as conn:
        user = conn.execute("SELECT is_banned FROM users WHERE id=?", (user_id,)).fetchone()
        if user and user["is_banned"]:
            await message.answer("🚫 Ваш аккаунт заблокирован.")
            return
    
    # Rate limit
    if not await check_rate_limit(user_id):
        await message.answer("⏳ Слишком много запросов. Подождите немного.")
        return
    
    await message.answer(
        "🤔 Не понимаю эту команду.\n"
        "Используй /menu или /help",
        reply_markup=main_menu_keyboard()
    )


@router.callback_query()
async def catch_all_callbacks(callback: CallbackQuery):
    """Обработчик необработанных callback'ов."""
    if callback.data == "noop":
        await callback.answer()
        return
    
    # Проверка бана
    with get_db() as conn:
        user = conn.execute(
            "SELECT is_banned FROM users WHERE id=?",
            (callback.from_user.id,)
        ).fetchone()
        if user and user["is_banned"]:
            await callback.answer("🚫 Аккаунт заблокирован", show_alert=True)
            return
    
    await callback.answer("⚠️ Неизвестное действие")

# ============================================================
# ОЧИСТКА УСТАРЕВШИХ СЕССИЙ (фоновая задача)
# ============================================================

async def cleanup_expired_sessions():
    """Очищать истёкшие игровые сессии."""
    while True:
        try:
            with get_db() as conn:
                # Истёкшие мини-игры
                expired = conn.execute(
                    """SELECT * FROM minigame_sessions 
                       WHERE state='playing' AND expires_at < datetime('now')"""
                ).fetchall()
                
                for session in expired:
                    # Возвращаем ставку если была
                    if session["bet"] > 0:
                        credit_user(session["user_id"], session["bet"], 
                                   "timeout_refund", "Возврат (таймаут)")
                    conn.execute(
                        "UPDATE minigame_sessions SET state='expired' WHERE id=?",
                        (session["id"],)
                    )
                
                # Истёкшие карточные сессии
                expired_cards = conn.execute(
                    """SELECT * FROM card_sessions 
                       WHERE state='active' AND expires_at < datetime('now')"""
                ).fetchall()
                
                for session in expired_cards:
                    players = conn.execute(
                        "SELECT * FROM card_players WHERE session_id=?",
                        (session["id"],)
                    ).fetchall()
                    
                    for p in players:
                        credit_user(p["user_id"], session["current_bet"],
                                   "timeout_refund", "Карточная игра (таймаут)")
                    
                    conn.execute(
                        "UPDATE card_sessions SET state='expired' WHERE id=?",
                        (session["id"],)
                    )
                
                # Очистка старой очереди (>10 мин)
                conn.execute(
                    "DELETE FROM card_queue WHERE joined_at < datetime('now', '-10 minutes')"
                )
                
                conn.commit()
        
        except Exception as e:
            logger.error(f"Ошибка очистки сессий: {e}")
        
        await asyncio.sleep(60)  # Каждую минуту

# ============================================================
# ЗАПУСК БОТА
# ============================================================

async def main():
    """Главная функция запуска."""
    logger.info("Инициализация базы данных...")
    init_db()
    
    logger.info("Запуск бота...")
    
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    dp.include_router(router)
    
    # Запуск фоновой задачи очистки
    asyncio.create_task(cleanup_expired_sessions())
    
    # Устанавливаем команды бота
    from aiogram.types import BotCommand
    commands = [
        BotCommand(command="start", description="Начало работы"),
        BotCommand(command="menu", description="Главное меню"),
        BotCommand(command="balance", description="Мой баланс"),
        BotCommand(command="daily", description="Ежедневный бонус"),
        BotCommand(command="quiz", description="Викторина"),
        BotCommand(command="minesweeper", description="Сапёр"),
        BotCommand(command="reaction", description="Игра на реакцию"),
        BotCommand(command="memory", description="Игра на память"),
        BotCommand(command="slots", description="Слоты"),
        BotCommand(command="roulette", description="Рулетка"),
        BotCommand(command="blackjack", description="Блэкджек"),
        BotCommand(command="crash", description="Краш"),
        BotCommand(command="dice", description="Дайс"),
        BotCommand(command="playcards", description="Карточная дуэль"),
        BotCommand(command="stats", description="Моя статистика"),
        BotCommand(command="referral", description="Реферальная ссылка"),
        BotCommand(command="help", description="Справка"),
        BotCommand(command="terms", description="Правила и условия"),
    ]
    
    await bot.set_my_commands(commands)
    
    logger.info("Бот запущен. Ожидание обновлений...")
    
    # Запускаем polling
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )


if __name__ == "__main__":
    asyncio.run(main())
