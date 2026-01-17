import React, { useState } from 'react';
import { Button } from '@/components/common/Button';

interface HomePageProps {
  onStartGame: (playerName: string) => void;
  onLoadGame: () => void;
}

export const HomePage: React.FC<HomePageProps> = ({ onStartGame, onLoadGame }) => {
  const [playerName, setPlayerName] = useState('');

  // TODO: Add title screen animation
  // TODO: Add background music
  // TODO: Add credits/about section

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black flex items-center justify-center">
      <div className="max-w-md w-full p-8">
        <h1 className="text-6xl font-bold text-white text-center mb-8">
          Star Odyssey
        </h1>

        <div className="space-y-6">
          <div>
            <label className="block text-gray-400 mb-2">Your Name</label>
            <input
              type="text"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              placeholder="Enter your name..."
              className="w-full bg-gray-800 text-white px-4 py-3 rounded border border-gray-700 focus:outline-none focus:border-blue-500"
            />
          </div>

          <Button
            onClick={() => onStartGame(playerName)}
            disabled={!playerName.trim()}
            fullWidth
            size="lg"
          >
            Start New Game
          </Button>

          <Button
            onClick={onLoadGame}
            variant="secondary"
            fullWidth
            size="lg"
          >
            Load Game
          </Button>
        </div>
      </div>
    </div>
  );
};
