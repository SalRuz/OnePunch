import os
import random
import time
import sqlite3
import asyncio
import logging
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = "8183582932:AAEIas0VlMxWSDvOLap_y6cTsZ9yqicmhYc"

DATA_DIR = Path("/app/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "bot.db"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PUNCH_TEXTS = [
    "{attacker} жестко дал пощёчину {victim}",
    "{attacker} врезал {victim} кулаком в челюсть",
    "{attacker} ударил {victim} под дых",
    "{attacker} съездил {victim} по ушам",
    "{attacker} отлупасил {victim} тапком",
    "{attacker} влепил {victim} смачную оплеуху",
    "{attacker} зарядил {victim} в нос",
    "{attacker} с размаху ударил {victim} лбом",
    "{attacker} кинул в {victim} кирпич",
    "{attacker} пнул {victim} под зад",
    "{attacker} съел печень {victim}",
    "{attacker} вырубил {victim} с одного удара",
    "{attacker} отхлестал {victim} по лицу",
    "{attacker} врезал {victim} коленом в пах",
    "{attacker} ударил {victim} стулом",
    "{attacker} дал {victim} в ухо",
    "{attacker} швырнул {victim} об стену",
    "{attacker} наступил {victim} на ногу",
    "{attacker} ударил {victim} бутылкой",
    "{attacker} съездил {victim} монтировкой",
    "{attacker} ударил {victim} газетой",
    "{attacker} кинул в {victim} банан",
    "{attacker} ударил {victim} подушкой",
    "{attacker} шлёпнул {victim} по попе",
    "{attacker} ударил {victim} сковородкой",
    "{attacker} пнул {victim} табуреткой",
    "{attacker} ударил {victim} вилкой",
    "{attacker} дал {victim} в глаз",
    "{attacker} ударил {victim} в спину",
    "{attacker} толкнул {victim} с лестницы",
    "{attacker} ударил {victim} головой",
    "{attacker} ударил {victim} локтем",
    "{attacker} ударил {victim} плечом",
    "{attacker} ударил {victim} коленом",
    "{attacker} ударил {victim} ногой",
    "{attacker} ударил {victim} рукой",
    "{attacker} ударил {victim} кулаком",
    "{attacker} ударил {victim} по голове",
    "{attacker} ударил {victim} по лицу",
    "{attacker} ударил {victim} по телу",
    "{attacker} ударил {victim} по рукам",
    "{attacker} ударил {victim} по ногам",
    "{attacker} ударил {victim} по спине",
    "{attacker} ударил {victim} по груди",
    "{attacker} ударил {victim} по животу",
    "{attacker} ударил {victim} по боку",
    "{attacker} ударил {victim} по шее",
    "{attacker} ударил {victim} по подбородку",
    "{attacker} ударил {victim} по скуле",
    "{attacker} ударил {victim} по виску",
    "{attacker} ударил {victim} по лбу",
    "{attacker} ударил {victim} по затылку",
    "{attacker} ударил {victim} по уху",
    "{attacker} ударил {victim} по носу",
    "{attacker} ударил {victim} по губе",
    "{attacker} ударил {victim} по зубам",
    "{attacker} ударил {victim} по плечу",
    "{attacker} ударил {victim} по предплечью",
    "{attacker} ударил {victim} по локтю",
    "{attacker} ударил {victim} по запястью",
    "{attacker} ударил {victim} по кисти",
    "{attacker} ударил {victim} по пальцам",
    "{attacker} ударил {victim} по рёбрам",
    "{attacker} ударил {victim} по пояснице",
    "{attacker} ударил {victim} по тазу",
    "{attacker} ударил {victim} по бедру",
    "{attacker} ударил {victim} по колену",
    "{attacker} ударил {victim} по голени",
    "{attacker} ударил {victim} по лодыжке",
    "{attacker} ударил {victim} по стопе",
    "{attacker} ударил {victim} по пятке",
    "{attacker} ударил {victim} по носку",
    "{attacker} ударил {victim} по мизинцу",
    "{attacker} ударил {victim} по большому пальцу",
    "{attacker} ударил {victim} по указательному",
    "{attacker} ударил {victim} по среднему",
    "{attacker} ударил {victim} по безымянному",
    "{attacker} ударил {victim} по ладони",
    "{attacker} ударил {victim} по тыльной стороне",
    "{attacker} ударил {victim} по плечевому суставу",
    "{attacker} ударил {victim} по ключице",
    "{attacker} ударил {victim} по лопатке",
    "{attacker} ударил {victim} по позвоночнику",
    "{attacker} ударил {victim} по кадыку",
    "{attacker} ударил {victim} по горлу",
    "{attacker} ударил {victim} по трахее",
    "{attacker} ударил {victim} по нерву",
    "{attacker} ударил {victim} по мышце",
    "{attacker} ударил {victim} по сухожилию",
    "{attacker} ударил {victim} по кости",
    "{attacker} ударил {victim} по коже",
    "{attacker} ударил {victim} по волосам",
    "{attacker} ударил {victim} по щекам",
    "{attacker} ударил {victim} по макушке",
]

POOP_TEXTS = [
    "😱 {nick} обосрался от страха!",
    "💩 После увиденного {nick} не удержался и обосрался!",
    "🚽 {nick} так испугался, что оставил кучу прямо в чате!",
    "😨 Удар был настолько страшным, что {nick} обосрался!",
    "💦 {nick} пролил не только слёзы, но и содержимое кишечника!",
    "🤢 Зрелище было жутким: {nick} обосрался прилюдно!",
    "📉 Стресс пробил дно: {nick} обосрался прямо на месте!",
    "🦥 {nick} так перепугался, что штаны не выдержали!",
    "🚨 Внимание! {nick} только что обосрался от страха!",
    "😵 Адреналин ударил в голову, а результат вышел из {nick}...",
]

POSITIVE_STATS = ["stat_regen", "stat_counter", "stat_block", "stat_jiu"]
ALL_STATS = POSITIVE_STATS + ["debuff_weak", "debuff_fear", "debuff_payoff"]
STAT_NAMES = {
    "stat_regen": "Регенерация", "stat_counter": "Отпор",
    "stat_block": "Блок", "stat_jiu": "Джиу-джитсу",
    "debuff_weak": "Слабость", "debuff_fear": "Страх", "debuff_payoff": "Откуп",
}

COOLDOWNS = {
    "punch": 1800,
    "punch_adren": 900,
    "job": 3600,
    "sport": 5400,
    "freed": 1800,
}

DEFAULT_REGEN_TIME = 3600

# ─── Утилиты ──────────────────────────────────────────────────────────────────

def calc_regen_time(stat_regen: int) -> float:
    return max(60, DEFAULT_REGEN_TIME * (1 - stat_regen / 100))

def format_time(seconds: float) -> str:
    seconds = int(max(0, seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}ч {m}м {s}с"
    elif m > 0:
        return f"{m}м {s}с"
    return f"{s}с"

def clean_nick(t: str) -> str:
    if not t:
        return "User"
    t = t.strip()
    for ch in ["@", "[", "]", "(", ")", "*", "_", "`", "~"]:
        t = t.replace(ch, "")
    return t or "User"

# ─── БД ───────────────────────────────────────────────────────────────────────

def _db():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

COL_DEFAULTS = {
    "user_id": 0, "chat_id": 0, "username": "User",
    "hp": 6, "max_hp": 6, "money": 0, "black_money": 0,
    "shield": 0, "last_punch": 0.0, "last_job": 0.0,
    "last_sport": 0.0, "last_hp_update": 0.0, "last_freed": 0.0,
    "stat_regen": 0, "stat_counter": 0, "stat_block": 0, "stat_jiu": 0,
    "debuff_weak": 0, "debuff_fear": 0, "debuff_payoff": 0,
    "casino_won": 0, "glove_durability": 0, "handcuffs": 0,
    "tranq_until": 0.0, "adren_until": 0.0, "tranq_stock": 0,
}
COL_NAMES = list(COL_DEFAULTS.keys())

def init_db():
    conn = _db()
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER,
            chat_id INTEGER,
            username TEXT DEFAULT "User",
            hp INTEGER DEFAULT 6,
            max_hp INTEGER DEFAULT 6,
            money INTEGER DEFAULT 0,
            black_money INTEGER DEFAULT 0,
            shield INTEGER DEFAULT 0,
            last_punch REAL DEFAULT 0,
            last_job REAL DEFAULT 0,
            last_sport REAL DEFAULT 0,
            last_hp_update REAL DEFAULT 0,
            last_freed REAL DEFAULT 0,
            stat_regen INTEGER DEFAULT 0,
            stat_counter INTEGER DEFAULT 0,
            stat_block INTEGER DEFAULT 0,
            stat_jiu INTEGER DEFAULT 0,
            debuff_weak INTEGER DEFAULT 0,
            debuff_fear INTEGER DEFAULT 0,
            debuff_payoff INTEGER DEFAULT 0,
            casino_won INTEGER DEFAULT 0,
            glove_durability INTEGER DEFAULT 0,
            handcuffs INTEGER DEFAULT 0,
            tranq_until REAL DEFAULT 0,
            adren_until REAL DEFAULT 0,
            tranq_stock INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, chat_id)
        )''')

        # Таблица подвала и рабства
        # escape_stage:
        #   подвал (sold=0): 0=просто в подвале, 1=в наручниках в подвале
        #   рабство (sold=1): 0=в рабстве без наручников, 1=в рабстве в наручниках
        # slave_owner_id / slave_owner_name — у кого в рабстве
        # dungeon_owner_id / dungeon_owner_name — у кого в подвале (после побега из рабства)
        c.execute('''CREATE TABLE IF NOT EXISTS kidnapped (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            victim_id INTEGER,
            victim_name TEXT,
            kidnapper_id INTEGER,
            kidnapper_name TEXT,
            chat_id INTEGER,
            kidnapped_at REAL DEFAULT 0,
            sold INTEGER DEFAULT 0,
            last_income REAL DEFAULT 0,
            handcuffed INTEGER DEFAULT 0,
            slave_owner_id INTEGER DEFAULT 0,
            slave_owner_name TEXT DEFAULT "",
            escape_stage INTEGER DEFAULT 0
        )''')
        conn.commit()

        existing = {row[1] for row in c.execute("PRAGMA table_info(users)")}
        migrations_users = {
            "black_money": "INTEGER DEFAULT 0",
            "last_freed": "REAL DEFAULT 0",
            "glove_durability": "INTEGER DEFAULT 0",
            "handcuffs": "INTEGER DEFAULT 0",
            "tranq_until": "REAL DEFAULT 0",
            "adren_until": "REAL DEFAULT 0",
            "tranq_stock": "INTEGER DEFAULT 0",
        }
        for col, typedef in migrations_users.items():
            if col not in existing:
                c.execute(f"ALTER TABLE users ADD COLUMN {col} {typedef}")
                logger.info(f"Migration users: added column {col}")

        existing_k = {row[1] for row in c.execute("PRAGMA table_info(kidnapped)")}
        migrations_kidnapped = {
            "slave_owner_id": "INTEGER DEFAULT 0",
            "slave_owner_name": "TEXT DEFAULT ''",
            "escape_stage": "INTEGER DEFAULT 0",
        }
        for col, typedef in migrations_kidnapped.items():
            if col not in existing_k:
                c.execute(f"ALTER TABLE kidnapped ADD COLUMN {col} {typedef}")
                logger.info(f"Migration kidnapped: added column {col}")

        c.execute("UPDATE users SET max_hp=6 WHERE max_hp < 6")
        conn.commit()
    finally:
        conn.close()

def _get_user(uid: int, cid: int, name: str) -> dict:
    conn = _db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id=? AND chat_id=?", (uid, cid))
        row = c.fetchone()
        if not row:
            now = time.time()
            safe_name = clean_nick(name) if name else "User"
            c.execute(
                """INSERT INTO users
                (user_id, chat_id, username, hp, max_hp, money, black_money,
                 shield, last_punch, last_job, last_sport, last_hp_update, last_freed,
                 stat_regen, stat_counter, stat_block, stat_jiu,
                 debuff_weak, debuff_fear, debuff_payoff, casino_won,
                 glove_durability, handcuffs, tranq_until, adren_until, tranq_stock)
                VALUES (?,?,?,6,6,0,0,0,0,0,0,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0)""",
                (uid, cid, safe_name, now)
            )
            conn.commit()
            c.execute("SELECT * FROM users WHERE user_id=? AND chat_id=?", (uid, cid))
            row = c.fetchone()

        result = dict(COL_DEFAULTS)
        for key in row.keys():
            result[key] = row[key]
        if not result.get("username"):
            result["username"] = clean_nick(name) if name else "User"
        return result
    finally:
        conn.close()

def _upd_user(uid: int, cid: int, fields: dict):
    if not fields:
        return
    conn = _db()
    try:
        c = conn.cursor()
        sets = ", ".join(f"{k}=?" for k in fields)
        vals = list(fields.values()) + [uid, cid]
        c.execute(f"UPDATE users SET {sets} WHERE user_id=? AND chat_id=?", vals)
        conn.commit()
    finally:
        conn.close()

def _upd_username(uid: int, cid: int, name: str):
    safe = clean_nick(name)
    if safe and safe != "User":
        _upd_user(uid, cid, {"username": safe})

def _recalc_hp(uid: int, cid: int) -> dict:
    u = _get_user(uid, cid, "")
    now = time.time()
    if u.get("tranq_until", 0) > now:
        return u
    elapsed = max(0, now - (u["last_hp_update"] or now))
    regen_time = calc_regen_time(u["stat_regen"])
    gained = int(elapsed // regen_time)
    if gained > 0:
        nhp = min(u["max_hp"], u["hp"] + gained)
        if nhp != u["hp"]:
            _upd_user(uid, cid, {"hp": nhp, "last_hp_update": now})
    return _get_user(uid, cid, "")

# ─── Async helpers ─────────────────────────────────────────────────────────────

async def db_task(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func, *args)

async def async_upd(uid: int, cid: int, fields: dict):
    await db_task(_upd_user, uid, cid, fields)

# ─── Подвал / Рабство helpers ─────────────────────────────────────────────────

def _get_kidnapped_by_victim(vid: int, cid: int):
    """Получить активную запись заключения жертвы (подвал или рабство)."""
    conn = _db()
    try:
        c = conn.cursor()
        # sold=0 — в подвале, sold=1 — в рабстве, но escaped не помечено
        # Ищем любую активную запись где жертва не освобождена окончательно
        c.execute(
            "SELECT * FROM kidnapped WHERE victim_id=? AND chat_id=? AND sold>=0 ORDER BY id DESC LIMIT 1",
            (vid, cid)
        )
        row = c.fetchone()
        if not row:
            return None
        r = dict(row)
        # sold=2 означает полностью освобождён
        if r.get("sold", 0) == 2:
            return None
        return r
    finally:
        conn.close()

def _get_kidnapped_by_kidnapper(kid: int, cid: int):
    """Получить всех заложников в подвале (sold=0) данного похитителя."""
    conn = _db()
    try:
        c = conn.cursor()
        c.execute(
            "SELECT * FROM kidnapped WHERE kidnapper_id=? AND chat_id=? AND sold=0 ORDER BY id",
            (kid, cid)
        )
        return [dict(r) for r in c.fetchall()]
    finally:
        conn.close()

def _get_slaves_by_owner(owner_id: int, cid: int):
    """Получить всех рабов (sold=1) данного владельца."""
    conn = _db()
    try:
        c = conn.cursor()
        c.execute(
            "SELECT * FROM kidnapped WHERE slave_owner_id=? AND chat_id=? AND sold=1 ORDER BY id",
            (owner_id, cid)
        )
        return [dict(r) for r in c.fetchall()]
    finally:
        conn.close()

def _add_kidnapped(vid, vname, kid, kname, cid):
    now = time.time()
    conn = _db()
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO kidnapped "
            "(victim_id, victim_name, kidnapper_id, kidnapper_name, chat_id, kidnapped_at, sold, last_income, handcuffed, slave_owner_id, slave_owner_name, escape_stage) "
            "VALUES (?,?,?,?,?,?,0,?,0,0,'',0)",
            (vid, vname, kid, kname, cid, now, now)
        )
        conn.commit()
        return c.lastrowid
    finally:
        conn.close()

def _free_kidnapped(record_id: int):
    """Полностью освободить (sold=2)."""
    conn = _db()
    try:
        c = conn.cursor()
        c.execute("UPDATE kidnapped SET sold=2 WHERE id=?", (record_id,))
        conn.commit()
    finally:
        conn.close()

def _sell_kidnapped(record_id: int, slave_owner_id: int, slave_owner_name: str):
    """Продать в рабство — sold=1, записываем владельца раба."""
    conn = _db()
    try:
        c = conn.cursor()
        now = time.time()
        c.execute(
            "UPDATE kidnapped SET sold=1, slave_owner_id=?, slave_owner_name=?, last_income=? WHERE id=?",
            (slave_owner_id, slave_owner_name, now, record_id)
        )
        conn.commit()
    finally:
        conn.close()

def _escape_from_slavery(record_id: int, new_kidnapper_id: int, new_kidnapper_name: str):
    """Сбежать из рабства обратно в подвал (к тому кто продал или к старому похитителю)."""
    conn = _db()
    try:
        c = conn.cursor()
        now = time.time()
        # sold=0 снова — теперь в подвале у kidnapper_id (тот, кто изначально держал)
        # Если был продан, то kidnapper_id — тот кто продал. Переводим к new_kidnapper
        c.execute(
            "UPDATE kidnapped SET sold=0, handcuffed=0, slave_owner_id=0, slave_owner_name='', "
            "kidnapper_id=?, kidnapper_name=?, kidnapped_at=? WHERE id=?",
            (new_kidnapper_id, new_kidnapper_name, now, record_id)
        )
        conn.commit()
    finally:
        conn.close()

def _set_handcuffed(record_id: int, val: int):
    conn = _db()
    try:
        c = conn.cursor()
        c.execute("UPDATE kidnapped SET handcuffed=? WHERE id=?", (val, record_id))
        conn.commit()
    finally:
        conn.close()

def _upd_kidnapped_income(record_id: int, last_income: float):
    conn = _db()
    try:
        c = conn.cursor()
        c.execute("UPDATE kidnapped SET last_income=? WHERE id=?", (last_income, record_id))
        conn.commit()
    finally:
        conn.close()

def _count_hostages(kid: int, cid: int) -> int:
    """Количество заложников в подвале."""
    conn = _db()
    try:
        c = conn.cursor()
        c.execute(
            "SELECT COUNT(*) as cnt FROM kidnapped WHERE kidnapper_id=? AND chat_id=? AND sold=0",
            (kid, cid)
        )
        return c.fetchone()["cnt"]
    finally:
        conn.close()

def _count_slaves(owner_id: int, cid: int) -> int:
    """Количество рабов."""
    conn = _db()
    try:
        c = conn.cursor()
        c.execute(
            "SELECT COUNT(*) as cnt FROM kidnapped WHERE slave_owner_id=? AND chat_id=? AND sold=1",
            (owner_id, cid)
        )
        return c.fetchone()["cnt"]
    finally:
        conn.close()

def _transfer_hostages(old_kidnapper_id: int, new_kidnapper_id: int, new_kidnapper_name: str, cid: int):
    """Перевести всех заложников и рабов от одного похитителя к другому."""
    conn = _db()
    try:
        c = conn.cursor()
        # Переводим подвальных заложников
        c.execute(
            "UPDATE kidnapped SET kidnapper_id=?, kidnapper_name=? "
            "WHERE kidnapper_id=? AND chat_id=? AND sold=0",
            (new_kidnapper_id, new_kidnapper_name, old_kidnapper_id, cid)
        )
        # Переводим рабов
        c.execute(
            "UPDATE kidnapped SET slave_owner_id=?, slave_owner_name=? "
            "WHERE slave_owner_id=? AND chat_id=? AND sold=1",
            (new_kidnapper_id, new_kidnapper_name, old_kidnapper_id, cid)
        )
        conn.commit()
    finally:
        conn.close()

# ─── Проверки ──────────────────────────────────────────────────────────────────

def _is_blocked(uid: int, cid: int) -> tuple:
    rec = _get_kidnapped_by_victim(uid, cid)
    if rec:
        if rec["sold"] == 1:
            if rec["handcuffed"]:
                return True, "⛓️ Вы в наручниках в рабстве! Сначала /freed (снять наручники)."
            return True, "🔒 Вы в рабстве! Используйте /freed чтобы сбежать в подвал."
        else:
            if rec["handcuffed"]:
                return True, "⛓️ Вы в наручниках в подвале! Сначала /freed (снять наручники), потом снова /freed (сбежать)."
            return True, "🔒 Вы в подвале! Используйте /freed чтобы сбежать."
    return False, ""

def _is_tranquilized(uid: int, cid: int) -> tuple:
    u = _get_user(uid, cid, "")
    now = time.time()
    if u.get("tranq_until", 0) > now:
        return True, u["tranq_until"] - now
    return False, 0.0

# ─── Общая функция вывода статов ──────────────────────────────────────────────

async def show_stats(m: types.Message, uid: int, cid: int, name: str):
    await db_task(_get_user, uid, cid, name)
    await db_task(_upd_username, uid, cid, name)
    await db_task(_recalc_hp, uid, cid)
    u = await db_task(_get_user, uid, cid, name)

    display_name = u.get("username") or name or "User"
    now = time.time()
    regen_time = calc_regen_time(u["stat_regen"])

    if u.get("tranq_until", 0) > now:
        regen_str = f"заморожен ({format_time(u['tranq_until'] - now)})"
    elif u["hp"] >= u["max_hp"]:
        regen_str = "макс HP"
    else:
        elapsed = max(0, now - (u["last_hp_update"] or now))
        time_to_next = regen_time - (elapsed % regen_time)
        regen_str = f"через {format_time(time_to_next)}"

    hostages = await db_task(_count_hostages, uid, cid)
    slaves = await db_task(_count_slaves, uid, cid)
    kidnap_rec = await db_task(_get_kidnapped_by_victim, uid, cid)

    # Список заложников в подвале
    hostage_list = await db_task(_get_kidnapped_by_kidnapper, uid, cid)
    slave_list = await db_task(_get_slaves_by_owner, uid, cid)

    kidnap_str = ""
    if kidnap_rec:
        if kidnap_rec["sold"] == 1:
            owner = kidnap_rec.get("slave_owner_name", "?")
            cuffs = " (в наручниках)" if kidnap_rec["handcuffed"] else ""
            kidnap_str = f"😱 В рабстве у: {owner}{cuffs}"
        else:
            kname = kidnap_rec.get("kidnapper_name", "?")
            cuffs = " (в наручниках)" if kidnap_rec["handcuffed"] else ""
            kidnap_str = f"🔒 В подвале у: {kname}{cuffs}"

    effects_lines = []
    if u.get("adren_until", 0) > now:
        effects_lines.append(f"🔥 Адреналин: {format_time(u['adren_until'] - now)}")
    if u.get("tranq_until", 0) > now:
        effects_lines.append(f"💉 Транквилизатор: {format_time(u['tranq_until'] - now)}")

    shield_str = "есть" if u["shield"] else "нет"
    glove_str = f"{u['glove_durability']}/10" if u["glove_durability"] > 0 else "нет"

    lines = [
        f"👤 Игрок: {display_name}",
        f"",
        f"❤️  HP: {u['hp']}/{u['max_hp']} ({regen_str})",
        f"⏱  Реген 1 HP: {format_time(regen_time)}",
        f"💰  Монеты: {u['money']}",
        f"🖤  Чёрные монеты: {u['black_money']}",
        f"🛡️  Щит: {shield_str}",
        f"🥊  Перчатка: {glove_str}",
        f"⛓️  Наручники: {u['handcuffs']} шт.",
        f"💉  Транки в запасе: {u.get('tranq_stock', 0)} шт.",
        f"🔒  Заложников в подвале: {hostages}",
        f"😈  Рабов: {slaves}",
    ]

    # Список заложников в подвале
    if hostage_list:
        lines.append("")
        lines.append("🔒 В подвале:")
        for h in hostage_list:
            cuffs = " ⛓️" if h["handcuffed"] else ""
            lines.append(f"   • {h['victim_name']}{cuffs}")

    # Список рабов
    if slave_list:
        lines.append("")
        lines.append("😈 Рабы:")
        for s in slave_list:
            cuffs = " ⛓️" if s["handcuffed"] else ""
            lines.append(f"   • {s['victim_name']}{cuffs}")

    if kidnap_str:
        lines.append("")
        lines.append(kidnap_str)

    if effects_lines:
        lines.append("")
        lines.append("✨ Активные эффекты:")
        for ef in effects_lines:
            lines.append(f"   {ef}")

    lines += [
        "",
        "📈 Навыки:",
        f"   🔄 Регенерация:  {u['stat_regen']}%",
        f"   🥊 Отпор:        {u['stat_counter']}%",
        f"   🛡️ Блок:         {u['stat_block']}%",
        f"   🥋 Джиу-джитсу: {u['stat_jiu']}%",
        "",
        "📉 Дебаффы:",
        f"   🦠 Слабость: {u['debuff_weak']}%",
        f"   😨 Страх:    {u['debuff_fear']}%",
        f"   💸 Откуп:    {u['debuff_payoff']}%",
        "",
        f"🎰 Выиграно в казино: {u['casino_won']}💰",
    ]

    await m.answer("\n".join(lines))

# ─── Удар ──────────────────────────────────────────────────────────────────────

async def do_punch(aid: int, aname: str, vid: int, cid: int, auto: bool = False):
    try:
        now = time.time()
        att = await db_task(_get_user, aid, cid, aname)
        vic = await db_task(_recalc_hp, vid, cid)
        vic = await db_task(_get_user, vid, cid, vic.get("username", ""))

        if not auto:
            punch_cd = COOLDOWNS["punch_adren"] if att.get("adren_until", 0) > now else COOLDOWNS["punch"]
            cd = punch_cd - (now - (att["last_punch"] or 0))
            if cd > 0:
                adren_note = " (🔥 адреналин)" if att.get("adren_until", 0) > now else ""
                return await bot.send_message(
                    cid, f"⏳ {att['username']}, кулдаун{adren_note}: {format_time(cd)}"
                )

        if vic["shield"] == 1:
            await async_upd(vid, cid, {"shield": 0})
            return await bot.send_message(cid, f"🛡️ Щит {vic['username']} поглотил удар!")

        if vic["debuff_payoff"] > 0 and vic["money"] > 0 and random.randint(1, 100) <= vic["debuff_payoff"]:
            amt = vic["money"] // 2
            await async_upd(vid, cid, {"money": vic["money"] - amt})
            await async_upd(aid, cid, {"money": att["money"] + amt})
            return await bot.send_message(cid, f"💸 Откуп! {vic['username']} отдал {amt}💰")

        if vic["stat_jiu"] > 0 and random.randint(1, 100) <= vic["stat_jiu"]:
            await bot.send_message(cid, f"🥋 {vic['username']} использовал джиу-джитсу! Контратака!")
            await do_punch(vid, vic["username"], aid, cid, auto=True)
            if not auto:
                await async_upd(aid, cid, {"last_punch": now})
            return

        if vic["stat_block"] > 0 and random.randint(1, 100) <= vic["stat_block"]:
            return await bot.send_message(cid, f"🛡️ {vic['username']} заблокировал удар!")

        base_dmg = 2 if att["glove_durability"] > 0 else 1
        weak_proc = vic["debuff_weak"] > 0 and random.randint(1, 100) <= vic["debuff_weak"]
        dmg = base_dmg * 2 if weak_proc else base_dmg
        nhp = max(0, vic["hp"] - dmg)

        glove_msg = ""
        if att["glove_durability"] > 0:
            new_dur = att["glove_durability"] - 1
            await async_upd(aid, cid, {"glove_durability": new_dur})
            att["glove_durability"] = new_dur
            glove_msg = "\n🥊 Перчатка сломалась!" if new_dur == 0 else f"\n🥊 Перчатка: {new_dur}/10"

        take = vic["money"] // 4
        new_vic_money = max(0, vic["money"] - take)
        new_att_money = att["money"] + take

        await async_upd(vid, cid, {"hp": nhp, "money": new_vic_money})
        await async_upd(aid, cid, {"money": new_att_money})

        black_msg = ""
        if vic["black_money"] > 0 and random.randint(1, 100) <= 10:
            await async_upd(vid, cid, {"black_money": max(0, vic["black_money"] - 1)})
            await async_upd(aid, cid, {"black_money": att["black_money"] + 1})
            black_msg = "\n🖤 Украдена 1 чёрная монета!"

        txt = random.choice(PUNCH_TEXTS).format(attacker=att["username"], victim=vic["username"])
        msg = f"💥 {txt}\n💰 +{take} | ❤️ {vic['username']}: {nhp}/{vic['max_hp']}"

        if weak_proc and base_dmg == 2:
            msg += "\n⚡ Перчатка + Слабость: 4 урона!"
        elif weak_proc:
            msg += "\n⚡ Слабость удвоила урон!"

        msg += glove_msg + black_msg

        if nhp == 0 and vic["glove_durability"] > 0:
            if att["glove_durability"] == 0:
                await async_upd(aid, cid, {"glove_durability": vic["glove_durability"]})
                await async_upd(vid, cid, {"glove_durability": 0})
                msg += f"\n🥊 Перчатка ({vic['glove_durability']}/10) перешла к {att['username']}!"
            else:
                await async_upd(vid, cid, {"glove_durability": 0})
                msg += f"\n🥊 Перчатка {vic['username']} уничтожена!"

        if nhp == 0 and vic["handcuffs"] > 0:
            await async_upd(aid, cid, {"handcuffs": att["handcuffs"] + vic["handcuffs"]})
            await async_upd(vid, cid, {"handcuffs": 0})
            msg += f"\n⛓️ Наручники ({vic['handcuffs']} шт.) перешли к {att['username']}!"

        if vic["stat_counter"] > 0 and random.randint(1, 100) <= vic["stat_counter"]:
            msg += f"\n🔄 {vic['username']} активировал Отпор!"
            await do_punch(vid, vic["username"], aid, cid, auto=True)

        if random.random() < 0.25:
            valid = [s for s in ALL_STATS if vic[s] < 100]
            if valid:
                st = random.choice(valid)
                nv = max(0, vic[st] - 1 if st in POSITIVE_STATS else vic[st] + 1)
                await async_upd(vid, cid, {st: nv})
                sign = "📉" if st in POSITIVE_STATS else "📈"
                msg += f"\n{sign} {STAT_NAMES[st]}: {vic[st]}% → {nv}%"
                if st == "stat_regen":
                    msg += f" (реген: {format_time(calc_regen_time(nv))}/HP)"

        conn = _db()
        try:
            cur = conn.cursor()
            cur.execute("SELECT username, debuff_fear FROM users WHERE chat_id=? AND debuff_fear>0", (cid,))
            fear_rows = cur.fetchall()
        finally:
            conn.close()

        for fr in fear_rows:
            if random.randint(1, 100) <= fr["debuff_fear"]:
                await bot.send_message(cid, random.choice(POOP_TEXTS).format(nick=fr["username"]))

        if not auto:
            await async_upd(aid, cid, {"last_punch": now})

        await bot.send_message(cid, msg)

    except Exception as e:
        logger.error(f"Punch error: {e}", exc_info=True)
        await bot.send_message(cid, "⚠️ Ошибка при ударе.")

# ─── Магазин ──────────────────────────────────────────────────────────────────

async def shop_cb(call: types.CallbackQuery):
    try:
        item = call.data.split(":")[1]
        uid = call.from_user.id
        cid = call.message.chat.id
        name = clean_nick(call.from_user.full_name)
        u = await db_task(_get_user, uid, cid, name)
        now = time.time()

        if item == "skip":
            if u["money"] < 3:
                return await call.answer("Нужно 3💰", show_alert=True)
            await async_upd(uid, cid, {"money": u["money"] - 3, "last_punch": now - COOLDOWNS["punch"]})
            await call.answer("Кулдаун сброшен!", show_alert=True)
            await call.message.edit_text(f"✅ {u['username']} купил сброс кулдауна")

        elif item == "life":
            if u["money"] < 5:
                return await call.answer("Нужно 5💰", show_alert=True)
            if u["hp"] >= u["max_hp"]:
                return await call.answer("Уже максимум HP!", show_alert=True)
            await async_upd(uid, cid, {"money": u["money"] - 5, "hp": u["hp"] + 1})
            await call.answer("+1 HP!", show_alert=True)
            await call.message.edit_text(f"❤️ {u['username']} купил +1 HP")

        elif item == "shield":
            if u["money"] < 4:
                return await call.answer("Нужно 4💰", show_alert=True)
            if u["shield"] == 1:
                return await call.answer("Щит уже есть!", show_alert=True)
            await async_upd(uid, cid, {"money": u["money"] - 4, "shield": 1})
            await call.answer("Щит получен!", show_alert=True)
            await call.message.edit_text(f"🛡️ {u['username']} купил щит")

        elif item == "exchange_black":
            if u["black_money"] < 1:
                return await call.answer("Нет чёрных монет!", show_alert=True)
            await async_upd(uid, cid, {"black_money": u["black_money"] - 1, "money": u["money"] + 10})
            await call.answer("1🖤 → 10💰!", show_alert=True)
            await call.message.edit_text(f"💱 {u['username']} разменял 1🖤 → 10💰")

        elif item == "glove":
            if u["black_money"] < 3:
                return await call.answer("Нужно 3🖤", show_alert=True)
            if u["glove_durability"] > 0:
                return await call.answer("Перчатка уже есть!", show_alert=True)
            await async_upd(uid, cid, {"black_money": u["black_money"] - 3, "glove_durability": 10})
            await call.answer("🥊 Перчатка получена!", show_alert=True)
            await call.message.edit_text(f"🥊 {u['username']} купил боксёрскую перчатку (10/10)")

        elif item == "handcuff":
            if u["black_money"] < 1:
                return await call.answer("Нужно 1🖤", show_alert=True)
            await async_upd(uid, cid, {"black_money": u["black_money"] - 1, "handcuffs": u["handcuffs"] + 1})
            await call.answer("⛓️ Наручники куплены!", show_alert=True)
            await call.message.edit_text(f"⛓️ {u['username']} купил наручники (всего: {u['handcuffs'] + 1} шт.)")

        elif item == "tranq":
            if u["black_money"] < 4:
                return await call.answer("Нужно 4🖤", show_alert=True)
            await async_upd(uid, cid, {
                "black_money": u["black_money"] - 4,
                "tranq_stock": u["tranq_stock"] + 1,
            })
            await call.answer("💉 Транквилизатор куплен! Используй /trank", show_alert=True)
            await call.message.edit_text(
                f"💉 {u['username']} купил транквилизатор!\n"
                f"Запас: {u['tranq_stock'] + 1} шт. Используй /trank ответом на жертву."
            )

        elif item == "adren":
            if u["black_money"] < 3:
                return await call.answer("Нужно 3🖤", show_alert=True)
            if u.get("adren_until", 0) > now:
                return await call.answer("Адреналин уже действует!", show_alert=True)
            adren_end = now + 10800
            await async_upd(uid, cid, {"black_money": u["black_money"] - 3, "adren_until": adren_end})
            await call.answer("🔥 Адреналин на 3 часа! КД удара: 15 минут", show_alert=True)
            await call.message.edit_text(
                f"🔥 {u['username']} выпил адреналин!\nКД удара снижен до 15 минут на 3 часа."
            )

    except Exception as e:
        logger.error(f"Shop error: {e}", exc_info=True)
        await call.answer("⚠️ Ошибка магазина", show_alert=True)

# ─── Глобальный обработчик ошибок ─────────────────────────────────────────────

@dp.errors()
async def errors_handler(update: types.Update, exception: Exception):
    logger.error(f"UNHANDLED: {type(exception).__name__}: {exception}", exc_info=True)
    return True

# ─── /help ────────────────────────────────────────────────────────────────────

@dp.message(Command("help"))
async def cmd_help(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id
        name = clean_nick(m.from_user.full_name)
        await db_task(_get_user, uid, cid, name)
        await db_task(_upd_username, uid, cid, name)

        kb = InlineKeyboardBuilder()
        for t, d in [
            ("📊 Статы", "stats"), ("🎰 Казино", "casino"),
            ("💼 Работа", "job"), ("🏋️ Спорт", "sport"),
            ("🏪 Магазин", "shop"), ("🏆 Топ", "casinotop"),
        ]:
            kb.button(text=t, callback_data=f"qcmd:{d}")
        kb.adjust(2)

        await m.answer(
            "📖 Помощь\n\n"
            "🥊 /punch (ответ) — удар (кд 30м)\n"
            "💼 /job — работа (+1💰, кд 1ч)\n"
            "🏋️ /sport — прокачка навыка (кд 1.5ч)\n"
            "🎰 /casino <сумма> — казино\n"
            "🏆 /casinotop — топ чата\n"
            "📊 /stats — мои статы (или ответом — чужие)\n"
            "🏪 /shop — магазин\n\n"
            "❤️ /hill (ответ) — передать 1 HP любому игроку (нужно >1 HP)\n\n"
            "🔒 Подвал и рабство:\n"
            "   /kidnap (ответ) — похитить игрока с 0 HP\n"
            "   /freed — сбежать (30% шанс, кд 30м)\n"
            "   /sell <номер> (ответ на игрока) — продать в рабство тому игроку\n"
            "   /handcuff <номер> или ответом — надеть наручники\n\n"
            "🔓 Порядок побега из рабства с наручниками:\n"
            "   1️⃣ /freed — снять наручники (30%, кд 30м)\n"
            "   2️⃣ /freed — сбежать из рабства в подвал (30%, кд 30м)\n"
            "   3️⃣ /freed — сбежать из подвала (30%, кд 30м)\n\n"
            "💉 Спецпредметы:\n"
            "   /trank (ответ) — транквилизатор: паралич 3ч + стоп регена (4🖤)\n"
            "   /adren — статус адреналина (купить 3🖤): КД удара 15м на 3ч\n\n"
            "⚠️ При 0 HP: только /shop и реген\n"
            "🌍 У каждого чата свой мир\n\n"
            "🖤 Чёрные монеты = 10💰\n"
            "🥊 Перчатка (3🖤) — x2 урон, 10 ударов\n"
            "⛓️ Наручники (1🖤) — сковать заложника/раба\n"
            "💉 Транквилизатор (4🖤) — паралич 3ч\n"
            "🔥 Адреналин (3🖤) — КД удара 15м на 3ч\n\n"
            "⚡ Если похитителя самого похитят — его заложники и рабы перейдут новому хозяину!",
            reply_markup=kb.as_markup()
        )
    except Exception as e:
        logger.error(f"/help error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка")

# ─── Quick cmd callback ────────────────────────────────────────────────────────

@dp.callback_query(lambda c: c.data.startswith("qcmd:"))
async def qcmd(call: types.CallbackQuery):
    try:
        cmd = call.data.split(":")[1]
        await call.answer()
        dispatch = {
            "stats": cmd_stats, "job": cmd_job,
            "sport": cmd_sport, "shop": cmd_shop,
            "casinotop": cmd_casinotop,
        }
        if cmd in dispatch:
            await dispatch[cmd](call.message)
        elif cmd == "casino":
            await call.message.answer("🎰 Использование: /casino <сумма>")
    except Exception as e:
        logger.error(f"qcmd error: {e}", exc_info=True)
        await call.answer("⚠️ Ошибка", show_alert=True)

# ─── /stats ───────────────────────────────────────────────────────────────────

@dp.message(Command("stats", "profile"))
async def cmd_stats(m: types.Message):
    try:
        cid = m.chat.id
        if m.reply_to_message and m.reply_to_message.from_user.id != bot.id:
            target = m.reply_to_message.from_user
            tuid = target.id
            tname = clean_nick(target.full_name)
            await show_stats(m, tuid, cid, tname)
        else:
            uid = m.from_user.id
            name = clean_nick(m.from_user.full_name)
            await show_stats(m, uid, cid, name)
    except Exception as e:
        logger.error(f"/stats error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка загрузки статов")

# ─── /punch ───────────────────────────────────────────────────────────────────

@dp.message(Command("punch"))
async def cmd_punch(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id
        name = clean_nick(m.from_user.full_name)

        await db_task(_get_user, uid, cid, name)
        await db_task(_upd_username, uid, cid, name)

        blocked, reason = await db_task(_is_blocked, uid, cid)
        if blocked:
            return await m.answer(reason)

        tranqed, t_left = await db_task(_is_tranquilized, uid, cid)
        if tranqed:
            return await m.answer(f"💉 Вы под транквилизатором! Осталось: {format_time(t_left)}")

        if not m.reply_to_message:
            return await m.answer("⚠️ Ответьте на сообщение игрока!")

        u = await db_task(_get_user, uid, cid, name)
        if u["hp"] <= 0:
            return await m.answer("💀 0 HP! Ждите реген или купите жизнь в /shop")

        target = m.reply_to_message.from_user
        if target.id == bot.id:
            return await m.answer("🤖 Ботов не бьём!")
        if target.id == uid:
            return await m.answer("🤡 Себя бить нельзя!")

        tname = clean_nick(target.full_name)
        await db_task(_get_user, target.id, cid, tname)
        await db_task(_upd_username, target.id, cid, tname)
        await do_punch(uid, u["username"], target.id, cid)
    except Exception as e:
        logger.error(f"/punch error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка удара")

# ─── /job ─────────────────────────────────────────────────────────────────────

@dp.message(Command("job"))
async def cmd_job(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id
        name = clean_nick(m.from_user.full_name)

        await db_task(_get_user, uid, cid, name)
        await db_task(_upd_username, uid, cid, name)

        blocked, reason = await db_task(_is_blocked, uid, cid)
        if blocked:
            return await m.answer(reason)

        tranqed, t_left = await db_task(_is_tranquilized, uid, cid)
        if tranqed:
            return await m.answer(f"💉 Вы под транквилизатором! Осталось: {format_time(t_left)}")

        u = await db_task(_get_user, uid, cid, name)
        if u["hp"] <= 0:
            return await m.answer("💀 0 HP! Нельзя работать")

        now = time.time()
        cd = COOLDOWNS["job"] - (now - (u["last_job"] or 0))
        if cd > 0:
            return await m.answer(f"⏳ Работа доступна через {format_time(cd)}")

        new_money = u["money"] + 1
        await async_upd(uid, cid, {"money": new_money, "last_job": now})
        await m.answer(f"💼 {u['username']} заработал +1💰\nБаланс: {new_money}💰")
    except Exception as e:
        logger.error(f"/job error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка работы")

# ─── /sport ───────────────────────────────────────────────────────────────────

@dp.message(Command("sport"))
async def cmd_sport(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id
        name = clean_nick(m.from_user.full_name)

        await db_task(_get_user, uid, cid, name)
        await db_task(_upd_username, uid, cid, name)

        blocked, reason = await db_task(_is_blocked, uid, cid)
        if blocked:
            return await m.answer(reason)

        tranqed, t_left = await db_task(_is_tranquilized, uid, cid)
        if tranqed:
            return await m.answer(f"💉 Вы под транквилизатором! Осталось: {format_time(t_left)}")

        u = await db_task(_get_user, uid, cid, name)
        if u["hp"] <= 0:
            return await m.answer("💀 0 HP! Тренировки запрещены")

        now = time.time()
        cd = COOLDOWNS["sport"] - (now - (u["last_sport"] or 0))
        if cd > 0:
            return await m.answer(f"⏳ Тренировка доступна через {format_time(cd)}")

        st = random.choice(POSITIVE_STATS)
        old_val = u[st]
        nv = min(100, old_val + 1)
        await async_upd(uid, cid, {st: nv, "last_sport": now})

        msg = f"🏋️ {u['username']} прокачал {STAT_NAMES[st]}: {old_val}% → {nv}%"
        if st == "stat_regen":
            msg += f"\n⏱ Время регена: {format_time(calc_regen_time(nv))}/HP"
        await m.answer(msg)
    except Exception as e:
        logger.error(f"/sport error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка тренировки")

# ─── /shop ────────────────────────────────────────────────────────────────────

@dp.message(Command("shop"))
async def cmd_shop(m: types.Message):
    try:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Сброс кд удара — 3💰", callback_data="shop:skip")],
            [InlineKeyboardButton(text="❤️ +1 жизнь — 5💰", callback_data="shop:life")],
            [InlineKeyboardButton(text="🛡️ Щит — 4💰", callback_data="shop:shield")],
            [InlineKeyboardButton(text="💱 Разменять 1🖤 → 10💰", callback_data="shop:exchange_black")],
            [InlineKeyboardButton(text="🥊 Перчатка x2 урон — 3🖤", callback_data="shop:glove")],
            [InlineKeyboardButton(text="⛓️ Наручники — 1🖤", callback_data="shop:handcuff")],
            [InlineKeyboardButton(text="💉 Транквилизатор — 4🖤", callback_data="shop:tranq")],
            [InlineKeyboardButton(text="🔥 Адреналин (КД 15м) — 3🖤", callback_data="shop:adren")],
        ])
        await m.answer(
            "🏪 Магазин (доступен при 0 HP)\n\n"
            "🥊 Перчатка — x2 урон, 10 ударов, только 1 шт.\n"
            "⛓️ Наручники — сковать заложника/раба (неограниченно)\n"
            "💉 Транквилизатор — /trank: паралич 3ч + стоп регена\n"
            "🔥 Адреналин — КД удара 15м вместо 30м на 3ч\n"
            "💱 1🖤 = 10💰",
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f"/shop error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка магазина")

@dp.callback_query(lambda c: c.data.startswith("shop:"))
async def shop_h(call: types.CallbackQuery):
    await shop_cb(call)

# ─── /casino ──────────────────────────────────────────────────────────────────

@dp.message(Command("casino"))
async def cmd_casino(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id
        name = clean_nick(m.from_user.full_name)

        await db_task(_get_user, uid, cid, name)
        await db_task(_upd_username, uid, cid, name)

        blocked, reason = await db_task(_is_blocked, uid, cid)
        if blocked:
            return await m.answer(reason)

        tranqed, t_left = await db_task(_is_tranquilized, uid, cid)
        if tranqed:
            return await m.answer(f"💉 Вы под транквилизатором! Осталось: {format_time(t_left)}")

        u = await db_task(_get_user, uid, cid, name)
        if u["hp"] <= 0:
            return await m.answer("💀 0 HP! Казино закрыто")

        parts = m.text.split()
        if len(parts) < 2:
            return await m.answer("🎰 Использование: /casino <сумма>")
        try:
            bet = int(parts[1])
        except ValueError:
            return await m.answer("❌ Введите целое число")
        if bet <= 0:
            return await m.answer("❌ Ставка > 0")
        if u["money"] < bet:
            return await m.answer(f"💸 Нужно {bet}💰, у вас {u['money']}💰")

        r = random.random()
        mult = 0 if r < 0.40 else 1 if r < 0.70 else 2 if r < 0.90 else 3 if r < 0.98 else 5
        win = bet * mult
        new_money = u["money"] - bet + win
        await async_upd(uid, cid, {"money": new_money, "casino_won": u["casino_won"] + win})

        labels = {0: "💀 Проигрыш", 1: "🔄 Возврат", 2: "🎉 x2!", 3: "🔥 x3!", 5: "💎 x5 ДЖЕКПОТ!!!"}
        await m.answer(
            f"🎰 {u['username']}: {labels[mult]}\n"
            f"Ставка: {bet}💰 | x{mult} | Выигрыш: {win}💰\n"
            f"💰 Баланс: {new_money}💰"
        )
    except Exception as e:
        logger.error(f"/casino error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка казино")

# ─── /casinotop ───────────────────────────────────────────────────────────────

@dp.message(Command("casinotop"))
async def cmd_casinotop(m: types.Message):
    try:
        conn = _db()
        try:
            c = conn.cursor()
            c.execute(
                "SELECT username, casino_won FROM users WHERE chat_id=? ORDER BY casino_won DESC LIMIT 10",
                (m.chat.id,)
            )
            rows = c.fetchall()
        finally:
            conn.close()

        if not rows:
            return await m.answer("📊 Пока никто не играл в казино")

        lines = ["🏆 Топ лудоманов чата:\n"]
        for i, row in enumerate(rows, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            uname = row["username"] or f"User{i}"
            lines.append(f"{medal} {uname}: {row['casino_won']}💰")
        await m.answer("\n".join(lines))
    except Exception as e:
        logger.error(f"/casinotop error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка топа")

# ─── /hill ────────────────────────────────────────────────────────────────────

@dp.message(Command("hill"))
async def cmd_hill(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id
        name = clean_nick(m.from_user.full_name)

        await db_task(_get_user, uid, cid, name)
        await db_task(_upd_username, uid, cid, name)

        blocked, reason = await db_task(_is_blocked, uid, cid)
        if blocked:
            return await m.answer(reason)

        tranqed, t_left = await db_task(_is_tranquilized, uid, cid)
        if tranqed:
            return await m.answer(f"💉 Вы под транквилизатором! Осталось: {format_time(t_left)}")

        if not m.reply_to_message:
            return await m.answer("⚠️ Ответьте на сообщение игрока которому хотите помочь!")

        target = m.reply_to_message.from_user
        if target.id == uid:
            return await m.answer("🤡 Нельзя делиться HP с собой!")
        if target.id == bot.id:
            return await m.answer("🤖 Боту HP не нужно!")

        await db_task(_recalc_hp, uid, cid)
        u = await db_task(_get_user, uid, cid, name)
        sender_name = u.get("username") or name

        if u["hp"] <= 1:
            return await m.answer(
                f"❤️ {sender_name}, у вас {u['hp']} HP — нельзя делиться!\n"
                f"Нужно больше 1 HP."
            )

        tname = clean_nick(target.full_name)
        await db_task(_get_user, target.id, cid, tname)
        await db_task(_upd_username, target.id, cid, tname)
        await db_task(_recalc_hp, target.id, cid)
        t = await db_task(_get_user, target.id, cid, tname)
        target_name = t.get("username") or tname

        if t["hp"] >= t["max_hp"]:
            return await m.answer(
                f"❤️ У {target_name} уже максимум HP ({t['hp']}/{t['max_hp']})!\n"
                f"Нет смысла делиться."
            )

        new_sender_hp = u["hp"] - 1
        new_target_hp = min(t["max_hp"], t["hp"] + 1)

        await async_upd(uid, cid, {"hp": new_sender_hp})
        await async_upd(target.id, cid, {"hp": new_target_hp})

        await m.answer(
            f"❤️ {sender_name} поделился 1 HP с {target_name}!\n"
            f"{sender_name}: {new_sender_hp}/{u['max_hp']} HP\n"
            f"{target_name}: {new_target_hp}/{t['max_hp']} HP"
        )
    except Exception as e:
        logger.error(f"/hill error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка")

# ─── /kidnap ──────────────────────────────────────────────────────────────────

@dp.message(Command("kidnap"))
async def cmd_kidnap(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id
        name = clean_nick(m.from_user.full_name)

        await db_task(_get_user, uid, cid, name)
        await db_task(_upd_username, uid, cid, name)

        blocked, reason = await db_task(_is_blocked, uid, cid)
        if blocked:
            return await m.answer(reason)

        tranqed, t_left = await db_task(_is_tranquilized, uid, cid)
        if tranqed:
            return await m.answer(f"💉 Вы под транквилизатором! Осталось: {format_time(t_left)}")

        if not m.reply_to_message:
            return await m.answer("⚠️ Ответьте на сообщение игрока!")

        target = m.reply_to_message.from_user
        if target.id == uid:
            return await m.answer("🤡 Нельзя похитить себя!")
        if target.id == bot.id:
            return await m.answer("🤖 Бота не похищают!")

        u = await db_task(_get_user, uid, cid, name)
        if u["hp"] <= 0:
            return await m.answer("💀 0 HP! Вы не можете похищать.")

        tname = clean_nick(target.full_name)
        await db_task(_get_user, target.id, cid, tname)
        await db_task(_upd_username, target.id, cid, tname)
        await db_task(_recalc_hp, target.id, cid)
        t = await db_task(_get_user, target.id, cid, tname)
        target_name = t.get("username") or tname

        if t["hp"] > 0:
            return await m.answer(f"❌ У {target_name} ещё есть HP ({t['hp']})! Похищать можно только при 0 HP.")

        existing = await db_task(_get_kidnapped_by_victim, target.id, cid)
        if existing:
            return await m.answer(f"🔒 {target_name} уже в чьём-то подвале или рабстве!")

        kid_name = u.get("username") or name
        await db_task(_add_kidnapped, target.id, target_name, uid, kid_name, cid)

        hostages = await db_task(_get_kidnapped_by_kidnapper, uid, cid)
        num = len(hostages)

        # Переносим заложников похищенного к новому похитителю
        await db_task(_transfer_hostages, target.id, uid, kid_name, cid)

        # Проверяем были ли переданы заложники
        transferred_hostages = await db_task(_get_kidnapped_by_kidnapper, uid, cid)
        extra_count = len(transferred_hostages) - num
        transfer_msg = ""
        if extra_count > 0:
            transfer_msg = f"\n⚡ {extra_count} заложник(ов) {target_name} перешли к {kid_name}!"

        await m.answer(
            f"🔒 {kid_name} похитил {target_name} и запер в подвале!\n"
            f"Заложник #{num}.\n"
            f"Жертва может сбежать: /freed (30% шанс, кд 30м)\n"
            f"Через 30м можно продать: /sell {num} (ответом на покупателя)"
            + transfer_msg
        )
    except Exception as e:
        logger.error(f"/kidnap error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка похищения")

# ─── /freed ───────────────────────────────────────────────────────────────────

@dp.message(Command("freed"))
async def cmd_freed(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id
        name = clean_nick(m.from_user.full_name)

        await db_task(_get_user, uid, cid, name)
        await db_task(_upd_username, uid, cid, name)
        u = await db_task(_get_user, uid, cid, name)
        display = u.get("username") or name

        rec = await db_task(_get_kidnapped_by_victim, uid, cid)
        if not rec:
            return await m.answer("🤷 Вы не в подвале и не в рабстве!")

        now = time.time()
        cd = COOLDOWNS["freed"] - (now - (u["last_freed"] or 0))
        if cd > 0:
            return await m.answer(f"⏳ Попытка побега через {format_time(cd)}")

        await async_upd(uid, cid, {"last_freed": now})

        # ════════════════════════════════════════════
        # РАБСТВО (sold=1)
        # ════════════════════════════════════════════
        if rec["sold"] == 1:
            owner_name = rec.get("slave_owner_name", "?")

            # Шаг 1: снять наручники в рабстве
            if rec["handcuffed"]:
                if random.randint(1, 100) <= 30:
                    await db_task(_set_handcuffed, rec["id"], 0)
                    return await m.answer(
                        f"⛓️ {display} снял наручники в рабстве у {owner_name}!\n"
                        f"Теперь попробуй сбежать (/freed через 30м)"
                    )
                else:
                    return await m.answer(
                        f"⛓️ {display} не смог снять наручники в рабстве у {owner_name}!\n"
                        f"Попробуй через 30м."
                    )

            # Шаг 2: сбежать из рабства обратно в подвал (к тому кто продал — kidnapper_id)
            if random.randint(1, 100) <= 30:
                # Сбегаем из рабства, возвращаемся в подвал к kidnapper_id
                old_kidnapper_id = rec["kidnapper_id"]
                old_kidnapper_name = rec["kidnapper_name"]
                await db_task(_escape_from_slavery, rec["id"], old_kidnapper_id, old_kidnapper_name)
                return await m.answer(
                    f"🏃 {display} сбежал из рабства {owner_name}!\n"
                    f"Теперь {display} снова в подвале у {old_kidnapper_name}.\n"
                    f"Используй /freed ещё раз чтобы сбежать окончательно (кд 30м)."
                )
            else:
                return await m.answer(
                    f"😢 {display} не смог сбежать из рабства {owner_name}!\n"
                    f"Следующая попытка через 30м."
                )

        # ════════════════════════════════════════════
        # ПОДВАЛ (sold=0)
        # ════════════════════════════════════════════
        kidnapper_name = rec.get("kidnapper_name", "?")

        # Шаг: снять наручники в подвале
        if rec["handcuffed"]:
            if random.randint(1, 100) <= 30:
                await db_task(_set_handcuffed, rec["id"], 0)
                return await m.answer(
                    f"⛓️ {display} снял наручники в подвале {kidnapper_name}!\n"
                    f"Теперь попробуй сбежать (/freed через 30м)"
                )
            else:
                return await m.answer(
                    f"⛓️ {display} не смог снять наручники в подвале {kidnapper_name}!\n"
                    f"Попробуй через 30м."
                )

        # Финальный побег из подвала
        if random.randint(1, 100) <= 30:
            await db_task(_free_kidnapped, rec["id"])
            await m.answer(f"🏃 {display} окончательно сбежал из подвала {kidnapper_name}! Свобода!")
        else:
            await m.answer(
                f"😢 {display} не смог сбежать из подвала {kidnapper_name}!\n"
                f"Следующая попытка через 30м."
            )
    except Exception as e:
        logger.error(f"/freed error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка побега")

# ─── /sell ────────────────────────────────────────────────────────────────────

@dp.message(Command("sell"))
async def cmd_sell(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id
        name = clean_nick(m.from_user.full_name)

        blocked, reason = await db_task(_is_blocked, uid, cid)
        if blocked:
            return await m.answer(reason)

        u = await db_task(_get_user, uid, cid, name)

        parts = m.text.split()
        if len(parts) < 2:
            return await m.answer(
                "⚠️ Использование: /sell <номер заложника> (ответом на игрока-покупателя)\n"
                "Пример: ответьте на сообщение покупателя и напишите /sell 1"
            )
        try:
            num = int(parts[1])
        except ValueError:
            return await m.answer("❌ Укажите номер")

        hostages = await db_task(_get_kidnapped_by_kidnapper, uid, cid)
        if not hostages or num < 1 or num > len(hostages):
            cnt = len(hostages) if hostages else 0
            return await m.answer(f"❌ Заложник #{num} не найден. У вас {cnt} заложник(ов) в подвале.")

        rec = hostages[num - 1]
        now = time.time()
        held = now - rec["kidnapped_at"]

        if held < 1800:
            return await m.answer(f"⏳ Ещё {format_time(1800 - held)} до продажи.")
        if rec["sold"] != 0:
            return await m.answer("❌ Уже продан или освобождён!")

        # Определяем покупателя
        if m.reply_to_message and m.reply_to_message.from_user.id != bot.id:
            buyer = m.reply_to_message.from_user
            buyer_id = buyer.id
            buyer_name = clean_nick(buyer.full_name)

            if buyer_id == uid:
                return await m.answer("❌ Нельзя продать самому себе!")
            if buyer_id == rec["victim_id"]:
                return await m.answer("❌ Нельзя продать жертве самой себе!")

            # Убеждаемся что покупатель зарегистрирован
            await db_task(_get_user, buyer_id, cid, buyer_name)
            await db_task(_upd_username, buyer_id, cid, buyer_name)
            b = await db_task(_get_user, buyer_id, cid, buyer_name)
            buyer_name = b.get("username") or buyer_name

            await db_task(_sell_kidnapped, rec["id"], buyer_id, buyer_name)

            seller_name = u.get("username") or name
            victim_name = rec["victim_name"]

            await m.answer(
                f"💰 {seller_name} продал {victim_name} в рабство {buyer_name}!\n"
                f"Доход {buyer_name}: 1🖤 каждые 2 часа.\n"
                f"Жертва может сбежать через /freed (сначала в подвал, потом на свободу)."
            )
            try:
                await bot.send_message(
                    cid,
                    f"😱 {victim_name} продан(а) в рабство к {buyer_name} за авторством {seller_name}!\n"
                    f"Используй /freed чтобы сбежать!\n"
                    f"Порядок побега:\n"
                    f"1️⃣ Снять наручники (если есть)\n"
                    f"2️⃣ Сбежать из рабства → подвал {seller_name}\n"
                    f"3️⃣ Сбежать из подвала → свобода!"
                )
            except Exception:
                pass
        else:
            return await m.answer(
                "⚠️ Чтобы продать, ответьте на сообщение игрока-покупателя!\n"
                "Пример: ответьте на сообщение покупателя и напишите /sell 1"
            )
    except Exception as e:
        logger.error(f"/sell error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка продажи")

# ─── /handcuff ────────────────────────────────────────────────────────────────

@dp.message(Command("handcuff"))
async def cmd_handcuff(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id
        name = clean_nick(m.from_user.full_name)

        blocked, reason = await db_task(_is_blocked, uid, cid)
        if blocked:
            return await m.answer(reason)

        u = await db_task(_get_user, uid, cid, name)
        if u["handcuffs"] <= 0:
            return await m.answer("⛓️ Нет наручников! Купи в /shop за 1🖤")

        # Ищем и в подвальных и в рабах
        hostages = await db_task(_get_kidnapped_by_kidnapper, uid, cid)
        slaves = await db_task(_get_slaves_by_owner, uid, cid)
        all_captives = hostages + slaves

        if not all_captives:
            return await m.answer("🔒 Нет заложников или рабов!")

        target_rec = None
        parts = m.text.split()

        if m.reply_to_message and m.reply_to_message.from_user.id != bot.id:
            tid = m.reply_to_message.from_user.id
            for h in all_captives:
                if h["victim_id"] == tid:
                    target_rec = h
                    break
            if not target_rec:
                return await m.answer("❌ Этот игрок не ваш заложник или раб!")
        elif len(parts) >= 2:
            try:
                num = int(parts[1])
            except ValueError:
                return await m.answer("❌ Укажите номер или ответьте на сообщение")
            if num < 1 or num > len(all_captives):
                return await m.answer(f"❌ Заключённый #{num} не найден")
            target_rec = all_captives[num - 1]
        else:
            lines = ["⛓️ Ваши заключённые:\n"]
            for i, h in enumerate(all_captives, 1):
                cuffs = " ⛓️" if h["handcuffed"] else ""
                status = "🔒 подвал" if h["sold"] == 0 else "😈 раб"
                lines.append(f"{i}. {h['victim_name']} [{status}]{cuffs}")
            lines.append("\nИспользование: /handcuff <номер> или ответом")
            return await m.answer("\n".join(lines))

        if target_rec["handcuffed"]:
            return await m.answer(f"⛓️ {target_rec['victim_name']} уже в наручниках!")

        await db_task(_set_handcuffed, target_rec["id"], 1)
        await async_upd(uid, cid, {"handcuffs": u["handcuffs"] - 1})
        uname = u.get("username") or name
        status_str = "раба" if target_rec["sold"] == 1 else "заложника"
        await m.answer(
            f"⛓️ {uname} надел наручники на {target_rec['victim_name']} ({status_str})!\n"
            f"Жертве нужно дополнительно использовать /freed для снятия наручников."
        )
    except Exception as e:
        logger.error(f"/handcuff error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка")

# ─── /trank ───────────────────────────────────────────────────────────────────

@dp.message(Command("trank"))
async def cmd_trank(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id
        name = clean_nick(m.from_user.full_name)

        await db_task(_get_user, uid, cid, name)
        await db_task(_upd_username, uid, cid, name)

        blocked, reason = await db_task(_is_blocked, uid, cid)
        if blocked:
            return await m.answer(reason)

        tranqed, t_left = await db_task(_is_tranquilized, uid, cid)
        if tranqed:
            return await m.answer(f"💉 Вы сами под транквилизатором! Осталось: {format_time(t_left)}")

        u = await db_task(_get_user, uid, cid, name)
        uname = u.get("username") or name

        if u.get("tranq_stock", 0) <= 0:
            return await m.answer("💉 Нет транквилизатора! Купи в /shop за 4🖤")

        if not m.reply_to_message:
            return await m.answer("⚠️ Ответьте на сообщение жертвы!")

        target = m.reply_to_message.from_user
        if target.id == uid:
            return await m.answer("🤡 Нельзя транквилизировать себя!")
        if target.id == bot.id:
            return await m.answer("🤖 Бота не транквилизируют!")

        tname = clean_nick(target.full_name)
        await db_task(_get_user, target.id, cid, tname)
        await db_task(_upd_username, target.id, cid, tname)
        t = await db_task(_get_user, target.id, cid, tname)
        target_name = t.get("username") or tname

        now = time.time()
        if t.get("tranq_until", 0) > now:
            return await m.answer(f"💉 {target_name} уже под транквилизатором!")

        tranq_end = now + 10800
        await async_upd(target.id, cid, {"tranq_until": tranq_end, "last_hp_update": now})
        await async_upd(uid, cid, {"tranq_stock": u["tranq_stock"] - 1})

        await m.answer(
            f"💉 {uname} вколол транквилизатор {target_name}!\n"
            f"Паралич на 3 часа. Реген остановлен.\n"
            f"Осталось транков: {u['tranq_stock'] - 1} шт."
        )
    except Exception as e:
        logger.error(f"/trank error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка")

# ─── /adren ───────────────────────────────────────────────────────────────────

@dp.message(Command("adren"))
async def cmd_adren(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id
        name = clean_nick(m.from_user.full_name)

        await db_task(_get_user, uid, cid, name)
        await db_task(_upd_username, uid, cid, name)
        u = await db_task(_get_user, uid, cid, name)
        uname = u.get("username") or name
        now = time.time()

        if u.get("adren_until", 0) > now:
            remaining = u["adren_until"] - now
            await m.answer(
                f"🔥 {uname}, адреналин активен!\n"
                f"Осталось: {format_time(remaining)}\n"
                f"КД удара сейчас: 15 минут"
            )
        else:
            await m.answer(
                f"🔥 {uname}, адреналин не активен.\n"
                f"Купи в /shop за 3🖤 — КД удара станет 15м на 3ч."
            )
    except Exception as e:
        logger.error(f"/adren error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка")

# ─── Фоновая задача: доход за рабство ─────────────────────────────────────────

async def income_loop():
    await asyncio.sleep(30)
    while True:
        try:
            now = time.time()
            conn = _db()
            try:
                c = conn.cursor()
                # Только активные рабы (sold=1)
                c.execute("SELECT * FROM kidnapped WHERE sold=1")
                rows = [dict(r) for r in c.fetchall()]
            finally:
                conn.close()

            for rec in rows:
                if now - rec["last_income"] >= 7200:
                    periods = int((now - rec["last_income"]) // 7200)
                    # Доход идёт slave_owner_id
                    owner_id = rec.get("slave_owner_id", 0)
                    owner_name = rec.get("slave_owner_name", "")
                    owner_cid = rec["chat_id"]

                    if owner_id and owner_id != 0:
                        kd = _get_user(owner_id, owner_cid, owner_name)
                        _upd_user(owner_id, owner_cid, {"black_money": kd["black_money"] + periods})
                        _upd_kidnapped_income(rec["id"], rec["last_income"] + periods * 7200)
                        try:
                            await bot.send_message(
                                owner_cid,
                                f"🖤 {owner_name} получил {periods}🖤 за раба {rec['victim_name']}!"
                            )
                        except Exception:
                            pass
        except Exception as e:
            logger.error(f"Income loop error: {e}", exc_info=True)
        await asyncio.sleep(300)

# ─── Main ──────────────────────────────────────────────────────────────────────

async def main():
    init_db()
    logger.info(f"БД: {DB_PATH}")
    await bot.set_my_commands([
        types.BotCommand(command="help",      description="Помощь"),
        types.BotCommand(command="stats",     description="Статы (или ответом — чужие)"),
        types.BotCommand(command="punch",     description="Ударить (ответом)"),
        types.BotCommand(command="job",       description="Работа +1💰"),
        types.BotCommand(command="sport",     description="Прокачка (кд 1.5ч)"),
        types.BotCommand(command="casino",    description="Казино: /casino 100"),
        types.BotCommand(command="casinotop", description="Топ казино чата"),
        types.BotCommand(command="shop",      description="Магазин"),
        types.BotCommand(command="hill",      description="Передать 1 HP (ответом)"),
        types.BotCommand(command="kidnap",    description="Похитить игрока с 0 HP"),
        types.BotCommand(command="freed",     description="Сбежать из подвала/рабства"),
        types.BotCommand(command="sell",      description="Продать заложника (ответом на покупателя)"),
        types.BotCommand(command="handcuff",  description="Надеть наручники на заложника/раба"),
        types.BotCommand(command="trank",     description="Транквилизатор (ответом)"),
        types.BotCommand(command="adren",     description="Статус адреналина"),
    ])
    asyncio.create_task(income_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"CRASH: {e}", exc_info=True)
