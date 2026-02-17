# Jeu de la Bombe (BombParty)

## Description

BombParty est un jeu de vocabulaire multijoueur en ligne où les joueurs doivent trouver, à tour de rôle, un mot contenant une syllabe (ou suite de lettres) imposée. Si un joueur ne valide pas son mot avant que la mèche de la bombe ne se consume entièrement, il perd une vie. Le dernier joueur encore en vie remporte la partie.

## Configuration de la partie

| Paramètre               | Valeur              |
| ------------------------ | ------------------- |
| Nombre de joueurs        | 2 – 8               |
| Nombre de vies initial   | 3 (♥♥♥)             |
| Timer de la bombe        | 20 – 40 s (aléatoire) |
| Pénalité sur faute       | −3 à −6 s sur le timer |

## Règles du jeu

### Déroulement d'un tour

1. Une **syllabe** (suite de 2-3 lettres) est générée aléatoirement et affichée à tous les joueurs.
2. Le joueur actif doit saisir un mot **contenant** cette syllabe.
3. Le mot est validé si :
   - Il existe dans le dictionnaire (langue française).
   - Il contient la syllabe imposée.
   - Il n'a **pas déjà été utilisé** dans la partie en cours.
4. Si le mot est valide, le tour passe au joueur suivant et une nouvelle syllabe est générée.
5. Si le mot est invalide (faute), le joueur reçoit un **feedback d'erreur** et le timer de la bombe est réduit de **3 à 6 secondes** (aléatoire).
6. Si la bombe **explose** (timer à 0), le joueur actif perd **une vie** et le tour passe au joueur suivant avec un nouveau timer et une nouvelle syllabe.

### Fin de partie

- Un joueur qui perd toutes ses vies est **éliminé**.
- Le **dernier joueur en vie** gagne la partie.
- Si un seul joueur reste, la partie se termine immédiatement avec un écran de victoire.

### Contraintes supplémentaires

- Les mots doivent contenir au minimum **3 lettres**.
- Les accents sont ignorés lors de la validation (ex : `é` = `e`).
- Les noms propres ne sont **pas acceptés**.

## Architecture technique

```
bombe/
├── backend/
│   ├── app.py             # Flask entry point (WS + static)
│   ├── game_state.py      # Logique de jeu thread-safe
│   ├── utils.py            # Dictionnaire, syllabes
│   ├── data/dictionary.txt
│   ├── static/             # JS, CSS (servis par Flask)
│   └── templates/          # HTML (Jinja2)
├── tests/
├── pyproject.toml          # Dépendances (uv)
└── Makefile
```

### Backend (`backend/`)

- **Langage** : Python 3.11+
- **Dépendances** : `uv` (gestion), `flask` + `flask-sock` + `threading`
- **Rôle** : Logique de jeu, WebSocket, sert le frontend.

### Frontend (`backend/static/` + `backend/templates/`)

- **Technologie** : React 18 via CDN (zéro npm/node)
- **Design** : Dark theme, Inter font, animations CSS

### Tooling
- **uv** : Gestion des dépendances Python
- **Makefile** : `install`, `test`, `run`, `format`, `clean`

## Fonctionnalités MVP

- [ ] Lobby : créer / rejoindre une partie avec un pseudo.
- [ ] Boucle de jeu complète (tours, timer, validation, vies).
- [ ] Dictionnaire français intégré pour la validation des mots.
- [ ] Affichage temps réel de l'état de la partie pour tous les joueurs.
- [ ] Écran de fin (victoire / défaite).

## Fonctionnalités bonus (post-MVP)

- [ ] Système de score cumulé sur plusieurs manches.
- [ ] Difficulté progressive (timer qui raccourcit au fil des tours).
- [ ] Choix de la langue (FR / EN).
- [ ] Chat textuel entre les joueurs.
- [ ] Sons et effets visuels avancés (tick-tock, explosion, etc.).
