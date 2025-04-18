from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models import Game
from config import bot
import keyboards as kb

router = Router()
active_games = {}  # {chat_id: {"status": str, "player1": int, "player2": int, "game": Game}}

# ======================
# Вспомогательные функции
# ======================
async def show_board(chat_id: int, board: list, is_hidden: bool = False):
    """Отображает доску с inline-кнопками"""
    builder = InlineKeyboardBuilder()
    
    for y in range(10):
        for x in range(10):
            cell = board[y][x]
            if is_hidden and cell == "🛳️":
                display = "🌊"
            else:
                display = cell
                
            builder.button(
                text=display,
                callback_data=f"shoot_{x}_{y}"
            )
    builder.adjust(10)  # 10 кнопок в ряд
    
    board_text = "  0 1 2 3 4 5 6 7 8 9\n"
    for y in range(10):
        board_text += f"{y} " + " ".join([cell if not is_hidden or cell in ("💥", "❌") else "🌊" for cell in board[y]]) + "\n"
    
    await bot.send_message(
        chat_id,
        f"<pre>{board_text}</pre>",
        reply_markup=builder.as_markup()
    )

# ======================
# Обработчики команд
# ======================
@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🚢 Добро пожаловать в Морской бой!\n\n"
        "Команды:\n"
        "/play - создать игру\n"
        "/join - присоединиться к игре",
        reply_markup=kb.get_main_menu()
    )

@router.message(Command("play"))
async def play(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Проверяем, не участвует ли уже пользователь в другой игре
    for game_data in active_games.values():
        if user_id in (game_data.get("player1"), game_data.get("player2")):
            await message.answer("Вы уже участвуете в другой игре!")
            return
    
    if chat_id in active_games:
        await message.answer("В этом чате уже есть активная игра!")
        return
    
    active_games[chat_id] = {
        "status": "waiting",
        "player1": user_id,
        "player2": None
    }
    await message.answer(
        "Игра создана! Ожидаем второго игрока...\n"
        "Пусть второй игрок напишет /join",
        reply_markup=kb.get_main_menu()
    )

@router.message(Command("join"))
async def join_game(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if chat_id not in active_games:
        await message.answer("В этом чате нет игр для присоединения!")
        return
    
    game_data = active_games[chat_id]
    
    if game_data["status"] != "waiting":
        await message.answer("Игра уже началась!")
        return
    
    if user_id == game_data["player1"]:
        await message.answer("Вы не можете играть сами с собой!")
        return
    
    game_data["player2"] = user_id
    game_data["status"] = "playing"
    game_data["game"] = Game(game_data["player1"], user_id)
    
    await message.answer("Игра началась! Делайте ходы, нажимая на клетки.")
    
    # Показываем доски
    game = game_data["game"]
    await show_board(chat_id, game.player1_board, is_hidden=False)  # Своя доска
    await show_board(chat_id, game.player2_board, is_hidden=True)   # Доска противника

# ======================
# Обработчики callback'ов
# ======================
@router.callback_query(F.data.startswith("shoot_"))
async def process_shoot(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    
    if chat_id not in active_games or active_games[chat_id]["status"] != "playing":
        await callback.answer("Игра не активна!", show_alert=True)
        return
    
    game_data = active_games[chat_id]
    game = game_data["game"]
    
    if user_id not in (game.player1, game.player2):
        await callback.answer("Вы не участник этой игры!", show_alert=True)
        return
    
    if user_id != game.current_turn:
        await callback.answer("Сейчас не ваш ход!", show_alert=True)
        return
    
    _, x, y = callback.data.split("_")
    x, y = int(x), int(y)
    
    # Определяем, в какую доску стреляем
    if user_id == game.player1:
        target_board = game.player2_board
        shots = game.player1_shots
    else:
        target_board = game.player1_board
        shots = game.player2_shots
    
    # Проверяем, не стреляли ли уже сюда
    if (x, y) in shots:
        await callback.answer("Вы уже стреляли сюда!", show_alert=True)
        return
    
    # Обрабатываем выстрел
    shots.add((x, y))
    if target_board[y][x] == "🛳️":
        target_board[y][x] = "💥"
        await callback.answer("Попадание! 🔥")
    else:
        target_board[y][x] = "❌"
        await callback.answer("Мимо! 🌊")
    
    # Проверяем победу
    if game.check_win(target_board):
        winner_name = callback.from_user.first_name
        await callback.message.answer(f"🎉 {winner_name} победил в этой игре!")
        del active_games[chat_id]
        return
    
    # Меняем ход
    game.current_turn = game.player2 if user_id == game.player1 else game.player1
    
    # Обновляем сообщение с доской
    await callback.message.edit_reply_markup(
        reply_markup=InlineKeyboardBuilder().as_markup()
    )
    await show_board(chat_id, target_board, is_hidden=(user_id == game.player1))