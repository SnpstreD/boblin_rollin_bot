from params import BOT_COMMANDS, PARAMETERS


def generate_parameters_text(user_data):
    """Генерирует текст с текущими параметрами на основе PARAMETERS"""
    lines = []

    for param_slug, param_data in PARAMETERS.items():
        value = user_data.get(param_slug, param_data['default'])
        display_value = param_data['display_value'](value)
        emoji = param_data.get('emoji', '•')
        display_name = param_data['display_name']
        lines.append(f'  <b>•  {emoji} {display_name}:</b> {display_value}')

    parameters_text = f"""
⚙️ <u><b>Настройки расчета</b></u>

{chr(10).join(lines)}

Выберите параметр для изменения или нажмите <b>«Рассчитать»</b>, чтобы продолжить:
    """

    return parameters_text


def generate_welcome_text():
    lines = []

    for command, description in BOT_COMMANDS.items():
        lines.append(f'<b>{command}</b> - {description}')

    welcome_text = f"""
🎲 <b>Boblin Rollin' Bot</b>
Твой карманный Dice Goblin.

Я помогаю анализировать распределение вероятностей для бросков в D&D.

<u>Доступные команды:</u>
{chr(10).join(lines)}
    """

    return welcome_text


def generate_help_text():
    lines = []

    for _, param_data in PARAMETERS.items():
        emoji = param_data.get('emoji', '•')
        short_name = param_data['short_name']
        description = param_data['description']
        lines.append(f'{emoji} <b>{short_name}</b>\n'
                    f'<i>{description}</i>\n\n')

    help_text = (
        "📖 <b>Помощь по боту</b>\n\n"
        "❓ <b>Как использовать:</b>\n"
        "1. Нажми /new_calc\n"
        "2. Настрой параметры\n"
        "3. Нажми «Рассчитать»\n"
        "4. Получи детальные графики!"
        "\n\n"
        "<b>Описание параметров:</b>\n\n"
        f"{''.join(lines)}"
    )

    return help_text
