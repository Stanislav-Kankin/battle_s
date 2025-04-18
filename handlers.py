from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command

from models import Game
from config import bot

router = Router()
waiting_games = {}  # {player1_id: {"chat_id": chat_id}}
active_games = {}   # {game_id: {"player1": id, "player2": id, "game": Game}}

# Соответствие букв цифрам (а=0, б=1, ...)
LETTERS = ['а', 'б', 'в', 'г', 'д', 'е', 'ж', 'з', 'и', 'к']

# ======================
# Вспомогательные функции
# ======================
def format_board(board: list, hide_ships: bool = False) -> str:
    """Форматирует доску в текстовый вид"""
    header = "  " + " ".join(str(i) for i in range(10)) + "\n"
    board_text = header
    
    for y in range(10):
        row = [LETTERS[y]]  # Буква для строки
        for x in range(10):
            cell = board[y][x]
            if hide_ships and cell == "🛳️":
                row.append("🌊")
            else:
                row.append(cell)
        board_text += " ".join(row) + "\n"
    
    return f"<pre>{board_text}</pre>"

async def send_boards(chat_id: int, game: Game, is_player1: bool):
    """Отправляет обе доски игроку"""
    # Своя доска (полная)
    my_board = game.player1_board if is_player1 else game.player2_board
    await bot.send_message(chat_id, "⚓ Ваши корабли:\n" + format_board(my_board))
    
    # Доска противника (скрытая)
    enemy_board = game.player2_board if is_player1 else game.player1_board
    await bot.send_message(chat_id, "🎯 Доска противника:\n" + format_board(enemy_board, hide_ships=True))
    
    # Подсказка по вводу
    await bot.send_message(
        chat_id,
        "Ваш ход! Введите координаты в формате <b>буква цифра</b> (например, 'а 1' или 'в 5')"
    )

def check_ship_sunk(board: list, x: int, y: int) -> bool:
    """Проверяет, полностью ли уничтожен корабль"""
    # Проверяем все клетки вокруг, чтобы найти весь корабль
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    ship_cells = []
    to_check = [(x, y)]
    
    while to_check:
        cx, cy = to_check.pop()
        if (cx, cy) in ship_cells:
            continue
        ship_cells.append((cx, cy))
        
        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < 10 and 0 <= ny < 10:
                if board[ny][nx] in ("🛳️", "💥") and (nx, ny) not in ship_cells:
                    to_check.append((nx, ny))
    
    # Если все клетки корабля подбиты
    return all(board[cy][cx] == "💥" for cx, cy in ship_cells)

# ======================
# Обработчики команд
# ======================
@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🚢 Добро пожаловать в Морской бой!\n\n"
        "Команды:\n"
        "/play - создать игру\n"
        "/join <ID> - присоединиться к игре\n\n"
        "Как играть:\n"
        "1. Первый игрок создает игру командой /play\n"
        "2. Второй игрок присоединяется командой /join <ID>\n"
        "3. По очереди вводите координаты (например, 'а 1' или 'в 5')\n"
        "4. При попадании ход остается, при промахе - переходит"
    )

@router.message(Command("play"))
async def play(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if user_id in waiting_games or any(user_id in (g["player1"], g["player2"]) for g in active_games.values()):
        await message.answer("Вы уже участвуете в другой игре!")
        return
    
    waiting_games[user_id] = {"chat_id": chat_id}
    await message.answer(
        f"Игра создана! Ваш ID игры: <code>{user_id}</code>\n\n"
        "Сообщите этот ID второму игроку для присоединения:\n"
        f"/join {user_id}"
    )

@router.message(Command("join"))
async def join_game(message: Message):
    try:
        game_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.answer("Используйте: /join <ID_игры>")
        return
    
    if game_id not in waiting_games:
        await message.answer("Игра не найдена или уже началась!")
        return
    
    player1_id = game_id
    player2_id = message.from_user.id
    player1_chat = waiting_games[game_id]["chat_id"]
    player2_chat = message.chat.id
    
    # Создаем игру
    game = Game(player1_id, player2_id)
    game_id = f"{player1_id}_{player2_id}"
    active_games[game_id] = {
        "player1": player1_id,
        "player2": player2_id,
        "player1_chat": player1_chat,
        "player2_chat": player2_chat,
        "game": game
    }
    
    del waiting_games[player1_id]
    
    # Оповещаем игроков
    await bot.send_message(
        player1_chat,
        f"Игрок {message.from_user.first_name} присоединился!\n"
        "Игра началась. Ваш ход первый."
    )
    await message.answer("Вы присоединились к игре! Ожидайте своего хода.")
    
    # Отправляем доски
    await send_boards(player1_chat, game, is_player1=True)

# ======================
# Обработчики ходов
# ======================
@router.message(F.text.regexp(r'^[а-икА-ИК]\s*[0-9]$'))
async def process_shot(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Находим игру
    game_data = None
    for gid, data in active_games.items():
        if user_id in (data["player1"], data["player2"]):
            game_data = data
            game_id = gid
            break
    
    if not game_data:
        await message.answer("Вы не в игре! Создайте /play или присоединитесь /join")
        return
    
    game = game_data["game"]
    
    if user_id != game.current_turn:
        await message.answer("Сейчас не ваш ход!")
        return
    
    # Парсим координаты (приводим букву к нижнему регистру)
    letter_part, num_part = message.text.lower().split()
    y = LETTERS.index(letter_part[0])  # Берем первый символ на случай лишних пробелов
    x = int(num_part)
    
    # Проверяем координаты
    if not (0 <= x <= 9) or not (0 <= y <= 9):
        await message.answer("Координаты вне диапазона! Используйте буквы а-и и цифры 0-9")
        return
    
    # Определяем параметры выстрела
    if user_id == game.player1:
        target_board = game.player2_board
        shots = game.player1_shots
        opponent_chat = game_data["player2_chat"]
        opponent_id = game_data["player2"]
    else:
        target_board = game.player1_board
        shots = game.player2_shots
        opponent_chat = game_data["player1_chat"]
        opponent_id = game_data["player1"]
    
    # Проверяем повторный выстрел
    if (x, y) in shots:
        await message.answer("Вы уже стреляли сюда!")
        return
    
    # Обрабатываем выстрел
    shots.add((x, y))
    if target_board[y][x] == "🛳️":
        target_board[y][x] = "💥"
        result = "Попадание! 🔥"
        
        # Проверяем, убит ли корабль
        if check_ship_sunk(target_board, x, y):
            result += "\nКорабль уничтожен! 💀"
        
        # Ход остается у текущего игрока
        keep_turn = True
    else:
        target_board[y][x] = "❌"
        result = "Мимо! 🌊"
        # Ход переходит противнику
        keep_turn = False
    
    # Проверяем победу
    if game.check_win(target_board):
        winner_name = message.from_user.first_name
        await bot.send_message(
            game_data["player1_chat"],
            f"🎉 {winner_name} победил в этой игре!"
        )
        await bot.send_message(
            game_data["player2_chat"],
            f"🎉 {winner_name} победил в этой игре!"
        )
        del active_games[game_id]
        return
    
    # Меняем ход (если нужно)
    if not keep_turn:
        game.current_turn = opponent_id
    
    # Отправляем обновленные доски
    await send_boards(chat_id, game, is_player1=(user_id == game.player1))
    await send_boards(opponent_chat, game, is_player1=(opponent_id == game.player1))
    
    # Уведомляем о результате
    await message.answer(result)
    
    if not keep_turn:
        await bot.send_message(
            opponent_chat,
            f"Противник сделал ход: {message.text}\n{result}\nТеперь ваш ход!"
        )
    else:
        await message.answer("Продолжайте ваш ход!")