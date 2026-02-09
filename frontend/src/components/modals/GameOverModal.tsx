import React from 'react';
import { Modal } from '@/components/common/Modal';
import { Button } from '@/components/common/Button';

interface GameOverModalProps {
  isOpen: boolean;
  endingTitle: string;
  endingNarration: string;
  onRestart: () => void;
  onMainMenu: () => void;
}

export const GameOverModal: React.FC<GameOverModalProps> = ({
  isOpen,
  endingTitle,
  endingNarration,
  onRestart,
  onMainMenu,
}) => {
  // TODO: Add statistics display (turns survived, crew alive, etc.)
  // TODO: Add achievements/unlocks
  // TODO: Add ending artwork/image

  return (
    <Modal isOpen={isOpen} onClose={() => {}} title={endingTitle} size="xl">
      <div className="space-y-6">
        <div className="text-gray-300 leading-relaxed whitespace-pre-wrap">
          {endingNarration}
        </div>

        <div className="flex gap-3 justify-center pt-4">
          <Button onClick={onRestart} variant="primary">
            Play Again
          </Button>
          <Button onClick={onMainMenu} variant="secondary">
            Main Menu
          </Button>
        </div>
      </div>
    </Modal>
  );
};
