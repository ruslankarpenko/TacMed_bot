import os
from dotenv import load_dotenv

load_dotenv()

# ===== Основні налаштування =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME", "Аркуш1")
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE", "credentials.json")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
PORT = int(os.getenv("PORT", "8080"))

# ===== Інститути =====
NOT_STUDENT = "Не є студентом політехніки"

INSTITUTES = [
    "ІАДУ", "ІАРД", "ІБІБ", "ІНЕМ", "ІЕСК", "ІКТЕ", "ІКНІ",
    "ІКМТ", "ІМІТ", "ІППТ", "ІПДО", "ІППО", "ІПМФ", "ІМТ",
    "ІХХХТ".replace("ХХХ", "ХХ"),  # ІХХТ — виправлено на правильну назву нижче
]

# Перепиши список чітко, без хаків:
INSTITUTES = [
    "ІАДУ", "ІАРД", "ІБІБ", "ІНЕМ", "ІЕСК", "ІКТЕ", "ІКНІ",
    "ІКМТ", "ІМІТ", "ІППТ", "ІПДО", "ІППО", "ІПМФ", "ІМТ",
    "ІХХТ", "ІГСН", "ІГД",
    NOT_STUDENT,
]
