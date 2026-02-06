import React from 'react';
import { clsx } from 'clsx';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  color?: 'cyan' | 'white' | 'gray';
  className?: string;
  label?: string;
}

const sizeStyles = {
  sm: 'w-4 h-4 border-2',
  md: 'w-6 h-6 border-2',
  lg: 'w-10 h-10 border-3',
  xl: 'w-16 h-16 border-4',
};

const colorStyles = {
  cyan: 'border-cyan-500 border-t-transparent',
  white: 'border-white border-t-transparent',
  gray: 'border-gray-400 border-t-transparent',
};

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  color = 'cyan',
  className,
  label,
}) => {
  return (
    <div className={clsx('flex flex-col items-center justify-center gap-3', className)}>
      <div
        className={clsx(
          'rounded-full animate-spin',
          sizeStyles[size],
          colorStyles[color]
        )}
        role="status"
        aria-label={label || 'Loading'}
      />
      {label && (
        <span className="text-sm text-gray-400 animate-pulse">{label}</span>
      )}
    </div>
  );
};

// Full-screen loading overlay
export const LoadingOverlay: React.FC<{ message?: string }> = ({ message }) => (
  <div className="fixed inset-0 bg-space-900/80 flex items-center justify-center z-50">
    <div className="text-center">
      <LoadingSpinner size="xl" />
      {message && (
        <p className="mt-4 text-gray-300 text-lg">{message}</p>
      )}
    </div>
  </div>
);

// Skeleton screen loading
export const LoadingSkeleton: React.FC<{
  width?: string;
  height?: string;
  className?: string;
}> = ({ width = '100%', height = '1rem', className }) => (
  <div
    className={clsx('bg-space-700 rounded animate-pulse', className)}
    style={{ width, height }}
  />
);

export default LoadingSpinner;