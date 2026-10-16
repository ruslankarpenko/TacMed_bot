from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile

from keyboards import main_menu_kb, back_to_menu_kb
from sheets import ensure_user_row, is_registered
import sheets

router = Router()

WELCOME = (
    "Привіт! 👋\n\n"
    "Тут можна зареєструватись на тренінг з тактичної медицини.\n"
    "Скажи, чи це тебе цікавить?"
)

ABOUT = (
    "🩺 <b>Про тренінг з тактичної медицини</b>\n\n"
    "Коли поруч людина потребує допомоги, часу на пошуки інструкцій немає.\n\n"
    "На вишколі з тактичної медицини ти дізнаєшся, як діяти при критичних кровотечах, "
    "правильно використовувати турнікет та надавати першу домедичну допомогу в умовах, "
    "наближених до реальних. А також — розбереш інші важливі навички, які можуть врятувати життя.\n\n"
    "🗓️ <b>Коли:</b> 23 жовтня, 12:00–16:00\n"
    "📍 <b>Де:</b> Студентська бібліотека «3 поверх» Митрополита Андрея 3, корпус 28\n\n"
    "Пройди інструктаж із тактичної медицини разом із інструктором "
    "12-ї бригади спеціального призначення «Азов» та відділу 4308.OSVITA\n\n"
    "Реєстрація — через кнопку в головному меню 👇"
)

PHOTO_PATH = "photo.png"

@router.message(CommandStart())
async def cmd_start(message: Message):
    u = message.from_user
    add_user(u.id, u.username, u.first_name)
    # Додаємо рядок у Google Таблицю, якщо його ще немає
    try:
        sheets.ensure_user_row(u.id, u.username, u.first_name)
    except Exception as e:
        print(f"[start] sheets error: {e}")

    await message.answer(WELCOME, reply_markup=main_menu_kb(is_registered(u.id)))


@router.callback_query(F.data == "about")
async def cb_about(call: CallbackQuery):
    try:
        await call.message.delete()
    except Exception:
        pass

    photo = FSInputFile(PHOTO_PATH)
    await call.message.answer_photo(
        photo=photo,
        caption=ABOUT,
        parse_mode="HTML",
        reply_markup=back_to_menu_kb(is_registered(call.from_user.id)),
    )
    await call.answer()


@router.callback_query(F.data == "menu")
async def cb_menu(call: CallbackQuery):
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(
        WELCOME,
        reply_markup=main_menu_kb(is_registered(call.from_user.id)),
    )
    await call.answer()
