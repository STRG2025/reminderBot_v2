import asyncio
from datetime import datetime, timedelta
from xmlrpc.client import DateTime
from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from scheduler import scheduler 

router = Router()

# Класс состояний FSM
class RemindStates(StatesGroup):
    waiting_for_time = State()  # Состояние ожидания времени
    waiting_for_text = State()  # Состояние ожидания текста

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        'Привет! Я бот-напоминалка.\n'
        'Чтобы создать напоминание - введите /remind'
        'Чтобы удалить существующение напоминание - введите /cancel'
    )

@router.message(Command("remind"))
async def cmd_remind(message: types.Message, state: FSMContext):
    await message.answer(
        'На какое время установить напоминание?\n'
        'Формат: HH:MM (например, 14:30)'
    )
    # Состояние ожидания времени
    await state.set_state(RemindStates.waiting_for_time)

async def send_remind(bot: Bot, user_id: int, text: str):
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f'Напоминание:\n{text}'
        )
    except Exception as e:
        print(f'Ошибка отправки: {e}')


@router.message(RemindStates.waiting_for_time)
async def take_time(message: types.Message, state: FSMContext): 
    try:
            # Сплитуем время из сообщения
            remind_time = datetime.strptime(message.text, '%H:%M').time()
            if remind_time <= datetime.now().time():
                await message.answer('Ошибка пространственно-временного континуума. Время должно быть в будущем!')
                return

            # Сохраняем время в FSM
            await state.update_data(remind_time = message.text)

            # Запрашиваем текст напоминания
            await message.answer('Теперь введите текст напоминания :')
            await state.set_state(RemindStates.waiting_for_text)

    except ValueError:
            await message.answer('Ошибка ввода времени. Проверьте корректность формата')


@router.message(RemindStates.waiting_for_text)
async def take_text(message: types.Message, state: FSMContext, bot: Bot):
    # Получаем сохранённое время
    data = await state.get_data()
    remind_time = data['remind_time']
    
    # Рассчитываем полную дату
    target_time = datetime.strptime(remind_time, "%H:%M").time()
    target_datetime = datetime.combine(datetime.now().date(), target_time)
    
    # Если время уже прошло сегодня, переносим на завтра
    if target_datetime < datetime.now():
        target_datetime += timedelta(days=1)
    
    # Добавляем задачу в планировщик
    scheduler.add_job (
        send_remind,  # Функция для отправки
        'date',
        run_date=target_datetime,
        args=(bot, message.from_user.id, message.text)
    )
    
    await message.answer(
        f'Напоминание установлено на {target_datetime.strftime('%H:%M %d.%m.%Y')}:\n'
        f' {message.text}'
    )
    await state.clear()  # Завершаем FSM


@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено")




