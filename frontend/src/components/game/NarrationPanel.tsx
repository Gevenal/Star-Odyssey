import React, { useRef, useEffect } from 'react';
import { clsx } from 'clsx';
import { BookOpen, User, Cpu, AlertCircle } from 'lucide-react';
import { useGameStore } from '@/stores/gameStore';

interface NarrationEntry {
  type: 'player' | 'narrator' | 'oracle' | 'event';
  content: string;
  timestamp: number;
}

interface NarrationPanelProps {
  className?: string;
  autoScroll?: boolean;
}

export const NarrationPanel: React.FC<NarrationPanelProps> = ({
  className,
  autoScroll = true,
}) => {
  const { narrationHistory, isStreaming, streamingContent } = useGameStore();
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [narrationHistory, streamingContent, autoScroll]);

  return (
    <div
      className={clsx(
        'h-full flex flex-col bg-space-800 rounded-lg overflow-hidden',
        className
      )}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-space-600 flex items-center gap-2">
        <BookOpen size={16} className="text-cyan-400" />
        <h3 className="text-cyan-400 font-bold text-sm uppercase tracking-wider">
          Ship's Log
        </h3>
      </div>

      {/* Content */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
      >
        {narrationHistory.length === 0 && !isStreaming && (
          <div className="text-center text-gray-500 py-8">
            <BookOpen size={32} className="mx-auto mb-2 opacity-50" />
            <p>Your story begins...</p>
          </div>
        )}

        {narrationHistory.map((entry, index) => (
          <NarrationEntry key={`${entry.timestamp}-${index}`} entry={entry} />
        ))}

        {/* Streaming Content */}
        {isStreaming && streamingContent && (
          <div className="space-y-2">
            <EntryHeader type="narrator" />
            <div className="text-gray-200 leading-relaxed pl-6">
              {streamingContent}
              <span className="inline-block w-2 h-4 bg-cyan-400 ml-1 animate-blink" />
            </div>
          </div>
        )}

        {/* Scroll anchor */}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};

// 单条叙事条目
interface NarrationEntryProps {
  entry: NarrationEntry;
}

const NarrationEntry: React.FC<NarrationEntryProps> = ({ entry }) => {
  const { type, content, timestamp } = entry;

  return (
    <div className={clsx('space-y-1', getEntryContainerStyle(type))}>
      <EntryHeader type={type} timestamp={timestamp} />
      <div className={clsx('pl-6 leading-relaxed', getEntryTextStyle(type))}>
        {content}
      </div>
    </div>
  );
};

// 条目头部（图标 + 类型标签）
interface EntryHeaderProps {
  type: NarrationEntry['type'];
  timestamp?: number;
}

const EntryHeader: React.FC<EntryHeaderProps> = ({ type, timestamp }) => {
  const config = getEntryConfig(type);

  return (
    <div className="flex items-center gap-2">
      <span className={clsx('flex-shrink-0', config.iconColor)}>
        {config.icon}
      </span>
      <span className={clsx('text-xs font-medium uppercase tracking-wider', config.labelColor)}>
        {config.label}
      </span>
      {timestamp && (
        <span className="text-xs text-gray-600 ml-auto">
          {formatTime(timestamp)}
        </span>
      )}
    </div>
  );
};

// 配置
interface EntryConfig {
  icon: React.ReactNode;
  iconColor: string;
  label: string;
  labelColor: string;
}

const getEntryConfig = (type: NarrationEntry['type']): EntryConfig => {
  switch (type) {
    case 'player':
      return {
        icon: <User size={14} />,
        iconColor: 'text-green-400',
        label: 'You',
        labelColor: 'text-green-400',
      };
    case 'narrator':
      return {
        icon: <BookOpen size={14} />,
        iconColor: 'text-cyan-400',
        label: 'Narrator',
        labelColor: 'text-cyan-400',
      };
    case 'oracle':
      return {
        icon: <Cpu size={14} />,
        iconColor: 'text-purple-400',
        label: 'ORACLE',
        labelColor: 'text-purple-400',
      };
    case 'event':
      return {
        icon: <AlertCircle size={14} />,
        iconColor: 'text-yellow-400',
        label: 'Event',
        labelColor: 'text-yellow-400',
      };
  }
};

const getEntryContainerStyle = (type: NarrationEntry['type']): string => {
  switch (type) {
    case 'player':
      return 'border-l-2 border-green-500/30 pl-3';
    case 'oracle':
      return 'bg-purple-500/5 border border-purple-500/20 rounded-lg p-3';
    case 'event':
      return 'bg-yellow-500/5 border border-yellow-500/20 rounded-lg p-3';
    default:
      return '';
  }
};

const getEntryTextStyle = (type: NarrationEntry['type']): string => {
  switch (type) {
    case 'player':
      return 'text-green-300 italic';
    case 'oracle':
      return 'text-purple-200 font-mono text-sm';
    case 'event':
      return 'text-yellow-200';
    default:
      return 'text-gray-200';
  }
};

const formatTime = (timestamp: number): string => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
};

export default NarrationPanel;