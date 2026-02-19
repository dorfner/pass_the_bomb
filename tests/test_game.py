import unittest

from backend.game_state import GameState


class MockWS:
    def __init__(self):
        self.sent = []

    def send(self, msg):
        self.sent.append(msg)



class TestGameState(unittest.TestCase):
    def setUp(self):
        self.game = GameState({
            'bizaʁ': ['bizarre', 'bizarres'],
            'ʁobo': ['robots', 'robot'],
            'vɛʁb': ['verbes', 'verbe'],
            'alyminjɔm': ['aluminium'],
            'baʁʒo': ['barjos',
                'bargeots',
                'barjots',
                'barjot',
                'bargeot',
                'barjots',
                'barjot',
                'barjo',
                'barjos',
                'barjo'],
            'mɛʁvɛjøz': ['merveilleuses',
                'merveilleuse',
                'merveilleuse',
                'merveilleuses'],
        })
        self.ws1 = MockWS()
        self.ws2 = MockWS()

    def tearDown(self):
        if self.game.timer:
            self.game.timer.cancel()

    def test_add_player_sends_lobby(self):
        self.game.add_player(self.ws1, "Alice")
        self.assertTrue(any('"LOBBY"' in m for m in self.ws1.sent))

    def test_no_start_missing_vote(self):
        self.game.add_player(self.ws1, "A")
        self.game.add_player(self.ws2, "B")
        self.game.vote_start(self.ws1)
        self.assertFalse(self.game.is_running)
    
    def test_start_with_two(self):
        self.game.add_player(self.ws1, "A")
        self.game.add_player(self.ws2, "B")
        self.game.vote_start(self.ws1)
        self.game.vote_start(self.ws2)
        self.assertTrue(self.game.is_running)

    def test_turn_based_only_active_submits(self):
        self.game.add_player(self.ws1, "A")
        self.game.add_player(self.ws2, "B")
        self.game.ipa_word = "ʁobo"

        # Determine who is active (current_turn=0 → ws1)
        active = self.game.player_order[self.game.current_turn]
        inactive = self.ws2 if active == self.ws1 else self.ws1

        # Inactive player submit should be ignored
        inactive.sent.clear()
        self.game.submit_word(inactive, "robot")
        self.assertFalse(any('"Valid"' in m for m in inactive.sent))

        # Active player submit should work
        self.game.submit_word(active, "robot")
        self.assertTrue(any('"Valid"' in m for m in active.sent))

    def test_turn_advances_after_valid(self):
        self.game.add_player(self.ws1, "A")
        self.game.add_player(self.ws2, "B")
        initial_turn = self.game.current_turn

        self.game.ipa_word = "ʁobo"
        active = self.game.player_order[self.game.current_turn]
        self.game.submit_word(active, "robot")

        self.assertNotEqual(self.game.current_turn, initial_turn)

    def test_remove_player(self):
        self.game.add_player(self.ws1, "Alice")
        self.game.remove_player(self.ws1)
        self.assertNotIn(self.ws1, self.game.players)


if __name__ == "__main__":
    unittest.main()
