import React, { useState } from 'react';
import { Button } from '@/components/common/Button';

interface ActionInputProps {
  onSubmit: (actionText: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export const ActionInput: React.FC<ActionInputProps> = ({
  onSubmit,
  disabled = false,
  placeholder = 'What do you do?',
}) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      onSubmit(input);
      setInput('');
    }
  };

  // TODO: Add command history navigation (up/down arrows)
  // TODO: Add autocomplete suggestions

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
        className="flex-1 bg-gray-800 text-white px-4 py-2 rounded border border-gray-700 focus:outline-none focus:border-blue-500"
      />
      <Button type="submit" disabled={disabled || !input.trim()}>
        Submit
      </Button>
    </form>
  );
};
