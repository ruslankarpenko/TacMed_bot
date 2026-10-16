from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import INSTITUTES, NOT_STUDENT


def main_menu_kb(is_reg: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="✅ Так, хочу зареєструватись", callback_data="reg_start")],
        [InlineKeyboardButton(text="ℹ️ Про тренінг", callback_data="about")],
        [InlineKeyboardButton(text="✉️ Зворотній зв'язок", callback_data="feedback")],
    ]
    if is_reg:
        rows.append([InlineKeyboardButton(text="🗑 Скасувати реєстрацію", callback_data="reg_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def institutes_kb() -> InlineKeyboardMarkup:
    rows = []
    row = []
    for inst in INSTITUTES:
        if inst == NOT_STUDENT:
            continue  # додамо окремим рядком знизу
        row.append(InlineKeyboardButton(text=inst, callback_data=f"inst:{inst}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    # Окрема кнопка на всю ширину
    rows.append([InlineKeyboardButton(
        text=f"🎓 {NOT_STUDENT}",
        callback_data=f"inst:{NOT_STUDENT}",
    )])
    rows.append([InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Підтвердити", callback_data="reg_confirm")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel")],
    ])


def back_to_menu_kb(is_reg: bool = False) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="🏠 Головне меню", callback_data="menu")]]
    if is_reg:
        rows.append([InlineKeyboardButton(text="🗑 Скасувати реєстрацію", callback_data="reg_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_menu_kb(reg_open: bool) -> InlineKeyboardMarkup:
    toggle = "🔒 Закрити реєстрацію" if reg_open else "🔓 Відкрити реєстрацію"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Розсилка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="✉️ Написати користувачу", callback_data="admin_dm")],
        [InlineKeyboardButton(text=toggle, callback_data="admin_toggle_reg")],
    ])


def broadcast_audience_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Всі, хто запускав бота", callback_data="bc:all")],
        [InlineKeyboardButton(text="✅ Тільки зареєстровані", callback_data="bc:reg")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="admin_cancel")],
    ])


def admin_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="admin_cancel")],
    ])
