import random
import string

from copy import copy
from itertools import cycle
from collections import Counter, defaultdict, namedtuple


ACTION_TAKE_CARD = 0
ACTION_PILE_CARD = 1
ACTION_SHOW_CARD = 2
ACTION_DISCARD_CARD = 3

ACTIONS = [
    ACTION_TAKE_CARD, ACTION_PILE_CARD,
    ACTION_SHOW_CARD, ACTION_DISCARD_CARD,
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
        self.actions_taken = Counter()

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

    def turn_action(self, player, card, action):
        """Handles player action and its influence on the game."""
        action_func = {
            ACTION_PILE_CARD: lambda: self.pile.append(card),
            ACTION_SHOW_CARD: lambda: self.public.append(card),
            ACTION_DISCARD_CARD: lambda: self.discarded.append(card),
        }.get(action, lambda: None)

        if self.state == 'public':
            # we're in the public phase so we first remove the card
            self.public.remove(card)

        action_func()
        self.actions_taken[action] += 1

        if action == ACTION_DISCARD_CARD:
            # discarding a card counts as taking it first as well
            self.actions_taken[ACTION_TAKE_CARD] += 1

    def turn_complete(self, player, card, action):
        """Handles moving to the next state and advancing player turns."""
        if self.turns_left == 0 and self.public:
            self.state = 'public'
            self.next_player()

        if self.deck_count == 0 and not self.public:
            self.state = 'auction'

        if self.state == 'public' and not self.public:
            # current player finished their turn
            self.state = 'next_player'
            self.next_player()

    def valid_actions(self, card):
        """Returns a list of valid actions for the current turn."""
        if self.state == 'public':
            if card['type'] == 'change':
                return [ACTION_DISCARD_CARD]
            return [ACTION_TAKE_CARD]

        actions = copy(ACTIONS)
        actions.remove(ACTION_DISCARD_CARD)

        # if we have shown enough cards remove the action
        if self.actions_taken[ACTION_SHOW_CARD] == self.player_count - 1:
            actions.remove(ACTION_SHOW_CARD)

        if self.actions_taken[ACTION_PILE_CARD]:
            actions.remove(ACTION_PILE_CARD)

        if self.actions_taken[ACTION_TAKE_CARD]:
            actions.remove(ACTION_TAKE_CARD)

        if card['type'] == 'change' and ACTION_TAKE_CARD in actions:
            actions.append(ACTION_DISCARD_CARD)

        return actions

    def reset_actions(self):
        self.actions_taken.clear()

    def winner(self):
        score = namedtuple('Score', ['value', 'player'])
        player_scores = defaultdict(lambda: 0)
        for color in COLORS:
            winner = sorted([score(player.score_type(color), player)
                             for player in self.players],
                            reverse=True)[0]
            if winner.value:
                player_scores[winner.player] += self.dice[color]
        # The rules don't say this but the author says "Those involved in the
        # tie for the win will use the Illuminator category as a tie-breaker;
        # hence, whoever has the highest total value wins, then it goes to
        # tie-breaker card. If none of the tied players have an Illuminator,
        # then it moves down the line to Scribes and so on. This way, everyone
        # knows that Illuminators are slightly more valuable to have."
        return max((score,
                    player.score_type('gold')[0],
                    player.score_type('brown')[0],
                    player.score_type('blue')[0],
                    player.score_type('green')[0],
                    player.score_type('orange')[0],
                    player.score_type('red')[0],
                    player)
                   for player, score in player_scores.iteritems())[7]


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

        self.game.turn_action(self, card, action)
        self.game.turn_complete(self, card, action)

        return action

    def score_type(self, type):
        cards = [(card['value'], card['letter'])
                 for card in self.cards if card['type'] == type]
        if not cards:
            return (0, None)
        return (sum(card[0] for card in cards),
                min(card[1] for card in cards))
