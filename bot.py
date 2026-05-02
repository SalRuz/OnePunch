import os
import random
import math
import time
import sqlite3
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 🔑 Токен бота
BOT_TOKEN = "8183582932:AAEIas0VlMxWSDvOLap_y6cTsZ9yqicmhYc"

# 📂 Настройки путей
DATA_DIR = Path("/app/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "bot.db"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

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
STAT_NAMES = {
    "stat_regen": "Регенерация", "stat_counter": "Отпор",
    "stat_block": "Блок", "stat_jiu": "Джиу-джитсу",
    "debuff_weak": "Слабость", "debuff_fear": "Страх", "debuff_payoff": "Откуп"
}

COOLDOWNS = {"punch": 1800, "job": 3600, "sport": 7200}

# 🗄️ DB Helpers (Sync)
def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    # Создаем полную таблицу пользователей
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        chat_id INTEGER, 
        username TEXT,
        hp INTEGER DEFAULT 3, 
        max_hp INTEGER DEFAULT 3, 
        money INTEGER DEFAULT 0,
        shield INTEGER DEFAULT 0, 
        last_punch REAL DEFAULT 0, 
        last_job REAL DEFAULT 0,
        last_sport REAL DEFAULT 0, 
        last_hp_update REAL DEFAULT 0,
        stat_regen INTEGER DEFAULT 0, 
        stat_counter INTEGER DEFAULT 0,
        stat_block INTEGER DEFAULT 0, 
        stat_jiu INTEGER DEFAULT 0,
        debuff_weak INTEGER DEFAULT 0, 
        debuff_fear INTEGER DEFAULT 0,
        debuff_payoff INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()

def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def ensure_user(user_id, chat_id, username):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    
    if not row:
        now = time.time()
        # 18 значений
        vals = (user_id, chat_id, username, 3, 3, 0, 0, 0, 0, 0, now, 0, 0, 0, 0, 0, 0, 0)
        cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", vals)
        conn.commit()
        row_dict = dict(zip([d[0] for d in cursor.description], vals))
    else:
        row_dict = dict(row)
    
    conn.close()
    return row_dict

def update_user(user_id, **kwargs):
    conn = get_conn()
    cursor = conn.cursor()
    set_clause = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [user_id]
    cursor.execute(f"UPDATE users SET {set_clause} WHERE user_id=?", values)
    conn.commit()
    conn.close()

def recalc_hp(user_id):
    user = ensure_user(user_id, 0, "")
    now = time.time()
    elapsed = now - user["last_hp_update"]
    # 1h base, -0.59s per %, min 60s at 100%
    regen_sec = max(60, 3600 * (1 - user["stat_regen"]/100))
    gained = int(elapsed // regen_sec)
    if gained > 0:
        new_hp = min(user["max_hp"], user["hp"] + gained)
        if new_hp != user["hp"]:
            update_user(user_id, hp=new_hp, last_hp_update=now)
    return ensure_user(user_id, 0, "")

def clean_nick(text):
    if not text: return "User"
    return text.replace("@", "").replace("[", "").replace("]", "").replace("(", "").replace(")", "").strip()

# 🥊 Combat Logic
def apply_punch(attacker_id, victim_id, chat_id, is_auto=False):
    now = time.time()
    # Получаем данные атакующего (нужен ник)
    att_member = bot.get_chat_member(chat_id, attacker_id)
    att_name = clean_nick(att_member.user.full_name)
    att = ensure_user(attacker_id, chat_id, att_name)
    
    vic = recalc_hp(victim_id)

    if not is_auto:
        cd_left = COOLDOWNS["punch"] - (now - att["last_punch"])
        if cd_left > 0:
            return bot.send_message(chat_id, f"⏳ {att['username']}, кулдаун удара ещё {int(cd_left//60)} мин {int(cd_left%60)} сек.")

    # 1. Щит
    if vic["shield"] == 1:
        update_user(victim_id, shield=0)
        return bot.send_message(chat_id, f"🛡️ Щит {vic['username']} поглотил удар и разбился!")

    # 2. Откуп
    if vic["debuff_payoff"] > 0 and vic["money"] > 0 and random.randint(1, 100) <= vic["debuff_payoff"]:
        amount = math.floor(vic["money"] * 0.5)
        update_user(victim_id, money=vic["money"]-amount)
        update_user(attacker_id, money=att["money"]+amount)
        return bot.send_message(chat_id, f"💸 Сработал откуп! {vic['username']} отдал {amount} монет, урон проигнорирован.")

    # 3. Джиу-джитсу
    if vic["stat_jiu"] > 0 and random.randint(1, 100) <= vic["stat_jiu"]:
        bot.send_message(chat_id, f"🥋 {vic['username']} использовал джиу-джитсу! Урон заблокирован и нанесён мгновенный ответный удар!")
        apply_punch(victim_id, attacker_id, chat_id, is_auto=True)
        if not is_auto:
            update_user(attacker_id, last_punch=now)
        return

    # 4. Блок
    if vic["stat_block"] > 0 and random.randint(1, 100) <= vic["stat_block"]:
        return bot.send_message(chat_id, f"🛡️ {vic['username']} заблокировал удар! ({vic['stat_block']}%)")

    # 5. Урон проходит
    dmg = 1
    extra = ""
    if vic["debuff_weak"] > 0 and random.randint(1, 100) <= vic["debuff_weak"]:
        dmg = 2
        extra = "\n⚡ Слабость удвоила урон!"
    
    new_hp = max(0, vic["hp"] - dmg)
    money_take = math.floor(vic["money"] * 0.25)
    
    update_user(victim_id, hp=new_hp, money=max(0, vic["money"]-money_take))
    update_user(attacker_id, money=att["money"]+money_take)

    txt = random.choice(PUNCH_TEXTS).format(attacker=att["username"], victim=vic["username"])
    result_msg = f"💥 {txt}\n💰 {att['username']} забрал {money_take} монет. ❤️ {vic['username']}: {new_hp}/{vic['max_hp']}{extra}"

    # 6. Отпор
    if vic["stat_counter"] > 0 and random.randint(1, 100) <= vic["stat_counter"]:
        result_msg += f"\n🔄 {vic['username']} активировал Отпор! Автоматический ответный удар!"
        apply_punch(victim_id, attacker_id, chat_id, is_auto=True)

    # 7. Дебафф/Нейтрализация стата (25%)
    if random.random() < 0.25:
        if random.random() < 0.5:
            stat = random.choice(POSITIVE_STATS)
            if vic[stat] > 0:
                new_val = vic[stat] - 1
                update_user(victim_id, **{stat: new_val})
                result_msg += f"\n📉 Удар ослабил навык {STAT_NAMES[stat]}: {vic[stat]}% → {new_val}%"
        else:
            debuff = random.choice(["debuff_weak", "debuff_fear", "debuff_payoff"])
            if vic[debuff] < 100:
                new_val = vic[debuff] + 1
                update_user(victim_id, **{debuff: new_val})
                result_msg += f"\n📀 Получен дебафф {STAT_NAMES[debuff]}: {vic[debuff]}% → {new_val}%"

    # 8. Страх (глобальная проверка в чате)
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, debuff_fear FROM users WHERE chat_id=? AND debuff_fear > 0", (chat_id,))
    fearful = cursor.fetchall()
    conn.close()
    
    for uid, uname, fear_lvl in fearful:
        if random.randint(1, 100) <= fear_lvl:
            txt = random.choice(POOP_TEXTS).format(nick=uname)
            bot.send_message(chat_id, txt)

    if not is_auto:
        update_user(attacker_id, last_punch=now)
    bot.send_message(chat_id, result_msg)

# 🛒 Магазин
def shop_callback(call: types.CallbackQuery):
    data = call.data.split(":")
    item = data[1]
    user = ensure_user(call.from_user.id, call.message.chat.id, clean_nick(call.from_user.full_name))
    now = time.time()

    if item == "skip":
        if user["money"] < 3: return call.answer("Недостаточно монет! Нужно 3.", show_alert=True)
        update_user(user["user_id"], money=user["money"]-3, last_punch=now-COOLDOWNS["punch"])
        call.answer("Кулдаун удара сброшен!", show_alert=True)
        call.message.edit_text(f"✅ {user['username']} купил пропуск кулдауна за 3 монеты.")

    elif item == "life":
        if user["money"] < 5: return call.answer("Недостаточно монет! Нужно 5.", show_alert=True)
        if user["hp"] >= 3: return call.answer("У вас максимум жизней!", show_alert=True)
        update_user(user["user_id"], money=user["money"]-5, hp=user["hp"]+1)
        call.answer("Дополнительная жизнь получена!", show_alert=True)
        call.message.edit_text(f"❤️ {user['username']} восстановил жизнь. HP: {user['hp']+1}/3")

    elif item == "shield":
        if user["money"] < 4: return call.answer("Недостаточно монет! Нужно 4.", show_alert=True)
        if user["shield"] == 1: return call.answer("У вас уже есть активный щит!", show_alert=True)
        update_user(user["user_id"], money=user["money"]-4, shield=1)
        call.answer("Щит получен!", show_alert=True)
        call.message.edit_text(f"🛡️ {user['username']} купил щит. Он блокирует 1 удар.")

# 📝 Handlers
@dp.message(Command("start", "register"))
async def cmd_start(message: types.Message):
    ensure_user(message.from_user.id, message.chat.id, clean_nick(message.from_user.full_name))
    await message.answer("✅ Вы зарегистрированы в системе! Используйте `/shop` для покупок, `/job` для заработка, `/sport` для прокачки и `/punch` (ответом на сообщение) для боя.")

@dp.message(Command("punch"))
async def cmd_punch(message: types.Message):
    if not message.reply_to_message:
        return await message.answer("⚠️ Ответьте на сообщение игрока, чтобы ударить его!")
    if message.reply_to_message.from_user.id == bot.id:
        return await message.answer("🤖 Ботов бить нельзя!")
    # Запускаем в отдельном потоке, чтобы не блокировать бота, если логика тяжелая, 
    # но здесь она быстрая, можно оставить так.
    apply_punch(message.from_user.id, message.reply_to_message.from_user.id, message.chat.id)

@dp.message(Command("job"))
async def cmd_job(message: types.Message):
    now = time.time()
    user = ensure_user(message.from_user.id, message.chat.id, clean_nick(message.from_user.full_name))
    cd_left = COOLDOWNS["job"] - (now - user["last_job"])
    if cd_left > 0:
        return await message.answer(f"⏳ До следующей работы осталось {int(cd_left//60)} мин {int(cd_left%60)} сек.")
    update_user(user["user_id"], money=user["money"]+1, last_job=now)
    await message.answer(f"💼 {user['username']} поработал и заработал 1 монету. Баланс: {user['money']+1}")

@dp.message(Command("sport"))
async def cmd_sport(message: types.Message):
    now = time.time()
    user = ensure_user(message.from_user.id, message.chat.id, clean_nick(message.from_user.full_name))
    cd_left = COOLDOWNS["sport"] - (now - user["last_sport"])
    if cd_left > 0:
        return await message.answer(f"⏳ До следующей тренировки осталось {int(cd_left//60)} мин {int(cd_left%60)} сек.")
    
    stat = random.choice(POSITIVE_STATS)
    new_val = min(100, user[stat] + 1)
    update_user(user["user_id"], **{stat: new_val}, last_sport=now)
    await message.answer(f"🏋️ {user['username']} прокачал {STAT_NAMES[stat]}: {user[stat]}% → {new_val}%")

@dp.message(Command("shop"))
async def cmd_shop(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Сброс кулдауна (/punch) - 3💰", callback_data="shop:skip")],
        [InlineKeyboardButton(text="❤️ Доп. жизнь (макс 3) - 5💰", callback_data="shop:life")],
        [InlineKeyboardButton(text="🛡️ Щит (блокирует 1 удар) - 4💰", callback_data="shop:shield")]
    ])
    await message.answer("🏪 Добро пожаловать в магазин! Выберите улучшение:", reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("shop:"))
async def shop_handler(call: types.CallbackQuery):
    shop_callback(call)

@dp.message(Command("stats", "profile"))
async def cmd_stats(message: types.Message):
    user = ensure_user(message.from_user.id, message.chat.id, clean_nick(message.from_user.full_name))
    user = recalc_hp(user["user_id"])
    
    text = (
        f"👤 {user['username']}\n"
        f"❤️ HP: {user['hp']}/{user['max_hp']}\n"
        f"💰 Монеты: {user['money']}\n"
        f"🛡️ Щит: {'✅' if user['shield'] else '❌'}\n\n"
        f"📈 Навыки:\n"
        f"🔄 Регенерация: {user['stat_regen']}%\n"
        f"🥊 Отпор: {user['stat_counter']}%\n"
        f"🛡️ Блок: {user['stat_block']}%\n"
        f"🥋 Джиу-джитсу: {user['stat_jiu']}%\n\n"
        f"📉 Дебаффы:\n"
        f"🦠 Слабость: {user['debuff_weak']}%\n"
        f"😨 Страх: {user['debuff_fear']}%\n"
        f"💸 Откуп: {user['debuff_payoff']}%"
    )
    await message.answer(text)

async def main():
    init_db()
    print(f"База данных готова: {DB_PATH}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
