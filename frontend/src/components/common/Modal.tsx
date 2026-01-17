import React from 'react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl';
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  maxWidth = 'md',
}) => {
  if (!isOpen) return null;

  // TODO: Implement proper modal with backdrop, animations
  const maxWidthClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-75"
        onClick={onClose}
      />

      {/* Modal content */}
      <div className={`relative bg-gray-800 rounded-lg shadow-xl ${maxWidthClasses[maxWidth]} w-full mx-4`}>
        {title && (
          <div className="border-b border-gray-700 px-6 py-4">
            <h2 className="text-xl font-bold text-white">{title}</h2>
          </div>
        )}

        <div className="p-6">
          {children}
        </div>
      </div>
    </div>
  );
};
