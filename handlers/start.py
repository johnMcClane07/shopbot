from aiogram import Router, types
from aiogram.filters.command import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import replies
from db import get_user, create_user
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

router = Router()

def get_main_menu():
    buttons = [
        [
            InlineKeyboardButton(text="📦 Каталог", callback_data='catalog'),
            InlineKeyboardButton(text="🛒 Корзина", callback_data='cart'),
            InlineKeyboardButton(text="👤 Профиль", callback_data='profile'),
            InlineKeyboardButton(text="🔎 Поиск", callback_data='search')
        ],
        [
            InlineKeyboardButton(text="🌐 Подписаться на наш Telegram-канал", url="https://t.me/AnonChatBot"),
            InlineKeyboardButton(text="❓ Вопрос", url="tg://resolve?domain=YOUR_BOT_USERNAME&start=question")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def delete_old_messages(state: FSMContext, bot, chat_id):

    data = await state.get_data()
    messages_to_delete = data.get("messages", [])

    for msg_id in messages_to_delete:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception as e:
            print(f"Ошибка удаления сообщения {msg_id}: {e}")  



@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if not get_user(user_id):  
        create_user(
            user_id=user_id,
            username=message.from_user.username or "Не указан",
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )

    await delete_old_messages(state, message.bot, message.chat.id)
    await state.clear()

    msg = await message.answer(replies.WELCOME_MESSAGE, parse_mode="HTML", reply_markup=get_main_menu())

    await state.update_data(messages=[msg.message_id])  


@router.callback_query(lambda c: c.data == "main_menu")
async def cmd_main_menu(callback_query: CallbackQuery, state: FSMContext):
    await delete_old_messages(state, callback_query.bot, callback_query.message.chat.id)
    await state.clear()

    msg = await callback_query.message.answer(replies.WELCOME_MESSAGE, parse_mode="HTML", reply_markup=get_main_menu())

    await state.update_data(messages=[msg.message_id])  
    await callback_query.answer()
