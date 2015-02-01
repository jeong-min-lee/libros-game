import random
from itertools import cycle


ACTION_TAKE_CARD = 0
ACTION_PILE_CARD = 1
ACTION_SHOW_CARD = 2

ACTIONS = [ACTION_TAKE_CARD, ACTION_PILE_CARD, ACTION_SHOW_CARD]


def deal(players):
    assert players in [2, 3, 4]
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
    for kind, value, count in cards:
        deck += [{kind: value} for _ in xrange(count)]
    random.shuffle(deck)
    if players == 4:
        return deck[7:]
    if players == 3:
        return deck[12:]
    if players == 2:
        return deck[21:]


class Game(object):
    def __init__(self):
        self.players = []
        self.deck = None
        self.state = 'waiting'
        self.player = None
        self.turns = 0
        self.pile = []
        self.public = []

    def join(self, player):
        self.players.append(player)
        player.join(self)

    def start(self):
        assert self.player_count in [2, 3, 4]
        self.state = 'place'
        self.player = self.players[0]
        # 1 into hand + 1 into pile + (player_count - 1) in front
        self.turns = 2 + self.player_count - 1
        self.deck = deal(self.player_count)

    @property
    def player_count(self):
        return len(self.players)

    @property
    def active_player(self):
        return self.player

    def turn(self):
        assert self.deck
        card = self.deck.pop()
        return self.active_player, card

    def pile_card(self, card):
        self.pile.append(card)

    def show_card(self, card):
        self.public.append(card)


class Player(object):
    def __init__(self):
        self.game = None
        self.cards = []

    def join(self, game):
        assert not self.game
        self.game = game

    def act(self, card):
        assert self.game

        choice = random.choice(ACTIONS)

        if choice == ACTION_TAKE_CARD:
            self.cards.append(card)
        elif choice == ACTION_PILE_CARD:
            self.game.pile_card(card)
        else:
            self.game.show_card(card)

        return choice
