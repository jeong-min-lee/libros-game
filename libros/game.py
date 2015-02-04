import random
import string

from copy import copy
from itertools import cycle


ACTION_TAKE_CARD = 0
ACTION_PILE_CARD = 1
ACTION_SHOW_CARD = 2
ACTION_DISCARD_CARD = 3
ACTION_TAKE_PUBLIC_CARD = 4

ACTIONS = [
    ACTION_TAKE_CARD, ACTION_PILE_CARD,
    ACTION_SHOW_CARD, ACTION_DISCARD_CARD,
    ACTION_TAKE_PUBLIC_CARD,
]

COLORS = ('blue', 'brown', 'red', 'orange', 'green')


def deal(players, cards_to_remove=None, gold_to_remove=None):
    assert players in [2, 3, 4]

    if cards_to_remove is None:
        cards_to_remove = {2: 21, 3: 12, 4: 7}.get(players)

    if gold_to_remove is None:
        gold_to_remove = 4 - players

    cards = (
        ('blue',    2, 4),
        ('blue',    3, 3),
        ('blue',    4, 2),
        ('brown',   2, 4),
        ('brown',   3, 3),
        ('brown',   4, 2),
        ('red',     1, 7),
        ('red',     2, 2),
        ('orange',  1, 7),
        ('orange',  2, 2),
        ('green',   1, 7),
        ('green',   2, 2),
        ('change', -2, 2),
        ('change', -1, 2),
        ('change',  2, 2),
        ('change',  1, 2),
        ('change',  0, 1),  # plus or minus
        ('gold',    1, 11 - gold_to_remove),
        ('gold',    2, 11 - gold_to_remove),
        ('gold',    3, 11 - gold_to_remove))
    deck = []
    letters = {}
    for color in COLORS:
        letters[color] = (x for x in string.ascii_uppercase)
    for kind, value, count in cards:
        deck += [{
            'type': kind,
            'value': value,
            'letter': letters.get(kind, cycle([None])).next(),
        } for _ in xrange(count)]
    random.shuffle(deck)

    return deck[cards_to_remove:]


class Game(object):
    def __init__(self):
        self.players = []
        self.players_cycle = []
        self.deck = None
        self.state = 'waiting'
        self.player = None
        self.player_turns_left = 0
        self.pile = []
        self.public = []
        self.discarded = []
        self.dice = {color: 3 for color in COLORS}

    def join(self, player):
        self.players.append(player)
        player.join(self, len(self.players))

    def start(self):
        assert self.player_count in [2, 3, 4]

        self.state = 'start'
        self.player_turns_left = self.turns_per_player
        self.deck = deal(self.player_count)
        self.players_cycle = cycle(self.players)

        self.state = 'next_player'
        self.next_player()

    @property
    def turns_per_player(self):
        # 1 into hand + 1 into pile + (player_count - 1) to the front
        return 2 + self.player_count - 1

    @property
    def player_count(self):
        return len(self.players)

    @property
    def deck_count(self):
        return len(self.deck)

    @property
    def pile_count(self):
        return len(self.pile)

    @property
    def discarded_count(self):
        return len(self.discarded)

    @property
    def public_count(self):
        return len(self.public)

    def next_player(self):
        if self.state == 'next_player':
            self.state = 'turn'
            self.reset_actions()
            self.player = next(self.players_cycle)
            self.player_turns_left = self.turns_per_player
        elif self.state == 'public':
            self.player = next(self.players_cycle)
        else:
            raise ValueError('Incorrect state.')

    @property
    def active_player(self):
        return self.player

    @property
    def turns_left(self):
        return self.player_turns_left

    def turn(self):
        if self.state == 'turn':
            assert self.deck
            assert self.turns_left > 0
            card = self.deck.pop()
            self.player_turns_left -= 1
        elif self.state == 'public':
            card = self.active_player.choose_public_card(copy(self.public))
        else:
            raise ValueError('Incorrect state.')

        return self.active_player, card, self.valid_actions(card)

    def use_change_card(self, card, colors):
        value = card['value']
        assert card['kind'] == 'change'
        assert len(colors) == 0 or len(colors) == max(abs(value), 1)

        if not colors:
            return

        if value == 0:
            value = colors[0] == '+' and 1 or -1
            colors = [colors[0][1:]]
        for color in colors:
            if value < 0:
                self.dice[color] -= 1
            else:
                self.dice[color] += 1
            

    def turn_complete(self, player):
        if self.turns_left == 0 and self.public:
            self.state = 'public'
            self.next_player()
        elif self.deck_count == 0:
            self.state = 'auction'
        elif self.state == 'public' and not self.public:
            self.next_player()  # == last active player => skip take public
            self.state = 'next_player'
            self.next_player()
        elif self.turns_left == 0:
            self.state = 'next_player'
            self.next_player()

    def valid_actions(self, card):
        if self.state == 'public':
            return [ACTION_TAKE_PUBLIC_CARD]

        actions = copy(ACTIONS)
        actions.remove(ACTION_TAKE_PUBLIC_CARD)
        actions.remove(ACTION_DISCARD_CARD)  # TODO: depends on card

        if self.action_show == self.player_count - 1:
            actions.remove(ACTION_SHOW_CARD)
        if self.action_pile:
            actions.remove(ACTION_PILE_CARD)
        if self.action_take_card:
            actions.remove(ACTION_TAKE_CARD)

        return actions

    def reset_actions(self):
        (self.action_discard, self.action_pile, self.action_take_card,
         self.action_show, self.action_take_public) = (0, 0, 0, 0, 0)

    def pile_card(self, card):
        self.action_pile += 1
        self.pile.append(card)

    def show_card(self, card):
        self.action_show += 1
        self.public.append(card)

    def discard_card(self, card):
        self.action_discard += 1
        self.discarded.append(card)

    def take_public_card(self, card):
        self.action_take_public += 1
        self.public.remove(card)

    def take_card(self, card):
        self.action_take_card += 1


class Player(object):
    def __init__(self):
        self.game = None
        self.cards = []
        self.id = None

    def __repr__(self):
        return u'ID: %d, Cards: %d' % (self.id, len(self.cards))

    def join(self, game, number):
        assert not self.game
        self.game = game
        self.id = number

    def choose_public_card(self, cards):
        assert cards
        return cards[0]

    def act(self, card, action=None):
        assert self.game
        assert card

        if action is None:
            action = random.choice(ACTIONS)

        assert action in ACTIONS

        if action == ACTION_TAKE_CARD:
            self.cards.append(card)
            self.game.take_card(card)
        elif action == ACTION_PILE_CARD:
            self.game.pile_card(card)
        elif action == ACTION_DISCARD_CARD:
            self.game.discard_card(card)
        elif action == ACTION_TAKE_PUBLIC_CARD:
            self.cards.append(card)
            self.game.take_public_card(card)
        else:
            self.game.show_card(card)

        self.game.turn_complete(self)

        return action
