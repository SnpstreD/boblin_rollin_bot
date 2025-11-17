import telebot
from telebot.types import ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup 

from config import BOT_TOKEN
from dice_distribution import DiceDistribution
from session_manager import SessionManager

from keyboard_utils import create_adv_type_menu, create_parameters_menu
from params import ADVANTAGE_TYPES, PARAMETERS
from text_utils import generate_parameters_text, generate_welcome_text, generate_help_text

bot = telebot.TeleBot(BOT_TOKEN)

# Храним состояние пользователей
session_handler = SessionManager()


@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = generate_welcome_text()
    bot.send_message(message.chat.id, welcome_text, parse_mode='html')


@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = generate_help_text()
    bot.send_message(message.chat.id, help_text, parse_mode='html')


@bot.message_handler(commands=['new_calc', 'reset'])
def create_new_calc(message):
    user_id = message.from_user.id

    # Создаем словарь с дефолтными значениями всех параметров
    default_params = {}
    for param_slug, param_data in PARAMETERS.items():
        default_params[param_slug] = param_data['default']

    # Инициализируем сессию пользователя с дефолтными параметрами
    session_handler.update_session(
        user_id,
        step='choosing_advantage',
        **default_params
    )

    text = """
        Выберите 🔄 Тип броска:
    """

    msg = bot.send_message(
        message.chat.id,
        text,
        reply_markup=create_adv_type_menu()
    )

    session_handler.update_session(user_id, last_bot_message_id=msg.message_id)


@bot.message_handler(func=lambda message: session_handler.get_user_step(message.from_user.id) is None)
def handle_no_session(message):
    bot.send_message(
        message.chat.id,
        "👋 Привет! Для начала работы используйте команду /start"
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('set_adv_type:') and session_handler.get_user_step(call.from_user.id) in ('choosing_advantage', 'editing_advantage'))
def handle_advantage_choice(call):
    bot.answer_callback_query(call.id)

    user_id = call.from_user.id
    chat_id = call.message.chat.id

    bot.delete_message(chat_id, session_handler.get_user_data(user_id, 'last_bot_message_id'))

    advantage_status = int(call.data.replace('set_adv_type:', ''))

    if session_handler.get_user_step(call.from_user.id) == 'editing_advantage':
        session_handler.update_session(
            user_id,
            step='adjusting_parameters',
            advantage_status=advantage_status
        )

        show_parameters(user_id, chat_id)
    else:
        session_handler.update_session(
            user_id,
            step='entering_to_hit',
            advantage_status=advantage_status
        )

        msg = bot.send_message(
            call.message.chat.id,
            f"✅ Выбран тип броска: <b>{ADVANTAGE_TYPES[advantage_status]}</b>\n\n"
            "Теперь введите модификаторы броска на попадание (без d20):\n"
            "Пример: <code>1d4 + 7</code>",
            parse_mode='html'
        )

        session_handler.update_session(user_id, last_bot_message_id=msg.message_id)


@bot.message_handler(func=lambda message: session_handler.get_user_step(message.from_user.id) == 'entering_to_hit')
def handle_to_hit_input(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    bot.delete_message(chat_id, session_handler.get_user_data(user_id, 'last_bot_message_id'))

    param_data = PARAMETERS['to_hit_roll']
    is_valid = param_data['validator'](message.text)
    if not is_valid:
        error_text = param_data['error_text']
        msg = bot.send_message(chat_id, error_text, parse_mode='html')
        session_handler.update_session(user_id, last_bot_message_id=msg.message_id)
        return  # Не сохраняем невалидное значение

    # Сохраняем to-hit roll и переходим к следующему шагу
    session_handler.update_session(
        user_id,
        step='choosing_to_enter_damage', 
        to_hit_roll=message.text
    )

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton('✅ Да', callback_data='add_damage_roll:1'),
        InlineKeyboardButton('❌ Нет', callback_data='add_damage_roll:0')
    )

    msg = bot.send_message(
        message.chat.id,
        f"✅ To-Hit Roll сохранен: <code>{message.text}</code>\n\n"
        "Добавить бросок урона (Damage Roll)?",
        parse_mode='html',
        reply_markup=markup
    )

    session_handler.update_session(user_id, last_bot_message_id=msg.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('add_damage_roll:') and session_handler.get_user_step(call.from_user.id) == 'choosing_to_enter_damage')
def handle_damage_choice(call):
    """Обработка выбора Damage Roll"""
    bot.answer_callback_query(call.id)

    user_id = call.from_user.id
    chat_id = call.message.chat.id

    bot.delete_message(chat_id, session_handler.get_user_data(user_id, 'last_bot_message_id'))

    if call.data == 'add_damage_roll:1':
        session_handler.update_session(
            user_id,
            step='entering_damage_roll'
        )

        msg = bot.send_message(
            call.message.chat.id,
            "Введите бросок урона (Damage Roll):\nПример: <code>2d6 + 3</code>",
            parse_mode='html',
            reply_markup=ReplyKeyboardRemove()
        )

        session_handler.update_session(user_id, last_bot_message_id=msg.message_id)

    else:
        # Пропускаем damage roll
        session_handler.update_session(
            user_id,
            step='adjusting_parameters'
        )
        show_parameters(user_id, call.message.chat.id)


@bot.message_handler(func=lambda message: session_handler.get_user_step(message.from_user.id) == 'entering_damage_roll')
def handle_damage_input(message):
    """Шаг 3a: Обработка ввода Damage Roll"""
    user_id = message.from_user.id
    chat_id = message.chat.id

    bot.delete_message(chat_id, session_handler.get_user_data(user_id, 'last_bot_message_id'))

    param_data = PARAMETERS['damage_roll']
    is_valid = param_data['validator'](message.text)
    if not is_valid:
        error_text = param_data['error_text']
        msg = bot.send_message(chat_id, error_text, parse_mode='html')
        session_handler.update_session(user_id, last_bot_message_id=msg.message_id)
        return  # Не сохраняем невалидное значение

    session_handler.update_session(
        user_id,
        step='adjusting_parameters',
        damage_roll=message.text
    )

    show_parameters(user_id, message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('param_change:'))
def handle_parameter_change(call):
    bot.answer_callback_query(call.id)

    user_id = call.from_user.id
    chat_id = call.message.chat.id

    bot.delete_message(chat_id, session_handler.get_user_data(user_id, 'last_bot_message_id'))

    param_slug = call.data.split(':')[1]
    param_type = PARAMETERS[param_slug]['type']

    if param_type == 'flag':
        current_value = session_handler.get_user_data(user_id, param_slug)
        new_value = 0 if current_value == 1 else 1
        session_handler.update_session(
            user_id,
            **{param_slug: new_value}
        )
        show_parameters(user_id, chat_id)

    elif param_type == 'user_text':  # изменить условие: параметр вводится со строки
        # принять сообщение с новым значением параметра
        session_handler.update_session(
            user_id,
            step=f'editing_{param_slug}'
        )

        text = f"Введите новое значение для {PARAMETERS[param_slug]['short_name']}:"

        msg = bot.send_message(
            chat_id,
            text,
            parse_mode='html'
        )

        session_handler.update_session(user_id, last_bot_message_id=msg.message_id)

    else:
        # Меняем advantage (единственный параметр, который вводится с inline кнопки)
        session_handler.update_session(
            user_id,
            step='editing_advantage'
        )

        msg = bot.send_message(
            call.message.chat.id,
            "Выберите новый тип броска:",
            reply_markup=create_adv_type_menu()
        )

        session_handler.update_session(user_id, last_bot_message_id=msg.message_id)


@bot.message_handler(func=lambda message: session_handler.get_user_step(message.from_user.id).startswith('editing_'))
def handle_parameter_text_input(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    current_step = session_handler.get_user_step(user_id)

    bot.delete_message(chat_id, session_handler.get_user_data(user_id, 'last_bot_message_id'))

    param_slug = current_step.replace('editing_', '')
    param_data = PARAMETERS[param_slug]

    if 'validator' in param_data:
        is_valid = param_data['validator'](message.text)
        if not is_valid:
            error_text = param_data['error_text']
            msg = bot.send_message(chat_id, error_text, parse_mode='html')
            session_handler.update_session(user_id, last_bot_message_id=msg.message_id)
            return  # Не сохраняем невалидное значение

    new_value = message.text
    if 'converter' in param_data:
        try:
            new_value = param_data['converter'](message.text)
        except (ValueError, TypeError) as e:
            error_text = param_data['error_text']
            msg = bot.send_message(chat_id, error_text, parse_mode='html')
            session_handler.update_session(user_id, last_bot_message_id=msg.message_id)
            return

    session_handler.update_session(
        user_id,
        step='adjusting_parameters',
        **{param_slug: new_value}
    )

    show_parameters(user_id, chat_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('calculate'))
def show_graphs(call):
    bot.answer_callback_query(call.id)

    user_id = call.from_user.id
    chat_id = call.message.chat.id

    session_handler.update_session(
        user_id,
        step='getting_graphs'
    )

    user_data = session_handler.get_user_data(user_id)

    dice_dist = DiceDistribution(**{
            param: user_data.get(param, PARAMETERS[param]['default'])
            for param in PARAMETERS.keys()
    })

    to_hit_img = dice_dist.plot_to_hit_distribution()
    bot.send_photo(chat_id, to_hit_img, caption="🎯 To-Hit Distribution")

    if dice_dist.damage_roll.strip():
        normal_dmg_img = dice_dist.plot_damage_distribution('normal')
        bot.send_photo(chat_id, normal_dmg_img, caption="🩸 Normal Damage Distribution")

        crit_dmg_img = dice_dist.plot_damage_distribution('critical')
        bot.send_photo(chat_id, crit_dmg_img, caption="💥 Critical Damage Distribution")


def show_parameters(user_id: int, chat_id: int):
    """Шаг 4: Показываем дополнительные параметры для изменения"""
    user_data = session_handler.get_user_data(user_id)

    # Обновляем шаг
    session_handler.update_session(
        user_id,
        step='adjusting_parameters'
    )

    parameters_text = generate_parameters_text(user_data)

    markup = create_parameters_menu()
    msg = bot.send_message(chat_id, parameters_text, parse_mode='html', reply_markup=markup)

    session_handler.update_session(user_id, last_bot_message_id=msg.message_id)


if __name__ == "__main__":
    print("🎲 D&D Dice Bot запущен!")
    print(f"🤖 Активных сессий: {len(session_handler.sessions)}")

    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
