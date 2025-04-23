from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from db import get_products_by_category
from aiogram.fsm.context import FSMContext
from handlers.start import delete_old_messages


router = Router()

@router.callback_query(lambda c: c.data == 'catalog')
async def cmd_catalog(callback_query: CallbackQuery, state: FSMContext):
    
    buttons = [
        [
            InlineKeyboardButton(text='Смартфоны', callback_data='category_smartphones'),
            InlineKeyboardButton(text='Планшеты', callback_data='category_tablets')
        ],
        [
            InlineKeyboardButton(text='Ноутбуки', callback_data='category_laptops'),
            InlineKeyboardButton(text='Аксессуары', callback_data='category_accessories')
        ],
        [
            InlineKeyboardButton(text="⬅ Назад", callback_data="main_menu")
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    
    await delete_old_messages(state, callback_query.bot, callback_query.message.chat.id) 

    msg = await callback_query.message.answer("📦 <b>Выберите категорию</b>:", parse_mode='HTML', reply_markup=keyboard)
    
    await state.update_data(messages=[msg.message_id])
    
    await callback_query.answer()

@router.callback_query(lambda c: c.data.startswith('category_'))
async def cmd_products(callback_query: CallbackQuery, state: FSMContext):
    category = callback_query.data

    products = get_products_by_category(category)

    await delete_old_messages(state, callback_query.bot, callback_query.message.chat.id)

    await state.update_data(messages=[])

    empty_buttons = [
            [InlineKeyboardButton(text="⬅ Назад к категориям", callback_data="catalog")]
        ]
    empty_keyboard = InlineKeyboardMarkup(inline_keyboard=empty_buttons)

    if not products:
        msg = await callback_query.message.answer("В этой категории пока нет товаров.", reply_markup=empty_keyboard)
        await state.update_data(messages=[msg.message_id])
        await callback_query.answer()
        return

    new_messages = []

    for product in products:
        text = f"<b>{product['name']}</b>\n\n{product['description']}\n💰 Цена: {product['price']} руб."

        buttons = [
            [InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data=f"add_to_cart_{product['id']}")],
            [InlineKeyboardButton(text="⬅ Назад к категориям", callback_data="catalog")]
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        msg = await callback_query.bot.send_photo(
            chat_id=callback_query.message.chat.id,
            photo=product['image_url'],
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        new_messages.append(msg.message_id)

    await state.update_data(messages=new_messages)

    await callback_query.answer()

