import { useState } from 'react';
import { HomePage } from '@/pages/HomePage';
import { GamePage } from '@/pages/GamePage';
import { useGameStore } from '@/stores/gameStore';
import { gameApi } from '@/api/gameApi';

type Screen = 'home' | 'game' | 'ending';

function App() {
  const [screen, setScreen] = useState<Screen>('home');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { setSession, setGameState, addNarration, setAvailableActions } = useGameStore();

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
      addNarration('narrator', response.initialNarration);
      if (response.oracleMessage) {
        addNarration('oracle', response.oracleMessage);
      }
      
      setScreen('game');
    } catch (err) {
      console.error('Failed to start game:', err);
      setError('Failed to start game. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadGame = () => {
    // TODO: Open save/load modal
    alert('Load game feature coming soon!');
  };

  const handleBackToHome = () => {
    useGameStore.getState().reset();
    setScreen('home');
  };

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

  return (
    <>
      {screen === 'home' && (
        <HomePage onStartGame={handleStartGame} onLoadGame={handleLoadGame} />
      )}
      {screen === 'game' && (
        <GamePage onExit={handleBackToHome} />
      )}
    </>
  );
}

export default App
