import asyncio
import logging
import re
from datetime import datetime
from html import escape as html_escape
 
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
 
from app.config import BOT_TOKEN
from app import db
 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
router = Router()
 
TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")
 
# ---------- Tugma matnlari (bitta joyda, xato qilmaslik uchun) ----------
BTN_LIST = "📋 Ro'yxat"
BTN_ADD = "➕ Qo'shish"
BTN_SETTIME = "⏰ Vaqt sozlash"
BTN_CLEAR = "🧹 Tozalash"
BTN_CANCEL = "⬅️ Bekor qilish"
 
 
class TaskStates(StatesGroup):
    waiting_for_task = State()
    waiting_for_time = State()
 
 
def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_LIST), KeyboardButton(text=BTN_ADD)],
            [KeyboardButton(text=BTN_SETTIME), KeyboardButton(text=BTN_CLEAR)],
        ],
        resize_keyboard=True,
    )
 
 
def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True,
    )
 
 
def format_task_list(tasks) -> str:
    if not tasks:
        return "Hozircha vazifalar yo'q. \"➕ Qo'shish\" tugmasini bosing."
    lines = []
    for t in tasks:
        mark = "✅" if t["is_done"] else "⬜️"
        lines.append(f"{mark} <b>#{t['id']}</b> {html_escape(t['task_text'])}")
    return "\n".join(lines)
 
 
def task_inline_keyboard(tasks) -> InlineKeyboardMarkup | None:
    """Har bir vazifa ostiga ✅ va 🗑 tugmalarini chiqaradi."""
    buttons = []
    for t in tasks:
        row = []
        if not t["is_done"]:
            row.append(InlineKeyboardButton(text=f"✅ #{t['id']}", callback_data=f"done:{t['id']}"))
        row.append(InlineKeyboardButton(text=f"🗑 #{t['id']}", callback_data=f"delete:{t['id']}"))
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
 
 
# ---------- /start ----------
 
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await db.upsert_user(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        full_name=message.from_user.full_name,
    )
    await message.answer(
        "Salom! 👋 Men kundalik vazifalar (to-do) botiman.\n\n"
        "Quyidagi tugmalardan foydalaning 👇",
        reply_markup=main_menu_keyboard(),
    )
 
 
# ---------- Ro'yxat ----------
 
async def _show_list(message: Message):
    tasks = await db.get_tasks(message.from_user.id)
    await message.answer(format_task_list(tasks), reply_markup=task_inline_keyboard(tasks))
 
 
@router.message(F.text == BTN_LIST)
@router.message(Command("list"))
async def cmd_list(message: Message):
    await _show_list(message)
 
 
# ---------- Qo'shish (FSM) ----------
 
@router.message(F.text == BTN_ADD)
async def btn_add(message: Message, state: FSMContext):
    await state.set_state(TaskStates.waiting_for_task)
    await message.answer(
        "Vazifa matnini yozing:",
        reply_markup=cancel_keyboard(),
    )
 
 
@router.message(Command("add"))
async def cmd_add(message: Message):
    text = message.text.replace("/add", "", 1).strip()
    if not text:
        await message.answer("Vazifa matnini yozing. Masalan:\n<code>/add Ingliz tili darsini tayyorlash</code>")
        return
    row = await db.add_task(message.from_user.id, text)
    await message.answer(f"✅ Qo'shildi (#{row['id']}): {html_escape(text)}")
 
 
@router.message(TaskStates.waiting_for_task, F.text == BTN_CANCEL)
async def cancel_add(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=main_menu_keyboard())
 
 
@router.message(TaskStates.waiting_for_task)
async def process_add(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text:
        await message.answer("Bo'sh matn qabul qilinmaydi. Qayta yozing:")
        return
    row = await db.add_task(message.from_user.id, text)
    await state.clear()
    await message.answer(
        f"✅ Qo'shildi (#{row['id']}): {html_escape(text)}",
        reply_markup=main_menu_keyboard(),
    )
 
 
# ---------- Vaqt sozlash (FSM) ----------
 
@router.message(F.text == BTN_SETTIME)
async def btn_settime(message: Message, state: FSMContext):
    await state.set_state(TaskStates.waiting_for_time)
    await message.answer(
        "Kunlik eslatma vaqtini SS:DD formatida yuboring (masalan 09:00):",
        reply_markup=cancel_keyboard(),
    )
 
 
@router.message(Command("settime"))
async def cmd_settime(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not TIME_RE.match(parts[1].strip()):
        await message.answer("To'g'ri formatda yozing: <code>/settime 09:00</code>")
        return
    time_str = parts[1].strip()
    await db.set_reminder_time(message.from_user.id, time_str)
    await message.answer(f"⏰ Kunlik eslatma vaqti {time_str} ga o'rnatildi.")
 
 
@router.message(TaskStates.waiting_for_time, F.text == BTN_CANCEL)
async def cancel_settime(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=main_menu_keyboard())
 
 
@router.message(TaskStates.waiting_for_time)
async def process_settime(message: Message, state: FSMContext):
    time_str = message.text.strip()
    if not TIME_RE.match(time_str):
        await message.answer("Noto'g'ri format. Masalan: 09:00. Qayta yozing:")
        return
    await db.set_reminder_time(message.from_user.id, time_str)
    await state.clear()
    await message.answer(
        f"⏰ Kunlik eslatma vaqti {time_str} ga o'rnatildi.",
        reply_markup=main_menu_keyboard(),
    )
 
 
# ---------- Tozalash ----------
 
@router.message(F.text == BTN_CLEAR)
@router.message(Command("clear"))
async def cmd_clear(message: Message):
    await db.clear_done(message.from_user.id)
    await message.answer("Bajarilgan vazifalar tozalandi.")
 
 
# ---------- Eski /done va /delete buyruqlari (ixtiyoriy, ID bilan) ----------
 
@router.message(Command("done"))
async def cmd_done(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        await message.answer("To'g'ri formatda yozing: <code>/done 3</code>")
        return
    task_id = int(parts[1].strip())
    ok = await db.mark_done(message.from_user.id, task_id)
    await message.answer("✅ Bajarildi deb belgilandi." if ok else "Bunday ID topilmadi.")
 
 
@router.message(Command("delete"))
async def cmd_delete(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        await message.answer("To'g'ri formatda yozing: <code>/delete 3</code>")
        return
    task_id = int(parts[1].strip())
    ok = await db.delete_task(message.from_user.id, task_id)
    await message.answer("🗑 O'chirildi." if ok else "Bunday ID topilmadi.")
 
 
# ---------- Inline tugmalar (✅ / 🗑) ----------
 
@router.callback_query(F.data.startswith("done:"))
async def cb_done(callback: CallbackQuery):
    task_id = int(callback.data.split(":", 1)[1])
    ok = await db.mark_done(callback.from_user.id, task_id)
    await callback.answer("✅ Bajarildi!" if ok else "Topilmadi", show_alert=False)
    tasks = await db.get_tasks(callback.from_user.id)
    await callback.message.edit_text(format_task_list(tasks), reply_markup=task_inline_keyboard(tasks))
 
 
@router.callback_query(F.data.startswith("delete:"))
async def cb_delete(callback: CallbackQuery):
    task_id = int(callback.data.split(":", 1)[1])
    ok = await db.delete_task(callback.from_user.id, task_id)
    await callback.answer("🗑 O'chirildi!" if ok else "Topilmadi", show_alert=False)
    tasks = await db.get_tasks(callback.from_user.id)
    await callback.message.edit_text(format_task_list(tasks), reply_markup=task_inline_keyboard(tasks))
 
 
# ---------- Kunlik eslatma ----------
 
async def send_daily_reminders(bot: Bot):
    """Har daqiqada ishga tushadi, vaqti kelgan foydalanuvchilarga ro'yxatni yuboradi."""
    now = datetime.now().strftime("%H:%M")
    users = await db.get_all_users()
    for u in users:
        user_reminder = u["reminder_time"].strftime("%H:%M")
        if user_reminder == now:
            tasks = await db.get_tasks(u["user_id"], only_pending=True)
            text = "📋 <b>Bugungi vazifalaringiz:</b>\n\n" + format_task_list(tasks)
            try:
                await bot.send_message(u["chat_id"], text, reply_markup=task_inline_keyboard(tasks))
            except Exception as e:
                logger.warning(f"Xabar yuborilmadi user_id={u['user_id']}: {e}")
 
 
async def main():
    await db.init_db()
 
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
 
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_reminders, CronTrigger(second=0), args=[bot])
    scheduler.start()
 
    logger.info("Bot ishga tushdi...")
    try:
        await dp.start_polling(bot)
    finally:
        await db.close_db()
 
 
if __name__ == "__main__":
    asyncio.run(main())