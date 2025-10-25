import re


def validate_dice_notation(text):
    """Проверяет корректность нотации броска одной регуляркой"""
    if not text or not text.strip():
        return False

    clean_text = text.replace(' ', '')

    pattern = r'^([+-]?(?:(?:[1-9]\d{0,2})?d[1-9]\d{0,2}|[1-9]\d{0,2})(?:[+-](?:(?:[1-9]\d{0,2})?d[1-9]\d{0,2}|[1-9]\d{0,2}))*)$'

    return bool(re.match(pattern, clean_text))


ADVANTAGE_TYPES = {
    -1: 'Disadvantage',
    0: 'Normal',
    1: 'Advantage',
    2: 'Super Advantage'
}

BOT_COMMANDS = {
    '/new_calc': 'Начать новый расчет',
    '/reset': 'Сбросить настройки расчета',
    '/help': 'Помощь по боту'
}

PARAMETERS = {
    'advantage_status': {
        'type': 'inline_button',
        'short_name': 'Тип броска',
        'default': 0,
        'display_name': 'Тип броска',
        'display_value': lambda value: ADVANTAGE_TYPES[value],
        'emoji': '🔄',
        'description': (
            'Определяет условия броска d20:\n'
            '• <b>Normal</b> - обычный бросок 1d20\n'
            '• <b>Disadvantage</b> - бросок 2d20, берется меньший\n'
            '• <b>Advantage</b> - бросок 2d20, берется больший\n'
            '• <b>Super Advantage</b> - бросок 3d20, берется наибольший'
        )
    },

    'to_hit_roll': {
        'type': 'user_text',
        'short_name': 'To-Hit',
        'default': '',
        'display_name': 'Модификатор броска на попадание',
        'display_value': lambda value: f"<code>{value}</code>" if value else "<code>Не задан</code>",
        'emoji': '🎯',
        'validator': validate_dice_notation,
        'error_text': '❌ Неверное значение! Введите корректную нотацию броска (например: <code>1d4 + 7</code>)',
        'description': (
            'Бонусы к броску на попадание (без d20)\n'
            '<b>Примеры:</b>\n'
            '• <code>5</code>\n'
            '• <code>1d4 + 7</code>\n'
            '• <code>2d6 - d4 + 3</code>'
        )
    },

    'damage_roll': {
        'type': 'user_text',
        'short_name': 'Damage',
        'default': '',
        'display_name': 'Бросок урона',
        'display_value': lambda value: f"<code>{value}</code>" if value else "<code>Не задан</code>",
        'emoji': '🩸',
        'validator': validate_dice_notation,
        'error_text': '❌ Неверное значение! Введите корректную нотацию броска (например: <code>2d6 + 1d8 + 3</code>)',
        'description': (
            'Формула урона при успешном попадании\n'
            '<b>Примеры:</b>\n'
            '• <code>2d6 + 4</code>\n'
            '• <code>1d8 + 2d6 + 3</code>\n'
            '• <code>d10 + 5 - d4</code>'
        )
    },

    'crit_hit_number': {
        'type': 'user_text',
        'short_name': 'Crit',
        'default': 20,
        'display_name': 'Критическое попадание при',
        'display_value': lambda value: f"{value}" if value == 20 else f"{value} - 20",
        'emoji': '💥',
        'validator': lambda text: text.isdigit() and 1 < int(text) <= 20,
        'converter': lambda text: int(text),
        'error_text': '❌ Неверное значение! Введите число от 2 до 20',
        'description': 'Значение d20, при котором попадание считается критическим.'
    },

    'great_weapon_fighting_active': {
        'type': 'flag',
        'short_name': 'GWF',
        'default': 0,
        'display_name': 'Great Weapon Fighting Style',
        'display_value': lambda value: '✅' if value == 1 else '❌',
        'emoji': '🗡️',
        'description': 'Боевой стиль "Сражение Большим Оружием"\nПеребрасывает <b>1</b> и <b>2</b> на кубах урона'
    },

    'halfling_luck_active': {
        'type': 'flag',
        'short_name': 'HL',
        'default': 0,
        'display_name': "Halfling's Luck",
        'display_value': lambda value: '✅' if value == 1 else '❌',
        'emoji': '🍀',
        'description': 'Расовая особенность Полуросликов\nПозволяет перебросить d20 при выпадении <b>1</b>'
    }
}
#  🛡️
