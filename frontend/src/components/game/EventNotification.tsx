import React, { useEffect, useState } from 'react';

interface EventNotificationProps {
  message: string;
  type?: 'info' | 'warning' | 'critical';
  duration?: number;
  onClose?: () => void;
}

export const EventNotification: React.FC<EventNotificationProps> = ({
  message,
  type = 'info',
  duration = 5000,
  onClose,
}) => {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        setVisible(false);
        onClose?.();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  if (!visible) return null;

  // TODO: Add slide-in animation
  // TODO: Add sound effects
  // TODO: Add icon based on type

  const typeStyles = {
    info: 'bg-blue-900 border-blue-500',
    warning: 'bg-yellow-900 border-yellow-500',
    critical: 'bg-red-900 border-red-500 animate-pulse',
  };

  return (
    <div className={`fixed top-4 right-4 ${typeStyles[type]} border-l-4 p-4 rounded shadow-lg max-w-md z-50`}>
      <div className="flex justify-between items-start">
        <div className="text-white">{message}</div>
        <button
          onClick={() => {
            setVisible(false);
            onClose?.();
          }}
          className="ml-4 text-white hover:opacity-75"
        >
          ✕
        </button>
      </div>
    </div>
  );
};
