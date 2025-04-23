from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import PreCheckoutQuery
from handlers.start import delete_old_messages
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import PreCheckoutQuery
from db import get_user, get_users_cart

router = Router()

class OrderState(StatesGroup):
    waiting_for_address = State()
    confirming_order = State()


async def update_messages_state(state: FSMContext, new_message_id: int):
    data = await state.get_data()
    messages = data.get("messages", [])
    messages.append(new_message_id)
    await state.update_data(messages=messages)

def get_order_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", callback_data="pay")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")]
    ])

def get_order_confirmation_text(user_cart, user_address):
    total_price = sum(product['price'] * product['quantity'] for product in user_cart)
    confirmation_text = (
        f"✅ Ваш заказ:\n"
        + "\n".join([f"🔹 {product['name']} — {product['price']} руб. Кол-во: {product['quantity']}" for product in user_cart])
        + f"\n📍 Адрес: {user_address}\n"
        f"💰 Итоговая сумма: {total_price} руб.\n\n"
        f"Нажмите 'Оплатить', чтобы завершить заказ."
    )
    return confirmation_text

@router.callback_query(lambda c: c.data == "order")
async def order_start(callback_query: CallbackQuery, state: FSMContext):
    msg = await callback_query.message.answer("Введите ваш адрес:")
    await update_messages_state(state, msg.message_id)
    await state.set_state(OrderState.waiting_for_address)

@router.message(OrderState.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    user_address = message.text
    data = await state.get_data()


    await state.update_data(address=user_address)
    user = get_user(message.from_user.id)
    if not user:
        msg = await message.answer("Пользователь не найден.")
        return

    user_cart = get_users_cart(message.from_user.id)
    confirmation_text = get_order_confirmation_text(user_cart, user_address)
    keyboard = get_order_confirmation_keyboard()

    msg = await message.answer(confirmation_text, reply_markup=keyboard)
    await update_messages_state(state, msg.message_id)

    await state.set_state(OrderState.confirming_order)

@router.callback_query(lambda c: c.data == "pay")
async def process_payment(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_address = data.get("address", "не указан")

    msg = await callback_query.message.answer_invoice(
        title="Оплата заказа",
        description=f"Ваш заказ будет доставлен по адресу: {user_address}",
        payload="order_12345",
        provider_token="ТОКЕН_ЮКАССЫ_ИЛИ_ДРУГОЙ_ПЛАТЕЖКИ",
        currency="RUB",
        prices=[{"label": "Сумма", "amount": 199900}],  
        start_parameter="order-payment"
    )

    await update_messages_state(state, msg.message_id)

    await callback_query.answer()

@router.pre_checkout_query(lambda query: True)
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(lambda message: message.successful_payment)
async def payment_success(message: Message, state: FSMContext):
    data = await state.get_data()
    user_address = data.get("address", "не указан")
    messages_to_delete = data.get("messages", [])

    msg = await message.answer(f"✅ Оплата прошла успешно!\n🚚 Заказ скоро будет доставлен по адресу: {user_address}")

    await delete_old_messages(state, message.bot, message.chat.id)

    await state.clear()

    await state.update_data(messages=[msg.message_id])


