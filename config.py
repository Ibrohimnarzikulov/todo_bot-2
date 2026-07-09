import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN ="8725244152:AAEiRSeUThnz4sWBqPk6UFS_SPIybXXhcjU"
DATABASE_URL ="postgresql://macbookair:1111@localhost:5432/todo_bot"
DEFAULT_REMINDER_TIME = "07:00"
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi! .env faylida BOT_TOKEN ni to'ldiring.")
