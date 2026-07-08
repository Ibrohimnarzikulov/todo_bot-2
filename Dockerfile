
FROM python:3.12-slim
 
WORKDIR /app
 
# Tizim kutubxonalari (asyncpg va boshqa paketlar uchun kerak bo'lishi mumkin)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
COPY . .
 
CMD ["python", "main.py"]
 