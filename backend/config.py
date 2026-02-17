import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Literal


@dataclass(frozen=True)
class AppConfig:
    # Server
    host: str = "0.0.0.0"
    port: int = 8765

    # Dictionary
    dictionary_file: str = "spelling_dict_reduced.json"

    # Game rules
    lives_per_player: int = 3
    timer_min_seconds: int = 20
    timer_max_seconds: int = 30
    turn_transition_delay_seconds: float = 2.5

    # Start behavior: "vote" or "auto"
    start_mode: Literal["vote", "auto"] = "vote"
    min_players_to_start: int = 1

    # UX / networking
    echo_typing_to_sender: bool = False
    normalize_spellings: bool = True


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _to_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("1", "true", "yes", "y", "on"):
            return True
        if v in ("0", "false", "no", "n", "off"):
            return False
    return default


def load_config(path: str | None = None) -> AppConfig:
    """Load configuration from JSON file. Uses defaults if file missing."""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "config.json")

    data: Dict[str, Any] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
    except FileNotFoundError:
        data = {}

    host = str(data.get("host", AppConfig.host))
    port = _to_int(data.get("port", AppConfig.port), AppConfig.port)
    dictionary_file = str(data.get("dictionary_file", AppConfig.dictionary_file))
    lives_per_player = _to_int(data.get("lives_per_player", AppConfig.lives_per_player), AppConfig.lives_per_player)
    timer_min_seconds = _to_int(data.get("timer_min_seconds", AppConfig.timer_min_seconds), AppConfig.timer_min_seconds)
    timer_max_seconds = _to_int(data.get("timer_max_seconds", AppConfig.timer_max_seconds), AppConfig.timer_max_seconds)
    turn_transition_delay_seconds = _to_float(
        data.get("turn_transition_delay_seconds", AppConfig.turn_transition_delay_seconds),
        AppConfig.turn_transition_delay_seconds,
    )
    start_mode = data.get("start_mode", AppConfig.start_mode)
    if start_mode not in ("vote", "auto"):
        start_mode = AppConfig.start_mode
    min_players_to_start = _to_int(data.get("min_players_to_start", AppConfig.min_players_to_start), AppConfig.min_players_to_start)
    if min_players_to_start < 1:
        min_players_to_start = 1
    echo_typing_to_sender = _to_bool(data.get("echo_typing_to_sender", AppConfig.echo_typing_to_sender), AppConfig.echo_typing_to_sender)
    normalize_spellings = _to_bool(data.get("normalize_spellings", AppConfig.normalize_spellings), AppConfig.normalize_spellings)

    if timer_min_seconds < 1:
        timer_min_seconds = 1
    if timer_max_seconds < timer_min_seconds:
        timer_max_seconds = timer_min_seconds

    return AppConfig(
        host=host,
        port=port,
        dictionary_file=dictionary_file,
        lives_per_player=lives_per_player,
        timer_min_seconds=timer_min_seconds,
        timer_max_seconds=timer_max_seconds,
        turn_transition_delay_seconds=turn_transition_delay_seconds,
        start_mode=start_mode,
        min_players_to_start=min_players_to_start,
        echo_typing_to_sender=echo_typing_to_sender,
        normalize_spellings=normalize_spellings,
    )
