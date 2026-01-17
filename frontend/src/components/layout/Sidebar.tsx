import React from 'react';
import { useUIStore } from '@/stores/uiStore';

interface SidebarProps {
  children: React.ReactNode;
}

export const Sidebar: React.FC<SidebarProps> = ({ children }) => {
  const { sidebarCollapsed, toggleSidebar } = useUIStore();

  // TODO: Add collapse animation
  // TODO: Add resize handle

  return (
    <aside
      className={`
        bg-gray-900 border-l border-gray-800 transition-all
        ${sidebarCollapsed ? 'w-0' : 'w-80'}
        overflow-hidden
      `}
    >
      <div className="h-full overflow-y-auto p-4">
        <button
          onClick={toggleSidebar}
          className="absolute top-4 -left-3 bg-gray-800 text-white p-1 rounded"
        >
          {sidebarCollapsed ? '→' : '←'}
        </button>
        {children}
      </div>
    </aside>
  );
};
