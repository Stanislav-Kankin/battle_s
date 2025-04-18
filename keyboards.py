from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/play")],
        ],
        resize_keyboard=True
    )


def get_board_keyboard(hidden: bool = False) -> InlineKeyboardMarkup:
    keyboard = []
    for y in range(10):
        row = []
        for x in range(10):
            row.append(InlineKeyboardButton(
                text="❓" if hidden else "🌊",  # Скрываем корабли противника
                callback_data=f"shoot_{x}_{y}"
            ))
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
