from aiogram import Router
import logging
from aiogram.types import CallbackQuery
from db import add_to_cart,get_users_cart,delete_from_cart
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from handlers.start import delete_old_messages  


router=Router()

@router.callback_query(lambda c: c.data.startswith("add_to_cart_"))
async def add_to_cart_handler(callback_query: CallbackQuery, state: FSMContext):
    await state.clear()

    user_id = callback_query.from_user.id 
    product_id = callback_query.data.split("_")[3]


    add_to_cart(product_id,user_id)
    
    buttons = [
        [InlineKeyboardButton(text="✅ Добавлено в корзину", callback_data="nothing")],  
        [InlineKeyboardButton(text="⬅ Назад к категориям", callback_data='catalog')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback_query.message.edit_reply_markup(reply_markup=keyboard)
    await callback_query.answer("Товар добавлен в корзину!")

  


@router.callback_query(lambda c: c.data.startswith("add_one_more_to_cart_"))
async def add_one_more_to_cart_handler(callback_query: CallbackQuery, state: FSMContext):

    user_id = callback_query.from_user.id 
    product_id = callback_query.data.split("_")[5]


    add_to_cart(product_id,user_id)
    
    buttons = [
        [InlineKeyboardButton(text="✅ Добавлено в корзину", callback_data="nothing")],  
        [InlineKeyboardButton(text="⬅ Назад к категориям", callback_data='catalog')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback_query.message.edit_reply_markup(reply_markup=keyboard)

    await callback_query.answer("Товар добавлен в корзину!")

    await show_cart(callback_query,state)
    

@router.callback_query(lambda c: c.data.startswith("remove_from_cart_"))
async def delete_from_cart_handler(callback_query: CallbackQuery, state: FSMContext):
    print(f"DEBUG: callback_query.data = {callback_query.data}")

    user_id = callback_query.from_user.id 
    product_id = callback_query.data.split("_")[3]
    print(f"DEBUG: product_id = {product_id}")

    delete_from_cart(user_id,product_id)

    await callback_query.message.delete()
    await callback_query.answer("Товар удален из корзины!")
    await show_cart(callback_query,state)



@router.callback_query(lambda c: c.data == 'cart')
async def show_cart(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_cart = get_users_cart(user_id)

    await delete_old_messages(state, callback_query.bot, callback_query.message.chat.id)

    new_messages = []
    total_price = 0

    
    if not user_cart:
        buttons_empty_cart = [[InlineKeyboardButton(text="⬅ Назад в меню", callback_data='main_menu')]]
        keyboard_empty_cart = InlineKeyboardMarkup(inline_keyboard=buttons_empty_cart)

        empty_cart = await callback_query.message.answer(
            "🛒 Ваша корзина пуста.", parse_mode="HTML", reply_markup=keyboard_empty_cart
        )
        await callback_query.answer("")
        await state.update_data(messages=[empty_cart.message_id])  
        return

    
    for product in user_cart:
        total_price += product["price"] * product["quantity"]

        text = (
            f"<b>{product.get('name', 'Без названия')}</b>\n\n"
            f"{product.get('description', 'Описание отсутствует')}\n"
            f"💰 Цена: {product.get('price', 'Не указана')} руб.\n"
            f"📦 Количество: {product.get('quantity', 'Не указано')}\n"
        )

        buttons = [
            [InlineKeyboardButton(text="➕ Добавить еще", callback_data=f"add_one_more_to_cart_{product.get('id', 0)}")],
            [InlineKeyboardButton(text="🗑 Удалить из корзины", callback_data=f"remove_from_cart_{int(product['id'])}")]
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        msg = await callback_query.bot.send_photo(
            chat_id=callback_query.message.chat.id,
            photo=product.get('image_url', 'https://via.placeholder.com/150'),
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await callback_query.answer("")
        new_messages.append(msg.message_id)

    
    buttons2 = [
        [InlineKeyboardButton(text="⬅ Назад в меню", callback_data='main_menu')],
        [InlineKeyboardButton(text="🛒 Оформить заказ", callback_data='order')]
    ]
    keyboard2 = InlineKeyboardMarkup(inline_keyboard=buttons2)

    final_cart_message = await callback_query.message.answer(
        f"🛒 <b>Итоговая стоимость вашей корзины:</b> {total_price} руб.",
        parse_mode="HTML",
        reply_markup=keyboard2
    )
    new_messages.append(final_cart_message.message_id)

    await state.update_data(messages=new_messages)

    await callback_query.answer()





    

    


    
