from typing import Callable, List

import numpy as np


class IncorrectMoveException(Exception):
    pass


class Game:
    board: list = None
    players: dict = None
    is_over = False
    winner = None
    current_player = 1

    def __init__(self, players):
        if len(players) != 2:
            raise Exception('This game requires 2 players')
        self.board = self._get_new_grid()
        self.players = dict(enumerate(players, 1))

    def _get_new_grid(self) -> np.array:
        return np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0]])

    def is_sequence_filled(self, sequence: list, player: int) -> bool:
        return len(set(sequence)) == 1 and player in set(sequence)

    @property
    def conditions(self) -> List[Callable]:
        return [self.row_win, self.col_win, self.diag_win]

    def row_win(self, player: int) -> bool:
        for i in range(len(self.board)):
            row = []
            for j in range(len(self.board)):
                row.append(self.board[i, j])
            if self.is_sequence_filled(row, player):
                return True
            continue
        return False

    def col_win(self, player: int) -> bool:
        for i in range(len(self.board)):
            col = []
            for j in range(len(self.board)):
                col.append(self.board[j][i])
            if self.is_sequence_filled(col, player):
                return True
            continue
        return False

    def diag_win(self, player: int) -> bool:
        diag = []
        for i in range(len(self.board)):
            diag.append(self.board[i, i])

        if self.is_sequence_filled(diag, player):
            return True
        # Check second diagonal
        diag.clear()
        j = 0
        for i in range(len(self.board)):
            j = len(self.board) - 1 - i
            diag.append(self.board[i, j])
        if self.is_sequence_filled(diag, player):
            return True
        return False

    def make_move(self, x: int, y: int, player):
        if self.is_over:
            return
        try:
            if player != self.players[self.current_player]:
                raise IncorrectMoveException("It's not your turn")
            current_value = self.board[x, y]
            if current_value == 0:
                self.board[x, y] = self.current_player
                self.current_player = 2 if self.current_player == 1 else 1
                return self.evaluate()
            else:
                raise IncorrectMoveException('You can not fill this cell')
        except IndexError:
            raise IncorrectMoveException('Incorrect coordinates')

    def evaluate(self) -> str:
        for player in self.players:
            if any(map(lambda f: f(player), self.conditions)):
                self.winner = self.players[player].display_name
                self.is_over = True
        if np.all(self.board != 0) and not self.winner:
            self.winner = 'Noone'
            self.is_over = True
        return self.winner
