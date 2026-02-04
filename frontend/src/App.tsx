import { useEffect, useState } from "react";
import {
  Routes,
  Route,
  useNavigate,
  useParams,
  Navigate,
} from "react-router-dom";
import { HomePage } from "@/pages/HomePage";
import { GamePage } from "@/pages/GamePage";
import { useGameStore } from "@/stores/gameStore";
import { gameApi } from "@/api/gameApi";
import { EndingPage } from "./pages/EndingPage";

const LAST_SESSION_KEY = "star_odyssey:last_session_id";

function HomeRoute() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { setSession, setGameState, addNarration, setAvailableActions } =
    useGameStore();

  const handleStartGame = async (playerName: string) => {
    if (!playerName.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await gameApi.startGame(playerName);

      // Store session and state
      setSession(response.sessionId);
      setGameState(response.gameState);
      setAvailableActions(response.availableActions || []);

      // Add opening narration
      addNarration("narrator", response.initialNarration);
      if (response.oracleMessage) {
        addNarration("oracle", response.oracleMessage);
      }

      localStorage.setItem(LAST_SESSION_KEY, response.sessionId);

      // 真正的“页面跳转”：URL 会变成 /game/<sessionId>
      navigate(`/game/${response.sessionId}`);
    } catch (err) {
      console.error("Failed to start game:", err);
      setError("Failed to start game. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadGame = () => {
    const lastSessionId = localStorage.getItem(LAST_SESSION_KEY);

    if (!lastSessionId) {
      setError("No saved session found. Start a new game first.");
      return;
    }

    navigate(`/game/${lastSessionId}`);
  };

  // 保留原有的 loading/error UI（现在只在 HomeRoute 里）
  if (isLoading) {
    return (
      <div className="min-h-screen bg-space-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-neon-cyan mx-auto mb-4"></div>
          <p className="text-space-400">Initializing ship systems...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-space-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error}</p>
          <button
            onClick={() => setError(null)}
            className="px-4 py-2 bg-neon-cyan text-black rounded hover:bg-neon-cyan/80"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return <HomePage onStartGame={handleStartGame} onLoadGame={handleLoadGame} />;
}

function GameRoute() {
  const navigate = useNavigate();
  const { sessionId } = useParams<{ sessionId: string }>();

  const { setSession, gameState, setGameState } = useGameStore();
  const [hydrating, setHydrating] = useState(false);
  const [hydrateError, setHydrateError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    // 1) 把 sessionId 写回 store（不要在 render 里写）
    setSession(sessionId);

    // 2) 如果刷新进来 store 没状态，就从后端拉一份
    if (!gameState) {
      setHydrating(true);
      setHydrateError(null);

      gameApi
        .getGameState(sessionId)
        .then((state) => {
          setGameState(state);
        })
        .catch((err) => {
          console.error("Failed to hydrate game state:", err);
          setHydrateError("Failed to load game state. Session may be invalid.");
        })
        .finally(() => {
          setHydrating(false);
        });
    }
  }, [sessionId]);

  if (!sessionId) return <Navigate to="/" replace />;

  if (hydrating) {
    return (
      <div className="min-h-screen bg-space-900 flex items-center justify-center text-white">
        Loading game state...
      </div>
    );
  }

  if (hydrateError) {
    return (
      <div className="min-h-screen bg-space-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">{hydrateError}</p>
          <button
            onClick={() => navigate("/")}
            className="px-4 py-2 bg-neon-cyan text-black rounded hover:bg-neon-cyan/80"
          >
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  const handleBackToHome = () => {
    useGameStore.getState().reset();
    navigate("/");
  };

  return <GamePage onExit={handleBackToHome} />;
}

function EndingRoute() {
  const navigate = useNavigate();
  const { sessionId } = useParams<{ sessionId: string }>();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [endingTitle, setEndingTitle] = useState("The End");
  const [endingNarration, setEndingNarration] = useState("");
  const [statistics, setStatistics] = useState<any>(null);

  useEffect(() => {
    if (!sessionId) return;

    setLoading(true);
    setError(null);

    gameApi
      .getGameState(sessionId)
      .then((state) => {
        // TODO: replace with real fields once defined
        setEndingTitle((state as any)?.ending?.title ?? "The End");
        setEndingNarration(
          (state as any)?.ending?.narration ?? "(No ending text)",
        );
        setStatistics((state as any)?.ending?.statistics ?? null);
      })
      .catch((e) => {
        console.error(e);
        setError("Failed to load ending.");
      })
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (!sessionId) return <Navigate to="/" replace />;
  if (loading)
    return (
      <div className="min-h-screen bg-space-900 flex items-center justify-center text-white">
        Loading ending...
      </div>
    );
  if (error)
    return (
      <div className="min-h-screen bg-space-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error}</p>
          <button
            onClick={() => navigate("/")}
            className="px-4 py-2 bg-neon-cyan text-black rounded"
          >
            Back to Home
          </button>
        </div>
      </div>
    );

  return (
    <EndingPage
      endingTitle={endingTitle}
      endingNarration={endingNarration}
      statistics={statistics ?? undefined}
      onRestart={() => navigate("/")}
      onMainMenu={() => navigate("/")}
    />
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomeRoute />} />
      <Route path="/game/:sessionId" element={<GameRoute />} />
      <Route path="/ending/:sessionId" element={<EndingRoute />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
