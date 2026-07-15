import asyncio
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "8762058651:AAGTU6a3ktSWK03lszxZa4iPc7-bawGK3Ek"  # ВАШ ТОКЕН
GROUP_ID = -1003666056371  # ПРАВИЛЬНЫЙ ID ГРУППЫ
ADMIN_IDS = [1487417026]  # ВАШ TELEGRAM ID
# =================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ========== ДАННЫЕ ДЛЯ СТАТИСТИКИ ==========
STATS_FILE = "stats.json"
daily_messages = defaultdict(int)
daily_new_members = 0
daily_left_members = 0
today = datetime.now().date()

def load_stats():
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {}

def save_stats(data):
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

# ========== ПРИВЕТСТВИЕ (компактное, без превью) ==========
@dp.message_handler(content_types=['new_chat_members'])
async def welcome_and_clean(message: types.Message):
    global daily_new_members, today
    
    now = datetime.now().date()
    if now != today:
        today = now
        daily_new_members = 0
        daily_left_members = 0
        daily_messages.clear()
    
    try:
        await message.delete()
    except:
        pass
    
    for user in message.new_chat_members:
        if user.id == bot.id:
            continue
        
        daily_new_members += 1
        
        greeting = (
            f"👋 Приветствуем {user.full_name}, в Лавке главного торговца!\n"
            f"Можешь пообщаться с нами в чате или:\n"
            f"• <a href='https://t.me/ShopkeepersCache/17163'>Узнать о нас подробнее</a>\n"
            f"• <a href='https://t.me/ShopkeepersCache'>Ознакомиться с ассортиментом</a>\n"
            f"• <a href='https://t.me/StashShopkeepers'>Посетить канал лавки</a>"
        )
        await message.answer(greeting, parse_mode="HTML", disable_web_page_preview=True)

# ========== УДАЛЕНИЕ СООБЩЕНИЙ О ВЫХОДЕ ==========
@dp.message_handler(content_types=['left_chat_member'])
async def goodbye_clean(message: types.Message):
    global daily_left_members, today
    
    now = datetime.now().date()
    if now != today:
        today = now
        daily_new_members = 0
        daily_left_members = 0
        daily_messages.clear()
    
    try:
        await message.delete()
    except:
        pass
    
    daily_left_members += 1

# ========== ЗАЩИТА ОТ СПАМА ==========
user_last_msg = {}
user_warns = {}

@dp.message_handler()
async def anti_spam(message: types.Message):
    if message.chat.id != GROUP_ID:
        return
    
    global daily_messages, today
    
    now = datetime.now().date()
    if now != today:
        today = now
        daily_new_members = 0
        daily_left_members = 0
        daily_messages.clear()
    
    if message.from_user.id in ADMIN_IDS or message.from_user.is_bot:
        return
    
    user_id = message.from_user.id
    daily_messages[user_id] += 1
    
    if user_id in user_last_msg:
        time_diff = (datetime.now() - user_last_msg[user_id]).seconds
        if time_diff < 5:
            user_warns[user_id] = user_warns.get(user_id, 0) + 1
            if user_warns[user_id] >= 3:
                await bot.ban_chat_member(GROUP_ID, user_id)
                await message.answer(f"🚫 {message.from_user.full_name} забанен за спам!")
                del user_last_msg[user_id]
                del user_warns[user_id]
                return
        else:
            user_warns[user_id] = 0
    user_last_msg[user_id] = datetime.now()

# ========== ЗАПРЕТ ДОБАВЛЯТЬ БОТОВ ==========
@dp.message_handler(content_types=['new_chat_members'])
async def block_bots(message: types.Message):
    for user in message.new_chat_members:
        if user.is_bot and user.id != bot.id:
            await bot.ban_chat_member(GROUP_ID, user.id)
            await message.answer(f"🚫 Бот {user.full_name} был удалён! Добавление ботов запрещено.")

# ========== КОМАНДЫ МОДЕРАЦИИ (ТОЛЬКО ДЛЯ АДМИНОВ) ==========
@dp.message_handler(commands=['mute'])
async def mute_user(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Только для админов!")
        return
    
    if not message.reply_to_message:
        await message.answer("❌ Ответь на сообщение пользователя!")
        return
    
    user_id = message.reply_to_message.from_user.id
    chat_member = await bot.get_chat_member(GROUP_ID, user_id)
    
    if chat_member.status in ["administrator", "creator"]:
        await message.answer("❌ Нельзя замутить администратора или создателя!")
        return
    
    until_date = datetime.now() + timedelta(minutes=5)
    
    try:
        await bot.restrict_chat_member(
            GROUP_ID, 
            user_id, 
            until_date=until_date,
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False
        )
        await message.answer(f"🔇 {message.reply_to_message.from_user.first_name} замучен на 5 минут!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)[:100]}")

@dp.message_handler(commands=['ban'])
async def ban_user(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Только для админов!")
        return
    
    if not message.reply_to_message:
        await message.answer("❌ Ответь на сообщение пользователя!")
        return
    
    user_id = message.reply_to_message.from_user.id
    chat_member = await bot.get_chat_member(GROUP_ID, user_id)
    
    if chat_member.status in ["administrator", "creator"]:
        await message.answer("❌ Нельзя забанить администратора или создателя!")
        return
    
    try:
        await bot.ban_chat_member(GROUP_ID, user_id)
        await message.answer(f"🚫 {message.reply_to_message.from_user.first_name} забанен!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)[:100]}")

# ========== ПЕРИОДИЧЕСКИЕ СООБЩЕНИЯ ==========
CONFIG_FILE = "config.json"

def load_config():
    default = {
        "periodic_messages": [
            "➤ Ищете компанию для игры в Dota 2 и отличного время препровождения? Всё это есть на нашем <a href='https://discord.gg/AtQypC6jK'>Discord-сервере</a>",
            "➤ Все свежие новости Лавки, горячие СКИДКИ на сеты и эксклюзивные скины теперь в одном месте!\n➤ Подписывайтесь на Telegram-канал <a href='https://t.me/StashShopkeepers'>«Тайны Торговца»</a>, чтобы не упустить выгоду!",
            "➤ Общайтесь, торгуйте, находите друзей по Dota 2 в нашем чате!"
        ],
        "current_index": 0,
        "last_message_id": None
    }
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data:
                    return data
    except:
        pass
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(default, f, ensure_ascii=False, indent=2)
    return default

def save_config(data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

async def periodic_messages():
    while True:
        try:
            now = datetime.now()
            if now.hour >= 23 or now.hour < 9:
                await asyncio.sleep(60)
                continue
            
            config = load_config()
            messages = config.get("periodic_messages", [])
            
            if messages:
                if config.get("last_message_id"):
                    try:
                        await bot.delete_message(GROUP_ID, config["last_message_id"])
                    except:
                        pass
                
                idx = config.get("current_index", 0) % len(messages)
                msg = messages[idx]
                
                sent = await bot.send_message(
                    GROUP_ID,
                    msg,
                    parse_mode="HTML",
                    disable_web_page_preview=False
                )
                
                config["current_index"] = idx + 1
                config["last_message_id"] = sent.message_id
                save_config(config)
            
            await asyncio.sleep(7200)
            
        except Exception as e:
            print(f"Ошибка в периодических сообщениях: {e}")
            await asyncio.sleep(60)

# ========== СТАТИСТИКА ГРУППЫ ==========
async def send_daily_stats():
    global daily_messages, daily_new_members, daily_left_members, today
    
    while True:
        try:
            now = datetime.now()
            
            if now.hour == 23 and now.minute == 0:
                try:
                    member_count = await bot.get_chat_member_count(GROUP_ID)
                except:
                    member_count = 0
                
                if daily_messages:
                    top_user_id = max(daily_messages, key=daily_messages.get)
                    top_count = daily_messages[top_user_id]
                    try:
                        top_user = await bot.get_chat(top_user_id)
                        top_name = top_user.first_name or "Неизвестный"
                    except:
                        top_name = "Неизвестный"
                else:
                    top_name = "Нет сообщений"
                    top_count = 0
                
                stats_text = (
                    "📊 <b>Статистика группы за сегодня</b>\n\n"
                    f"👥 Всего участников: {member_count}\n"
                    f"💬 Сообщений: {sum(daily_messages.values())}\n"
                    f"🆕 Новых участников: {daily_new_members}\n"
                    f"📅 {now.strftime('%d.%m.%Y')}"
                )
                
                await bot.send_message(GROUP_ID, stats_text, parse_mode="HTML")
                
                await asyncio.sleep(10)
                daily_messages.clear()
                daily_new_members = 0
                daily_left_members = 0
                today = datetime.now().date() + timedelta(days=1)
                
                await asyncio.sleep(60)
            
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"Ошибка в статистике: {e}")
            await asyncio.sleep(60)

# ========== УТРЕННЕЕ И ВЕЧЕРНЕЕ ==========
async def daily_greetings():
    last_greeting = None
    last_farewell = None
    
    while True:
        try:
            now = datetime.now()
            
            if now.hour == 9 and now.minute == 0 and last_greeting != now.date():
                await bot.send_message(
                    GROUP_ID,
                    "☀️ <b>Начинаем новый день в мире Dota 2!</b>\n\n"
                    "Наш магазинчик снова открыт для вас.\n"
                    "➤ Свежие сеты уже на полках.\n"
                    "➤ Будьте вежливы и соблюдайте правила чата.\n"
                    "➤ Хороших покупок и приятной игры! 🎮",
                    parse_mode="HTML"
                )
                last_greeting = now.date()
                await asyncio.sleep(60)
            
            if now.hour == 23 and now.minute == 0 and last_farewell != now.date():
                await bot.send_message(
                    GROUP_ID,
                    "🌙 <b>Лавка закрывается!</b>\n\n"
                    "Всем спать! Завтра будет новый день.\n"
                    "➤ Не шалите без меня! 😴\n"
                    "➤ Завтра я открою для тебя новые тайны..\n"
                    "➤ До встречи на рассвете! 🗡️",
                    parse_mode="HTML"
                )
                last_farewell = now.date()
                await asyncio.sleep(60)
            
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"Ошибка в ежедневных приветствиях: {e}")
            await asyncio.sleep(60)

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    from aiogram import executor
    print("🛡 Лавка Торговца — бот запущен!")
    print("✅ Приветствие новых участников (компактное, без превью)")
    print("✅ Удаление системных сообщений")
    print("✅ Защита от спама")
    print("✅ Запрет ботов")
    print("✅ Периодические сообщения (каждые 2 часа)")
    print("✅ Утреннее приветствие (9:00) и вечернее прощание (23:00)")
    print("✅ Статистика активности группы (в 23:00)")
    print("✅ Админ-команды: /mute, /ban")
    
    # Запускаем фоновые задачи
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_messages())
    loop.create_task(daily_greetings())
    loop.create_task(send_daily_stats())
    
    executor.start_polling(dp, skip_updates=True)