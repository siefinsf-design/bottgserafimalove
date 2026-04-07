import asyncio
import logging
from datetime import datetime, date, timedelta
from pathlib import Path

import pytz
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO)

TOKEN = "8676599620:AAGz20iFRxqbgZ6EISZSYNu31IDT2BIPjWI"

MOSCOW_TZ = pytz.timezone("Europe/Moscow")
DATE_MET = date(2024, 3, 27)
DATE_TOGETHER = date(2024, 7, 2)

SAKURA = "🌸"
HEART  = "🤍"
# Специальный невидимый символ для удержания ширины
EMPTY = "⠀" 

# Сетки 10x13 (добавлены нули по бокам для "окружения" сакурой)
GRID_HEART = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,1,1,1,0,0,0,1,1,1,0,0],
    [0,1,1,1,1,1,0,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,1,1,1,1,1,1,1,1,1,0,0],
    [0,0,0,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,1,1,1,1,0,0,0,0],
    [0,0,0,0,0,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0],
]

L_GRID = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,1,1,0,0,0,0,0,0,0,0,0],
    [0,0,1,1,0,0,0,0,0,0,0,0,0],
    [0,0,1,1,0,0,0,0,0,0,0,0,0],
    [0,0,1,1,0,0,0,0,0,0,0,0,0],
    [0,0,1,1,0,0,0,0,0,0,0,0,0],
    [0,0,1,1,0,0,0,0,0,0,0,0,0],
    [0,0,1,1,1,1,1,1,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0],
]

O_GRID = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0,0],
    [0,0,1,1,0,0,0,1,1,0,0,0,0],
    [0,0,1,1,0,0,0,1,1,0,0,0,0],
    [0,0,1,1,0,0,0,1,1,0,0,0,0],
    [0,0,1,1,0,0,0,1,1,0,0,0,0],
    [0,0,1,1,0,0,0,1,1,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0],
]

V_GRID = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,1,1,0,0,0,0,0,1,1,0,0,0],
    [0,1,1,0,0,0,0,0,1,1,0,0,0],
    [0,0,1,1,0,0,0,1,1,0,0,0,0],
    [0,0,1,1,0,0,0,1,1,0,0,0,0],
    [0,0,0,1,1,0,1,1,0,0,0,0,0],
    [0,0,0,1,1,0,1,1,0,0,0,0,0],
    [0,0,0,0,1,1,1,0,0,0,0,0,0],
    [0,0,0,0,0,1,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0],
]

E_GRID = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,1,1,1,1,1,1,1,0,0,0,0],
    [0,0,1,1,0,0,0,0,0,0,0,0,0],
    [0,0,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,1,1,0,0,0,0,0,0,0,0,0],
    [0,0,1,1,0,0,0,0,0,0,0,0,0],
    [0,0,1,1,1,1,1,1,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0],
]

ID_FILE = Path("serafima_id.txt")

# ==================== ВСПОМОГАТЕЛЬНОЕ ====================

def day_word(n: int) -> str:
    if 11 <= n % 100 <= 14: return "дней"
    r = n % 10
    if r == 1: return "день"
    if 2 <= r <= 4: return "дня"
    return "дней"

def year_word(n: int) -> str:
    if 11 <= n % 100 <= 14: return "лет"
    r = n % 10
    if r == 1: return "год"
    if 2 <= r <= 4: return "года"
    return "лет"

# ==================== ЛОГИКА ОТРИСОВКИ ====================

def render_frame(grid: list, phase: str, step: int) -> str:
    lines = []
    for i in range(10):
        if phase == 'wall':
            if i < step: lines.append(SAKURA * 13)
            else: lines.append(EMPTY * 13)
        else:
            if i < step:
                row = grid[i]
                line = "".join([HEART if cell == 1 else SAKURA for cell in row])
                lines.append(line)
            else:
                lines.append(SAKURA * 13)
    return "\n".join(lines)

async def safe_edit(bot, chat_id, msg_id, text):
    from telegram.error import RetryAfter
    try:
        await bot.edit_message_text(text, chat_id, msg_id)
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after + 0.1)
        await bot.edit_message_text(text, chat_id, msg_id)
    except: pass

# ==================== КОМАНДЫ ====================

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    ID_FILE.write_text(str(chat_id))
    bot = ctx.bot

    msg = await bot.send_message(chat_id, "Приготовься...")
    await asyncio.sleep(1.5)

    # ОБРАТНЫЙ ОТСЧЕТ 1, 2, 3
    for count in ["1...", "2...", "3..."]:
        await safe_edit(bot, chat_id, msg.message_id, count)
        await asyncio.sleep(1)

    # 1. СТРОИМ СТЕНУ ИЗ САКУР
    for i in range(1, 11):
        await safe_edit(bot, chat_id, msg.message_id, render_frame(None, 'wall', i))
        await asyncio.sleep(0.3)

    # 2. СЕРДЦЕ
    for i in range(1, 11):
        await safe_edit(bot, chat_id, msg.message_id, render_frame(GRID_HEART, 'symbol', i))
        await asyncio.sleep(0.3)
    
    await asyncio.sleep(1.5)

    # 3. БУКВЫ L, O, V, E
    for g in [L_GRID, O_GRID, V_GRID, E_GRID]:
        for i in range(1, 11):
            await safe_edit(bot, chat_id, msg.message_id, render_frame(g, 'symbol', i))
            await asyncio.sleep(0.2)
        await asyncio.sleep(1)

    # 4. ФИНАЛЬНОЕ СЕРДЦЕ
    for i in range(1, 11):
        await safe_edit(bot, chat_id, msg.message_id, render_frame(GRID_HEART, 'symbol', i))
        await asyncio.sleep(0.3)

    await bot.send_message(chat_id, "Люблю тебя очень сильно, Серафима! 💖")

# ==================== ТЕСТ И ЕЖЕДНЕВНЫЕ СООБЩЕНИЯ ====================

def get_message_for_date(target_date: date) -> str:
    d_met = (target_date - DATE_MET).days
    d_tog = (target_date - DATE_TOGETHER).days

    if target_date.month == 3 and target_date.day == 27:
        return f"🎉 Годовщина знакомства! 🎉\n\nПрошло {d_met} {day_word(d_met)}\n💖"
    
    if target_date.month == 7 and target_date.day == 2:
        return f"🎉 Годовщина отношений! 🎉\n\nВместе {d_tog} {day_word(d_tog)}\n💖"

    return (
        "🌸 Наша история любви 🌸\n\n"
        f"✨ Знакомство: {d_met} {day_word(d_met)}\n"
        f"🤍 Вместе: {d_tog} {day_word(d_tog)}\n\n"
        "💖 Люблю тебя!"
    )

async def test_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        date_str = ctx.args[0]
        y, m, d = map(int, date_str.split('-'))
        test_d = date(y, m, d)
        await update.message.reply_text(f"📅 Тест на {test_d}:\n\n" + get_message_for_date(test_d))
    except:
        await update.message.reply_text("Используй: /test_date 2025-03-27")

async def daily_job(bot: Bot):
    chat_id = ID_FILE.read_text().strip() if ID_FILE.exists() else None
    if chat_id:
        today = datetime.now(MOSCOW_TZ).date()
        await bot.send_message(chat_id, get_message_for_date(today))

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_date", test_date))

    scheduler = AsyncIOScheduler(timezone=MOSCOW_TZ)
    scheduler.add_job(daily_job, trigger="cron", hour=0, minute=1, kwargs={"bot": app.bot})
    scheduler.start()

    app.run_polling()

if __name__ == "__main__":
    main()
