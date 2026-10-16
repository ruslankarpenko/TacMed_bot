from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
import asyncio

from config import ADMIN_ID
from states import AdminFlow
from keyboards import (
    admin_menu_kb, broadcast_audience_kb, admin_cancel_kb,
)
from database import (
    all_users, registered_users, registration_open, set_registration_open,
)

router = Router()


def _is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


@router.message(F.text == "/admin")
async def admin_panel(message: Message):
    if not _is_admin(message.from_user.id):
        return
    await message.answer(
        "🛠 <b>Адмін-панель</b>\n\nОбери дію:",
        parse_mode="HTML",
        reply_markup=admin_menu_kb(registration_open()),
    )


@router.callback_query(F.data == "admin_cancel")
async def admin_cancel(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return
    await state.clear()
    await call.message.edit_text(
        "🛠 <b>Адмін-панель</b>\n\nОбери дію:",
        parse_mode="HTML",
        reply_markup=admin_menu_kb(registration_open()),
    )
    await call.answer()


# ===== РЕЄСТРАЦІЯ: відкрити/закрити =====
@router.callback_query(F.data == "admin_toggle_reg")
async def admin_toggle_reg(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        return
    new_state = not registration_open()
    set_registration_open(new_state)
    await call.message.edit_text(
        f"Реєстрацію {'відкрито 🔓' if new_state else 'закрито 🔒'}.\n\n🛠 <b>Адмін-панель</b>:",
        parse_mode="HTML",
        reply_markup=admin_menu_kb(new_state),
    )
    await call.answer("Готово")


# ===== РОЗСИЛКА =====
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return
    await state.set_state(AdminFlow.broadcast_choose_audience)
    await call.message.edit_text(
        "📢 <b>Кому надіслати?</b>",
        parse_mode="HTML",
        reply_markup=broadcast_audience_kb(),
    )
    await call.answer()


@router.callback_query(AdminFlow.broadcast_choose_audience, F.data.startswith("bc:"))
async def admin_broadcast_audience(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return
    audience = call.data.split(":", 1)[1]  # all | reg
    await state.update_data(audience=audience)
    await state.set_state(AdminFlow.broadcast_content)
    label = "усім" if audience == "all" else "зареєстрованим"
    await call.message.edit_text(
        f"📝 Надішли повідомлення для розсилки {label}.\n"
        "Можна текст, фото або файл. (Підпис до фото — якщо треба).",
        reply_markup=admin_cancel_kb(),
    )
    await call.answer()


@router.message(AdminFlow.broadcast_content)
async def admin_broadcast_send(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    data = await state.get_data()
    audience = data.get("audience", "all")

    targets = all_users() if audience == "all" else registered_users()
    targets = [uid for uid in targets if uid != ADMIN_ID]

    sent, failed = 0, 0
    status = await message.answer(f"⏳ Розсилаю... (0/{len(targets)})")

    for i, uid in enumerate(targets, 1):
        try:
            await message.copy_to(uid)
            sent += 1
        except Exception:
            failed += 1
        if i % 20 == 0:
            try:
                await status.edit_text(f"⏳ Розсилаю... ({i}/{len(targets)})")
            except Exception:
                pass
        await asyncio.sleep(0.05)  # щоб не зловити flood-wait

    await status.edit_text(
        f"✅ Розсилку завершено.\n"
        f"Надіслано: {sent}\n"
        f"Не вдалося: {failed}",
        reply_markup=admin_menu_kb(registration_open()),
    )
    await state.clear()


# ===== ІНДИВІДУАЛЬНЕ ПОВІДОМЛЕННЯ =====
@router.callback_query(F.data == "admin_dm")
async def admin_dm_start(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        return
    await state.set_state(AdminFlow.dm_user_id)
    await call.message.edit_text(
        "✉️ Надішли <b>Telegram ID</b> користувача, якому хочеш написати:",
        parse_mode="HTML",
        reply_markup=admin_cancel_kb(),
    )
    await call.answer()


@router.message(AdminFlow.dm_user_id, F.text)
async def admin_dm_id(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    text = message.text.strip()
    if not text.lstrip("-").isdigit():
        await message.answer("Це не схоже на ID. Спробуй ще раз (тільки цифри).")
        return
    await state.update_data(target_id=int(text))
    await state.set_state(AdminFlow.dm_content)
    await message.answer(
        f"Тепер надішли повідомлення для <code>{text}</code> (текст/фото/файл):",
        parse_mode="HTML",
        reply_markup=admin_cancel_kb(),
    )


@router.message(AdminFlow.dm_content)
async def admin_dm_send(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    data = await state.get_data()
    target_id = data["target_id"]

    try:
        await message.bot.send_message(target_id, "📬 <b>Повідомлення від адміністратора:</b>",
                                       parse_mode="HTML")
        await message.copy_to(target_id)
        await message.answer("✅ Надіслано.",
                             reply_markup=admin_menu_kb(registration_open()))
    except Exception as e:
        await message.answer(f"❌ Не вдалося: {e}",
                             reply_markup=admin_menu_kb(registration_open()))
    await state.clear()
