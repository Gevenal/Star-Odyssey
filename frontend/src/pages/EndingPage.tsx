import React from 'react';
import { Button } from '@/components/common/Button';

interface EndingPageProps {
  endingTitle: string;
  endingNarration: string;
  statistics?: {
    daysServived: number;
    crewSurvived: number;
    secretsDiscovered: number;
  };
  onRestart: () => void;
  onMainMenu: () => void;
}

export const EndingPage: React.FC<EndingPageProps> = ({
  endingTitle,
  endingNarration,
  statistics,
  onRestart,
  onMainMenu,
}) => {
  // TODO: Add ending artwork
  // TODO: Add scrolling credits
  // TODO: Add achievement display

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black flex items-center justify-center p-8">
      <div className="max-w-3xl w-full">
        <h1 className="text-5xl font-bold text-white text-center mb-8">
          {endingTitle}
        </h1>

        <div className="bg-gray-900 rounded-lg p-8 mb-8">
          <div className="text-gray-300 leading-relaxed whitespace-pre-wrap mb-6">
            {endingNarration}
          </div>

          {statistics && (
            <div className="border-t border-gray-700 pt-6 mt-6">
              <h3 className="text-white font-bold mb-4">Mission Summary</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-400">
                    {statistics.daysServived}
                  </div>
                  <div className="text-gray-400 text-sm">Days Survived</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-400">
                    {statistics.crewSurvived}
                  </div>
                  <div className="text-gray-400 text-sm">Crew Survived</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-400">
                    {statistics.secretsDiscovered}
                  </div>
                  <div className="text-gray-400 text-sm">Secrets Discovered</div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="flex gap-4 justify-center">
          <Button onClick={onRestart} variant="primary" size="lg">
            Play Again
          </Button>
          <Button onClick={onMainMenu} variant="secondary" size="lg">
            Main Menu
          </Button>
        </div>
      </div>
    </div>
  );
};
