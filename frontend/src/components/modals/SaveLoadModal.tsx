import React, { useState } from 'react';
import { Modal } from '@/components/common/Modal';
import { Button } from '@/components/common/Button';

interface SaveSlot {
  id: string;
  timestamp: string;
  day: number;
  turn: number;
  playerName: string;
}

interface SaveLoadModalProps {
  isOpen: boolean;
  onClose: () => void;
  mode: 'save' | 'load';
  saves: SaveSlot[];
  onSave: (slotId: string) => void;
  onLoad: (slotId: string) => void;
}

export const SaveLoadModal: React.FC<SaveLoadModalProps> = ({
  isOpen,
  onClose,
  mode,
  saves,
  onSave,
  onLoad,
}) => {
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);

  // TODO: Add save deletion
  // TODO: Add save screenshots/previews
  // TODO: Add auto-save indicator

  const handleAction = () => {
    if (selectedSlot) {
      if (mode === 'save') {
        onSave(selectedSlot);
      } else {
        onLoad(selectedSlot);
      }
      onClose();
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={mode === 'save' ? 'Save Game' : 'Load Game'}
      size="lg"
    >
      <div className="space-y-4">
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {saves.map((save) => (
            <div
              key={save.id}
              onClick={() => setSelectedSlot(save.id)}
              className={`
                p-4 rounded border cursor-pointer
                ${selectedSlot === save.id ? 'border-blue-500 bg-blue-900' : 'border-gray-700 bg-gray-800'}
              `}
            >
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="text-white font-bold">{save.playerName}</h4>
                  <p className="text-gray-400 text-sm">
                    Day {save.day}, Turn {save.turn}
                  </p>
                </div>
                <span className="text-gray-500 text-xs">
                  {new Date(save.timestamp).toLocaleString()}
                </span>
              </div>
            </div>
          ))}
        </div>

        <div className="flex gap-3 justify-end pt-4 border-t border-gray-700">
          <Button onClick={onClose} variant="secondary">
            Cancel
          </Button>
          <Button
            onClick={handleAction}
            disabled={!selectedSlot}
            variant="primary"
          >
            {mode === 'save' ? 'Save' : 'Load'}
          </Button>
        </div>
      </div>
    </Modal>
  );
};
