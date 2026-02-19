import json
import random
import threading
import time
from src.config import AppConfig
from src.utils import remove_accents


class GameState:
    """Thread-safe, turn-based game state manager."""

    def __init__(self, spelling_dict: dict, config: AppConfig | None = None):
        if config is None:
            config = AppConfig()

        self.lock = threading.Lock()
        self.player_order = []  # ordered list of ws for turn rotation
        self.players = {}  # ws → {"name": str, "lives": int}
        self.spelling_dict = spelling_dict
        self.spelling_dict_keys = list(spelling_dict)

        # Configurable rules / behavior
        self.lives_per_player = config.lives_per_player
        self.timer_min_seconds = config.timer_min_seconds
        self.timer_max_seconds = config.timer_max_seconds
        self.turn_transition_delay_seconds = config.turn_transition_delay_seconds
        self.start_mode = config.start_mode
        self.min_players_to_start = config.min_players_to_start
        self.normalize_spellings = config.normalize_spellings

        self.question = ""
        self.answers = []
        self.previous_question = ""
        self.previous_answers = []
        self.timer = None
        self.timer_ends_at = None  # when current turn timer expires (for -1s on wrong)
        self.is_running = False
        self.current_turn = 0  # index into player_order
        self.start_votes = set()  # ws that voted to start

    # ── Public API ────────────────────────────────────────────────

    def add_player(self, ws, name):
        with self.lock:
            self.players[ws] = {"name": name, "lives": self.lives_per_player}
            self.player_order.append(ws)
            self._broadcast_lobby()
            if (
                not self.is_running
                and self.start_mode == "auto"
                and len(self.players) >= self.min_players_to_start
            ):
                self._start_game()

    def remove_player(self, ws):
        with self.lock:
            if ws not in self.players:
                return

            was_current = (
                self.is_running
                and self.player_order
                and self.player_order[self.current_turn % len(self.player_order)] == ws
            )

            self.players.pop(ws, None)
            self.start_votes.discard(ws)
            if ws in self.player_order:
                idx = self.player_order.index(ws)
                self.player_order.remove(ws)
                # Adjust current_turn if the removed player was before/at current
                if idx < self.current_turn:
                    self.current_turn -= 1
                elif idx == self.current_turn and self.player_order:
                    self.current_turn = self.current_turn % len(self.player_order)

            if len(self.players) < 1 and self.is_running:
                self._end_game()
            elif was_current and self.is_running:
                self._start_turn()

            if self.players:
                self._broadcast_lobby()

    def submit_answer(self, ws, player_answer):
        with self.lock:
            if not self.is_running or not self.player_order:
                return

            # Only the current player can submit
            active_ws = self.player_order[self.current_turn % len(self.player_order)]
            if ws != active_ws:
                return

            if (self.normalize_spellings):
                player_answer = remove_accents(player_answer.lower().strip())
                accepted_answers = [remove_accents(s.lower().strip()) for s in self.answers]
            else:
                player_answer = player_answer.lower().strip()
                accepted_answers = self.answers

            if player_answer in accepted_answers:
                self._broadcast({"type": "Valid", "answer": player_answer})
                self._advance_turn()
                self._start_turn()
            else:
                self._reduce_timer_by_seconds(1)
                try:
                    ws.send(json.dumps({"type": "Invalid"}))
                except Exception:
                    pass

    def broadcast_typing(self, ws, text: str):
        """Broadcast the active player's current input to all players."""
        with self.lock:
            if not self.is_running or not self.player_order:
                return

            active_ws = self.player_order[self.current_turn % len(self.player_order)]
            if ws != active_ws:
                return

            # Don't echo typing back to the sender (fixes solo self-echo).
            msg_json = json.dumps(
                {
                    "type": "TYPING",
                    "player": self.players[ws]["name"],
                    "text": text,
                }
            )

            dead = []
            for other_ws in self.player_order:
                if other_ws is ws:
                    continue
                try:
                    other_ws.send(msg_json)
                except Exception:
                    dead.append(other_ws)
            for other_ws in dead:
                self.remove_player_internal(other_ws)

    def vote_start(self, ws):
        """Record that this player voted to start. Start game when all have voted."""
        with self.lock:
            if (
                self.is_running
                or self.start_mode != "vote"
                or ws not in self.players
                or len(self.players) < self.min_players_to_start
            ):
                return
            self.start_votes.add(ws)
            self._broadcast_lobby()
            if len(self.start_votes) == len(self.player_order):
                self._start_game()

    # ── Internal (must hold self.lock) ────────────────────────────

    def _broadcast_lobby(self):
        voted_names = [self.players[ws]["name"] for ws in self.player_order if ws in self.start_votes]
        self._broadcast(
            {
                "type": "LOBBY",
                "count": len(self.players),
                "players": [self.players[ws]["name"] for ws in self.player_order],
                "startVotes": voted_names,
            }
        )

    def _start_game(self):
        self.is_running = True
        self.start_votes.clear()
        self.current_turn = 0
        self._start_turn()

    def _end_game(self):
        if self.timer:
            self.timer.cancel()
            self.timer = None
        self.timer_ends_at = None
        self.is_running = False

        if self.players:
            winner = list(self.players.values())[0]["name"]
            self._broadcast({"type": "GAME_OVER", "winner": winner})

    def _advance_turn(self):
        if self.player_order:
            self.current_turn = (self.current_turn + 1) % len(self.player_order)

    def _reduce_timer_by_seconds(self, seconds: float):
        """Shorten the current turn timer by the given seconds. Caller must hold lock."""
        if not self.timer or self.timer_ends_at is None:
            return
        self.timer.cancel()
        self.timer = None
        remaining = self.timer_ends_at - time.time() - seconds
        remaining = max(1.0, remaining)
        self.timer_ends_at = time.time() + remaining
        self.timer = threading.Timer(remaining, self._handle_timeout)
        self.timer.daemon = True
        self.timer.start()

    def _start_turn(self):
        if not self.player_order:
            return

        # Save previous question before selecting new one
        if self.question:  # Only save if we had a previous question
            self.previous_question = self.question
            self.previous_answers = self.answers.copy()

        self.question = random.choice(self.spelling_dict_keys)
        self.answers = self.spelling_dict[self.question]

        active_ws = self.player_order[self.current_turn % len(self.player_order)]
        active_name = self.players[active_ws]["name"]
        
        print(self.answers)
        self._broadcast(
            {
                "type": "NEW_TURN",
                "question": self.question,
                "activePlayer": active_name,
                "players": [
                    {"name": self.players[ws]["name"], "lives": self.players[ws]["lives"]}
                    for ws in self.player_order
                ],
                "previousAnswers": self.answers,
                "previousQuestion": self.previous_question,
                "previousQuestionAnswers": self.previous_answers,
            }
        )

        # Only start a new timer when there isn't one running (game start or after timeout).
        # On valid answer we advance turn but keep the same bomb timer.
        if self.timer is None:
            duration = random.randint(self.timer_min_seconds, self.timer_max_seconds)
            self.timer_ends_at = time.time() + duration
            self.timer = threading.Timer(duration, self._handle_timeout)
            self.timer.daemon = True
            self.timer.start()

    def _handle_timeout(self):
        with self.lock:
            if not self.is_running or not self.player_order:
                return

            self.timer = None  # So next _start_turn() will start a fresh timer

            active_ws = self.player_order[self.current_turn % len(self.player_order)]
            self.players[active_ws]["lives"] -= 1

            if self.players[active_ws]["lives"] <= 0:
                dead_name = self.players[active_ws]["name"]
                self._broadcast(
                    {"type": "EXPLODE",
                     "player": dead_name,
                     "eliminated": True
                })
                self.remove_player_internal(active_ws)
            else:
                self._broadcast({
                    "type": "EXPLODE",
                    "player": self.players[active_ws]["name"],
                    "eliminated": False,
                })
                self._advance_turn()

            if self.is_running:
                t = threading.Timer(self.turn_transition_delay_seconds, self._safe_next_turn)
                t.daemon = True
                t.start()

    def remove_player_internal(self, ws):
        """Remove a player without re-acquiring the lock (already held)."""
        self.players.pop(ws, None)
        if ws in self.player_order:
            idx = self.player_order.index(ws)
            self.player_order.remove(ws)
            if idx < self.current_turn:
                self.current_turn -= 1
            elif self.player_order:
                self.current_turn = self.current_turn % len(self.player_order)

        if len(self.players) < 1:
            self._end_game()

    def _safe_next_turn(self):
        with self.lock:
            if self.is_running:
                self._start_turn()

    def _broadcast(self, message):
        msg_json = json.dumps(message)
        dead = []
        for ws in self.player_order:
            try:
                ws.send(msg_json)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.remove_player_internal(ws)
