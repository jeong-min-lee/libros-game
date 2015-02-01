from unittest import TestCase

from libros.game import (
    deal, Game, Player,
    ACTIONS, ACTION_PILE_CARD, ACTION_SHOW_CARD, ACTION_TAKE_CARD,
)


class TestGame(TestCase):
    def test_deal(self):
        self.assertEqual(len(deal(4)), 80)
        self.assertEqual(len(deal(3)), 72)
        self.assertEqual(len(deal(2)), 60)

    def test_join(self):
        player1 = Player()
        player2 = Player()
        game = Game()
        game.join(player1)
        self.assertEqual(game.state, 'waiting')
        self.assertEqual(game.player_count, 1)
        game.join(player2)
        self.assertEqual(game.state, 'waiting')
        self.assertEqual(game.player_count, 2)
        game.start()
        self.assertEqual(game.state, 'turn')

    def _start_game(self, num_players=2):
        players = [Player() for i in range(num_players)]

        game = Game()

        for player in players:
            game.join(player)

        game.start()

        self.assertEqual(game.state, 'turn')
        self.assertEqual(game.player_count, num_players)

        return game, players

    def _player_turn(self, game, action=None):
        active_player = game.active_player

        player, card = game.turn()
        action = player.act(card, action)

        self.assertIn(action, ACTIONS)
        self.assertEqual(player, active_player)

        return player, card, action

    def test_pile_card(self):
        game, players = self._start_game()

        active_player = game.active_player

        self.assertEqual(len(game.pile), 0)
        self.assertEqual(len(game.public), 0)
        self.assertEqual(len(active_player.cards), 0)

        player, card, action = self._player_turn(game, ACTION_PILE_CARD)

        self.assertEqual(action, ACTION_PILE_CARD)
        self.assertEqual(len(game.pile), 1)
        self.assertEqual(len(game.public), 0)
        self.assertEqual(len(active_player.cards), 0)

    def test_show_card(self):
        game, players = self._start_game()

        active_player = game.active_player

        self.assertEqual(len(game.pile), 0)
        self.assertEqual(len(game.public), 0)
        self.assertEqual(len(active_player.cards), 0)

        player, card, action = self._player_turn(game, ACTION_SHOW_CARD)

        self.assertEqual(action, ACTION_SHOW_CARD)
        self.assertEqual(len(game.pile), 0)
        self.assertEqual(len(game.public), 1)
        self.assertEqual(len(active_player.cards), 0)

    def test_take_card(self):
        game, players = self._start_game()

        active_player = game.active_player

        self.assertEqual(len(game.pile), 0)
        self.assertEqual(len(game.public), 0)
        self.assertEqual(len(active_player.cards), 0)

        player, card, action = self._player_turn(game, ACTION_TAKE_CARD)

        self.assertEqual(action, ACTION_TAKE_CARD)
        self.assertEqual(len(game.pile), 0)
        self.assertEqual(len(game.public), 0)
        self.assertEqual(len(active_player.cards), 1)

    def test_game(self):
        game, players = self._start_game()

        active_player = game.active_player
        deck_count = game.deck_count
        self.assertIn(active_player, players)

        for i in range(game.turns_per_player):
            player, card, action = self._player_turn(game)
            self.assertEqual(player, active_player)

        self.assertEqual(game.deck_count, deck_count - game.turns_per_player)
        self.assertEqual(game.turns_left, 0)

        next_active_player = game.active_player
        self.assertNotEqual(active_player, next_active_player)
