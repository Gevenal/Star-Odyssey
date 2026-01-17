import React from 'react';

interface InventoryPanelProps {
  items: string[];
  onItemClick?: (item: string) => void;
}

export const InventoryPanel: React.FC<InventoryPanelProps> = ({
  items,
  onItemClick,
}) => {
  // TODO: Add item icons/images
  // TODO: Add item details on hover
  // TODO: Group items by type

  return (
    <div className="bg-gray-900 rounded-lg p-4">
      <h3 className="text-white font-bold mb-3">Inventory</h3>

      {items.length === 0 ? (
        <p className="text-gray-500 text-sm italic">Empty</p>
      ) : (
        <div className="space-y-2">
          {items.map((item, index) => (
            <div
              key={index}
              onClick={() => onItemClick?.(item)}
              className={`
                text-gray-300 text-sm px-3 py-2 rounded
                ${onItemClick ? 'cursor-pointer hover:bg-gray-800' : ''}
              `}
            >
              {item}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
