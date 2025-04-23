from aiogram import Router 
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from db import get_user
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import replies
from handlers.start import delete_old_messages

router = Router()


@router.callback_query(lambda c: c.data == 'profile')
async def cmd_profile(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user = get_user(user_id)

    await delete_old_messages(state, callback_query.bot, callback_query.message.chat.id)

    buttons = [
        [InlineKeyboardButton(text="Изменить данные", callback_data="edit_profile")],
        [InlineKeyboardButton(text="История заказов", callback_data="order_history")],
        [InlineKeyboardButton(text="⬅ Назад в меню", callback_data="main_menu")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    msg = await callback_query.message.answer(replies.PROFILE_TEXT.format(user["first_name"], user["last_name"], user["username"]), parse_mode="HTML", reply_markup=keyboard)

    await state.update_data(messages=[msg.message_id])

    await callback_query.answer()


