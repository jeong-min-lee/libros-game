from unittest import TestCase

from libros.game import deal


class TestGame(TestCase):
    def test_deal(self):
        self.assertEqual(len(deal(4)), 80)
        self.assertEqual(len(deal(3)), 72)
        self.assertEqual(len(deal(2)), 60)
