from aiogram import Router 
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram import types
from db import search 
from handlers.start import delete_old_messages


router = Router()

class SearchState(StatesGroup):
    search = State()


@router.callback_query(lambda c: c.data == "search")
async def cmd_search(callback_query: CallbackQuery, state: FSMContext):
    await delete_old_messages(state, callback_query.bot, callback_query.message.chat.id)

    msg = await callback_query.message.answer("🔍 Введите слово для поиска:")
    await state.update_data(messages=[msg.message_id])

    await state.set_state(SearchState.search)
    await callback_query.answer()


@router.message(SearchState.search)
async def handle_search(message: types.Message, state: FSMContext):
    await delete_old_messages(state, message.bot, message.chat.id)

    search_query = message.text
    results = search(search_query)  

    new_messages = [message.message_id]  

    if not results:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅ Вернуться в меню", callback_data="main_menu")]
        ])
        
        msg = await message.answer(
            "❌ Ничего не найдено. Попробуйте другой запрос.",
            reply_markup=keyboard
        )
        
        new_messages.append(msg.message_id)
    else:
        for product in results:
            text = f"<b>{product['name']}</b>\n\n{product['description']}\n💰 Цена: {product['price']} руб."

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data=f"add_to_cart_{product['id']}")],
                [InlineKeyboardButton(text="⬅ Назад в меню", callback_data="main_menu")]
            ])

            msg = await message.bot.send_photo(
                chat_id=message.chat.id,
                photo=product['image_url'],
                caption=text,
                parse_mode="HTML",
                reply_markup=keyboard
            )

            new_messages.append(msg.message_id)

    await state.update_data(messages=new_messages) 




    

