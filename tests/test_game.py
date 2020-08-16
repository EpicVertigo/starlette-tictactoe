from unittest import TestCase

from star.game import Game, IncorrectMoveException


class GameTestCase(TestCase):

    def setUp(self):
        self.players = ['test1', 'test2']
        self.game = Game(self.players)

    def test_full_game(self):
        game = self.game
        game.make_move(0, 0, 'test1')
        game.make_move(2, 2, 'test2')
        game.make_move(0, 1, 'test1')
        game.make_move(2, 1, 'test2')
        game.make_move(0, 2, 'test1')

        self.assertTrue(game.winner)
        self.assertTrue(game.is_over)
