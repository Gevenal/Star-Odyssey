import React, { useMemo } from 'react';
import clsx from 'clsx';
import {
  AlertTriangle,
  Package,
  Users,
  Search,
  Zap,
  Coffee,
  ChevronRight,
} from 'lucide-react';
import Button from '@/components/common/Button';
import { LoadingSkeleton } from '@/components/common/LoadingSpinner';

// Import from API types (provided by Team Member A)
interface ActionDefinition {
  actionId: string;
  displayName: string;
  description: string;
  category: string;
  timeCost?: number;
  requirements?: {
    location?: string;
    items?: string[];
    npcPresent?: string;
  };
}

interface ActionMenuProps {
  actions: ActionDefinition[];
  onActionSelect: (action: ActionDefinition) => void;
  isLoading?: boolean;
  disabled?: boolean;
  className?: string;
}

// Category configuration
interface CategoryConfig {
  icon: React.ReactNode;
  color: string;
  bgColor: string;
}

const CATEGORY_CONFIG: Record<string, CategoryConfig> = {
  crisis_response: {
    icon: <AlertTriangle size={14} />,
    color: 'text-red-400',
    bgColor: 'bg-red-500/10 hover:bg-red-500/20',
  },
  resource_management: {
    icon: <Package size={14} />,
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500/10 hover:bg-yellow-500/20',
  },
  social_interaction: {
    icon: <Users size={14} />,
    color: 'text-green-400',
    bgColor: 'bg-green-500/10 hover:bg-green-500/20',
  },
  investigation: {
    icon: <Search size={14} />,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10 hover:bg-purple-500/20',
  },
  movement: {
    icon: <ChevronRight size={14} />,
    color: 'text-sky-400',
    bgColor: 'bg-sky-500/10 hover:bg-sky-500/20',
  },
  critical_decision: {
    icon: <Zap size={14} />,
    color: 'text-cyan-400',
    bgColor: 'bg-cyan-500/10 hover:bg-cyan-500/20',
  },
  rest_recovery: {
    icon: <Coffee size={14} />,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10 hover:bg-blue-500/20',
  },
  freeform: {
    icon: <ChevronRight size={14} />,
    color: 'text-gray-300',
    bgColor: 'bg-gray-500/10 hover:bg-gray-500/20',
  },
};

const DEFAULT_CONFIG: CategoryConfig = {
  icon: <ChevronRight size={14} />,
  color: 'text-gray-400',
  bgColor: 'bg-gray-500/10 hover:bg-gray-500/20',
};

export const ActionMenu: React.FC<ActionMenuProps> = ({
  actions,
  onActionSelect,
  isLoading = false,
  disabled = false,
  className,
}) => {
  // Group by category
  const groupedActions = useMemo(() => {
    const groups: Record<string, ActionDefinition[]> = {};
    
    actions.forEach((action) => {
      const category = action.category || 'other';
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push(action);
    });

    return groups;
  }, [actions]);

  // Format category name
  const formatCategoryName = (category: string): string => {
    return category
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  };

  if (isLoading) {
    return (
      <div className={clsx('space-y-4', className)}>
        {[1, 2, 3].map((i) => (
          <div key={i} className="space-y-2">
            <LoadingSkeleton width="100px" height="14px" />
            <div className="grid grid-cols-2 gap-2">
              <LoadingSkeleton height="40px" />
              <LoadingSkeleton height="40px" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (actions.length === 0) {
    return (
      <div className={clsx('text-center py-8 text-gray-500', className)}>
        <p>No actions available at this moment.</p>
        <p className="text-sm mt-1">Try exploring or talking to crew members.</p>
      </div>
    );
  }

  return (
    <div className={clsx('space-y-4', className)}>
      {Object.entries(groupedActions).map(([category, categoryActions]) => {
        const config = CATEGORY_CONFIG[category] || DEFAULT_CONFIG;

        return (
          <div key={category}>
            {/* Category Header */}
            <div className="flex items-center gap-2 mb-2">
              <span className={config.color}>{config.icon}</span>
              <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider">
                {formatCategoryName(category)}
              </h4>
              <span className="text-xs text-gray-600">
                ({categoryActions.length})
              </span>
            </div>

            {/* Actions Grid */}
            <div className="grid grid-cols-2 gap-2">
              {categoryActions.map((action) => (
                <ActionButton
                  key={action.actionId}
                  action={action}
                  config={config}
                  onClick={() => onActionSelect(action)}
                  disabled={disabled}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// Single action button
interface ActionButtonProps {
  action: ActionDefinition;
  config: CategoryConfig;
  onClick: () => void;
  disabled: boolean;
}

const ActionButton: React.FC<ActionButtonProps> = ({
  action,
  config,
  onClick,
  disabled,
}) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={action.description}
      className={clsx(
        'w-full text-left px-3 py-2 rounded-lg transition-colors',
        'border border-transparent',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        config.bgColor,
        'hover:border-space-500'
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="text-sm text-gray-200 line-clamp-2">
          {action.displayName}
        </span>
        {action.timeCost && (
          <span className="text-xs text-gray-500 flex-shrink-0">
            {action.timeCost}h
          </span>
        )}
      </div>
      
      {/* Requirements hint */}
      {action.requirements?.npcPresent && (
        <div className="text-xs text-gray-500 mt-1 flex items-center gap-1">
          <Users size={10} />
          <span>Requires: {action.requirements.npcPresent}</span>
        </div>
      )}
    </button>
  );
};

export default ActionMenu;