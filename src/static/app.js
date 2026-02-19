/* global React, ReactDOM */
const { useState, useEffect, useRef, useCallback } = React;

// ── WebSocket Hook ───────────────────────────────────────────────

function useWebSocket() {
    const [connected, setConnected] = useState(false);
    const [lastMsg, setLastMsg] = useState(null);
    const ws = useRef(null);

    useEffect(() => {
        const proto = location.protocol === "https:" ? "wss" : "ws";
        ws.current = new WebSocket(`${proto}://${location.host}/ws`);

        ws.current.onopen = () => setConnected(true);
        ws.current.onclose = () => setConnected(false);
        ws.current.onmessage = (e) => setLastMsg(JSON.parse(e.data));

        return () => ws.current.close();
    }, []);

    const send = useCallback((obj) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify(obj));
        }
    }, []);

    return { connected, send, lastMsg };
}

// ── Lobby ────────────────────────────────────────────────────────

function Lobby({ onJoin }) {
    const [name, setName] = useState("");

    const submit = (e) => {
        e.preventDefault();
        if (name.trim()) onJoin(name.trim());
    };

    return (
        <div className="card lobby">
            <h1>💣 BombParty</h1>
            <p>Trouve un mot contenant la syllabe… avant que ça explose !</p>
            <form onSubmit={submit}>
                <input
                    type="text"
                    placeholder="Ton pseudo"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    autoFocus
                />
                <button disabled={!name.trim()}>Rejoindre</button>
            </form>
        </div>
    );
}

// ── Waiting Room ─────────────────────────────────────────────────

function WaitingRoom({ lobby, myName, onVoteStart }) {
    const voted = lobby.startVotes || [];
    const hasVoted = voted.includes(myName);
    const allVoted = voted.length === lobby.count && lobby.count > 0;

    return (
        <div className="card waiting">
            <h2>⏳ En attente de joueurs…</h2>
            <p className="waiting-hint">La partie commence quand tout le monde a voté</p>
            <div className="waiting-count">
                {lobby.count} {lobby.count === 1 ? "joueur" : "joueurs"}
            </div>
            <div className="waiting-players">
                {lobby.players.map((name, i) => (
                    <span key={i} className="waiting-tag">{name}</span>
                ))}
            </div>
            {lobby.count > 0 && (
                <div className="waiting-vote">
                    <p className="vote-count">{voted.length} / {lobby.count} ont voté</p>
                    <button
                        type="button"
                        className="btn-start"
                        onClick={onVoteStart}
                        disabled={hasVoted || allVoted}
                    >
                        {hasVoted ? "✓ Vous avez voté" : "Lancer la partie"}
                    </button>
                </div>
            )}
        </div>
    );
}

// ── Game Over ────────────────────────────────────────────────────

function GameOver({ winner }) {
    return (
        <div className="card gameover">
            <h1>🏆 Victoire !</h1>
            <p className="winner-name">{winner}</p>
            <p className="gameover-hint">Recharge la page pour rejouer</p>
        </div>
    );
}

// ── Game ─────────────────────────────────────────────────────────

function Game({ gameState, myName, onSubmit, feedback, onTyping, typing }) {
    const [answer, setWord] = useState("");
    const inputRef = useRef(null);
    const timerRef = useRef(null);

    const isMyTurn = gameState.activePlayer === myName;

    // Reset on new question
    useEffect(() => {
        setWord("");
        if (isMyTurn) inputRef.current?.focus();

        if (timerRef.current) {
            timerRef.current.style.transition = "none";
            timerRef.current.style.width = "100%";
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    if (timerRef.current) {
                        timerRef.current.style.transition = "width 25s linear";
                        timerRef.current.style.width = "0%";
                    }
                });
            });
        }
    }, [gameState.question, gameState.activePlayer]);

    const submit = (e) => {
        e.preventDefault();
        if (answer.trim() && isMyTurn) {
            onSubmit(answer.trim());
            setWord("");
            if (onTyping) onTyping("");
        }
    };

    return (
        <div className="game-container">
            <div className="game-main">
                <div className="card game">
                    <div className="turn-info">
                        {isMyTurn
                            ? <span className="your-turn">🎯 C'est ton tour !</span>
                            : <span className="other-turn">⏳ Tour de <strong>{gameState.activePlayer}</strong></span>
                        }
                    </div>

                    <div className="question">{gameState.question}</div>

                    <form onSubmit={submit}>
                        <input
                            ref={inputRef}
                            type="text"
                            value={answer}
                            onChange={(e) => {
                                const value = e.target.value;
                                setWord(value);
                                if (isMyTurn && onTyping) onTyping(value);
                            }}
                            placeholder={isMyTurn ? "Tape un mot…" : "Ce n'est pas ton tour"}
                            disabled={!isMyTurn}
                            autoFocus
                        />
                        <button disabled={!answer.trim() || !isMyTurn}>Envoyer</button>
                    </form>

                    {typing?.text && (
                        <div className="typing-indicator">
                            <span className="ghost-word">{typing.text}</span>
                        </div>
                    )}

                    <div className={`feedback ${feedback?.cls || ""}`}>
                        {feedback?.text || "\u00A0"}
                    </div>
                </div>

                <div className="players">
                    {gameState.players.map((p, i) => (
                        <div key={i} className={`player ${p.name === gameState.activePlayer ? "active" : ""}`}>
                            <div className="name">{p.name}</div>
                            <div className="lives">{"♥".repeat(Math.max(0, p.lives))}</div>
                        </div>
                    ))}
                </div>
            </div>

            {gameState.previousQuestion && (
                <div className="card previous-question">
                    <h3>Mot précédent</h3>
                    <div className="question">{gameState.previousQuestion}</div>
                    <div className="previous-answers-label">Réponses correctes :</div>
                    <div className="previous-answers">
                        {gameState.previousQuestionAnswers.map((answer, i) => (
                            <span key={i} className="answer-tag">{answer}</span>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

// ── App ──────────────────────────────────────────────────────────

function App() {
    const { connected, send, lastMsg } = useWebSocket();
    const [myName, setMyName] = useState("");
    const [joined, setJoined] = useState(false);
    const [gameStarted, setGameStarted] = useState(false);
    const [gameOver, setGameOver] = useState(null);
    const [lobby, setLobby] = useState({ count: 0, players: [] });
    const [gameState, setGameState] = useState({ question: "···", players: [], activePlayer: "", previousQuestion: "", previousQuestionAnswers: [] });
    const [feedback, setFeedback] = useState(null);
    const [typing, setTyping] = useState(null);

    useEffect(() => {
        if (!lastMsg) return;

        switch (lastMsg.type) {
            case "LOBBY":
                setLobby({
                    count: lastMsg.count,
                    players: lastMsg.players,
                    startVotes: lastMsg.startVotes || [],
                });
                break;
            case "NEW_TURN":
                setGameStarted(true);
                setGameState({
                    question: lastMsg.question,
                    players: lastMsg.players,
                    activePlayer: lastMsg.activePlayer,
                    previousQuestion: lastMsg.previousQuestion || "",
                    previousQuestionAnswers: lastMsg.previousQuestionAnswers || [],
                });
                setFeedback({
                    previousAnswers: lastMsg.previousAnswers,
                });
                setTyping(null);
                break;
            case "TYPING":
                setTyping({ player: lastMsg.player, text: lastMsg.text });
                break;
            case "Valid":
                setFeedback({ cls: "valid", text: `✓ ${lastMsg.anwser}` });
                break;
            case "Invalid":
                setFeedback({ cls: "invalid", text: "✗ Mot invalide" });
                break;
            case "EXPLODE":
                setFeedback({
                    cls: "explode",
                    text: lastMsg.eliminated
                        ? `💥 ${lastMsg.player} éliminé !`
                        : `💥 ${lastMsg.player} perd une vie !`,
                });
                break;
            case "GAME_OVER":
                setGameOver(lastMsg.winner);
                break;
        }
    }, [lastMsg]);

    // Not connected yet
    if (!connected) {
        return (
            <div className="card connecting">
                Connexion au serveur<span className="dot">...</span>
            </div>
        );
    }

    // Game ended
    if (gameOver) {
        return <GameOver winner={gameOver} />;
    }

    // Step 1: Lobby — enter name
    if (!joined) {
        return (
            <Lobby onJoin={(name) => {
                setMyName(name);
                send({ type: "JOIN", name });
                setJoined(true);
            }} />
        );
    }

    // Step 2: Waiting room
    if (!gameStarted) {
        return (
            <WaitingRoom
                lobby={lobby}
                myName={myName}
                onVoteStart={() => send({ type: "VOTE_START" })}
            />
        );
    }

    // Step 3: Game
    return (
        <Game
            gameState={gameState}
            myName={myName}
            onSubmit={(answer) => send({ type: "SUBMIT", answer })}
            feedback={feedback}
            typing={typing}
            onTyping={(text) => send({ type: "TYPING", text })}
        />
    );
}

// ── Mount ────────────────────────────────────────────────────────

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
