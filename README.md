# Kundalik Vazifalar (To-Do) Telegram Bot

Python + aiogram 3 + PostgreSQL (asyncpg) + APScheduler bilan yozilgan.

## Imkoniyatlari
- `/add <matn>` — vazifa qo'shish
- `/list` — barcha vazifalarni ko'rish
- `/done <id>` — bajarilgan deb belgilash
- `/delete <id>` — o'chirish
- `/clear` — bajarilgan vazifalarni tozalash
- `/settime SS:DD` — har kuni belgilangan vaqtda joriy vazifalar ro'yxati avtomatik xabar qilinadi

## O'rnatish

### 1. PostgreSQL'ni ishga tushirish
Docker orqali eng oson yo'l:
```bash
docker compose up -d
```
Yoki o'zingizda mavjud PostgreSQL serverdan foydalaning — `.env` faylida `DATABASE_URL` ni moslang.

### 2. Bog'liqliklarni o'rnatish
```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. .env faylini sozlash
```bash
cp .env.example .env
```
`.env` faylni oching va:
- `BOT_TOKEN` — @BotFather orqali olingan tokenni qo'ying
- `DATABASE_URL` — agar docker-compose ishlatgan bo'lsangiz, standart qiymat ishlaydi

### 4. Botni ishga tushirish
```bash
python -m app.bot
```

## Fayl tuzilishi
```
todo_bot/
├── app/
│   ├── __init__.py
│   ├── bot.py         # handlerlar + scheduler + main()
│   ├── config.py       # .env o'qish
│   └── db.py           # PostgreSQL bilan ishlash (asyncpg)
├── requirements.txt
├── .env.example
├── docker-compose.yml
└── README.md
```

## Eslatma tizimi qanday ishlaydi
`APScheduler` har daqiqada (`second=0`) `send_daily_reminders` funksiyasini ishga tushiradi.
U barcha foydalanuvchilarni tekshiradi va joriy vaqt (soat:daqiqa) foydalanuvchi
o'rnatgan `reminder_time` bilan mos kelsa, o'sha foydalanuvchiga bajarilmagan
vazifalar ro'yxatini yuboradi.

> Eslatma: server vaqti (timezone) muhim — agar bot serveri boshqa vaqt zonasida
> bo'lsa, `/settime` bilan berilgan vaqt shu server vaqtiga nisbatan hisoblanadi.
