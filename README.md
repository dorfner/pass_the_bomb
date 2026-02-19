# Pass the bomb

## Quickstart

### Installation
```
make install
```

### Jouer au jeu
```
make run
```
Se connecter au jeu sur n'importe quelle IP au port 8765.


## Description

Jeu multijoueur dans lequel les joueurs doivent trouver, à tour de rôle, un mot répondant à une question s'affichant. Si un joueur ne valide pas son mot avant que la mèche de la bombe ne se consume entièrement, il perd une vie. Le dernier joueur encore en vie remporte la partie.


## Architecture technique

```
pass_the_bomb/
├── src/
│   ├── app.py              # Flask entry point (WS + static)
│   ├── game_state.py       # Logique de jeu thread-safe
│   ├── utils.py
│   ├── config.py
│   ├── config.json         # Paramètres du jeu
│   ├── data/               # Dictionnaire questions réponses
│   ├── static/             # JS, CSS (servis par Flask)
│   └── templates/          # HTML (Jinja2)
├── tests/
├── pyproject.toml          # Dépendances
└── Makefile
```

### Backend (`backend/`)

- **Langage** : Python 3.11+
- **Dépendances** : `flask` + `flask-sock` + `threading`
- **Rôle** : Logique de jeu, WebSocket, sert le frontend.

### Frontend (`backend/static/` + `backend/templates/`)

- **Technologie** : React 18 via CDN (zéro npm/node)
- **Design** : Dark theme, Inter font, animations CSS

### Tooling
- **Makefile** : `install`, `test`, `run`, `format`, `clean`
