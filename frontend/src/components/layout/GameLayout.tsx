import React from 'react';
import clsx from 'clsx';
import { Header } from './Header';

interface GameLayoutProps {
  children: React.ReactNode;
  sidebar?: React.ReactNode;
  rightPanel?: React.ReactNode;
  showHeader?: boolean;
  className?: string;
}

export const GameLayout: React.FC<GameLayoutProps> = ({
  children,
  sidebar,
  rightPanel,
  showHeader = true,
  className,
}) => {
  return (
    <div className={clsx('min-h-screen flex flex-col bg-space-900', className)}>
      {/* Header */}
      {showHeader && <Header />}

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        {sidebar && (
          <aside className="w-72 bg-space-800 border-r border-space-600 overflow-y-auto flex-shrink-0">
            <div className="p-4">
              {sidebar}
            </div>
          </aside>
        )}

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="h-full p-4">
            {children}
          </div>
        </main>

        {/* Right Panel (optional) */}
        {rightPanel && (
          <aside className="w-80 bg-space-800 border-l border-space-600 overflow-y-auto flex-shrink-0">
            <div className="p-4">
              {rightPanel}
            </div>
          </aside>
        )}
      </div>
    </div>
  );
};

export default GameLayout;