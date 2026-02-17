import unittest

from backend.game_state import GameState
from backend.utils import remove_accents, generate_syllable


class MockWS:
    def __init__(self):
        self.sent = []

    def send(self, msg):
        self.sent.append(msg)


class TestUtils(unittest.TestCase):
    def test_remove_accents(self):
        self.assertEqual(remove_accents("fenêtre"), "fenetre")
        self.assertEqual(remove_accents("café"), "cafe")
        self.assertEqual(remove_accents("hello"), "hello")

    def test_generate_syllable_length(self):
        syl = generate_syllable({"maison", "ordinateur", "chocolat"})
        self.assertIn(len(syl), [2, 3])

    def test_generate_syllable_empty(self):
        self.assertEqual(generate_syllable(set()), "ent")


class TestGameState(unittest.TestCase):
    def setUp(self):
        self.game = GameState({"maison", "bombe", "chocolat", "fromage"})
        self.ws1 = MockWS()
        self.ws2 = MockWS()

    def tearDown(self):
        if self.game.timer:
            self.game.timer.cancel()

    def test_add_player_sends_lobby(self):
        self.game.add_player(self.ws1, "Alice")
        self.assertTrue(any('"LOBBY"' in m for m in self.ws1.sent))

    def test_no_start_with_one_player(self):
        self.game.add_player(self.ws1, "Alice")
        self.assertFalse(self.game.is_running)

    def test_auto_start_with_two(self):
        self.game.add_player(self.ws1, "A")
        self.game.add_player(self.ws2, "B")
        self.assertTrue(self.game.is_running)

    def test_turn_based_only_active_submits(self):
        self.game.add_player(self.ws1, "A")
        self.game.add_player(self.ws2, "B")
        self.game.syllable = "mai"

        # Determine who is active (current_turn=0 → ws1)
        active = self.game.player_order[self.game.current_turn]
        inactive = self.ws2 if active == self.ws1 else self.ws1

        # Inactive player submit should be ignored
        inactive.sent.clear()
        self.game.submit_word(inactive, "maison")
        self.assertFalse(any('"Valid"' in m for m in inactive.sent))

        # Active player submit should work
        self.game.submit_word(active, "maison")
        self.assertTrue(any('"Valid"' in m for m in active.sent))

    def test_turn_advances_after_valid(self):
        self.game.add_player(self.ws1, "A")
        self.game.add_player(self.ws2, "B")
        initial_turn = self.game.current_turn

        self.game.syllable = "mai"
        active = self.game.player_order[self.game.current_turn]
        self.game.submit_word(active, "maison")

        self.assertNotEqual(self.game.current_turn, initial_turn)

    def test_remove_player(self):
        self.game.add_player(self.ws1, "Alice")
        self.game.remove_player(self.ws1)
        self.assertNotIn(self.ws1, self.game.players)

    def test_no_reuse(self):
        self.game.add_player(self.ws1, "A")
        self.game.add_player(self.ws2, "B")
        self.game.syllable = "mai"

        active = self.game.player_order[self.game.current_turn]
        self.game.submit_word(active, "maison")

        # Force syllable back and try reuse from next active player
        self.game.syllable = "mai"
        new_active = self.game.player_order[self.game.current_turn]
        new_active.sent.clear()
        self.game.submit_word(new_active, "maison")
        self.assertTrue(any('"Invalid"' in m for m in new_active.sent))


if __name__ == "__main__":
    unittest.main()
