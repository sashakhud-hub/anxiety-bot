import os

# Токен бота от @BotFather (будет через переменную окружения)
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Username канала для проверки подписки
CHANNEL_USERNAME = "@panichkaa"

# Настройки базы данных
DATABASE_URL = os.getenv("DATABASE_URL", "anxiety_bot.db")

# Настройки для деплоя
PORT = int(os.getenv("PORT", 10000))  # Railway использует порт 10000
WEBHOOK_URL = os.getenv("WEBHOOK_URL", None)
