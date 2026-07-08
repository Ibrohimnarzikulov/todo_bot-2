# Docker orqali serverga joylashtirish

## Talab qilinadigan narsalar serverda
- Docker
- Docker Compose (yangi Docker versiyalarida `docker compose` sifatida ichida keladi)

O'rnatish (Ubuntu server uchun):
```bash
curl -fsSL https://get.docker.com | sh
```

## 1. Loyihani serverga yuklash
```bash
scp -r todo_bot root@SIZNING_SERVER_IP:/opt/
```
yoki GitHub orqali:
```bash
git clone SIZNING_REPO_MANZILI /opt/todo_bot
```

## 2. .env faylini sozlash
```bash
cd /opt/todo_bot
nano .env
```
Kamida shu qatorni to'ldiring:
```
BOT_TOKEN=haqiqiy_tokeningiz
```
`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` — xohlasangiz o'zgartiring
(ishlab chiqarish muhitida kuchliroq parol qo'yish tavsiya etiladi).

## 3. Qurish va ishga tushirish
```bash
docker compose up -d --build
```

Bu buyruq ikkita konteyner ishga tushiradi:
- `todo_bot_db` — PostgreSQL 16, ma'lumotlar `pgdata` nomli Docker volume'da saqlanadi
- `aiogram_bot` — sizning botingiz, avtomatik `todo_bot_db`ga ulanadi

## 4. Holatini tekshirish
```bash
docker compose ps
docker compose logs -f bot
```

`Bot ishga tushdi...` yozuvini ko'rsangiz — tayyor.

## Botni to'xtatish / qayta ishga tushirish
```bash
docker compose down          # to'xtatish (ma'lumotlar saqlanib qoladi)
docker compose up -d         # qayta ishga tushirish
```

## Kod yangilanganda
```bash
git pull                      # yoki fayllarni qayta yuklang
docker compose up -d --build  # qayta quriladi va ishga tushadi
```

## Ma'lumotlar xavfsizligi
PostgreSQL ma'lumotlari `pgdata` nomli Docker volume'da saqlanadi — `docker compose down`
qilganda ham yo'qolmaydi. Faqat quyidagi buyruq bilan **butunlay o'chirib yuborish** mumkin:
```bash
docker compose down -v   # DIQQAT: bu barcha ma'lumotlarni o'chiradi!
```

## Zaxira nusxa olish (backup)
```bash
docker compose exec db pg_dump -U macbookair todo_bot > backup.sql
```

## Nega Python 3.13-slim?
`Dockerfile` `python:3.13-slim` image'idan foydalanadi. Ichida `gcc` va `libpq-dev`
o'rnatilgan — bu `asyncpg` kabi kutubxonalarni to'g'ri build qilish uchun kerak.
