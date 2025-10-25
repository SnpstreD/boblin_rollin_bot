from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from params import ADVANTAGE_TYPES, PARAMETERS


def create_adv_type_menu():
    """Создает клавиатуру для выбора типа Advantage"""
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton(name, callback_data=f'set_adv_type:{type}')
        for type, name in ADVANTAGE_TYPES.items()
    ]
    markup.add(*buttons)
    return markup


def create_parameters_menu():
    """Создает клавиатуру для изменения параметров"""
    markup = InlineKeyboardMarkup(row_width=2)
    param_buttons = [
        InlineKeyboardButton(f"{data['emoji']} {data['short_name']}", callback_data=f'param_change:{param}')
        for param, data in PARAMETERS.items()
    ]
    calculate_button = InlineKeyboardButton('📊 Рассчитать', callback_data='calculate')
    markup.add(*param_buttons)
    markup.add(calculate_button)

    return markup
