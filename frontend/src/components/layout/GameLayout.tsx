import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

interface GameLayoutProps {
  children: React.ReactNode;
  sidebar?: React.ReactNode;
}

export const GameLayout: React.FC<GameLayoutProps> = ({ children, sidebar }) => {
  // TODO: Implement responsive grid layout
  // TODO: Add collapsible sidebar
  // TODO: Add panel resizing

  return (
    <div className="h-screen flex flex-col bg-gray-950">
      <Header />

      <div className="flex-1 flex overflow-hidden">
        {/* Main content */}
        <main className="flex-1 p-4 overflow-auto">
          {children}
        </main>

        {/* Sidebar */}
        {sidebar && (
          <Sidebar>
            {sidebar}
          </Sidebar>
        )}
      </div>
    </div>
  );
};
