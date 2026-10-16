import os
from dotenv import load_dotenv

# Завантажує змінні з .env у змінні середовища
load_dotenv()

# ===== Основні налаштування =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME", "Аркуш1")
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE", "credentials.json")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
PORT = int(os.getenv("PORT", "8080"))

# ===== Список інститутів (для inline-кнопок при реєстрації) =====
NOT_STUDENT = "Не є студентом Політехніки"
INSTITUTES = [
    "ІАДУ", "ІАРД", "ІБІБ", "ІГДГ", "ІНЕМ", "ІЕСК", "ІКТА", "ІКТЕ", "ІКНІ",
    "ІКМТ", "ІМІТ", "ІППТ", "ІПДО", "ІППО", "ІПМФ", "ІПМТ",
    "ІХХТ", "ІГСН", "ІГДГ", NOT_STUDENT,
]
