import React from 'react';
import { Button } from '@/components/common/Button';

interface Action {
  id: string;
  label: string;
  category: string;
  requiresTarget?: boolean;
}

interface ActionMenuProps {
  actions: Action[];
  onActionSelect: (actionId: string) => void;
  disabled?: boolean;
}

export const ActionMenu: React.FC<ActionMenuProps> = ({
  actions,
  onActionSelect,
  disabled = false,
}) => {
  // TODO: Group actions by category
  // TODO: Add icons for action types
  // TODO: Add tooltips for action descriptions

  const categories = Array.from(new Set(actions.map((a) => a.category)));

  return (
    <div className="bg-gray-900 rounded-lg p-4">
      <h3 className="text-white font-bold mb-3">Quick Actions</h3>

      <div className="space-y-4">
        {categories.map((category) => (
          <div key={category}>
            <h4 className="text-gray-400 text-sm uppercase mb-2">{category}</h4>
            <div className="grid grid-cols-2 gap-2">
              {actions
                .filter((a) => a.category === category)
                .map((action) => (
                  <Button
                    key={action.id}
                    onClick={() => onActionSelect(action.id)}
                    disabled={disabled}
                    variant="ghost"
                    size="sm"
                  >
                    {action.label}
                  </Button>
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
