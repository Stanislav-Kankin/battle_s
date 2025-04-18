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
        """Автоматическая расстановка кораблей."""
        ships = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]  # Длины кораблей
        for board in [self.player1_board, self.player2_board]:
            for ship_length in ships:
                self.place_ship(board, ship_length)

    def place_ship(self, board: List[List[str]], ship_length: int):
        placed = False
        while not placed:
            x, y = random.randint(0, 9), random.randint(0, 9)
            orientation = random.choice(["horizontal", "vertical"])
            if self.can_place_ship(board, x, y, ship_length, orientation):
                for i in range(ship_length):
                    if orientation == "horizontal":
                        board[y][x + i] = "🛳️"
                    else:
                        board[y + i][x] = "🛳️"
                placed = True

    def can_place_ship(self, board: List[List[str]], x: int, y: int, length: int, orientation: str) -> bool:
        if orientation == "horizontal":
            if x + length > 10:
                return False
            for i in range(length):
                if board[y][x + i] != "🌊":
                    return False
        else:
            if y + length > 10:
                return False
            for i in range(length):
                if board[y + i][x] != "🌊":
                    return False
        return True

    def check_win(self, board: List[List[str]]) -> bool:
        return all(cell != "🛳️" for row in board for cell in row)