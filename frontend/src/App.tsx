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
import { useGameStore, getNarrationFromStorage } from "@/stores/gameStore";
import { gameApi } from "@/api/gameApi";
import { EndingPage } from "./pages/EndingPage";

const LAST_SESSION_KEY = "star_odyssey:last_session_id";

type NarrationEntry = {
  type: "player" | "narrator" | "oracle" | "event";
  content: string;
  timestamp: number;
};

function buildNarrationFromHistory(
  history: Record<string, unknown>[] | undefined
): NarrationEntry[] {
  if (!history?.length) {
    return [
      {
        type: "event",
        content: "Session restored. Your journey continues.",
        timestamp: Date.now(),
      },
    ];
  }
  const baseTime = Date.now() - history.length * 60000;
  return history.map((entry, i) => {
    const content =
      (entry.narration as string) ||
      (entry.narration_text as string) ||
      (entry.event as string) ||
      (entry.action_text as string) ||
      (typeof entry.action === "string" ? entry.action : null) ||
      "Something happened.";
    return {
      type: (entry.type as NarrationEntry["type"]) || "narrator",
      content: String(content),
      timestamp: baseTime + i * 60000,
    };
  });
}

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

      localStorage.setItem(LAST_SESSION_KEY, response.sessionId);

      // Actual page navigation: URL will become /game/<sessionId>
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

  // Keep original loading/error UI (now only in HomeRoute)
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

  const { setSession, gameState, setGameState, setNarrationHistory, reset } =
    useGameStore();
  const [hydrating, setHydrating] = useState(false);
  const [hydrateError, setHydrateError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    // 1) Write sessionId back to store (don't write in render)
    setSession(sessionId);

    // 2) If store has no state on refresh, fetch from backend
    if (!gameState) {
      setHydrating(true);
      setHydrateError(null);

      gameApi
        .getGameState(sessionId)
        .then((state) => {
          setGameState(state);
          // Restore narration from localStorage (persisted on each addNarration)
          const stored = getNarrationFromStorage(sessionId);
          const entries =
            stored.length > 0
              ? stored
              : buildNarrationFromHistory(state.history);
          setNarrationHistory(entries);
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
    reset();
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
      .getEnding(sessionId)
      .then((ending) => {
        setEndingTitle(ending.title || "The End");
        setEndingNarration(ending.narration || "(No ending text)");
        setStatistics({
          daysServived: ending.statistics.daysSurvived,
          crewSurvived: ending.statistics.crewSurvived,
          secretsDiscovered: ending.statistics.secretsDiscovered,
        });
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
