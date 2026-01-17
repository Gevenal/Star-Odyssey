import React from 'react';
import { useGameStore } from '@/stores/gameStore';

export const Header: React.FC = () => {
  const { gameState } = useGameStore();

  // TODO: Add menu button
  // TODO: Add settings button
  // TODO: Add save/load buttons

  return (
    <header className="bg-gray-900 border-b border-gray-800 px-6 py-3">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold text-white">Star Odyssey</h1>
          {gameState && (
            <div className="text-gray-400 text-sm">
              Day {gameState.world.day} • Turn {gameState.world.turn}
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          {/* TODO: Add header controls */}
          <button className="text-gray-400 hover:text-white">
            Settings
          </button>
        </div>
      </div>
    </header>
  );
};
