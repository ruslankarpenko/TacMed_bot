from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states import Feedback
from keyboards import back_to_menu_kb
from config import ADMIN_ID
from sheets import save_admin_msg, is_registered, get_user_for_admin_msg

router = Router()


@router.callback_query(F.data == "feedback")
async def feedback_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(Feedback.waiting)
    await call.message.edit_text(
        "✉️ Напиши своє повідомлення адміністратору — я передам.\n"
        "Можна надіслати текст, фото або файл.",
        reply_markup=back_to_menu_kb(is_registered(call.from_user.id)),
    )
    await call.answer()


@router.message(Feedback.waiting)
async def feedback_send(message: Message, state: FSMContext):
    u = message.from_user
    header = (
        f"📨 <b>Нове звернення</b>\n"
        f"Від: <a href='tg://user?id={u.id}'>{u.full_name}</a>\n"
        f"ID: <code>{u.id}</code>\n"
        f"Username: @{u.username if u.username else '—'}\n"
        f"━━━━━━━━━━━━━━━\n"
    )

    try:
        await message.bot.send_message(ADMIN_ID, header, parse_mode="HTML")
        sent = await message.copy_to(ADMIN_ID)
        save_admin_msg(sent.message_id, u.id)
        await message.answer(
            "✅ Повідомлення надіслано адміну. Очікуй на відповідь!",
            reply_markup=back_to_menu_kb(is_registered(u.id)),
        )
    except Exception as e:
        print(f"[feedback] error: {e}")
        await message.answer("Не вдалося надіслати 😔 Спробуй пізніше.")

    await state.clear()


@router.message(F.reply_to_message, F.from_user.id == ADMIN_ID)
async def admin_reply(message: Message):
    """Адмін робить reply на переіслане повідомлення → відповідь летить юзеру."""
    from database import get_user_for_admin_msg
    replied_id = message.reply_to_message.message_id
    user_id = get_user_for_admin_msg(replied_id)
    if not user_id:
        return  # це не відповідь на звернення

    try:
        await message.bot.send_message(user_id, "📬 <b>Відповідь від адміністратора:</b>",
                                       parse_mode="HTML")
        await message.copy_to(user_id)
        await message.answer("✅ Відправлено.")
    except Exception as e:
        await message.answer(f"❌ Не вдалося: {e}")
