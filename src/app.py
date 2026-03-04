"""BombParty server — Flask + flask-sock, threaded."""

import traceback
import json
import os

from flask import Flask, render_template
from flask_sock import Sock

from src.config import load_config
from src.game_state import GameState
from src.utils import load_dictionary_from_file


# ── App setup ─────────────────────────────────────────────────────

_base = os.path.dirname(os.path.abspath(__file__))
config = load_config()

app = Flask(
    __name__,
    static_folder=os.path.join(_base, "static"),
    template_folder=os.path.join(_base, "templates"),
)
sock = Sock(app)

dictionary = load_dictionary_from_file(config.dictionary_file)
game = GameState(dictionary, config=config)


# ── Routes ────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@sock.route("/ws")
def websocket(ws):
    try:
        while True:
            data = ws.receive()
            if not data:
                break

            msg = json.loads(data)
            msg_type = msg.get("type")

            if msg_type == "JOIN":
                game.add_player(ws, msg.get("name", "Anonyme"))

            elif msg_type == "SUBMIT":
                answer = msg.get("answer")
                if answer:
                    game.submit_answer(ws, answer)

            elif msg_type == "PASS":
                game.pass_turn(ws)

            elif msg_type == "TYPING":
                text = msg.get("text", "")
                game.broadcast_typing(ws, text)

            elif msg_type == "VOTE_START":
                game.vote_start(ws)

    except Exception:
        # print(f"WS error: {e}")
        print(traceback.format_exc())
    finally:
        game.remove_player(ws)


# ── Entry point ───────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host=config.host, port=config.port, threaded=True)
