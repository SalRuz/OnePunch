import os
import random
import math
import time
import sqlite3
import asyncio
import logging
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# 🔑 Токен бота
BOT_TOKEN = "8183582932:AAEIas0VlMxWSDvOLap_y6cTsZ9yqicmhYc"

# 📂 Настройки путей
DATA_DIR = Path("/app/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "bot.db"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# 📜 Тексты для ударов (100 уникальных)
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
    "{attacker} ударил {victim} по рукам", "{attacker} ударил {victim} по ногам",
    "{attacker} ударил {victim} по спине", "{attacker} ударил {victim} по груди",
    "{attacker} ударил {victim} по животу", "{attacker} ударил {victim} по боку",    "{attacker} ударил {victim} по шее", "{attacker} ударил {victim} по подбородку",
    "{attacker} ударил {victim} по скуле", "{attacker} ударил {victim} по виску",
    "{attacker} ударил {victim} по лбу", "{attacker} ударил {victim} по затылку",
    "{attacker} ударил {victim} по уху", "{attacker} ударил {victim} по носу",
    "{attacker} ударил {victim} по губе", "{attacker} ударил {victim} по зубам",
    "{attacker} ударил {victim} по плечу", "{attacker} ударил {victim} по предплечью",
    "{attacker} ударил {victim} по локтю", "{attacker} ударил {victim} по запястью",
    "{attacker} ударил {victim} по кисти", "{attacker} ударил {victim} по пальцам",
    "{attacker} ударил {victim} по груди", "{attacker} ударил {victim} по рёбрам",
    "{attacker} ударил {victim} по животу", "{attacker} ударил {victim} по пояснице",
    "{attacker} ударил {victim} по тазу", "{attacker} ударил {victim} по бедру",
    "{attacker} ударил {victim} по колену", "{attacker} ударил {victim} по голени",
    "{attacker} ударил {victim} по лодыжке", "{attacker} ударил {victim} по стопе",
    "{attacker} ударил {victim} по пятке", "{attacker} ударил {victim} по носку",
    "{attacker} ударил {victim} по мизинцу", "{attacker} ударил {victim} по большому пальцу",
    "{attacker} ударил {victim} по указательному", "{attacker} ударил {victim} по среднему",
    "{attacker} ударил {victim} по безымянному", "{attacker} ударил {victim} по мизинцу",
    "{attacker} ударил {victim} по ладони", "{attacker} ударил {victim} по тыльной стороне",
    "{attacker} ударил {victim} по локтю", "{attacker} ударил {victim} по плечевому суставу",
    "{attacker} ударил {victim} по ключице", "{attacker} ударил {victim} по лопатке",
    "{attacker} ударил {victim} по позвоночнику", "{attacker} ударил {victim} по шее",
    "{attacker} ударил {victim} по кадыку", "{attacker} ударил {victim} по горлу",
    "{attacker} ударил {victim} по трахее", "{attacker} ударил {victim} по артерии",
    "{attacker} ударил {victim} по вене", "{attacker} ударил {victim} по капилляру",
    "{attacker} ударил {victim} по нерву", "{attacker} ударил {victim} по мышце",
    "{attacker} ударил {victim} по сухожилию", "{attacker} ударил {victim} по связке",
    "{attacker} ударил {victim} по хрящу", "{attacker} ударил {victim} по кости",
    "{attacker} ударил {victim} по коже", "{attacker} ударил {victim} по жировой ткани",
    "{attacker} ударил {victim} по волосам", "{attacker} ударил {victim} по ногтям",
    "{attacker} ударил {victim} по ресницам", "{attacker} ударил {victim} по бровям",
    "{attacker} ударил {victim} по щекам", "{attacker} ударил {victim} по лбу",
    "{attacker} ударил {victim} по затылку", "{attacker} ударил {victim} по макушке"
]

# 💩 10 вариаций текста «обосрался» (ВОССТАНОВЛЕНО)
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

COOLDOWNS = {"punch": 1800, "job": 3600, "sport": 7200}

# 🗄️ DB Helpers - БЕЗОПАСНАЯ работа с БД
def _get_db():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _get_db()
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER, chat_id INTEGER, username TEXT,
            hp INTEGER DEFAULT 3, max_hp INTEGER DEFAULT 3, money INTEGER DEFAULT 0,
            shield INTEGER DEFAULT 0, last_punch REAL DEFAULT 0, last_job REAL DEFAULT 0,
            last_sport REAL DEFAULT 0, last_hp_update REAL DEFAULT 0,
            stat_regen INTEGER DEFAULT 0, stat_counter INTEGER DEFAULT 0,
            stat_block INTEGER DEFAULT 0, stat_jiu INTEGER DEFAULT 0,
            debuff_weak INTEGER DEFAULT 0, debuff_fear INTEGER DEFAULT 0,
            debuff_payoff INTEGER DEFAULT 0, casino_won INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, chat_id)
        )''')
        conn.commit()
    finally:
        conn.close()

def _ensure_user(user_id, chat_id, username):
    conn = _get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id=? AND chat_id=?", (user_id, chat_id))
        row = c.fetchone()
        if not row:
            now = time.time()
            vals = (user_id, chat_id, username, 3, 3, 0, 0, 0, 0, 0, now, 0, 0, 0, 0, 0, 0, 0, 0)
            c.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", vals)
            conn.commit()
            return dict(zip([d[0] for d in c.description], vals))
        return dict(row)
    finally:
        conn.close()

def _update_user(user_id, chat_id, **kwargs):    
    conn = _get_db()
    try:
        c = conn.cursor()
        set_clause = ", ".join(f"{k}=?" for k in kwargs)
        vals = list(kwargs.values()) + [user_id, chat_id]
        c.execute(f"UPDATE users SET {set_clause} WHERE user_id=? AND chat_id=?", vals)
        conn.commit()
    finally:
        conn.close()

def _recalc_hp(user_id, chat_id):
    user = _ensure_user(user_id, chat_id, "")
    now = time.time()
    elapsed = now - user["last_hp_update"]
    regen_sec = max(60, 3600 * (1 - user["stat_regen"]/100))
    gained = int(elapsed // regen_sec)
    if gained > 0:
        new_hp = min(user["max_hp"], user["hp"] + gained)
        if new_hp != user["hp"]:
            _update_user(user_id, chat_id, hp=new_hp, last_hp_update=now)
    return _ensure_user(user_id, chat_id, "")

def clean_nick(text):
    if not text: return "User"
    return text.replace("@", "").replace("[", "").replace("]", "").replace("(", "").replace(")", "").strip()

async def get_user_ctx(message):
    loop = asyncio.get_running_loop()
    uid = message.from_user.id
    cid = message.chat.id
    name = clean_nick(message.from_user.full_name or message.from_user.first_name or "User")
    return await loop.run_in_executor(None, _ensure_user, uid, cid, name)

# 🥊 Combat
async def apply_punch(att_id, att_name, vic_id, chat_id, is_auto=False):
    loop = asyncio.get_running_loop()
    now = time.time()
    
    att = await loop.run_in_executor(None, _ensure_user, att_id, chat_id, att_name)
    vic = await loop.run_in_executor(None, _recalc_hp, vic_id, chat_id)

    if not is_auto:
        cd = COOLDOWNS["punch"] - (now - att["last_punch"])
        if cd > 0:
            return await bot.send_message(chat_id, f"⏳ {att['username']}, кулдаун: {int(cd//60)}м {int(cd%60)}с")

    # Щит
    if vic["shield"] == 1:
        await loop.run_in_executor(None, _update_user, vic_id, chat_id, shield=0)
        return await bot.send_message(chat_id, f"🛡️ Щит {vic['username']} поглотил удар!")
    # Откуп
    if vic["debuff_payoff"] > 0 and vic["money"] > 0 and random.randint(1,100) <= vic["debuff_payoff"]:
        amount = vic["money"] // 2
        await loop.run_in_executor(None, _update_user, vic_id, chat_id, money=vic["money"]-amount)
        await loop.run_in_executor(None, _update_user, att_id, chat_id, money=att["money"]+amount)
        return await bot.send_message(chat_id, f"💸 Откуп! {vic['username']} отдал {amount}💰")

    # Джиу-джитсу
    if vic["stat_jiu"] > 0 and random.randint(1,100) <= vic["stat_jiu"]:
        await bot.send_message(chat_id, f"🥋 {vic['username']} использовал джиу-джитсу! Контратака!")
        await apply_punch(vic_id, vic["username"], att_id, chat_id, is_auto=True)
        if not is_auto:
            await loop.run_in_executor(None, _update_user, att_id, chat_id, last_punch=now)
        return

    # Блок
    if vic["stat_block"] > 0 and random.randint(1,100) <= vic["stat_block"]:
        return await bot.send_message(chat_id, f"🛡️ {vic['username']} заблокировал удар!")

    # Урон
    dmg = 2 if (vic["debuff_weak"] > 0 and random.randint(1,100) <= vic["debuff_weak"]) else 1
    new_hp = max(0, vic["hp"] - dmg)
    take = vic["money"] // 4
    
    await loop.run_in_executor(None, _update_user, vic_id, chat_id, hp=new_hp, money=max(0, vic["money"]-take))
    await loop.run_in_executor(None, _update_user, att_id, chat_id, money=att["money"]+take)

    txt = random.choice(PUNCH_TEXTS).format(attacker=att["username"], victim=vic["username"])
    msg = f"💥 {txt}\n💰 +{take} | ❤️ {vic['username']}: {new_hp}/{vic['max_hp']}"
    if dmg == 2: msg += "\n⚡ Слабость удвоила урон!"

    # Отпор
    if vic["stat_counter"] > 0 and random.randint(1,100) <= vic["stat_counter"]:
        msg += f"\n🔄 {vic['username']} активировал Отпор!"
        await apply_punch(vic_id, vic["username"], att_id, chat_id, is_auto=True)

    # Бафф/Дебафф (гарантированно рандомно)
    if random.random() < 0.25:
        valid = [s for s in ALL_STATS if vic[s] < 100]
        if valid:
            stat = random.choice(valid)
            if stat in POSITIVE_STATS:
                nv = vic[stat] - 1
                await loop.run_in_executor(None, _update_user, vic_id, chat_id, **{stat: nv})
                msg += f"\n📉 {STAT_NAMES[stat]}: {vic[stat]}% → {nv}%"
            else:
                nv = vic[stat] + 1
                await loop.run_in_executor(None, _update_user, vic_id, chat_id, **{stat: nv})
                msg += f"\n📀 {STAT_NAMES[stat]}: {vic[stat]}% → {nv}%"
    # Страх (глобально в чате)
    conn = _get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT username, debuff_fear FROM users WHERE chat_id=? AND debuff_fear>0", (chat_id,))
        for uname, flvl in c.fetchall():
            if random.randint(1,100) <= flvl:
                await bot.send_message(chat_id, random.choice(POOP_TEXTS).format(nick=uname))
    finally:
        conn.close()

    if not is_auto:
        await loop.run_in_executor(None, _update_user, att_id, chat_id, last_punch=now)
    await bot.send_message(chat_id, msg)

# 🛒 Магазин
async def shop_cb(call: types.CallbackQuery):
    loop = asyncio.get_running_loop()
    item = call.data.split(":")[1]
    u = await loop.run_in_executor(None, _ensure_user, call.from_user.id, call.message.chat.id, clean_nick(call.from_user.full_name or "User"))
    now = time.time()

    if item == "skip":
        if u["money"] < 3: return await call.answer("Нужно 3💰", show_alert=True)
        await loop.run_in_executor(None, _update_user, u["user_id"], call.message.chat.id, money=u["money"]-3, last_punch=now-COOLDOWNS["punch"])
        await call.answer("Кулдаун сброшен!", show_alert=True)
        await call.message.edit_text(f"✅ {u['username']} купил сброс кулдауна")
    elif item == "life":
        if u["money"] < 5: return await call.answer("Нужно 5💰", show_alert=True)
        if u["hp"] >= 3: return await call.answer("Максимум жизней!", show_alert=True)
        await loop.run_in_executor(None, _update_user, u["user_id"], call.message.chat.id, money=u["money"]-5, hp=u["hp"]+1)
        await call.answer("Жизнь восстановлена!", show_alert=True)
        await call.message.edit_text(f"❤️ {u['username']} +1 HP")
    elif item == "shield":
        if u["money"] < 4: return await call.answer("Нужно 4💰", show_alert=True)
        if u["shield"] == 1: return await call.answer("Щит уже есть!", show_alert=True)
        await loop.run_in_executor(None, _update_user, u["user_id"], call.message.chat.id, money=u["money"]-4, shield=1)
        await call.answer("Щит получен!", show_alert=True)
        await call.message.edit_text(f"🛡️ {u['username']} купил щит")

# 📝 Handlers
@dp.message(Command("help"))
async def cmd_help(m: types.Message):
    await get_user_ctx(m)
    kb = InlineKeyboardBuilder()
    for t, d in [("📊 Статы","stats"),("🎰 Казино","casino"),("💼 Работа","job"),("🏋️ Спорт","sport"),("🏪 Магазин","shop"),("🏆 Топ лудоманов","casinotop")]:
        kb.button(text=t, callback_data=f"qcmd:{d}")
    kb.adjust(2)
    await m.answer("📖 **Помощь**\n🥊 /punch (ответ) — удар\n💼 /job — работа (+1💰)\n🏋️ /sport — прокачка навыка\n🎰 /casino <сумма> — казино (0/1/2/3/5х)\n🏆 /casinotop — топ чата\n📊 /stats — мои статы\n🏪 /shop — магазин\n⚠️ При 0 HP: только /shop и реген.\n🌍 У каждого чата свой мир!", parse_mode="Markdown", reply_markup=kb.as_markup())
@dp.callback_query(lambda c: c.data.startswith("qcmd:"))
async def qcmd(call: types.CallbackQuery):
    cmd = call.data.split(":")[1]
    await call.answer()
    msgs = {"stats": cmd_stats, "job": cmd_job, "sport": cmd_sport, "shop": cmd_shop, "casinotop": cmd_casinotop}
    if cmd in msgs: await msgs[cmd](call.message)
    elif cmd == "casino": await call.message.answer("🎰 Пример: `/casino 100`")

@dp.message(Command("punch"))
async def cmd_punch(m: types.Message):
    if not m.reply_to_message: return await m.answer("⚠️ Ответьте на игрока!")
    u = await get_user_ctx(m)
    if u["hp"] <= 0: return await m.answer("💀 0 HP! Ждите реген или /shop")
    if m.reply_to_message.from_user.id == bot.id: return await m.answer("🤖 Ботов не бьём")
    await apply_punch(m.from_user.id, u["username"], m.reply_to_message.from_user.id, m.chat.id)

@dp.message(Command("job"))
async def cmd_job(m: types.Message):
    u = await get_user_ctx(m)
    if u["hp"] <= 0: return await m.answer("💀 0 HP! Нельзя работать")
    now = time.time()
    cd = COOLDOWNS["job"] - (now - u["last_job"])
    if cd > 0: return await m.answer(f"⏳ Работа через {int(cd//60)}м {int(cd%60)}с")
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _update_user, u["user_id"], m.chat.id, money=u["money"]+1, last_job=now)
    await m.answer(f"💼 {u['username']} +1💰 | Баланс: {u['money']+1}")

@dp.message(Command("sport"))
async def cmd_sport(m: types.Message):
    u = await get_user_ctx(m)
    if u["hp"] <= 0: return await m.answer("💀 0 HP! Тренировки запрещены")
    now = time.time()
    cd = COOLDOWNS["sport"] - (now - u["last_sport"])
    if cd > 0: return await m.answer(f"⏳ Тренировка через {int(cd//60)}м {int(cd%60)}с")
    stat = random.choice(POSITIVE_STATS)
    nv = min(100, u[stat]+1)
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _update_user, u["user_id"], m.chat.id, **{stat: nv}, last_sport=now)
    await m.answer(f"🏋️ {u['username']} +1% {STAT_NAMES[stat]}: {u[stat]}→{nv}%")

@dp.message(Command("shop"))
async def cmd_shop(m: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Сброс кулдауна - 3💰", callback_data="shop:skip")],
        [InlineKeyboardButton(text="❤️ +1 жизнь (макс 3) - 5💰", callback_data="shop:life")],
        [InlineKeyboardButton(text="🛡️ Щит (1 удар) - 4💰", callback_data="shop:shield")]
    ])
    await m.answer("🏪 Магазин (доступен при 0 HP)", reply_markup=kb)
@dp.callback_query(lambda c: c.data.startswith("shop:"))
async def shop_h(call: types.CallbackQuery): await shop_cb(call)

@dp.message(Command("casino"))
async def cmd_casino(m: types.Message):
    u = await get_user_ctx(m)
    if u["hp"] <= 0: return await m.answer("💀 0 HP! Казино закрыто")
    parts = m.text.split()
    if len(parts) < 2: return await m.answer("🎰 /casino <сумма>")
    try: bet = int(parts[1])
    except: return await m.answer("❌ Целое число")
    if bet <= 0: return await m.answer("❌ Ставка > 0")
    if u["money"] < bet: return await m.answer(f"💸 Нужно {bet}, у вас {u['money']}")
    
    r = random.random()
    mult = 0 if r < 0.40 else 1 if r < 0.70 else 2 if r < 0.90 else 3 if r < 0.98 else 5
    win = bet * mult
    new_m = u["money"] - bet + win
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _update_user, u["user_id"], m.chat.id, money=new_m, casino_won=u["casino_won"]+win)
    
    res = {0:"💀 Проигрыш",1:"🔄 Возврат",2:"🎉 x2",3:"🔥 x3",5:"💎 x5 ДЖЕКПОТ"}[mult]
    await m.answer(f"🎰 {u['username']}: {res}\n💰 Выпало {mult}x | +{win} | Баланс: {new_m}")

@dp.message(Command("casinotop"))
async def cmd_casinotop(m: types.Message):
    conn = _get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT username,casino_won FROM users WHERE chat_id=? ORDER BY casino_won DESC LIMIT 10",(m.chat.id,))
        rows = c.fetchall()
    finally: conn.close()
    if not rows: return await m.answer("📊 Нет данных")
    txt = f"🏆 Топ лудоманов (мир {m.chat.id}):\n"
    for i,(n,w) in enumerate(rows,1):
        txt += f"{'🥇'if i==1 else '🥈'if i==2 else '🥉'if i==3 else f'{i}.'} {n}: {w}💰\n"
    await m.answer(txt)

@dp.message(Command("stats","profile"))
async def cmd_stats(m: types.Message):
    u = await get_user_ctx(m)
    loop = asyncio.get_running_loop()
    u = await loop.run_in_executor(None, _recalc_hp, u["user_id"], m.chat.id)
    txt = (f"👤 {u['username']}\n❤️ HP: {u['hp']}/{u['max_hp']}\n💰 {u['money']}\n🛡️ {'✅'if u['shield']else'❌'}\n\n"
           f"📈 Навыки:\n🔄 Реген: {u['stat_regen']}%\n🥊 Отпор: {u['stat_counter']}%\n🛡️ Блок: {u['stat_block']}%\n🥋 Джиу: {u['stat_jiu']}%\n\n"
           f"📉 Дебаффы:\n🦠 Слабость: {u['debuff_weak']}%\n😨 Страх: {u['debuff_fear']}%\n💸 Откуп: {u['debuff_payoff']}%")
    await m.answer(txt)

async def main():
    init_db()    logging.info(f"✅ БД: {DB_PATH}")
    await bot.set_my_commands([
        types.BotCommand("help","Помощь + кнопки"), types.BotCommand("stats","Мои статы"),
        types.BotCommand("punch","Ударить (ответом)"), types.BotCommand("job","Работа +1💰"),
        types.BotCommand("sport","Прокачка"), types.BotCommand("casino","Казино: /casino 100"),
        types.BotCommand("casinotop","Топ чата"), types.BotCommand("shop","Магазин")
    ])
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
