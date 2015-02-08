import random

try:
    from mock import patch
except ImportError:
    from unittest.mock import patch
from itertools import repeat
from unittest import TestCase, skip

from libros.game import (
    deal, Game, Player,
    ACTIONS, ACTION_PILE_CARD, ACTION_SHOW_CARD,
    ACTION_TAKE_CARD, ACTION_DISCARD_CARD,
)


class TestGame(TestCase):
    def test_deal(self):
        self.assertEqual(len(deal(4)), 80)
        self.assertEqual(len(deal(3)), 72)
        self.assertEqual(len(deal(2)), 60)

    def test_deal_cards(self):
        deck = deal(2, cards_to_remove=0, gold_to_remove=0)

        color_distribution = {
            'red': zip('ABCDEFGHI', '1' * 7 + '2' * 2),
            'orange': zip('ABCDEFGHI', '1' * 7 + '2' * 2),
            'green': zip('ABCDEFGHI', '1' * 7 + '2' * 2),
            'blue': zip('ABCDEFGHI', '2' * 4 + '3' * 3 + '4' * 2),
            'brown': zip('ABCDEFGHI', '2' * 4 + '3' * 3 + '4' * 2),
            'gold': zip(repeat(None), '1' * 11 + '2' * 11 + '3' * 11),
            'change': zip(repeat(None), [-2, -2, -1, -1, 0, 1, 1, 2, 2]),
        }

        sort_key = lambda x: (x['type'], x['letter'], x['value'])
        self.assertEqual(
            sorted(deck, key=sort_key),
            sorted(({"type": color, "letter": letter, "value": int(value)}
                    for color, distribution in color_distribution.items()
                    for letter, value in distribution), key=sort_key)
        )

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

        player, card, valid_actions = game.turn()

        if action not in valid_actions:
            action = random.choice(valid_actions)

        action = player.act(card, action)

        self.assertIn(action, ACTIONS)
        self.assertEqual(player, active_player)

        return player, card, action

    def _assert_cards_count(self, game, check_player,
                            pile, public, discarded, player):
        self.assertEqual(len(game.pile), pile)
        self.assertEqual(len(game.public), public)
        self.assertEqual(len(game.discarded), discarded)
        self.assertEqual(len(check_player.cards), player)

    def test_pile_card(self):
        game, players = self._start_game()

        active_player = game.active_player

        self._assert_cards_count(
            game, active_player, pile=0, public=0, discarded=0, player=0)

        player, card, action = self._player_turn(game, ACTION_PILE_CARD)

        self.assertEqual(action, ACTION_PILE_CARD)
        self._assert_cards_count(
            game, active_player, pile=1, public=0, discarded=0, player=0)

    def test_show_card(self):
        game, players = self._start_game()

        active_player = game.active_player

        self._assert_cards_count(
            game, active_player, pile=0, public=0, discarded=0, player=0)

        player, card, action = self._player_turn(game, ACTION_SHOW_CARD)

        self.assertEqual(action, ACTION_SHOW_CARD)
        self._assert_cards_count(
            game, active_player, pile=0, public=1, discarded=0, player=0)

    def test_take_card(self):
        game, players = self._start_game()

        active_player = game.active_player

        self._assert_cards_count(
            game, active_player, pile=0, public=0, discarded=0, player=0)

        player, card, action = self._player_turn(game, ACTION_TAKE_CARD)

        self.assertEqual(action, ACTION_TAKE_CARD)
        self._assert_cards_count(
            game, active_player, pile=0, public=0, discarded=0, player=1)

    def test_discard_card(self):
        game, players = self._start_game()

        active_player = game.active_player

        self._assert_cards_count(
            game, active_player, pile=0, public=0, discarded=0, player=0)

        with patch.object(game, "deck") as fake_deck:
            change_card = {"type": "change", "letter": None, "value": 2}
            fake_deck.pop.return_value = change_card
            player, card, action = self._player_turn(game, ACTION_DISCARD_CARD)
            self.assertEqual(card, change_card)

        self.assertEqual(action, ACTION_DISCARD_CARD)
        self._assert_cards_count(
            game, active_player, pile=0, public=0, discarded=1, player=0)

    def test_game(self):
        game, players = self._start_game()

        active_player = game.active_player
        deck_count = game.deck_count
        self.assertIn(active_player, players)

        self.assertEqual(set(game.dice.values()), {3})

        for i in range(game.turns_per_player):
            player, card, action = self._player_turn(game)
            self.assertEqual(player, active_player)

        self.assertEqual(game.deck_count, deck_count - game.turns_per_player)

        self.assertEqual(game.public_count, game.player_count - 1)
        self.assertEqual(game.state, 'public')
        self.assertNotEqual(active_player, game.active_player)

        player, card, action = self._player_turn(game)

        self.assertNotEqual(active_player, player)
        self.assertEqual(game.turns_left, 3)

    def test_using_dice_change_cards(self):
        game, players = self._start_game()
        card = {'type': 'change', 'value': -1, 'letter': None}

        game.use_change_card(card, [])
        self.assertEqual(sum(game.dice.values()), 15)

        card['value'] = 2
        game.use_change_card(card, ['brown', 'red'])
        self.assertEqual(sum(game.dice.values()), 17)

        card['value'] = 0
        game.use_change_card(card, ['-blue'])
        self.assertEqual(sum(game.dice.values()), 16)

    def test_until_auction_phase_2_players(self):
        game, players = self._start_game(2)

        self.assertEqual(len(game.deck), 60)

        while game.state != 'auction':
            player, card, action = self._player_turn(game)

        player_cards = sum(len(p.cards) for p in players)

        self.assertEqual(game.public_count, 0)
        self.assertEqual(game.pile_count, 20)
        self.assertEqual(game.discarded_count + player_cards, 40)

        while game.state != 'end':
            player, card, action = self._player_turn(game)

        player_cards = sum(len(p.cards) for p in players)

        self.assertEqual(game.public_count, 0)
        self.assertEqual(game.pile_count, 0)
        self.assertEqual(game.discarded_count + player_cards, 60)

    def test_until_auction_phase_3_players(self):
        game, players = self._start_game(3)

        self.assertEqual(len(game.deck), 72)

        while game.state != 'auction':
            player, card, action = self._player_turn(game)

        player_cards = sum(len(p.cards) for p in players)

        self.assertEqual(game.public_count, 0)
        self.assertEqual(game.pile_count, 18)
        self.assertEqual(game.discarded_count + player_cards, 54)

        while game.state != 'end':
            player, card, action = self._player_turn(game)

        player_cards = sum(len(p.cards) for p in players)

        self.assertEqual(game.public_count, 0)
        self.assertEqual(game.pile_count, 0)
        self.assertEqual(game.discarded_count + player_cards, 72)

    def test_until_auction_phase_4_players(self):
        game, players = self._start_game(4)

        self.assertEqual(len(game.deck), 80)

        while game.state != 'auction':
            player, card, action = self._player_turn(game)

        player_cards = sum(len(p.cards) for p in players)

        self.assertEqual(game.public_count, 0)
        self.assertEqual(game.pile_count, 16)
        self.assertEqual(game.discarded_count + player_cards, 64)

        while game.state != 'end':
            player, card, action = self._player_turn(game)

        player_cards = sum(len(p.cards) for p in players)

        self.assertEqual(game.public_count, 0)
        self.assertEqual(game.pile_count, 0)
        self.assertEqual(game.discarded_count + player_cards, 80)

    def test_player_score(self):
        player = Player()
        player.cards = [{'type': 'gold', 'value': 3, 'letter': None},
                        {'type': 'green', 'value': 1, 'letter': 'A'},
                        {'type': 'green', 'value': 2, 'letter': 'D'}]
        self.assertEqual(player.score_type('green'), (3, 'A'))
        self.assertEqual(player.score_type('gold'), (3, None))
        self.assertEqual(player.score_type('red'), (0, None))

    def test_game_score(self):
        game, players = self._start_game(2)
        game.dice = {'green': 3, 'blue': 1, 'red': 1, 'orange': 1, 'brown': 1}
        players[0].cards = [{'type': 'green', 'value': 2, 'letter': 'D'},
                            {'type': 'blue', 'value': 3, 'letter': 'D'}]
        players[1].cards = [{'type': 'red', 'value': 1, 'letter': 'A'},
                            {'type': 'orange', 'value': 1, 'letter': 'A'},
                            {'type': 'brown', 'value': 3, 'letter': 'D'}]
        self.assertEqual(game.winner(), players[0])

    def test_game_score_gold_tiebreaker(self):
        game, players = self._start_game(2)
        game.dice = {'green': 2, 'blue': 1, 'red': 1, 'orange': 1, 'brown': 1}
        players[0].cards = [{'type': 'green', 'value': 2, 'letter': 'D'},
                            {'type': 'blue', 'value': 3, 'letter': 'D'},
                            {'type': 'gold', 'value': 2, 'letter': None}]
        players[1].cards = [{'type': 'red', 'value': 1, 'letter': 'A'},
                            {'type': 'orange', 'value': 1, 'letter': 'A'},
                            {'type': 'brown', 'value': 3, 'letter': 'D'},
                            {'type': 'gold', 'value': 3, 'letter': None}]
        self.assertEqual(game.winner(), players[1])

    def test_game_score_monk_tiebreaker(self):
        game, players = self._start_game(2)
        game.dice = {'green': 2, 'blue': 1, 'red': 1, 'orange': 1, 'brown': 1}
        players[0].cards = [{'type': 'green', 'value': 2, 'letter': 'D'},
                            {'type': 'brown', 'value': 2, 'letter': 'D'},
                            {'type': 'gold', 'value': 3, 'letter': None}]
        players[1].cards = [{'type': 'red', 'value': 1, 'letter': 'A'},
                            {'type': 'orange', 'value': 1, 'letter': 'A'},
                            {'type': 'blue', 'value': 3, 'letter': 'D'},
                            {'type': 'gold', 'value': 3, 'letter': None}]
        self.assertEqual(game.winner(), players[0])

    def test_game_score_orange_tiebreaker(self):
        game, players = self._start_game(3)
        game.dice = {'green': 2, 'blue': 1, 'red': 1, 'orange': 1, 'brown': 1}
        players[0].cards = [{'type': 'red', 'value': 2, 'letter': 'D'},
                            {'type': 'brown', 'value': 2, 'letter': 'B'},
                            {'type': 'gold', 'value': 3, 'letter': None}]
        players[1].cards = [{'type': 'orange', 'value': 3, 'letter': 'A'},
                            {'type': 'gold', 'value': 3, 'letter': None}]
        # player 2 should not be considered for the tie breaker because his
        # score was too low
        players[2].cards = [{'type': 'brown', 'value': 4, 'letter': 'C'}]
        self.assertEqual(game.winner(), players[1])
