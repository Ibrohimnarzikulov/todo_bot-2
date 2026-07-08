# Serverga joylashtirish (Ubuntu VPS)

Quyidagi qadamlar Ubuntu 22.04/24.04 VPS uchun mo'ljallangan (DigitalOcean, Hetzner,
Timeweb va h.k. — barchasida bir xil ishlaydi).

## 1. Serverga ulanish va tizimni yangilash
```bash
ssh root@SIZNING_SERVER_IP
apt update && apt upgrade -y
```

## 2. Kerakli paketlarni o'rnatish
```bash
apt install -y python3-venv python3-pip postgresql postgresql-contrib git
```

## 3. PostgreSQL sozlash
```bash
sudo -u postgres psql -c "CREATE USER todobot WITH PASSWORD 'kuchli_parol_qoying';"
sudo -u postgres psql -c "CREATE DATABASE todo_bot OWNER todobot;"
```

## 4. Bot uchun alohida foydalanuvchi yaratish (xavfsizlik uchun)
```bash
adduser --system --group todobot
mkdir -p /opt/todo_bot
```

## 5. Loyihani serverga yuklash
Fayllarni `scp` bilan yuklashingiz mumkin (o'z kompyuteringizdan):
```bash
scp -r todo_bot/* root@SIZNING_SERVER_IP:/opt/todo_bot/
```
Yoki GitHub'ga joylab, serverda `git clone` qiling.

## 6. Virtual muhit va kutubxonalar
```bash
cd /opt/todo_bot
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## 7. .env faylini sozlash
```bash
cp .env.example .env
nano .env
```
Quyidagicha to'ldiring:
```
BOT_TOKEN=SIZNING_TOKEN
DATABASE_URL=postgresql://todobot:kuchli_parol_qoying@localhost:5432/todo_bot
```

## 8. Egalik huquqlarini berish
```bash
chown -R todobot:todobot /opt/todo_bot
```

## 9. systemd service o'rnatish
`todo-bot.service` faylini serverga yuklang:
```bash
cp todo-bot.service /etc/systemd/system/todo-bot.service
systemctl daemon-reload
systemctl enable todo-bot
systemctl start todo-bot
```

## 10. Holatini tekshirish
```bash
systemctl status todo-bot
journalctl -u todo-bot -f      # jonli loglarni ko'rish
```

## Yangilash (kod o'zgarganda)
```bash
cd /opt/todo_bot
git pull                        # yoki qayta scp qiling
./venv/bin/pip install -r requirements.txt
systemctl restart todo-bot
```

## Muhim eslatmalar
- Server vaqt zonasini tekshiring: `timedatectl`. Agar `/settime` bilan
  berilgan vaqt kutilganidek ishlamasa, server timezone'ini Toshkent vaqtiga
  o'rnating: `timedatectl set-timezone Asia/Tashkent`
- PostgreSQL parolini kuchli qiling va `.env` faylini hech kimga bermang
  (`.gitignore` ga qo'shishni unutmang, agar Git ishlatsangiz)
- Firewall PostgreSQL portini (5432) tashqariga ochmasin — faqat localhost
  orqali ulanish yetarli
