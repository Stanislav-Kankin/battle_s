import random
from typing import List, Tuple, Set

class Game:
    def __init__(self, player1: int, player2: int):
        self.player1 = player1
        self.player2 = player2
        self.current_turn = player1
        self.player1_board = self.create_empty_board()
        self.player2_board = self.create_empty_board()
        self.player1_shots: Set[Tuple[int, int]] = set()
        self.player2_shots: Set[Tuple[int, int]] = set()
        self.setup_ships()

    @staticmethod
    def create_empty_board() -> List[List[str]]:
        return [["🌊" for _ in range(10)] for _ in range(10)]

    def setup_ships(self):
        """Автоматическая расстановка кораблей с соблюдением правил"""
        ships_layout = [
            (4, 1),  # 1 корабль на 4 клетки
            (3, 2),  # 2 корабля на 3 клетки
            (2, 3),  # 3 корабля на 2 клетки
            (1, 4)   # 4 корабля на 1 клетку
        ]
        
        for board in [self.player1_board, self.player2_board]:
            for ship_length, ship_count in ships_layout:
                for _ in range(ship_count):
                    self.place_ship(board, ship_length)

    def place_ship(self, board: List[List[str]], ship_length: int):
        """Пытается разместить корабль на доске с соблюдением всех правил"""
        max_attempts = 100
        for _ in range(max_attempts):
            x = random.randint(0, 9)
            y = random.randint(0, 9)
            orientation = random.choice(["horizontal", "vertical"])
            
            if self.can_place_ship(board, x, y, ship_length, orientation):
                # Размещаем корабль
                for i in range(ship_length):
                    if orientation == "horizontal":
                        board[y][x + i] = "🚤️"
                    else:
                        board[y + i][x] = "🚤️"
                return
        
        # Если не удалось разместить после max_attempts попыток
        raise RuntimeError(f"Не удалось разместить корабль длиной {ship_length}")

    def can_place_ship(self, board: List[List[str]], x: int, y: int, length: int, orientation: str) -> bool:
        """Проверяет, можно ли разместить корабль с учетом всех правил"""
        # Проверяем выход за границы
        if orientation == "horizontal":
            if x + length > 10:
                return False
        else:
            if y + length > 10:
                return False
        
        # Проверяем, что все клетки свободны и вокруг них тоже
        for i in range(length):
            # Координаты текущей клетки корабля
            cx = x + (i if orientation == "horizontal" else 0)
            cy = y + (i if orientation == "vertical" else 0)
            
            # Проверяем саму клетку и все соседние
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < 10 and 0 <= ny < 10:
                        if board[ny][nx] != "🌊":
                            return False
        return True

    def check_win(self, board: List[List[str]]) -> bool:
        return all(cell != "🚤️" for row in board for cell in row)
