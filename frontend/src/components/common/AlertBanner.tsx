import React from 'react';

interface AlertBannerProps {
  type: 'info' | 'warning' | 'error' | 'success';
  message: string;
  onClose?: () => void;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({
  type,
  message,
  onClose,
}) => {
  // TODO: Implement alert banner with icons and animations
  const typeClasses = {
    info: 'bg-blue-900 border-blue-600 text-blue-200',
    warning: 'bg-yellow-900 border-yellow-600 text-yellow-200',
    error: 'bg-red-900 border-red-600 text-red-200',
    success: 'bg-green-900 border-green-600 text-green-200',
  };

  return (
    <div className={`border-l-4 p-4 ${typeClasses[type]} flex justify-between items-center`}>
      <p>{message}</p>
      {onClose && (
        <button
          onClick={onClose}
          className="ml-4 text-white hover:opacity-75"
        >
          ✕
        </button>
      )}
    </div>
  );
};
