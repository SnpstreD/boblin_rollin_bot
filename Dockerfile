# Dockerfile
FROM python:3.11-slim

# Устанавливаем системные зависимости (если нужны)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем зависимости сначала (для кэширования)
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем не-root пользователя (безопаснее)
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Запускаем бота
CMD ["python", "bot.py"]
