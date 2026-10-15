import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from config import SPREADSHEET_ID, SHEET_NAME, CREDENTIALS_FILE

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

STATUS_REGISTERED = "Зареєстрований"
STATUS_NOT_REGISTERED = "Не зареєстровано"

# Індекси колонок (1-based, як у gspread)
COL_DATE = 1
COL_TIME = 2
COL_TG_ID = 3
COL_USERNAME = 4
COL_FIRST = 5
COL_LAST = 6
COL_INST = 7
COL_GROUP = 8
COL_COURSE = 9
COL_STATUS = 10

_client = None
_sheet = None


def _get_sheet():
    global _client, _sheet
    if _sheet is None:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        _client = gspread.authorize(creds)
        _sheet = _client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    return _sheet


def _find_row(user_id: int):
    """Повертає номер рядка за Telegram ID або None."""
    try:
        ids = _get_sheet().col_values(COL_TG_ID)
    except Exception as e:
        print(f"[sheets] find_row error: {e}")
        return None
    for idx, value in enumerate(ids, start=1):
        if str(value).strip() == str(user_id):
            return idx
    return None


def ensure_user_row(user_id: int, username: str | None, tg_first_name: str | None):
    """Викликається на /start. Створює рядок, якщо його ще немає."""
    if _find_row(user_id) is not None:
        return
    now = datetime.now()
    row = [
        now.strftime("%d.%m.%Y"),
        now.strftime("%H:%M:%S"),
        str(user_id),
        f"@{username}" if username else "—",
        tg_first_name or "—",
        "—",  # Прізвище
        "—",  # Інститут
        "—",  # Група
        "—",  # Курс
        STATUS_NOT_REGISTERED,
    ]
    _get_sheet().append_row(row, value_input_option="USER_ENTERED")


def save_registration(user_id, first_name, last_name, institute, group, course):
    """Оновлює рядок користувача даними реєстрації."""
    row_idx = _find_row(user_id)
    if row_idx is None:
        # На випадок, якщо рядок зник — створюємо
        now = datetime.now()
        _get_sheet().append_row([
            now.strftime("%d.%m.%Y"), now.strftime("%H:%M:%S"), str(user_id),
            "—", first_name, last_name, institute, group, course, STATUS_REGISTERED,
        ], value_input_option="USER_ENTERED")
        return

    sheet = _get_sheet()
    # Оновлюємо тільки поля реєстрації + статус (дата/час/username лишаємо)
    sheet.update(
        f"E{row_idx}:J{row_idx}",
        [[first_name, last_name, institute, group, course, STATUS_REGISTERED]],
        value_input_option="USER_ENTERED",
    )


def clear_registration(user_id: int) -> bool:
    """Скасовує реєстрацію: чистить поля, ставить статус «Не зареєстровано»."""
    row_idx = _find_row(user_id)
    if row_idx is None:
        return False
    _get_sheet().update(
        f"E{row_idx}:J{row_idx}",
        [["—", "—", "—", "—", "—", STATUS_NOT_REGISTERED]],
        value_input_option="USER_ENTERED",
    )
    return True
