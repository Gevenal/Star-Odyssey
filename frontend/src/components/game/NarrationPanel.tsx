import React from 'react';
import { useGameStore } from '@/stores/gameStore';

interface NarrationPanelProps {
  className?: string;
}

export const NarrationPanel: React.FC<NarrationPanelProps> = ({ className = '' }) => {
  const { narrationHistory, streamingContent, isStreaming } = useGameStore();

  // TODO: Implement typewriter effect for streaming
  // TODO: Add scrolling behavior
  // TODO: Add message grouping by type

  return (
    <div className={`bg-gray-900 rounded-lg p-6 h-full overflow-y-auto ${className}`}>
      <div className="space-y-4">
        {narrationHistory.map((entry, index) => (
          <div
            key={index}
            className={`
              ${entry.type === 'player' ? 'text-blue-300' : ''}
              ${entry.type === 'narrator' ? 'text-gray-100' : ''}
              ${entry.type === 'oracle' ? 'text-green-300 font-mono' : ''}
              ${entry.type === 'event' ? 'text-yellow-300 italic' : ''}
            `}
          >
            {entry.type === 'player' && <span className="font-bold">&gt; </span>}
            {entry.type === 'oracle' && <span className="font-bold">[ORACLE]: </span>}
            {entry.content}
          </div>
        ))}

        {isStreaming && streamingContent && (
          <div className="text-gray-100">
            {streamingContent}
            <span className="animate-pulse">▋</span>
          </div>
        )}
      </div>
    </div>
  );
};
