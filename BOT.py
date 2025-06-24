import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

# Завантажимо налаштування
load_dotenv()
API_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not API_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is not set. Please create a .env file with TELEGRAM_TOKEN=<your token>")

# Ініціалізація бота
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Встановлюємо команду меню «Почнемо»
async def on_startup(dp: Dispatcher):
    await bot.set_my_commands([
        BotCommand(command="start", description="Почнемо"),
    ])

# Шляхи до локальних зображень
BASE_DIR = os.path.dirname(__file__)
IMAGE_PATHS = {
    'welcome': os.path.join(BASE_DIR, 'images', 'welcome.jpg'),
    'goal': os.path.join(BASE_DIR, 'images', 'goal.jpg'),
    'gender': os.path.join(BASE_DIR, 'images', 'gender.jpg'),
    'age': os.path.join(BASE_DIR, 'images', 'age.jpg'),
    'height': os.path.join(BASE_DIR, 'images', 'height.jpg'),
    'weight': os.path.join(BASE_DIR, 'images', 'weight.jpg'),
    'activity': os.path.join(BASE_DIR, 'images', 'activity.jpg'),
    'result': os.path.join(BASE_DIR, 'images', 'result.jpg')
}

# Вітальне повідомлення при першому відкритті чату
@dp.chat_member_handler()
async def welcome_new_user(chat_member: ChatMemberUpdated):
    if chat_member.chat.type == 'private' and chat_member.new_chat_member.status == 'member':
        chat_id = chat_member.chat.id
        try:
            with open(IMAGE_PATHS['welcome'], 'rb') as img:
                await bot.send_photo(chat_id, img,
                    caption="Вітаю в моєму телеграм-боті. Тут ти зможеш підрахувати кількість калорій та отримувати актуальні новини та поради"
                )
        except FileNotFoundError:
            await bot.send_message(chat_id,
                "Вітаю в боті! Тут ти зможеш підрахувати калорії та отримувати новини.")
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🚀 Почнемо", callback_data="start_calc"))
        await bot.send_message(chat_id, "Натисни кнопку, щоб розпочати:", reply_markup=kb)

# Стани FSM
class Form(StatesGroup):
    goal = State()
    gender = State()
    age = State()
    height = State()
    weight = State()
    activity = State()

# Розрахункові функції
def calculate_bmr(weight, height, age, gender):
    return 9.99 * weight + 6.25 * height - 4.92 * age + (5 if gender=='male' else -161)

def activity_factor(code):
    factors = {'1.2':1.2, '1.375':1.375, '1.55':1.55, '1.725':1.725, '1.9':1.9}
    return factors.get(code)

# Обробник «На початок»
@dp.callback_query_handler(lambda c: c.data=='home', state='*')
async def go_home(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await cmd_start(callback.message, state)

# Стартова команда (/start)
@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message, state: FSMContext=None):
    if state:
        await state.finish()
    try:
        with open(IMAGE_PATHS['welcome'], 'rb') as img:
            await bot.send_photo(message.chat.id, img,
                caption="Вітаю в моєму телеграм-боті. Тут ти зможеш підрахувати кількість калорій та отримувати актуальні новини та поради")
    except FileNotFoundError:
        await message.answer("Вітаю в боті! Тут ти зможеш підрахувати калорії та отримувати новини.")
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🚀 Почнемо", callback_data="start_calc"))
    await message.answer("Натисни кнопку, щоб розпочати:", reply_markup=kb)

# Крок 1: вибір мети
@dp.callback_query_handler(lambda c: c.data=='start_calc', state='*')
async def process_start(callback: types.CallbackQuery):
    await callback.answer()
    await show_goal(callback.message)
    await Form.goal.set()

async def show_goal(msg: types.Message):
    try:
        with open(IMAGE_PATHS['goal'], 'rb') as img:
            await bot.send_photo(msg.chat.id, img)
    except FileNotFoundError:
        pass
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("Схуднути", callback_data="goal_loss"),
        InlineKeyboardButton("Норма калорій", callback_data="goal_maintain"),
        InlineKeyboardButton("Набрати", callback_data="goal_gain"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_goal"),
        InlineKeyboardButton("🏠 На початок", callback_data="home")
    )
    await msg.answer("Яка Ваша ціль?", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data=='back_goal', state=Form.goal)
async def back_goal(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await cmd_start(callback.message, state)

@dp.callback_query_handler(lambda c: c.data.startswith('goal_'), state=Form.goal)
async def process_goal(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(goal=callback.data.split('_')[1])
    await show_gender(callback.message)
    await Form.gender.set()

# Крок 2: стать
async def show_gender(msg: types.Message):
    try:
        with open(IMAGE_PATHS['gender'], 'rb') as img:
            await bot.send_photo(msg.chat.id, img)
    except FileNotFoundError:
        pass
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("Чоловік", callback_data="gender_male"),
        InlineKeyboardButton("Жінка", callback_data="gender_female"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_gender"),
        InlineKeyboardButton("🏠 На початок", callback_data="home")
    )
    await msg.answer("Оберіть стать:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data=='back_gender', state=Form.gender)
async def back_gender(callback: types.CallbackQuery):
    await callback.answer()
    await show_goal(callback.message)
    await Form.goal.set()

@dp.callback_query_handler(lambda c: c.data.startswith('gender_'), state=Form.gender)
async def process_gender(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(gender=callback.data.split('_')[1])
    await show_age(callback.message)
    await Form.age.set()

# Крок 3: вік
async def show_age(msg: types.Message):
    try:
        with open(IMAGE_PATHS['age'], 'rb') as img:
            await bot.send_photo(msg.chat.id, img)
    except FileNotFoundError:
        pass
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("⬅️ Назад", callback_data="back_age"),
        InlineKeyboardButton("🏠 На початок", callback_data="home")
    )
    await msg.answer("Скільки Вам років?", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data=='back_age', state=Form.age)
async def back_age(callback: types.CallbackQuery):
    await callback.answer()
    await show_gender(callback.message)
    await Form.gender.set()

@dp.message_handler(lambda m: m.text.isdigit(), state=Form.age)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=int(message.text))
    await show_height(message)
    await Form.height.set()

# Крок 4: зріст
async def show_height(msg: types.Message):
    try:
        with open(IMAGE_PATHS['height'], 'rb') as img:
            await bot.send_photo(msg.chat.id, img)
    except FileNotFoundError:
        pass
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("⬅️ Назад", callback_data="back_height"),
        InlineKeyboardButton("🏠 На початок", callback_data="home")
    )
    await msg.answer("Який Ваш зріст (см)?", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data=='back_height', state=Form.height)
async def back_height(callback: types.CallbackQuery):
    await callback.answer()
    await show_age(callback.message)
    await Form.age.set()

@dp.message_handler(lambda m: m.text.replace('.', '', 1).isdigit(), state=Form.height)
async def process_height(message: types.Message, state: FSMContext):
    await state.update_data(height=float(message.text))
    await show_weight(message)
    await Form.weight.set()

# Крок 5: вага
async def show_weight(msg: types.Message):
    try:
        with open(IMAGE_PATHS['weight'], 'rb') as img:
            await bot.send_photo(msg.chat.id, img)
    except FileNotFoundError:
        pass
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("⬅️ Назад", callback_data="back_weight"),
        InlineKeyboardButton("🏠 На початок", callback_data="home")
    )
    await msg.answer("Яка Ваша вага (кг)?", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data=='back_weight', state=Form.weight)
async def back_weight(callback: types.CallbackQuery):
    await callback.answer()
    await show_height(callback.message)
    await Form.height.set()

@dp.message_handler(lambda m: m.text.replace('.', '', 1).isdigit(), state=Form.weight)
async def process_weight(message: types.Message, state: FSMContext):
    await state.update_data(weight=float(message.text))
    await show_activity(message)
    await Form.activity.set()

# Крок 6: активність
async def show_activity(msg: types.Message):
    try:
        with open(IMAGE_PATHS['activity'], 'rb') as img:
            await bot.send_photo(msg.chat.id, img)
    except FileNotFoundError:
        pass
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("Малорухливий (офісна робота)", callback_data="act_1.2"),
        InlineKeyboardButton("Легка (справи по дому)", callback_data="act_1.375"),
        InlineKeyboardButton("Помірна (3–5 тренувань/тиждень)", callback_data="act_1.55"),
        InlineKeyboardButton("Висока (6–7 тренувань/тиждень)", callback_data="act_1.725"),
        InlineKeyboardButton("Дуже висока (фізична робота + тренування)", callback_data="act_1.9"),
        InlineKeyboardButton("⬅️ Назад", callback_data="back_activity"),
        InlineKeyboardButton("🏠 На початок", callback_data="home")
    )
    await msg.answer("Оцініть свій рівень активності:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data=='back_activity', state=Form.activity)
async def back_activity(callback: types.CallbackQuery):
    await callback.answer()
    await show_weight(callback.message)
    await Form.weight.set()

@dp.callback_query_handler(lambda c: c.data.startswith('act_'), state=Form.activity)
async def process_activity(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    code = callback.data.split('_')[1]
    data = await state.get_data()
    bmr = calculate_bmr(data['weight'], data['height'], data['age'], data['gender'])
    tdee = bmr * float(code)
    goal = data['goal']
    if goal=='loss': calories, purpose = tdee-500, 'для схуднення'
    elif goal=='maintain': calories, purpose = tdee, 'для підтримки'
    else: calories, purpose = tdee+500, 'для набору'
    try:
        with open(IMAGE_PATHS['result'], 'rb') as img:
            await bot.send_photo(callback.message.chat.id, img,
                caption=f"Ваша добова норма {purpose}: {calories:.0f} ккал.")
    except FileNotFoundError:
        await callback.message.reply(f"Ваша добова норма {purpose}: {calories:.0f} ккал.")
    # Кнопки після підрахунку
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("🔄 Порахувати ще раз", callback_data="start_calc"),
        InlineKeyboardButton("🏠 На початок", callback_data="home")
    )
    await callback.message.answer("Що бажаєте далі?", reply_markup=kb)
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
