import os
import random
import math
import time
import sqlite3
import asyncio
import logging
from pathlib import Path
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

# 🔑 Токен бота
BOT_TOKEN = "8183582932:AAEIas0VlMxWSDvOLap_y6cTsZ9yqicmhYc"

# 📂 Настройки
DATA_DIR = Path("/app/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "bot.db"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 📜 Тексты
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
    "{attacker} ударил {victim} по рукам", "{attacker} ударил {victim} по ногам",    "{attacker} ударил {victim} по спине", "{attacker} ударил {victim} по груди",
    "{attacker} ударил {victim} по животу", "{attacker} ударил {victim} по боку",
    "{attacker} ударил {victim} по шее", "{attacker} ударил {victim} по подбородку",
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

# 💩 10 текстов «обосрался» (ВОССТАНОВЛЕНО)
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

# 🗄️ БД — безопасно и просто
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

def _get_user(uid, cid, name):
    conn = _db()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id=? AND chat_id=?", (uid, cid))
        row = c.fetchone()
        if not row:
            now = time.time()
            vals = (uid, cid, name, 3, 3, 0, 0, 0, 0, 0, now, 0, 0, 0, 0, 0, 0, 0, 0)
            c.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", vals)
            conn.commit()
            return dict(zip([d[0] for d in c.description], vals))
        return dict(row)
    finally:
        conn.close()
def _upd_user(uid, cid, **kw):
    conn = _db()
    try:
        c = conn.cursor()
        sets = ", ".join(f"{k}=?" for k in kw)
        c.execute(f"UPDATE users SET {sets} WHERE user_id=? AND chat_id=?", [*kw.values(), uid, cid])
        conn.commit()
    finally:
        conn.close()

def _recalc_hp(uid, cid):
    u = _get_user(uid, cid, "")
    now = time.time()
    elapsed = now - u["last_hp_update"]
    regen = max(60, 3600 * (1 - u["stat_regen"]/100))
    gained = int(elapsed // regen)
    if gained > 0:
        nhp = min(u["max_hp"], u["hp"] + gained)
        if nhp != u["hp"]:
            _upd_user(uid, cid, hp=nhp, last_hp_update=now)
    return _get_user(uid, cid, "")

def clean_nick(t):
    return (t or "User").replace("@","").replace("[","").replace("]","").replace("(","").replace(")","").strip()

# 🔁 Хелпер для БД в async
async def db_task(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func, *args)

# 🥊 Удар
async def do_punch(aid, aname, vid, cid, auto=False):
    try:
        loop = asyncio.get_running_loop()
        now = time.time()
        att = await db_task(_get_user, aid, cid, aname)
        vic = await db_task(_recalc_hp, vid, cid)

        if not auto:
            cd = COOLDOWNS["punch"] - (now - att["last_punch"])
            if cd > 0:
                return await bot.send_message(cid, f"⏳ {att['username']}, кулдаун: {int(cd//60)}м {int(cd%60)}с")

        # Щит
        if vic["shield"] == 1:
            await db_task(_upd_user, vid, cid, shield=0)
            return await bot.send_message(cid, f"🛡️ Щит {vic['username']} поглотил удар!")

        # Откуп
        if vic["debuff_payoff"] > 0 and vic["money"] > 0 and random.randint(1,100) <= vic["debuff_payoff"]:            amt = vic["money"] // 2
            await db_task(_upd_user, vid, cid, money=vic["money"]-amt)
            await db_task(_upd_user, aid, cid, money=att["money"]+amt)
            return await bot.send_message(cid, f"💸 Откуп! {vic['username']} отдал {amt}💰")

        # Джиу
        if vic["stat_jiu"] > 0 and random.randint(1,100) <= vic["stat_jiu"]:
            await bot.send_message(cid, f"🥋 {vic['username']} использовал джиу-джитсу! Контратака!")
            await do_punch(vid, vic["username"], aid, cid, auto=True)
            if not auto:
                await db_task(_upd_user, aid, cid, last_punch=now)
            return

        # Блок
        if vic["stat_block"] > 0 and random.randint(1,100) <= vic["stat_block"]:
            return await bot.send_message(cid, f"🛡️ {vic['username']} заблокировал удар!")

        # Урон
        dmg = 2 if (vic["debuff_weak"]>0 and random.randint(1,100)<=vic["debuff_weak"]) else 1
        nhp = max(0, vic["hp"]-dmg)
        take = vic["money"] // 4
        await db_task(_upd_user, vid, cid, hp=nhp, money=max(0,vic["money"]-take))
        await db_task(_upd_user, aid, cid, money=att["money"]+take)

        txt = random.choice(PUNCH_TEXTS).format(attacker=att["username"], victim=vic["username"])
        msg = f"💥 {txt}\n💰 +{take} | ❤️ {vic['username']}: {nhp}/{vic['max_hp']}"
        if dmg==2: msg+="\n⚡ Слабость удвоила урон!"

        # Отпор
        if vic["stat_counter"]>0 and random.randint(1,100)<=vic["stat_counter"]:
            msg+=f"\n🔄 {vic['username']} активировал Отпор!"
            await do_punch(vid, vic["username"], aid, cid, auto=True)

        # Бафф/Дебафф (гарантированно рандомно)
        if random.random() < 0.25:
            valid = [s for s in ALL_STATS if vic[s]<100]
            if valid:
                st = random.choice(valid)
                nv = vic[st]-1 if st in POSITIVE_STATS else vic[st]+1
                await db_task(_upd_user, vid, cid, **{st: nv})
                sign = "📉" if st in POSITIVE_STATS else "📀"
                msg+=f"\n{sign} {STAT_NAMES[st]}: {vic[st]}% → {nv}%"

        # Страх (глобально)
        conn = _db()
        try:
            c = conn.cursor()
            c.execute("SELECT username,debuff_fear FROM users WHERE chat_id=? AND debuff_fear>0",(cid,))
            for nm,fl in c.fetchall():
                if random.randint(1,100)<=fl:                    await bot.send_message(cid, random.choice(POOP_TEXTS).format(nick=nm))
        finally:
            conn.close()

        if not auto:
            await db_task(_upd_user, aid, cid, last_punch=now)
        await bot.send_message(cid, msg)
    except Exception as e:
        logger.error(f"❌ Punch error: {e}", exc_info=True)
        await bot.send_message(cid, "⚠️ Ошибка при ударе. Попробуйте позже.")

# 🛒 Магазин
async def shop_cb(call: types.CallbackQuery):
    try:
        loop = asyncio.get_running_loop()
        item = call.data.split(":")[1]
        u = await db_task(_get_user, call.from_user.id, call.message.chat.id, clean_nick(call.from_user.full_name))
        now = time.time()

        if item=="skip":
            if u["money"]<3: return await call.answer("Нужно 3💰",show_alert=True)
            await db_task(_upd_user, u["user_id"], call.message.chat.id, money=u["money"]-3, last_punch=now-COOLDOWNS["punch"])
            await call.answer("Кулдаун сброшен!",show_alert=True)
            await call.message.edit_text(f"✅ {u['username']} купил сброс кулдауна")
        elif item=="life":
            if u["money"]<5: return await call.answer("Нужно 5💰",show_alert=True)
            if u["hp"]>=3: return await call.answer("Максимум жизней!",show_alert=True)
            await db_task(_upd_user, u["user_id"], call.message.chat.id, money=u["money"]-5, hp=u["hp"]+1)
            await call.answer("Жизнь восстановлена!",show_alert=True)
            await call.message.edit_text(f"❤️ {u['username']} +1 HP")
        elif item=="shield":
            if u["money"]<4: return await call.answer("Нужно 4💰",show_alert=True)
            if u["shield"]==1: return await call.answer("Щит уже есть!",show_alert=True)
            await db_task(_upd_user, u["user_id"], call.message.chat.id, money=u["money"]-4, shield=1)
            await call.answer("Щит получен!",show_alert=True)
            await call.message.edit_text(f"🛡️ {u['username']} купил щит")
    except Exception as e:
        logger.error(f"❌ Shop error: {e}", exc_info=True)
        await call.answer("⚠️ Ошибка магазина", show_alert=True)

# 🌐 Глобальный обработчик ошибок
@dp.errors()
async def errors_handler(update: types.Update, exception: Exception):
    logger.error(f"🔥 UNHANDLED ERROR: {type(exception).__name__}: {exception}", exc_info=True)
    if isinstance(update, types.Message) and update.message:
        await update.message.answer("⚠️ Произошла ошибка. Попробуйте позже.")
    return True

# 📝 Handlers
@dp.message(Command("help"))async def cmd_help(m: types.Message):
    try:
        await db_task(_get_user, m.from_user.id, m.chat.id, clean_nick(m.from_user.full_name))
        kb = InlineKeyboardBuilder()
        for t,d in [("📊 Статы","stats"),("🎰 Казино","casino"),("💼 Работа","job"),("🏋️ Спорт","sport"),("🏪 Магазин","shop"),("🏆 Топ","casinotop")]:
            kb.button(text=t, callback_data=f"qcmd:{d}")
        kb.adjust(2)
        await m.answer("📖 **Помощь**\n🥊 /punch (ответ) — удар\n💼 /job — работа (+1💰)\n🏋️ /sport — прокачка\n🎰 /casino <сумма> — казино (0/1/2/3/5х)\n🏆 /casinotop — топ чата\n📊 /stats — мои статы\n🏪 /shop — магазин\n⚠️ При 0 HP: только /shop и реген.\n🌍 У каждого чата свой мир!", parse_mode="Markdown", reply_markup=kb.as_markup())
    except Exception as e:
        logger.error(f"❌ /help error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка загрузки помощи")

@dp.callback_query(lambda c: c.data.startswith("qcmd:"))
async def qcmd(call: types.CallbackQuery):
    try:
        cmd = call.data.split(":")[1]
        await call.answer()
        cmds = {"stats":cmd_stats,"job":cmd_job,"sport":cmd_sport,"shop":cmd_shop,"casinotop":cmd_casinotop}
        if cmd in cmds: await cmds[cmd](call.message)
        elif cmd=="casino": await call.message.answer("🎰 Пример: `/casino 100`")
    except Exception as e:
        logger.error(f"❌ Quick cmd error: {e}", exc_info=True)
        await call.answer("⚠️ Ошибка", show_alert=True)

@dp.message(Command("punch"))
async def cmd_punch(m: types.Message):
    try:
        if not m.reply_to_message: return await m.answer("⚠️ Ответьте на игрока!")
        u = await db_task(_get_user, m.from_user.id, m.chat.id, clean_nick(m.from_user.full_name))
        if u["hp"]<=0: return await m.answer("💀 0 HP! Ждите реген или /shop")
        if m.reply_to_message.from_user.id==bot.id: return await m.answer("🤖 Ботов не бьём")
        await do_punch(m.from_user.id, u["username"], m.reply_to_message.from_user.id, m.chat.id)
    except Exception as e:
        logger.error(f"❌ /punch error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка удара")

@dp.message(Command("job"))
async def cmd_job(m: types.Message):
    try:
        u = await db_task(_get_user, m.from_user.id, m.chat.id, clean_nick(m.from_user.full_name))
        if u["hp"]<=0: return await m.answer("💀 0 HP! Нельзя работать")
        now = time.time()
        cd = COOLDOWNS["job"] - (now - u["last_job"])
        if cd>0: return await m.answer(f"⏳ Работа через {int(cd//60)}м {int(cd%60)}с")
        await db_task(_upd_user, u["user_id"], m.chat.id, money=u["money"]+1, last_job=now)
        await m.answer(f"💼 {u['username']} +1💰 | Баланс: {u['money']+1}")
    except Exception as e:
        logger.error(f"❌ /job error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка работы")
@dp.message(Command("sport"))
async def cmd_sport(m: types.Message):
    try:
        u = await db_task(_get_user, m.from_user.id, m.chat.id, clean_nick(m.from_user.full_name))
        if u["hp"]<=0: return await m.answer("💀 0 HP! Тренировки запрещены")
        now = time.time()
        cd = COOLDOWNS["sport"] - (now - u["last_sport"])
        if cd>0: return await m.answer(f"⏳ Тренировка через {int(cd//60)}м {int(cd%60)}с")
        st = random.choice(POSITIVE_STATS)
        nv = min(100, u[st]+1)
        await db_task(_upd_user, u["user_id"], m.chat.id, **{st: nv}, last_sport=now)
        await m.answer(f"🏋️ {u['username']} +1% {STAT_NAMES[st]}: {u[st]}→{nv}%")
    except Exception as e:
        logger.error(f"❌ /sport error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка тренировки")

@dp.message(Command("shop"))
async def cmd_shop(m: types.Message):
    try:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Сброс кулдауна - 3💰", callback_data="shop:skip")],
            [InlineKeyboardButton(text="❤️ +1 жизнь - 5💰", callback_data="shop:life")],
            [InlineKeyboardButton(text="🛡️ Щит (1 удар) - 4💰", callback_data="shop:shield")]
        ])
        await m.answer("🏪 Магазин (доступен при 0 HP)", reply_markup=kb)
    except Exception as e:
        logger.error(f"❌ /shop error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка магазина")

@dp.callback_query(lambda c: c.data.startswith("shop:"))
async def shop_h(call: types.CallbackQuery): await shop_cb(call)

@dp.message(Command("casino"))
async def cmd_casino(m: types.Message):
    try:
        u = await db_task(_get_user, m.from_user.id, m.chat.id, clean_nick(m.from_user.full_name))
        if u["hp"]<=0: return await m.answer("💀 0 HP! Казино закрыто")
        parts = m.text.split()
        if len(parts)<2: return await m.answer("🎰 /casino <сумма>")
        try: bet = int(parts[1])
        except: return await m.answer("❌ Целое число")
        if bet<=0: return await m.answer("❌ Ставка > 0")
        if u["money"]<bet: return await m.answer(f"💸 Нужно {bet}, у вас {u['money']}")
        
        r = random.random()
        mult = 0 if r<0.40 else 1 if r<0.70 else 2 if r<0.90 else 3 if r<0.98 else 5
        win = bet * mult
        nm = u["money"] - bet + win
        await db_task(_upd_user, u["user_id"], m.chat.id, money=nm, casino_won=u["casino_won"]+win)
                res = {0:"💀 Проигрыш",1:"🔄 Возврат",2:"🎉 x2",3:"🔥 x3",5:"💎 x5 ДЖЕКПОТ"}[mult]
        await m.answer(f"🎰 {u['username']}: {res}\n💰 Выпало {mult}x | +{win} | Баланс: {nm}")
    except Exception as e:
        logger.error(f"❌ /casino error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка казино")

@dp.message(Command("casinotop"))
async def cmd_casinotop(m: types.Message):
    try:
        conn = _db()
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
    except Exception as e:
        logger.error(f"❌ /casinotop error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка топа")

@dp.message(Command("stats","profile"))
async def cmd_stats(m: types.Message):
    try:
        u = await db_task(_get_user, m.from_user.id, m.chat.id, clean_nick(m.from_user.full_name))
        u = await db_task(_recalc_hp, u["user_id"], m.chat.id)
        txt = (f"👤 {u['username']}\n❤️ HP: {u['hp']}/{u['max_hp']}\n💰 {u['money']}\n🛡️ {'✅'if u['shield']else'❌'}\n\n"
               f"📈 Навыки:\n🔄 Реген: {u['stat_regen']}%\n🥊 Отпор: {u['stat_counter']}%\n🛡️ Блок: {u['stat_block']}%\n🥋 Джиу: {u['stat_jiu']}%\n\n"
               f"📉 Дебаффы:\n🦠 Слабость: {u['debuff_weak']}%\n😨 Страх: {u['debuff_fear']}%\n💸 Откуп: {u['debuff_payoff']}%")
        await m.answer(txt)
    except Exception as e:
        logger.error(f"❌ /stats error: {e}", exc_info=True)
        await m.answer("⚠️ Ошибка загрузки статов")

async def main():
    init_db()
    logger.info(f"✅ БД: {DB_PATH}")
    await bot.set_my_commands([
        types.BotCommand(command="help", description="Помощь + кнопки"),
        types.BotCommand(command="stats", description="Мои статы"),
        types.BotCommand(command="punch", description="Ударить (ответом)"),
        types.BotCommand(command="job", description="Работа +1💰"),
        types.BotCommand(command="sport", description="Прокачка"),
        types.BotCommand(command="casino", description="Казино: /casino 100"),
        types.BotCommand(command="casinotop", description="Топ чата"),
        types.BotCommand(command="shop", description="Магазин")
    ])    logger.info("✅ Commands set")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"🔥 CRASH: {e}", exc_info=True)
