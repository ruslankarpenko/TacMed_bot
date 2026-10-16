import os
import json
import time
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from config import (
    SPREADSHEET_ID, SHEET_NAME, CREDENTIALS_FILE,
    REPLIES_SHEET, SETTINGS_SHEET,
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

STATUS_REGISTERED = "Зареєстрований"
STATUS_NOT_REGISTERED = "Не зареєстровано"

# Індекси колонок (1-based)
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
_spreadsheet = None


def _load_credentials():
    """Читає credentials з env-змінної (пріоритет) або з файлу (локально)."""
    json_str = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if json_str:
        print("=" * 60)
        print(f"[creds] Довжина JSON: {len(json_str)} символів")
        info = json.loads(json_str)
        print(f"[creds] client_email: {info.get('client_email')}")
        print(f"[creds] private_key_id: {info.get('private_key_id')}")
        pk = info.get('private_key', '')
        print(f"[creds] Довжина private_key: {len(pk)}")
        print("=" * 60)
        return Credentials.from_service_account_info(info, scopes=SCOPES)

    print("[creds] Використовую файл credentials.json (локальна розробка)")
    return Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)


def _retry(func, *args, max_retries=4, **kwargs):
    """Повторює виклик при мережевих помилках."""
    last_error = None
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            print(f"[sheets] спроба {attempt + 1}/{max_retries} не вдалась: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    raise last_error


def _get_spreadsheet():
    global _client, _spreadsheet
    if _spreadsheet is None:
        def _init():
            global _client, _spreadsheet
            creds = _load_credentials()
            _client = gspread.authorize(creds)
            _spreadsheet = _client.open_by_key(SPREADSHEET_ID)
        _retry(_init)
    return _spreadsheet


def _get_sheet(name=None):
    name = name or SHEET_NAME
    return _get_spreadsheet().worksheet(name)


# ===== ОСНОВНИЙ АРКУШ (реєстрація) =====

def _find_row(user_id: int):
    """Повертає номер рядка за Telegram ID або None."""
    def _do():
        ids = _get_sheet().col_values(COL_TG_ID)
        for idx, value in enumerate(ids, start=1):
            if str(value).strip() == str(user_id):
                return idx
        return None
    try:
        return _retry(_do)
    except Exception as e:
        print(f"[sheets] find_row error: {e}")
        return None


def ensure_user_row(user_id: int, username: str | None, tg_first_name: str | None):
    """Створює рядок користувача при /start, якщо його ще немає."""
    try:
        if _find_row(user_id) is not None:
            return
        now = datetime.now()
        row = [
            now.strftime("%d.%m.%Y"),
            now.strftime("%H:%M:%S"),
            str(user_id),
            f"@{username}" if username else "—",
            tg_first_name or "—",
            "—", "—", "—", "—",
            STATUS_NOT_REGISTERED,
        ]
        _retry(_get_sheet().append_row, row, value_input_option="USER_ENTERED")
    except Exception as e:
        print(f"[sheets] ensure_user_row помилка: {e}")


def save_registration(user_id, first_name, last_name, institute, group, course):
    """Оновлює рядок користувача даними реєстрації."""
    row_idx = _find_row(user_id)
    if row_idx is None:
        now = datetime.now()
        _retry(
            _get_sheet().append_row,
            [now.strftime("%d.%m.%Y"), now.strftime("%H:%M:%S"), str(user_id),
             "—", first_name, last_name, institute, group, course, STATUS_REGISTERED],
            value_input_option="USER_ENTERED",
        )
        return
    _retry(
        _get_sheet().update,
        f"E{row_idx}:J{row_idx}",
        [[first_name, last_name, institute, group, course, STATUS_REGISTERED]],
        value_input_option="USER_ENTERED",
    )


def clear_registration(user_id: int) -> bool:
    """Скасовує реєстрацію: чистить поля, ставить статус «Не зареєстровано»."""
    row_idx = _find_row(user_id)
    if row_idx is None:
        return False
    _retry(
        _get_sheet().update,
        f"E{row_idx}:J{row_idx}",
        [["—", "—", "—", "—", "—", STATUS_NOT_REGISTERED]],
        value_input_option="USER_ENTERED",
    )
    return True


def is_registered(user_id: int) -> bool:
    """Читає статус реєстрації з основного аркуша."""
    try:
        sheet = _get_sheet()
        ids = sheet.col_values(COL_TG_ID)
        statuses = sheet.col_values(COL_STATUS)
        for i, uid in enumerate(ids):
            if str(uid).strip() == str(user_id) and i < len(statuses):
                return statuses[i].strip() == STATUS_REGISTERED
        return False
    except Exception as e:
        print(f"[sheets] is_registered error: {e}")
        return False


# ===== РОЗСИЛКА =====

def get_all_user_ids() -> list[int]:
    """Усі, хто натискав /start."""
    try:
        values = _get_sheet().col_values(COL_TG_ID)[1:]  # без заголовка
        return [int(v) for v in values if v.strip().isdigit()]
    except Exception as e:
        print(f"[sheets] get_all_user_ids error: {e}")
        return []


def get_registered_user_ids() -> list[int]:
    """Тільки ті, хто зареєструвався."""
    try:
        sheet = _get_sheet()
        ids = sheet.col_values(COL_TG_ID)[1:]
        statuses = sheet.col_values(COL_STATUS)[1:]
        result = []
        for uid, st in zip(ids, statuses):
            if st.strip() == STATUS_REGISTERED and uid.strip().isdigit():
                result.append(int(uid))
        return result
    except Exception as e:
        print(f"[sheets] get_registered_user_ids error: {e}")
        return []


# ===== REPLY (аркуш Replies) =====

def save_admin_msg(admin_msg_id: int, user_id: int):
    """Зберігає зв'язку admin_msg_id → user_id для reply."""
    try:
        _retry(
            _get_sheet(REPLIES_SHEET).append_row,
            [str(admin_msg_id), str(user_id), datetime.now().strftime("%d.%m.%Y %H:%M:%S")],
            value_input_option="USER_ENTERED",
        )
    except Exception as e:
        print(f"[sheets] save_admin_msg error: {e}")


def get_user_for_admin_msg(admin_msg_id: int) -> int | None:
    """Знаходить user_id за admin_msg_id."""
    try:
        sheet = _get_sheet(REPLIES_SHEET)
        rows = sheet.get_all_values()[1:]  # без заголовка
        for row in rows:
            if len(row) >= 2 and str(row[0]).strip() == str(admin_msg_id):
                return int(row[1])
        return None
    except Exception as e:
        print(f"[sheets] get_user_for_admin_msg error: {e}")
        return None


# ===== SETTINGS (аркуш Settings) =====

def registration_open() -> bool:
    """Чи відкрита реєстрація."""
    try:
        sheet = _get_sheet(SETTINGS_SHEET)
        rows = sheet.get_all_values()[1:]  # без заголовка
        for row in rows:
            if len(row) >= 2 and row[0].strip() == "registration_open":
                return row[1].strip() == "1"
        return True  # default
    except Exception as e:
        print(f"[sheets] registration_open error: {e}")
        return True


def set_registration_open(open_: bool):
    """Встановлює стан реєстрації."""
    try:
        sheet = _get_sheet(SETTINGS_SHEET)
        rows = sheet.get_all_values()
        for i, row in enumerate(rows):
            if row and row[0].strip() == "registration_open":
                _retry(
                    sheet.update,
                    f"B{i+1}",
                    [["1" if open_ else "0"]],
                    value_input_option="USER_ENTERED",
                )
                return
        # якщо рядка немає — додати
        _retry(
            sheet.append_row,
            ["registration_open", "1" if open_ else "0"],
            value_input_option="USER_ENTERED",
        )
    except Exception as e:
        print(f"[sheets] set_registration_open error: {e}")
