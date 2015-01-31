import random
from itertools import cycle


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

    def join(self, player):
        self.players.append(player)

    def start(self):
        assert self.player_count in [2, 3, 4]
        self.state = 'place'
        self.deck = deal(self.player_count)

    @property
    def player_count(self):
        return len(self.players)


class Player(object):
    pass
