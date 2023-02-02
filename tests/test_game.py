from unittest import TestCase

from src.game import Game, IncorrectMoveException


class FakePlayer:
    def __init__(self, uid):
        self.uid = uid
        self.display_name = uid


class GameTestCase(TestCase):

    def setUp(self):
        self.player1, self.player2 = FakePlayer('1'), FakePlayer('2')
        self.players = [self.player1, self.player2]
        self.game = Game(self.players)

    def test_full_game(self):
        game = self.game
        game.make_move(0, 0, self.player1)
        game.make_move(2, 2, self.player2)
        game.make_move(0, 1, self.player1)
        game.make_move(2, 1, self.player2)
        game.make_move(0, 2, self.player1)

        self.assertTrue(game.winner)
        self.assertTrue(game.is_over)
