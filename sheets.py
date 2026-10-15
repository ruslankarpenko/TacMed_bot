import os
import json
import time
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


def _load_credentials():
    """Читає credentials з env-змінної (пріоритет) або з файлу (локально)."""
    json_str = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if json_str:
        print("=" * 60)
        print(f"[creds] Довжина JSON: {len(json_str)} символів")
        print(f"[creds] Починається з: {json_str[:50]!r}")
        print(f"[creds] Закінчується на: {json_str[-60:]!r}")
        print(f"[creds] Містить '\\n': {'\\n' in json_str}")
        print(f"[creds] Містить реальні переноси: {chr(10) in json_str}")

        info = json.loads(json_str)
        print(f"[creds] client_email: {info.get('client_email')}")
        print(f"[creds] private_key_id: {info.get('private_key_id')}")
        print(f"[creds] project_id: {info.get('project_id')}")
        pk = info.get('private_key', '')
        print(f"[creds] private_key починається з: {pk[:30]!r}")
        print(f"[creds] private_key закінчується на: {pk[-30:]!r}")
        print(f"[creds] Довжина private_key: {len(pk)}")
        print("=" * 60)
        return Credentials.from_service_account_info(info, scopes=SCOPES)

    print("[creds] Використовую файл credentials.json (локальна розробка)")
    return Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)


def _retry(func, *args, max_retries=4, **kwargs):
    """Повторює виклик при мережевих помилках (SSL, timeout)."""
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


def _get_sheet():
    global _client, _sheet
    if _sheet is None:
        def _init():
            global _client, _sheet
            creds = _load_credentials()   # ← ✅ ТУТ викликаємо правильно
            _client = gspread.authorize(creds)
            _sheet = _client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
        _retry(_init)
    return _sheet


def _find_row(user_id: int):
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
