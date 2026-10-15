import re
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states import Registration
from keyboards import institutes_kb, confirm_kb, back_to_menu_kb, main_menu_kb
import sheets
from database import (
    is_registered, mark_registered, unmark_registered, registration_open,
)

router = Router()


@router.callback_query(F.data == "reg_start")
async def reg_start(call: CallbackQuery, state: FSMContext):
    if not registration_open():
        await call.answer("Реєстрацію закрито 😔", show_alert=True)
        return
    if is_registered(call.from_user.id):
        await call.answer("Ти вже зареєстрований ✅", show_alert=True)
        return
    await state.set_state(Registration.first_name)
    await call.message.edit_text(
        "Крок 1/4. Введи своє <b>Ім'я</b>:",
        parse_mode="HTML",
        reply_markup=None,
    )
    await call.answer()


@router.message(Registration.first_name, F.text)
async def reg_first(message: Message, state: FSMContext):
    await state.update_data(first_name=message.text.strip())
    await state.set_state(Registration.last_name)
    await message.answer("Крок 2/4. Введи своє <b>Прізвище</b>:", parse_mode="HTML")


@router.message(Registration.last_name, F.text)
async def reg_last(message: Message, state: FSMContext):
    await state.update_data(last_name=message.text.strip())
    await state.set_state(Registration.institute)
    await message.answer("Крок 3/4. Обери свій <b>інститут</b>:", parse_mode="HTML",
                         reply_markup=institutes_kb())


@router.callback_query(Registration.institute, F.data.startswith("inst:"))
async def reg_institute(call: CallbackQuery, state: FSMContext):
    inst = call.data.split(":", 1)[1]
    await state.update_data(institute=inst)
    await state.set_state(Registration.group)
    await call.message.edit_text(
        f"Інститут: <b>{inst}</b>\n\nКрок 4/4. Введи свою <b>групу</b> (наприклад, АР-112):",
        parse_mode="HTML",
    )
    await call.answer()


@router.message(Registration.group, F.text)
async def reg_group(message: Message, state: FSMContext):
    group = message.text.strip().upper()
    # Курс — перша цифра з номера групи
    m = re.search(r"\d", group)
    if not m:
        await message.answer("У групі має бути хоча б одна цифра. Спробуй ще раз 👇")
        return
    course = m.group(0)

    await state.update_data(group=group, course=course)
    data = await state.get_data()

    summary = (
        "Перевір свої дані 👇\n\n"
        f"👤 Ім'я: <b>{data['first_name']}</b>\n"
        f"👤 Прізвище: <b>{data['last_name']}</b>\n"
        f"🏛 Інститут: <b>{data['institute']}</b>\n"
        f"🎓 Група: <b>{data['group']}</b> (курс {data['course']})\n\n"
        "Все вірно?"
    )
    await state.set_state(Registration.confirm)
    await message.answer(summary, parse_mode="HTML", reply_markup=confirm_kb())


@router.callback_query(Registration.confirm, F.data == "reg_confirm")
async def reg_confirm(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    try:
        sheets.save_registration(
            call.from_user.id,
            data["first_name"], data["last_name"],
            data["institute"], data["group"], data["course"],
        )
        mark_registered(call.from_user.id)
        await call.message.edit_text(
            "🎉 Готово! Тебе зареєстровано на тренінг.\n"
            "Чекаємо на тебе в п'ятницю, 23 жовтня, в Студентській бібліотеці 😊",
            reply_markup=back_to_menu_kb(is_reg=True),
        )
    except Exception as e:
        print(f"[reg_confirm] error: {e}")
        await call.message.edit_text(
            "Ой, сталася помилка при збереженні 😔\nСпробуй пізніше або напиши адміну.",
            reply_markup=back_to_menu_kb(),
        )
    await state.clear()
    await call.answer()


@router.callback_query(F.data == "cancel")
async def reg_cancel_dialog(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Окей, скасовано.", reply_markup=main_menu_kb(is_registered(call.from_user.id)))
    await call.answer()


@router.callback_query(F.data == "reg_cancel")
async def reg_cancel_registration(call: CallbackQuery, state: FSMContext):
    """Скасування вже наявної реєстрації."""
    await state.clear()
    try:
        sheets.clear_registration(call.from_user.id)
        unmark_registered(call.from_user.id)
        await call.message.edit_text(
            "🗑 Твою реєстрацію скасовано.\n"
            "Якщо захочеш знову — натисни «Так, хочу зареєструватись».",
            reply_markup=main_menu_kb(is_reg=False),
        )
    except Exception as e:
        print(f"[reg_cancel] error: {e}")
        await call.message.edit_text("Не вдалося скасувати 😔 Спробуй пізніше.")
    await call.answer()