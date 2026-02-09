import React from 'react';
import { Modal } from '@/components/common/Modal';
import { Button } from '@/components/common/Button';

interface Choice {
  id: string;
  text: string;
  description?: string;
}

interface ChoiceModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  choices: Choice[];
  onChoiceSelect: (choiceId: string) => void;
}

export const ChoiceModal: React.FC<ChoiceModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  choices,
  onChoiceSelect,
}) => {
  // TODO: Add visual styling for different choice types
  // TODO: Add keyboard shortcuts (1, 2, 3...)

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="lg">
      {description && (
        <p className="text-gray-300 mb-4">{description}</p>
      )}

      <div className="space-y-3">
        {choices.map((choice, index) => (
          <div
            key={choice.id}
            className="bg-gray-800 p-4 rounded border border-gray-700 hover:border-blue-500 cursor-pointer"
            onClick={() => {
              onChoiceSelect(choice.id);
              onClose();
            }}
          >
            <div className="flex items-start gap-3">
              <span className="text-blue-400 font-bold">{index + 1}.</span>
              <div className="flex-1">
                <p className="text-white font-semibold">{choice.text}</p>
                {choice.description && (
                  <p className="text-gray-400 text-sm mt-1">{choice.description}</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Modal>
  );
};
