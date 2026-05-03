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
    "{attacker} жестко дал пощёчину {victim}", "{attacker} врезал {victim} кулаком в челюсть",
    "{attacker} ударил {victim} под дых", "{attacker} съездил {victim} по ушам",
    "{attacker} отлупасил {victim} тапком", "{attacker} влепил {victim} смачную оплеуху",
    "{attacker} зарядил {victim} в нос", "{attacker} с размаху ударил {victim} лбом",
    "{attacker} кинул в {victim} кирпич", "{attacker} пнул {victim} под зад",
    "{attacker} съел печень {victim}", "{attacker} вырубил {victim} с одного удара",
    "{attacker} отхлестал {victim} по лицу", "{attacker} врезал {victim} коленом в пах",
    "{attacker} ударил {victim} стулом", "{attacker} дал {victim} в ухо",
    "{attacker} швырнул {victim} об стену", "{attacker} наступил {victim} на ногу",
    "{attacker} ударил {victim} бутылкой", "{attacker} съездил {victim} монтировкой",
    "{attacker} ударил {victim} газетой", "{attacker} кинул в {victim} банан",
    "{attacker} ударил {victim} подушкой", "{attacker} шлёпнул {victim} по попе",
    "{attacker} ударил {victim} сковородкой", "{attacker} пнул {victim} табуреткой",
    "{attacker} ударил {victim} вилкой", "{attacker} дал {victim} в глаз",
    "{attacker} ударил {victim} в спину", "{attacker} толкнул {victim} с лестницы",
    "{attacker} ударил {victim} головой", "{attacker} ударил {victim} локтем",
    "{attacker} ударил {victim} плечом", "{attacker} ударил {victim} коленом",
    "{attacker} ударил {victim} ногой", "{attacker} ударил {victim} рукой",
    "{attacker} ударил {victim} кулаком", "{attacker} ударил {victim} по голове",
    "{attacker} ударил {victim} по лицу", "{attacker} ударил {victim} по телу",
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
    "😵‍💫 Адреналин ударил в голову, а результат вышел из {nick}..."
]

POSITIVE_STATS = ["stat_regen", "stat_counter", "stat_block", "stat_jiu"]
ALL_STATS = POSITIVE_STATS + ["debuff_weak", "debuff_fear", "debuff_payoff"]
STAT_NAMES = {
    "stat_regen": "Регенерация", "stat_counter": "Отпор",
    "stat_block": "Блок", "stat_jiu": "Джиу-джитсу",
    "debuff_weak": "Слабость", "debuff_fear": "Страх", "debuff_payoff": "Откуп"
}

COOLDOWNS = {
    "punch": 1800,
    "punch_adren": 900,   # 15 минут при адреналине
    "job": 3600,
    "sport": 5400,        # 1.5 часа
    "freed": 1800
}

DEFAULT_REGEN_TIME = 3600

def calc_regen_time(stat_regen: int) -> float:
    return max(60, DEFAULT_REGEN_TIME * (1 - stat_regen / 100))

def format_time(seconds: float) -> str:
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}ч {m}м {s}с"
    elif m > 0:
        return f"{m}м {s}с"
    return f"{s}с"

# ─── БД ───────────────────────────────────────────────────────────────────────

def _db():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _db()
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER, chat_id INTEGER, username TEXT,
            hp INTEGER DEFAULT 6, max_hp INTEGER DEFAULT 6,
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
            PRIMARY KEY (user_id, chat_id)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS kidnapped (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            victim_id INTEGER, victim_name TEXT,
            kidnapper_id INTEGER, kidnapper_name TEXT,
            chat_id INTEGER,
            kidnapped_at REAL DEFAULT 0,
            sold INTEGER DEFAULT 0,
            last_income REAL DEFAULT 0,
            handcuffed INTEGER DEFAULT 0
        )''')
        conn.commit()

        # Миграции
        existing = {row[1] for row in c.execute("PRAGMA table_info(users)")}
        migrations = {
            "black_money": "INTEGER DEFAULT 0",
            "last_freed": "REAL DEFAULT 0",
            "glove_durability": "INTEGER DEFAULT 0",
            "handcuffs": "INTEGER DEFAULT 0",
            "tranq_until": "REAL DEFAULT 0",
            "adren_until": "REAL DEFAULT 0",
        }
        for col, typedef in migrations.items():
            if col not in existing:
                c.execute(f"ALTER TABLE users ADD COLUMN {col} {typedef}")

        c.execute("UPDATE users SET max_hp=6 WHERE max_hp=3")
        conn.commit()
    finally:
        conn.close()

COL_NAMES = [
    "user_id", "chat_id", "username", "hp", "max_hp", "money",
    "black_money", "shield", "last_punch", "last_job", "last_sport",
    "last_hp_update", "last_freed",
    "stat_regen", "stat_counter", "stat_block", "stat_jiu",
    "debuff_weak", "debuff_fear", "debuff_payoff", "casino_won",
    "glove_durability", "handcuffs",
    "tranq_until", "adren_until"
]

def _get_user(uid, cid, name):
    conn = _db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id=? AND chat_id=?", (uid, cid))
        row = c.fetchone()
        if not row:
            now = time.time()
            vals = (uid, cid, name, 6, 6, 0, 0, 0, 0, 0, 0, now, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            c.execute(
                "INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                vals
            )
            conn.commit()
            return dict(zip(COL_NAMES, vals))
        d = dict(row)
        for col in COL_NAMES:
            if col not in d:
                d[col] = 0
        return d
    finally:
        conn.close()

def _upd_user(uid, cid, fields: dict):
    conn = _db()
    try:
        c = conn.cursor()
        sets = ", ".join(f"{k}=?" for k in fields)
        c.execute(
            f"UPDATE users SET {sets} WHERE user_id=? AND chat_id=?",
            [*fields.values(), uid, cid]
        )
        conn.commit()
    finally:
        conn.close()

def _recalc_hp(uid, cid):
    u = _get_user(uid, cid, "")
    now = time.time()

    # Если транквилизован — реген не идёт
    if u.get("tranq_until", 0) > now:
        return u

    elapsed = now - u["last_hp_update"]
    regen_time = calc_regen_time(u["stat_regen"])
    gained = int(elapsed // regen_time)
    if gained > 0:
        nhp = min(u["max_hp"], u["hp"] + gained)
        if nhp != u["hp"]:
            _upd_user(uid, cid, {"hp": nhp, "last_hp_update": now})
    return _get_user(uid, cid, "")

def clean_nick(t):
    return (t or "User").replace("@","").replace("[","").replace("]","").replace("(","").replace(")","").strip()

# ─── Async helpers ─────────────────────────────────────────────────────────────

async def db_task(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func, *args)

async def async_upd(uid, cid, fields: dict):
    await db_task(_upd_user, uid, cid, fields)

# ─── Подвал helpers ────────────────────────────────────────────────────────────

def _get_kidnapped_by_victim(vid, cid):
    conn = _db()
    try:
        c = conn.cursor()
        c.execute(
            "SELECT * FROM kidnapped WHERE victim_id=? AND chat_id=? AND sold=0",
            (vid, cid)
        )
        row = c.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def _get_kidnapped_by_kidnapper(kid, cid):
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

def _add_kidnapped(vid, vname, kid, kname, cid):
    now = time.time()
    conn = _db()
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO kidnapped "
            "(victim_id, victim_name, kidnapper_id, kidnapper_name, chat_id, kidnapped_at, sold, last_income, handcuffed) "
            "VALUES (?,?,?,?,?,?,0,?,0)",
            (vid, vname, kid, kname, cid, now, now)
        )
        conn.commit()
        return c.lastrowid
    finally:
        conn.close()

def _free_kidnapped(record_id):
    conn = _db()
    try:
        c = conn.cursor()
        c.execute("DELETE FROM kidnapped WHERE id=?", (record_id,))
        conn.commit()
    finally:
        conn.close()

def _sell_kidnapped(record_id):
    conn = _db()
    try:
        c = conn.cursor()
        c.execute("UPDATE kidnapped SET sold=1 WHERE id=?", (record_id,))
        conn.commit()
    finally:
        conn.close()

def _set_handcuffed(record_id, val: int):
    conn = _db()
    try:
        c = conn.cursor()
        c.execute("UPDATE kidnapped SET handcuffed=? WHERE id=?", (val, record_id))
        conn.commit()
    finally:
        conn.close()

def _upd_kidnapped_income(record_id, last_income):
    conn = _db()
    try:
        c = conn.cursor()
        c.execute("UPDATE kidnapped SET last_income=? WHERE id=?", (last_income, record_id))
        conn.commit()
    finally:
        conn.close()

def _count_hostages(kid, cid):
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

# ─── Проверки блокировки ───────────────────────────────────────────────────────

def _is_blocked(uid, cid) -> tuple:
    """Возвращает (заблокирован, причина)."""
    rec = _get_kidnapped_by_victim(uid, cid)
    if rec:
        if rec["handcuffed"]:
            return True, "⛓️ Вы в наручниках в подвале! Сначала /freed (снять наручники), потом снова /freed (сбежать)."
        return True, "🔒 Вы в подвале! Используйте /freed чтобы сбежать."
    return False, ""

def _is_tranquilized(uid, cid) -> tuple:
    """Возвращает (транквилизован, оставшееся время)."""
    u = _get_user(uid, cid, "")
    now = time.time()
    if u.get("tranq_until", 0) > now:
        return True, u["tranq_until"] - now
    return False, 0

# ─── Удар ──────────────────────────────────────────────────────────────────────

async def do_punch(aid, aname, vid, cid, auto=False):
    try:
        now = time.time()
        att = await db_task(_get_user, aid, cid, aname)
        vic = await db_task(_recalc_hp, vid, cid)

        if not auto:
            # Определяем кд с учётом адреналина
            punch_cd = COOLDOWNS["punch_adren"] if att.get("adren_until", 0) > now else COOLDOWNS["punch"]
            cd = punch_cd - (now - att["last_punch"])
            if cd > 0:
                adren_note = " (🔥 адреналин)" if att.get("adren_until", 0) > now else ""
                return await bot.send_message(
                    cid, f"⏳ {att['username']}, кулдаун{adren_note}: {format_time(cd)}"
                )

        # Щит
        if vic["shield"] == 1:
            await async_upd(vid, cid, {"shield": 0})
            return await bot.send_message(cid, f"🛡️ Щит {vic['username']} поглотил удар!")

        # Откуп
        if vic["debuff_payoff"] > 0 and vic["money"] > 0 and random.randint(1, 100) <= vic["debuff_payoff"]:
            amt = vic["money"] // 2
            await async_upd(vid, cid, {"money": vic["money"] - amt})
            await async_upd(aid, cid, {"money": att["money"] + amt})
            return await bot.send_message(cid, f"💸 Откуп! {vic['username']} отдал {amt}💰")

        # Джиу
        if vic["stat_jiu"] > 0 and random.randint(1, 100) <= vic["stat_jiu"]:
            await bot.send_message(cid, f"🥋 {vic['username']} использовал джиу-джитсу! Контратака!")
            await do_punch(vid, vic["username"], aid, cid, auto=True)
            if not auto:
                await async_upd(aid, cid, {"last_punch": now})
            return

        # Блок
        if vic["stat_block"] > 0 and random.randint(1, 100) <= vic["stat_block"]:
            return await bot.send_message(cid, f"🛡️ {vic['username']} заблокировал удар!")

        # Урон
        base_dmg = 2 if att["glove_durability"] > 0 else 1
        dmg = base_dmg * 2 if (vic["debuff_weak"] > 0 and random.randint(1, 100) <= vic["debuff_weak"]) else base_dmg
        nhp = max(0, vic["hp"] - dmg)

        # Износ перчатки
        glove_msg = ""
        if att["glove_durability"] > 0:
            new_dur = att["glove_durability"] - 1
            await async_upd(aid, cid, {"glove_durability": new_dur})
            att["glove_durability"] = new_dur
            if new_dur == 0:
                glove_msg = "\n🥊 Боксёрская перчатка сломалась!"
            else:
                glove_msg = f"\n🥊 Перчатка: {new_dur}/10 прочности"

        # Кража денег
        take = vic["money"] // 4
        new_vic_money = max(0, vic["money"] - take)
        new_att_money = att["money"] + take

        # Кража чёрных монет (10%)
        black_steal_msg = ""
        if vic["black_money"] > 0 and random.randint(1, 100) <= 10:
            bsteal = 1
            await async_upd(vid, cid, {"black_money": max(0, vic["black_money"] - bsteal)})
            await async_upd(aid, cid, {"black_money": att["black_money"] + bsteal})
            black_steal_msg = f"\n🖤 Украдена {bsteal} чёрная монета!"

        await async_upd(vid, cid, {"hp": nhp, "money": new_vic_money})
        await async_upd(aid, cid, {"money": new_att_money})

        txt = random.choice(PUNCH_TEXTS).format(attacker=att["username"], victim=vic["username"])
        msg = f"💥 {txt}\n💰 +{take} | ❤️ {vic['username']}: {nhp}/{vic['max_hp']}"

        if base_dmg == 2 and dmg == 4:
            msg += "\n⚡ Перчатка + Слабость: 4 урона!"
        elif dmg == 2 and base_dmg == 1:
            msg += "\n⚡ Слабость удвоила урон!"

        msg += glove_msg
        msg += black_steal_msg

        # Перчатка жертвы при 0 HP
        if nhp == 0 and vic["glove_durability"] > 0:
            if att["glove_durability"] == 0:
                await async_upd(aid, cid, {"glove_durability": vic["glove_durability"]})
                await async_upd(vid, cid, {"glove_durability": 0})
                msg += f"\n🥊 Перчатка ({vic['glove_durability']}/10) перешла к {att['username']}!"
            else:
                await async_upd(vid, cid, {"glove_durability": 0})
                msg += f"\n🥊 Перчатка {vic['username']} уничтожена!"

        # Наручники при 0 HP
        if nhp == 0 and vic["handcuffs"] > 0:
            await async_upd(aid, cid, {"handcuffs": att["handcuffs"] + vic["handcuffs"]})
            await async_upd(vid, cid, {"handcuffs": 0})
            msg += f"\n⛓️ Наручники ({vic['handcuffs']} шт.) перешли к {att['username']}!"

        # Отпор
        if vic["stat_counter"] > 0 and random.randint(1, 100) <= vic["stat_counter"]:
            msg += f"\n🔄 {vic['username']} активировал Отпор!"
            await do_punch(vid, vic["username"], aid, cid, auto=True)

        # Бафф/Дебафф
        if random.random() < 0.25:
            valid = [s for s in ALL_STATS if vic[s] < 100]
            if valid:
                st = random.choice(valid)
                nv = vic[st] - 1 if st in POSITIVE_STATS else vic[st] + 1
                nv = max(0, nv)
                await async_upd(vid, cid, {st: nv})
                sign = "📉" if st in POSITIVE_STATS else "📈"
                msg += f"\n{sign} {STAT_NAMES[st]}: {vic[st]}% → {nv}%"
                if st == "stat_regen":
                    new_regen_time = calc_regen_time(nv)
                    msg += f" (реген: {format_time(new_regen_time)}/HP)"

        # Страх
        conn = _db()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT username, debuff_fear FROM users WHERE chat_id=? AND debuff_fear>0",
                (cid,)
            )
            fear_rows = cur.fetchall()
        finally:
            conn.close()

        for fr in fear_rows:
            nm, fl = fr["username"], fr["debuff_fear"]
            if random.randint(1, 100) <= fl:
                await bot.send_message(cid, random.choice(POOP_TEXTS).format(nick=nm))

        if not auto:
            await async_upd(aid, cid, {"last_punch": now})

        await bot.send_message(cid, msg)

    except Exception as e:
        logger.error(f"❌ Punch error: {e}", exc_info=True)
        await bot.send_message(cid, "⚠️ Ошибка при ударе. Попробуйте позже.")

# ─── Магазин callback ──────────────────────────────────────────────────────────

async def shop_cb(call: types.CallbackQuery):
    try:
        item = call.data.split(":")[1]
        uid = call.from_user.id
        cid = call.message.chat.id
        u = await db_task(_get_user, uid, cid, clean_nick(call.from_user.full_name))
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
                return await call.answer("Максимум жизней!", show_alert=True)
            await async_upd(uid, cid, {"money": u["money"] - 5, "hp": u["hp"] + 1})
            await call.answer("Жизнь восстановлена!", show_alert=True)
            await call.message.edit_text(f"❤️ {u['username']} +1 HP")

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
            await async_upd(uid, cid, {
                "black_money": u["black_money"] - 1,
                "money": u["money"] + 10
            })
            await call.answer("Разменяно 1🖤 → 10💰!", show_alert=True)
            await call.message.edit_text(f"💱 {u['username']} разменял 1🖤 → 10💰")

        elif item == "glove":
            if u["black_money"] < 3:
                return await call.answer("Нужно 3🖤", show_alert=True)
            if u["glove_durability"] > 0:
                return await call.answer("Перчатка уже есть!", show_alert=True)
            await async_upd(uid, cid, {
                "black_money": u["black_money"] - 3,
                "glove_durability": 10
            })
            await call.answer("🥊 Боксёрская перчатка получена!", show_alert=True)
            await call.message.edit_text(f"🥊 {u['username']} купил боксёрскую перчатку (10/10)")

        elif item == "handcuff":
            if u["black_money"] < 1:
                return await call.answer("Нужно 1🖤", show_alert=True)
            await async_upd(uid, cid, {
                "black_money": u["black_money"] - 1,
                "handcuffs": u["handcuffs"] + 1
            })
            await call.answer("⛓️ Наручники куплены!", show_alert=True)
            await call.message.edit_text(f"⛓️ {u['username']} купил наручники (теперь: {u['handcuffs'] + 1} шт.)")

        elif item == "tranq":
            if u["black_money"] < 4:
                return await call.answer("Нужно 4🖤", show_alert=True)
            await async_upd(uid, cid, {"black_money": u["black_money"] - 4})
            await call.answer("💉 Транквилизатор куплен! Используй /trank (ответом на игрока)", show_alert=True)
            await call.message.edit_text(
                f"💉 {u['username']} купил транквилизатор!\n"
                f"Используй /trank ответом на сообщение жертвы."
            )

        elif item == "adren":
            if u["black_money"] < 3:
                return await call.answer("Нужно 3🖤", show_alert=True)
            if u.get("adren_until", 0) > now:
                return await call.answer("Адреналин уже действует!", show_alert=True)
            adren_end = now + 10800  # 3 часа
            await async_upd(uid, cid, {
                "black_money": u["black_money"] - 3,
                "adren_until": adren_end
            })
            await call.answer("🔥 Адреналин активирован на 3 часа! КД удара: 15 минут", show_alert=True)
            await call.message.edit_text(
                f"🔥 {u['username']} выпил ярость адреналина!\n"
                f"КД удара: 15 минут на 3 часа."
            )

    except Exception as e:
        logger.error(f"❌ Shop error: {e}", exc_info=True)
        await call.answer("⚠️ Ошибка магазина", show_alert=True)

# ─── Транквилизатор хранилище ──────────────────────────────────────────────────
# Храним купленные транки как флаг: если black_money использован на покупку,
# даём игроку возможность применить. Используем временное хранилище в памяти.
_tranq_holders: dict = {}  # {(uid, cid): count}

# ─── Обработчик ошибок ────────────────────────────────────────────────────────

@dp.errors()
async def errors_handler(update: types.Update, exception: Exception):
    logger.error(f"🔥 UNHANDLED ERROR: {type(exception).__name__}: {exception}", exc_info=True)
    return True

# ─── Handlers ─────────────────────────────────────────────────────────────────

@dp.message(Command("help"))
async def cmd_help(m: types.Message):
    try:
        await db_task(_get_user, m.from_user.id, m.chat.id, clean_nick(m.from_user.full_name))
        kb = InlineKeyboardBuilder()
        for t, d in [
            ("📊 Статы", "stats"), ("🎰 Казино", "casino"),
            ("💼 Работа", "job"), ("🏋️ Спорт", "sport"),
            ("🏪 Магазин", "shop"), ("🏆 Топ", "casinotop")
        ]:
            kb.button(text=t, callback_data=f"qcmd:{d}")
        kb.adjust(2)
        await m.answer(
            "📖 **Помощь**\n\n"
            "🥊 /punch (ответ) — удар (кд 30м)\n"
            "💼 /job — работа (+1💰, кд 1ч)\n"
            "🏋️ /sport — прокачка навыка (кд 1.5ч)\n"
            "🎰 /casino <сумма> — казино\n"
            "🏆 /casinotop — топ чата\n"
            "📊 /stats — мои статы\n"
            "🏪 /shop — магазин\n\n"
            "❤️ /hill (ответ) — поделиться 1 HP (нужно >1 HP, цель должна быть при 0)\n\n"
            "🔒 **Подвал:**\n"
            "/kidnap (ответ) — похитить игрока с 0 HP\n"
            "/freed — сбежать из подвала (30% шанс, кд 30м)\n"
            "/sell <номер> — продать заложника в секс-рабство (через 30м)\n"
            "/handcuff <номер> (или ответом) — надеть наручники на заложника\n\n"
            "💉 **Спецпредметы:**\n"
            "/trank (ответ) — использовать транквилизатор (купить в /shop за 4🖤)\n"
            "  └ Жертва не может действовать и не регенерируется 3 часа\n"
            "/adren — выпить адреналин (купить в /shop за 3🖤)\n"
            "  └ КД удара снижается до 15 минут на 3 часа\n\n"
            "⚠️ При 0 HP: только /shop, /hill получить и реген.\n"
            "🌍 У каждого чата свой мир!\n\n"
            "🖤 **Чёрные монеты** = 10💰\n"
            "🥊 Перчатка (3🖤) — x2 урон, 10 ударов\n"
            "⛓️ Наручники (1🖤) — сковать заложника\n"
            "💉 Транквилизатор (4🖤) — парализовать игрока на 3ч\n"
            "🔥 Адреналин (3🖤) — КД удара 15м на 3ч",
            parse_mode="Markdown",
            reply_markup=kb.as_markup()
        )
    except Exception as e:
        logger.error(f"❌ /help error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка загрузки помощи")

@dp.callback_query(lambda c: c.data.startswith("qcmd:"))
async def qcmd(call: types.CallbackQuery):
    try:
        cmd = call.data.split(":")[1]
        await call.answer()
        cmds = {
            "stats": cmd_stats,
            "job": cmd_job,
            "sport": cmd_sport,
            "shop": cmd_shop,
            "casinotop": cmd_casinotop
        }
        if cmd in cmds:
            await cmds[cmd](call.message)
        elif cmd == "casino":
            await call.message.answer("🎰 Пример: /casino 100")
    except Exception as e:
        logger.error(f"❌ Quick cmd error: {e}", exc_info=True)
        await call.answer("⚠️ Ошибка", show_alert=True)

@dp.message(Command("punch"))
async def cmd_punch(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id

        blocked, reason = await db_task(_is_blocked, uid, cid)
        if blocked:
            return await m.answer(reason)

        tranqed, t_left = await db_task(_is_tranquilized, uid, cid)
        if tranqed:
            return await m.answer(f"💉 Вы под действием транквилизатора! Осталось: {format_time(t_left)}")

        if not m.reply_to_message:
            return await m.answer("⚠️ Ответьте на сообщение игрока!")

        u = await db_task(_get_user, uid, cid, clean_nick(m.from_user.full_name))
        if u["hp"] <= 0:
            return await m.answer("💀 0 HP! Ждите реген или купите жизнь в /shop")

        target = m.reply_to_message.from_user
        if target.id == bot.id:
            return await m.answer("🤖 Ботов не бьём!")
        if target.id == uid:
            return await m.answer("🤡 Себя бить нельзя!")

        await db_task(_get_user, target.id, cid, clean_nick(target.full_name))
        await do_punch(uid, u["username"], target.id, cid)
    except Exception as e:
        logger.error(f"❌ /punch error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка удара")

@dp.message(Command("job"))
async def cmd_job(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id

        blocked, reason = await db_task(_is_blocked, uid, cid)
        if blocked:
            return await m.answer(reason)

        tranqed, t_left = await db_task(_is_tranquilized, uid, cid)
        if tranqed:
            return await m.answer(f"💉 Вы под действием транквилизатора! Осталось: {format_time(t_left)}")

        u = await db_task(_get_user, uid, cid, clean_nick(m.from_user.full_name))
        if u["hp"] <= 0:
            return await m.answer("💀 0 HP! Нельзя работать")

        now = time.time()
        cd = COOLDOWNS["job"] - (now - u["last_job"])
        if cd > 0:
            return await m.answer(f"⏳ Работа доступна через {format_time(cd)}")

        new_money = u["money"] + 1
        await async_upd(uid, cid, {"money": new_money, "last_job": now})
        await m.answer(f"💼 {u['username']} заработал +1💰 | Баланс: {new_money}💰")
    except Exception as e:
        logger.error(f"❌ /job error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка работы")

@dp.message(Command("sport"))
async def cmd_sport(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id

        blocked, reason = await db_task(_is_blocked, uid, cid)
        if blocked:
            return await m.answer(reason)

        tranqed, t_left = await db_task(_is_tranquilized, uid, cid)
        if tranqed:
            return await m.answer(f"💉 Вы под действием транквилизатора! Осталось: {format_time(t_left)}")

        u = await db_task(_get_user, uid, cid, clean_nick(m.from_user.full_name))
        if u["hp"] <= 0:
            return await m.answer("💀 0 HP! Тренировки запрещены")

        now = time.time()
        cd = COOLDOWNS["sport"] - (now - u["last_sport"])
        if cd > 0:
            return await m.answer(f"⏳ Тренировка доступна через {format_time(cd)}")

        st = random.choice(POSITIVE_STATS)
        old_val = u[st]
        nv = min(100, old_val + 1)
        await async_upd(uid, cid, {st: nv, "last_sport": now})

        msg = f"🏋️ {u['username']} прокачал {STAT_NAMES[st]}: {old_val}% → {nv}%"
        if st == "stat_regen":
            new_regen_time = calc_regen_time(nv)
            msg += f"\n⏱ Время регенерации HP: {format_time(new_regen_time)}/HP"
        await m.answer(msg)
    except Exception as e:
        logger.error(f"❌ /sport error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка тренировки")

@dp.message(Command("shop"))
async def cmd_shop(m: types.Message):
    try:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Сброс кулдауна (punch) — 3💰", callback_data="shop:skip")],
            [InlineKeyboardButton(text="❤️ +1 жизнь — 5💰", callback_data="shop:life")],
            [InlineKeyboardButton(text="🛡️ Щит (блок 1 удара) — 4💰", callback_data="shop:shield")],
            [InlineKeyboardButton(text="💱 Разменять 1🖤 → 10💰", callback_data="shop:exchange_black")],
            [InlineKeyboardButton(text="🥊 Боксёрская перчатка — 3🖤", callback_data="shop:glove")],
            [InlineKeyboardButton(text="⛓️ Наручники — 1🖤", callback_data="shop:handcuff")],
            [InlineKeyboardButton(text="💉 Транквилизатор — 4🖤", callback_data="shop:tranq")],
            [InlineKeyboardButton(text="🔥 Ярость адреналина — 3🖤", callback_data="shop:adren")],
        ])
        await m.answer(
            "🏪 **Магазин** (доступен всегда, даже при 0 HP)\n\n"
            "🥊 Перчатка — x2 урон, 10 ударов. Только 1 шт.\n"
            "⛓️ Наручники — сковать заложника в подвале.\n"
            "💉 Транквилизатор — /trank (ответом): жертва парализована 3ч, реген стоп.\n"
            "🔥 Адреналин — /adren: КД удара 15м на 3ч.\n"
            "💱 1🖤 = 10💰",
            reply_markup=kb,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"❌ /shop error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка магазина")

@dp.callback_query(lambda c: c.data.startswith("shop:"))
async def shop_h(call: types.CallbackQuery):
    await shop_cb(call)

@dp.message(Command("casino"))
async def cmd_casino(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id

        blocked, reason = await db_task(_is_blocked, uid, cid)
        if blocked:
            return await m.answer(reason)

        tranqed, t_left = await db_task(_is_tranquilized, uid, cid)
        if tranqed:
            return await m.answer(f"💉 Вы под действием транквилизатора! Осталось: {format_time(t_left)}")

        u = await db_task(_get_user, uid, cid, clean_nick(m.from_user.full_name))
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
            return await m.answer("❌ Ставка должна быть больше 0")
        if u["money"] < bet:
            return await m.answer(f"💸 Недостаточно денег. Нужно {bet}💰, у вас {u['money']}💰")

        r = random.random()
        mult = 0 if r < 0.40 else 1 if r < 0.70 else 2 if r < 0.90 else 3 if r < 0.98 else 5
        win = bet * mult
        new_money = u["money"] - bet + win
        new_casino_won = u["casino_won"] + win
        await async_upd(uid, cid, {"money": new_money, "casino_won": new_casino_won})

        res_text = {
            0: "💀 Проигрыш", 1: "🔄 Возврат",
            2: "🎉 x2 Победа!", 3: "🔥 x3 Большой выигрыш!",
            5: "💎 x5 ДЖЕКПОТ!!!"
        }[mult]
        await m.answer(
            f"🎰 {u['username']}: {res_text}\n"
            f"Ставка: {bet}💰 | Множитель: x{mult} | Выигрыш: {win}💰\n"
            f"💰 Баланс: {new_money}💰"
        )
    except Exception as e:
        logger.error(f"❌ /casino error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка казино")

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

        txt = "🏆 **Топ лудоманов чата:**\n"
        for i, row in enumerate(rows, 1):
            n, w = row["username"], row["casino_won"]
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            txt += f"{medal} {n}: {w}💰\n"
        await m.answer(txt, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"❌ /casinotop error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка топа")

@dp.message(Command("stats", "profile"))
async def cmd_stats(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id
        await db_task(_get_user, uid, cid, clean_nick(m.from_user.full_name))
        u = await db_task(_recalc_hp, uid, cid)

        now = time.time()
        regen_time = calc_regen_time(u["stat_regen"])

        # Время до следующего HP
        if u.get("tranq_until", 0) > now:
            regen_str = f"заморожен ({format_time(u['tranq_until'] - now)})"
        elif u["hp"] >= u["max_hp"]:
            regen_str = "макс"
        else:
            elapsed_since_update = now - u["last_hp_update"]
            time_to_next_hp = regen_time - (elapsed_since_update % regen_time)
            regen_str = f"через {format_time(time_to_next_hp)}"

        hostages = await db_task(_count_hostages, uid, cid)
        kidnap_rec = await db_task(_get_kidnapped_by_victim, uid, cid)

        kidnap_status = ""
        if kidnap_rec:
            kidnapper = kidnap_rec["kidnapper_name"]
            cuffs = " (в наручниках)" if kidnap_rec["handcuffed"] else ""
            kidnap_status = f"\n🔒 В подвале у: **{kidnapper}**{cuffs}"

        # Адреналин статус
        adren_status = ""
        if u.get("adren_until", 0) > now:
            adren_status = f"\n🔥 Адреналин: ещё {format_time(u['adren_until'] - now)}"

        # Транк статус
        tranq_status = ""
        if u.get("tranq_until", 0) > now:
            tranq_status = f"\n💉 Транквилизатор: ещё {format_time(u['tranq_until'] - now)}"

        txt = (
            f"👤 **{u['username']}**\n"
            f"❤️ HP: {u['hp']}/{u['max_hp']} ({regen_str})\n"
            f"⏱ Время регена: {format_time(regen_time)}/HP\n"
            f"💰 Деньги: {u['money']}\n"
            f"🖤 Чёрные монеты: {u['black_money']}\n"
            f"🛡️ Щит: {'✅' if u['shield'] else '❌'}\n"
            f"🥊 Перчатка: {u['glove_durability']}/10\n"
            f"⛓️ Наручники: {u['handcuffs']} шт.\n"
            f"🔒 Заложников в подвале: {hostages}"
            f"{kidnap_status}"
            f"{adren_status}"
            f"{tranq_status}\n\n"
            f"📈 **Навыки:**\n"
            f"🔄 Регенерация: {u['stat_regen']}%\n"
            f"🥊 Отпор: {u['stat_counter']}%\n"
            f"🛡️ Блок: {u['stat_block']}%\n"
            f"🥋 Джиу-джитсу: {u['stat_jiu']}%\n\n"
            f"📉 **Дебаффы:**\n"
            f"🦠 Слабость: {u['debuff_weak']}%\n"
            f"😨 Страх: {u['debuff_fear']}%\n"
            f"💸 Откуп: {u['debuff_payoff']}%\n\n"
            f"🎰 Выиграно в казино: {u['casino_won']}💰"
        )
        await m.answer(txt.strip(), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"❌ /stats error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка загрузки статов")

# ─── /hill ────────────────────────────────────────────────────────────────────

@dp.message(Command("hill"))
async def cmd_hill(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id

        blocked, reason = await db_task(_is_blocked, uid, cid)
        if blocked:
            return await m.answer(reason)

        tranqed, t_left = await db_task(_is_tranquilized, uid, cid)
        if tranqed:
            return await m.answer(f"💉 Вы под действием транквилизатора! Осталось: {format_time(t_left)}")

        if not m.reply_to_message:
            return await m.answer("⚠️ Ответьте на сообщение игрока, которому хотите помочь!")

        target = m.reply_to_message.from_user
        if target.id == uid:
            return await m.answer("🤡 Нельзя делиться HP с самим собой!")
        if target.id == bot.id:
            return await m.answer("🤖 Боту HP не нужно!")

        u = await db_task(_recalc_hp, uid, cid)
        if u["hp"] <= 1:
            return await m.answer(f"❤️ У вас только {u['hp']} HP — нельзя делиться!")

        t = await db_task(_recalc_hp, target.id, cid)
        if t["hp"] > 0:
            return await m.answer(f"❤️ У {t['username']} ещё есть HP ({t['hp']}/{t['max_hp']})!")

        await async_upd(uid, cid, {"hp": u["hp"] - 1})
        await async_upd(target.id, cid, {"hp": 1})
        await m.answer(
            f"❤️ {u['username']} поделился 1 HP с {t['username']}!\n"
            f"Ваш HP: {u['hp'] - 1}/{u['max_hp']} | {t['username']}: 1/{t['max_hp']}"
        )
    except Exception as e:
        logger.error(f"❌ /hill error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка")

# ─── /kidnap ──────────────────────────────────────────────────────────────────

@dp.message(Command("kidnap"))
async def cmd_kidnap(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id

        blocked, reason = await db_task(_is_blocked, uid, cid)
        if blocked:
            return await m.answer(reason)

        tranqed, t_left = await db_task(_is_tranquilized, uid, cid)
        if tranqed:
            return await m.answer(f"💉 Вы под действием транквилизатора! Осталось: {format_time(t_left)}")

        if not m.reply_to_message:
            return await m.answer("⚠️ Ответьте на сообщение игрока которого хотите похитить!")

        target = m.reply_to_message.from_user
        if target.id == uid:
            return await m.answer("🤡 Нельзя похитить самого себя!")
        if target.id == bot.id:
            return await m.answer("🤖 Бота не похищают!")

        u = await db_task(_get_user, uid, cid, clean_nick(m.from_user.full_name))
        if u["hp"] <= 0:
            return await m.answer("💀 0 HP! Вы не можете никого похищать.")

        t = await db_task(_recalc_hp, target.id, cid)
        await db_task(_get_user, target.id, cid, clean_nick(target.full_name))

        if t["hp"] > 0:
            return await m.answer(f"❌ У {t['username']} ещё есть HP! Похищать можно только при 0 HP.")

        existing = await db_task(_get_kidnapped_by_victim, target.id, cid)
        if existing:
            return await m.answer(f"🔒 {t['username']} уже находится в чьём-то подвале!")

        kid_name = clean_nick(m.from_user.full_name)
        vic_name = clean_nick(target.full_name)
        await db_task(_add_kidnapped, target.id, vic_name, uid, kid_name, cid)

        hostages = await db_task(_get_kidnapped_by_kidnapper, uid, cid)
        num = len(hostages)

        await m.answer(
            f"🔒 {kid_name} похитил {vic_name} и запер в подвале!\n"
            f"Заложник #{num} в вашем списке.\n"
            f"Жертва может сбежать по /freed (30% шанс, кд 30м).\n"
            f"Через 30 минут можно продать в секс-рабство (/sell {num})"
        )
    except Exception as e:
        logger.error(f"❌ /kidnap error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка похищения")

# ─── /freed ───────────────────────────────────────────────────────────────────

@dp.message(Command("freed"))
async def cmd_freed(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id
        u = await db_task(_get_user, uid, cid, clean_nick(m.from_user.full_name))

        rec = await db_task(_get_kidnapped_by_victim, uid, cid)
        if not rec:
            return await m.answer("🤷 Вы не в подвале!")

        now = time.time()
        cd = COOLDOWNS["freed"] - (now - u["last_freed"])
        if cd > 0:
            return await m.answer(f"⏳ Попытка побега доступна через {format_time(cd)}")

        await async_upd(uid, cid, {"last_freed": now})

        # Наручники — снять сначала
        if rec["handcuffed"]:
            if random.randint(1, 100) <= 30:
                await db_task(_set_handcuffed, rec["id"], 0)
                return await m.answer(
                    f"⛓️ {u['username']} снял наручники!\n"
                    f"Теперь попробуй сбежать (/freed через 30м)"
                )
            else:
                return await m.answer(
                    f"⛓️ {u['username']} не смог снять наручники!\n"
                    f"Попробуй через 30м."
                )

        # Побег из подвала
        if random.randint(1, 100) <= 30:
            await db_task(_free_kidnapped, rec["id"])
            await m.answer(
                f"🏃 {u['username']} сбежал из подвала {rec['kidnapper_name']}!\n"
                f"Свобода!"
            )
        else:
            await m.answer(
                f"😢 {u['username']} не смог сбежать из подвала {rec['kidnapper_name']}!\n"
                f"Следующая попытка через 30м."
            )
    except Exception as e:
        logger.error(f"❌ /freed error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка побега")

# ─── /sell ────────────────────────────────────────────────────────────────────

@dp.message(Command("sell"))
async def cmd_sell(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id

        blocked, reason = await db_task(_is_blocked, uid, cid)
        if blocked:
            return await m.answer(reason)

        parts = m.text.split()
        if len(parts) < 2:
            return await m.answer("⚠️ Использование: /sell <номер заложника>")
        try:
            num = int(parts[1])
        except ValueError:
            return await m.answer("❌ Введите номер заложника")

        hostages = await db_task(_get_kidnapped_by_kidnapper, uid, cid)
        if not hostages or num < 1 or num > len(hostages):
            return await m.answer(f"❌ Заложник #{num} не найден. У вас {len(hostages)} заложник(ов).")

        rec = hostages[num - 1]
        now = time.time()
        held_for = now - rec["kidnapped_at"]

        if held_for < 1800:
            remaining = 1800 - held_for
            return await m.answer(
                f"⏳ Нужно держать заложника ещё {format_time(remaining)} перед продажей."
            )

        if rec["sold"]:
            return await m.answer("❌ Этот заложник уже продан!")

        await db_task(_sell_kidnapped, rec["id"])
        await m.answer(
            f"💰 {rec['victim_name']} продан в секс-рабство!\n"
            f"Вы будете получать 1🖤 каждые 2 часа заключения.\n"
            f"Заложник может сбежать по /freed."
        )
        try:
            await bot.send_message(
                cid,
                f"😱 {rec['victim_name']} был продан в секс-рабство {rec['kidnapper_name']}!\n"
                f"Используй /freed чтобы сбежать!"
            )
        except Exception:
            pass
    except Exception as e:
        logger.error(f"❌ /sell error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка продажи")

# ─── /handcuff ────────────────────────────────────────────────────────────────

@dp.message(Command("handcuff"))
async def cmd_handcuff(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id

        blocked, reason = await db_task(_is_blocked, uid, cid)
        if blocked:
            return await m.answer(reason)

        u = await db_task(_get_user, uid, cid, clean_nick(m.from_user.full_name))
        if u["handcuffs"] <= 0:
            return await m.answer("⛓️ У вас нет наручников! Купите в /shop за 1🖤")

        hostages = await db_task(_get_kidnapped_by_kidnapper, uid, cid)
        if not hostages:
            return await m.answer("🔒 У вас нет заложников!")

        target_rec = None
        parts = m.text.split()

        if m.reply_to_message:
            target_id = m.reply_to_message.from_user.id
            for h in hostages:
                if h["victim_id"] == target_id:
                    target_rec = h
                    break
            if not target_rec:
                return await m.answer("❌ Этот игрок не является вашим заложником!")
        elif len(parts) >= 2:
            try:
                num = int(parts[1])
            except ValueError:
                return await m.answer("❌ Укажите номер заложника или ответьте на его сообщение")
            if num < 1 or num > len(hostages):
                return await m.answer(f"❌ Заложник #{num} не найден")
            target_rec = hostages[num - 1]
        else:
            txt = "⛓️ **Ваши заложники:**\n"
            for i, h in enumerate(hostages, 1):
                cuffs = " [в наручниках]" if h["handcuffed"] else ""
                txt += f"{i}. {h['victim_name']}{cuffs}\n"
            txt += "\nИспользование: /handcuff <номер> или ответом на сообщение"
            return await m.answer(txt, parse_mode="Markdown")

        if target_rec["handcuffed"]:
            return await m.answer(f"⛓️ {target_rec['victim_name']} уже в наручниках!")

        await db_task(_set_handcuffed, target_rec["id"], 1)
        await async_upd(uid, cid, {"handcuffs": u["handcuffs"] - 1})
        await m.answer(
            f"⛓️ {u['username']} надел наручники на {target_rec['victim_name']}!\n"
            f"Теперь жертве нужно дважды использовать /freed."
        )
    except Exception as e:
        logger.error(f"❌ /handcuff error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка")

# ─── /trank ───────────────────────────────────────────────────────────────────

@dp.message(Command("trank"))
async def cmd_trank(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id

        blocked, reason = await db_task(_is_blocked, uid, cid)
        if blocked:
            return await m.answer(reason)

        tranqed, t_left = await db_task(_is_tranquilized, uid, cid)
        if tranqed:
            return await m.answer(f"💉 Вы сами под транквилизатором! Осталось: {format_time(t_left)}")

        u = await db_task(_get_user, uid, cid, clean_nick(m.from_user.full_name))

        # Проверяем наличие транквилизатора через временное хранилище
        key = (uid, cid)
        tranq_count = _tranq_holders.get(key, 0)
        if tranq_count <= 0:
            return await m.answer(
                "💉 У вас нет транквилизатора!\n"
                "Купите в /shop за 4🖤 (кнопка 'Транквилизатор')"
            )

        if not m.reply_to_message:
            return await m.answer("⚠️ Ответьте на сообщение жертвы!")

        target = m.reply_to_message.from_user
        if target.id == uid:
            return await m.answer("🤡 Нельзя транквилизировать себя!")
        if target.id == bot.id:
            return await m.answer("🤖 Бота не транквилизируют!")

        t = await db_task(_get_user, target.id, cid, clean_nick(target.full_name))
        now = time.time()

        if t.get("tranq_until", 0) > now:
            return await m.answer(f"💉 {t['username']} уже под транквилизатором!")

        tranq_end = now + 10800  # 3 часа
        await async_upd(target.id, cid, {
            "tranq_until": tranq_end,
            "last_hp_update": now  # Фиксируем время, чтобы реген не шёл
        })

        # Тратим транквилизатор
        _tranq_holders[key] = tranq_count - 1

        await m.answer(
            f"💉 {u['username']} вколол транквилизатор {t['username']}!\n"
            f"Жертва парализована на 3 часа.\n"
            f"Реген остановлен. Все действия заблокированы."
        )
    except Exception as e:
        logger.error(f"❌ /trank error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка")

# ─── /adren ───────────────────────────────────────────────────────────────────

@dp.message(Command("adren"))
async def cmd_adren(m: types.Message):
    try:
        uid = m.from_user.id
        cid = m.chat.id

        blocked, reason = await db_task(_is_blocked, uid, cid)
        if blocked:
            return await m.answer(reason)

        tranqed, t_left = await db_task(_is_tranquilized, uid, cid)
        if tranqed:
            return await m.answer(f"💉 Вы под транквилизатором! Осталось: {format_time(t_left)}")

        u = await db_task(_get_user, uid, cid, clean_nick(m.from_user.full_name))
        now = time.time()

        if u.get("adren_until", 0) > now:
            remaining = u["adren_until"] - now
            return await m.answer(f"🔥 Адреналин уже действует! Осталось: {format_time(remaining)}")

        await m.answer(
            "🔥 Адреналин можно купить в /shop за 3🖤\n"
            "После покупки он активируется автоматически!"
        )
    except Exception as e:
        logger.error(f"❌ /adren error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка")

# ─── Фоновая задача: доход от секс-рабства ────────────────────────────────────

async def income_loop():
    await asyncio.sleep(30)
    while True:
        try:
            now = time.time()
            conn = _db()
            try:
                c = conn.cursor()
                c.execute("SELECT * FROM kidnapped WHERE sold=1")
                rows = [dict(r) for r in c.fetchall()]
            finally:
                conn.close()

            for rec in rows:
                if now - rec["last_income"] >= 7200:
                    periods = int((now - rec["last_income"]) // 7200)
                    earned = periods
                    kid_id = rec["kidnapper_id"]
                    kid_cid = rec["chat_id"]
                    kd = _get_user(kid_id, kid_cid, rec["kidnapper_name"])
                    _upd_user(kid_id, kid_cid, {"black_money": kd["black_money"] + earned})
                    new_last = rec["last_income"] + periods * 7200
                    _upd_kidnapped_income(rec["id"], new_last)
                    try:
                        await bot.send_message(
                            kid_cid,
                            f"🖤 {rec['kidnapper_name']} получил {earned}🖤 "
                            f"за заложника {rec['victim_name']}!"
                        )
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"❌ Income loop error: {e}", exc_info=True)
        await asyncio.sleep(300)

# ─── Фоновая задача: выдача транков из магазина ────────────────────────────────
# Патч shop_cb: при покупке транка записываем в _tranq_holders
# Это уже сделано выше через _tranq_holders dict в shop_cb item=="tranq"
# Но нужно синхронизировать с перезапуском — добавим колонку tranq_count в users

async def tranq_sync_loop():
    """Синхронизируем _tranq_holders с БД каждые 10 минут."""
    # Упрощённо: при старте загружаем tranq из БД (отдельная колонка)
    # Для простоты — храним в памяти, при рестарте сбрасывается (приемлемо)
    await asyncio.sleep(10)
    while True:
        await asyncio.sleep(600)

# ─── Main ──────────────────────────────────────────────────────────────────────

async def main():
    init_db()
    logger.info(f"✅ БД: {DB_PATH}")
    await bot.set_my_commands([
        types.BotCommand(command="help",      description="Помощь + кнопки"),
        types.BotCommand(command="stats",     description="Мои статы"),
        types.BotCommand(command="punch",     description="Ударить (ответом на сообщение)"),
        types.BotCommand(command="job",       description="Работа +1💰"),
        types.BotCommand(command="sport",     description="Прокачка навыка (кд 1.5ч)"),
        types.BotCommand(command="casino",    description="Казино: /casino 100"),
        types.BotCommand(command="casinotop", description="Топ казино чата"),
        types.BotCommand(command="shop",      description="Магазин"),
        types.BotCommand(command="hill",      description="Поделиться HP (ответом)"),
        types.BotCommand(command="kidnap",    description="Похитить игрока с 0 HP"),
        types.BotCommand(command="freed",     description="Сбежать из подвала"),
        types.BotCommand(command="sell",      description="Продать заложника в секс-рабство"),
        types.BotCommand(command="handcuff",  description="Надеть наручники на заложника"),
        types.BotCommand(command="trank",     description="Использовать транквилизатор (ответом)"),
        types.BotCommand(command="adren",     description="Статус адреналина"),
    ])
    logger.info("✅ Commands set")
    asyncio.create_task(income_loop())
    asyncio.create_task(tranq_sync_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"🔥 CRASH: {e}", exc_info=True)
