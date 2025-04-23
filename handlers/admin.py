from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from db import add_product,delete_product,search,add_discount_to_product
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.filters.command import Command
import config
from aiogram.filters import BaseFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram import types
from aiogram import F
import logging


router = Router()


class AddProductState(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_photo = State()
    confirming_product = State()
    waiting_for_category = State()

class DeleteProductState(StatesGroup):
    waiting_for_product_id = State()

class AddDiscountState(StatesGroup):
    waiting_for_product_id = State()
    waiting_for_discount = State()

class IsAdminFilter(BaseFilter):
    
    async def __call__(self, obj: Message | CallbackQuery) -> bool:
        return obj.from_user.id in config.ADMIN_IDS

@router.message(Command("admin"), IsAdminFilter())
async def cmd_admin(message: Message, state: FSMContext):

    await state.clear()
    
    buttons = [
        [InlineKeyboardButton(text="Добавить товары", callback_data="admin_add_products")],
        [InlineKeyboardButton(text="Удалить товары", callback_data="admin_remove_products")],
        [InlineKeyboardButton(text="Добавить скидки", callback_data="admin_add_discounts")],
        [InlineKeyboardButton(text="⬅ Назад в меню", callback_data="main_menu")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    msg = await message.answer("👤 Панель администратора", reply_markup=keyboard)

    await state.update_data(messages=[msg.message_id])

@router.callback_query(lambda c: c.data == 'admin_menu', IsAdminFilter())
async def cmd_admin(callback_query: CallbackQuery, state: FSMContext):

    data = await state.get_data()
    messages_to_delete = data.get("messages", [])

    for msg_id in messages_to_delete:
        try:
            await callback_query.bot.delete_message(chat_id=callback_query.message.chat.id, message_id=msg_id)
        except:
            pass

    await state.clear()
    
    buttons = [
        [InlineKeyboardButton(text="Добавить товары", callback_data="admin_add_products")],
        [InlineKeyboardButton(text="Удалить товары", callback_data="admin_remove_products")],
        [InlineKeyboardButton(text="Добавить скидки", callback_data="admin_add_discounts")],
        [InlineKeyboardButton(text="⬅ Назад в меню", callback_data="main_menu")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    msg = await callback_query.message.answer("👤 Панель администратора", reply_markup=keyboard)

    await state.update_data(messages=[msg.message_id])

    await callback_query.answer()

    

@router.callback_query(lambda c: c.data == 'admin_add_products', IsAdminFilter())
async def cmd_admin_add_products(callback_query: CallbackQuery, state: FSMContext):

    data=await state.get_data()
    messages_to_delete=data.get("messages",[])

    for msg_id in messages_to_delete:
        try:
            await callback_query.bot.delete_message(chat_id=callback_query.message.chat.id, message_id=msg_id)
        except:
            pass

    await state.clear()

    data=await state.get_data()
    old_messages=data.get("messages",[])

    msg = await callback_query.message.answer("📝 Введите название товара:")

    old_messages.append(msg.message_id)

    await state.update_data(messages=old_messages)
    logging.info(f'дата из стейт {old_messages}')
    await state.set_state(AddProductState.waiting_for_name)

@router.message(AddProductState.waiting_for_name, IsAdminFilter())
async def process_name(message: types.Message, state: FSMContext):
    data=await state.get_data()
    old_messages=data.get("messages",[])
    old_messages.append(message.message_id)

    await state.update_data(name=message.text)
    
    msg =await message.answer("✏ Введите описание товара:")

    old_messages.append(msg.message_id)

    await state.update_data(messages=old_messages)
    logging.info(f'дата из стейт {old_messages}')
    await state.set_state(AddProductState.waiting_for_description)


@router.message(AddProductState.waiting_for_description, IsAdminFilter())
async def process_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    old_messages = data.get("messages", [])
    
    # Сохраняем ID сообщения с описанием
    old_messages.append(message.message_id)

    await state.update_data(description=message.text)
    
    # Запрашиваем категорию товара
    msg = await message.answer("🗂️ Выберите категорию товара:")

    # Добавляем ID сообщения в список
    old_messages.append(msg.message_id)

    # Обновляем данные в state
    await state.update_data(messages=old_messages)
    
    # Переходим к следующему шагу, запрос категории
    await state.set_state(AddProductState.waiting_for_category)


@router.message(AddProductState.waiting_for_category, IsAdminFilter())
async def process_category(message: types.Message, state: FSMContext):
    category = message.text
    
    data = await state.get_data()
    old_messages = data.get("messages", [])
    
    # Сохраняем категорию товара в состояние
    await state.update_data(category=category)
    
    # Сохраняем ID сообщения с категорией
    old_messages.append(message.message_id)

    await state.update_data(messages=old_messages)
    
    # Запрашиваем цену товара
    msg = await message.answer("💰 Введите цену товара (в рублях):")
    
    # Добавляем ID нового сообщения в список
    old_messages.append(msg.message_id)
    await state.update_data(messages=old_messages)
    
    # Переходим к следующему шагу
    await state.set_state(AddProductState.waiting_for_price)



@router.message(AddProductState.waiting_for_price, IsAdminFilter())
async def process_price(message: types.Message, state: FSMContext):
    data=await state.get_data()
    old_messages=data.get("messages",[])
    old_messages.append(message.message_id)
    try:
        price = float(message.text)
        if price <= 0:
            raise ValueError
    except ValueError:
        msg=await message.answer("❌ Введите корректную цену (число больше 0).")
        old_messages.append(msg.message_id)
        return

    msg = await message.answer("📸 Отправьте фото товара:")

    old_messages.append(msg.message_id)
    await state.update_data(messages=old_messages, price=price)

    logging.info(f'дата из стейт {old_messages}')
    await state.set_state(AddProductState.waiting_for_photo)

@router.message(AddProductState.waiting_for_photo, IsAdminFilter())
async def process_photo(message: types.Message, state: FSMContext):
    data=await state.get_data()
    old_messages=data.get("messages",[])
    old_messages.append(message.message_id)

    photo_id = message.photo[0].file_id
    logging.info(photo_id)
    await state.update_data(photo=photo_id, messages=old_messages)

    data = await state.get_data()

    confirmation_text = (
        f"🛍 <b>Добавление товара</b>\n\n"
        f"📌 <b>Название:</b> {data.get('name', 'Не указано')}\n"
        f"📝 <b>Описание:</b> {data.get('description', 'Не указано')}\n"
        f"🗂️ <b>Категория:</b> {data.get('category', 'Не указано')}\n"
        f"💰 <b>Цена:</b> {data.get('price', 'Не указано')} руб.\n\n"
        f"✅ Подтвердите добавление товара."
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_add_product")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_add_product")]
    ])

    msg = await message.answer_photo(photo=photo_id, caption=confirmation_text, parse_mode="HTML", reply_markup=keyboard)

    old_messages.append(msg.message_id)

    await state.update_data(messages=old_messages)
    logging.info(f'дата из стейт {old_messages}')
    await state.set_state(AddProductState.confirming_product)

@router.callback_query(lambda c: c.data == "confirm_add_product", IsAdminFilter())
async def confirm_add_product(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    old_messages=data.get("messages",[])

    
    add_product(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        image_url=data['photo'],
        category=data['category']
    )
    
    buttons=[
        [InlineKeyboardButton(text="Добавить еще товар", callback_data="admin_add_products")],
        [InlineKeyboardButton(text="⬅ Назад в меню", callback_data="admin_menu")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    msg = await callback_query.message.answer("✅ Товар успешно добавлен в каталог!", reply_markup=keyboard)

    old_messages.append(msg.message_id)
    await state.clear()
    await state.update_data(messages=old_messages)
    logging.info(f'дата из стейт {old_messages}')
    await callback_query.answer()

@router.callback_query(lambda c: c.data == "cancel_add_product", IsAdminFilter())
async def cancel_add_product(callback_query: CallbackQuery, state: FSMContext):
    data=await state.get_data()
    old_messages=data.get("messages",[])
    buttons=[
        [InlineKeyboardButton(text="Добавить еще товар", callback_data="admin_add_products")],
        [InlineKeyboardButton(text="⬅ Назад в меню", callback_data="admin_menu")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    msg = await callback_query.message.answer("❌ Добавление товара отменено.", reply_markup=keyboard)

    old_messages.append(msg.message_id)
    await state.update_data(messages=old_messages)

    logging.info(f'дата из стейт {old_messages}')
    await callback_query.answer()



@router.callback_query(lambda c: c.data == "admin_remove_products", IsAdminFilter())
async def cmd_admin_remove_products(callback_query: CallbackQuery, state: FSMContext):
    data=await state.get_data()
    old_messages=data.get("messages",[])

    msg = await callback_query.message.answer("📝 Введите название товара для удаления:")

    old_messages.append(msg.message_id)

    await state.update_data(messages=old_messages)
    logging.info(f'дата из стейт {old_messages}')
    await state.set_state(DeleteProductState.waiting_for_product_id)

    await callback_query.answer()

@router.message(DeleteProductState.waiting_for_product_id, IsAdminFilter())
async def search_product(message: types.Message, state: FSMContext):
    data = await state.get_data()
    old_messages = data.get("messages", [])
    old_messages.append(message.message_id)

    await state.update_data( messages=old_messages)

    msg = await message.answer("🔎 Поиск товара...")

    old_messages.append(msg.message_id)

    result = search(message.text)
    

    if result:
        

        for product in result:
            logging.info(dict(product))
            buttons = [
            [InlineKeyboardButton(text="✅ Удалить", callback_data=f"confirm_delete_product_{product['id']}")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="admin_menu")]
        ]
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            # Доступ к полям через квадратные скобки
            caption = (
        f"📌 <b>Название:</b> {product['name']}\n"
        f"📝 <b>Описание:</b> {product['description']}\n"
        f"🗂️ <b>Категория:</b> {product['category']}\n"
        f"💰 <b>Цена:</b> {product['price']} руб.\n"
    )
            
            msg = await message.answer_photo(
                photo=product['image_url'],
                caption=caption,
                parse_mode="HTML", 
                reply_markup=keyboard
            )

            old_messages.append(msg.message_id)
    else:
        msg = await message.answer("❌ Товар не найден.")

    old_messages.append(msg.message_id)

    await state.update_data(messages=old_messages)
    logging.info(f'дата из стейт {old_messages}')

@router.callback_query(lambda c: c.data.startswith("confirm_delete_product_"), IsAdminFilter())
async def confirm_delete_product(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    old_messages = data.get("messages", [])
    logging.info(f'{callback_query.data}')
    product_id = callback_query.data.split("_")[3]

    delete_product(product_id)

    buttons=[
        [InlineKeyboardButton(text="⬅ Назад в меню", callback_data="admin_menu")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    msg = await callback_query.message.answer("✅ Товар успешно удален.", reply_markup=keyboard)

    old_messages.append(msg.message_id)
    await state.clear()
    await state.update_data(messages=old_messages)
    logging.info(f'дата из стейт {old_messages}')
    await callback_query.answer()






    















@router.callback_query(lambda c: c.data == "admin_add_discounts", IsAdminFilter())
async def cmd_admin_add_discount(callback_query: CallbackQuery, state: FSMContext):
    data=await state.get_data()
    old_messages=data.get("messages",[])

    msg = await callback_query.message.answer("📝 Введите название товара:")

    old_messages.append(msg.message_id)

    await state.update_data(messages=old_messages)
    logging.info(f'дата из стейт {old_messages}')
    await state.set_state(AddDiscountState.waiting_for_product_id)

    await callback_query.answer()

# Обработчик перехода к добавлению скидки для товара
@router.callback_query(lambda c: c.data.startswith("confirm_add_discount_"), IsAdminFilter())
async def confirm_add_discount(callback_query: CallbackQuery, state: FSMContext):
    # Извлекаем ID продукта из callback_data
    product_id = int(callback_query.data.split("_")[3])

    # Сохраняем ID товара в состояние
    await state.update_data(product_id=product_id)

    # Запрашиваем скидку для товара
    msg = await callback_query.message.answer("💸 Введите скидку для этого товара (в процентах):")
    
    # Сохраняем ID этого сообщения для будущего удаления
    data = await state.get_data()
    old_messages = data.get("messages", [])
    old_messages.append(msg.message_id)
    await state.update_data(messages=old_messages)

    # Подтверждаем действие
    await callback_query.answer()

# Обработчик ввода скидки для товара
@router.message(AddDiscountState.waiting_for_discount, IsAdminFilter())
async def process_discount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    old_messages = data.get("messages", [])
    old_messages.append(message.message_id)

    # Получаем ID товара из состояния
    product_id = data.get("product_id")

    try:
        # Преобразуем введенную скидку в число
        discount_value = float(message.text)

        # Проверяем, что скидка находится в допустимом диапазоне
        if discount_value < 0 or discount_value > 100:
            raise ValueError

    except ValueError:
        msg = await message.answer("❌ Пожалуйста, введите корректную скидку (от 0 до 100).")
        old_messages.append(msg.message_id)
        await state.update_data(messages=old_messages)
        return

    # Сохраняем скидку в базу данных
    add_discount_to_product(product_id, discount_value)

    # Подтверждаем добавление скидки
    msg = await message.answer(f"✅ Скидка {discount_value}% успешно добавлена для товара.")
    
    old_messages.append(msg.message_id)
    await state.update_data(messages=old_messages)

    logging.info(f'Данные из стейт {old_messages}')

    # Возвращаем состояние к ожиданию ID товара для следующего действия
    await state.set_state(AddDiscountState.waiting_for_product_id)

# Обработчик поиска товара для добавления скидки
@router.message(AddDiscountState.waiting_for_product_id, IsAdminFilter())
async def search_product(message: types.Message, state: FSMContext):
    data = await state.get_data()
    old_messages = data.get("messages", [])
    old_messages.append(message.message_id)

    await state.update_data(messages=old_messages)

    msg = await message.answer("🔎 Поиск товара...")

    old_messages.append(msg.message_id)

    # Ищем продукт по названию
    result = search(message.text)
    
    # Если товар найден, показываем его и предлагаем добавить скидку
    if result:
        for product in result:
            buttons = [
                [InlineKeyboardButton(text="✅ Добавить", callback_data=f"confirm_add_discount_{product['id']}")],
                [InlineKeyboardButton(text="❌ Отменить", callback_data="admin_menu")]
            ]
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            # Отправляем фото и информацию о товаре
            msg = await message.answer_photo(
                photo=product['image_url'],
                caption=f"📌 <b>Название:</b> {product['name']}\n"
                        f"📝 <b>Описание:</b> {product['description']}\n"
                        f"🗂️ <b>Категория:</b> {product['category']}\n"  
                        f"💰 <b>Цена:</b> {product['price']} руб.\n",
                parse_mode="HTML", 
                reply_markup=keyboard
            )

            # Добавляем ID сообщения в список для возможного удаления
            old_messages.append(msg.message_id)
    else:
        msg = await message.answer("❌ Товар не найден.")

    old_messages.append(msg.message_id)

    await state.update_data(messages=old_messages)
    logging.info(f'Данные из стейт {old_messages}')

    # Переходим к следующему состоянию (ожидание ID товара для скидки)
    await state.set_state(AddDiscountState.waiting_for_discount)
