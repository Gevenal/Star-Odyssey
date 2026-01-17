import React, { useState } from 'react';

interface Message {
  sender: 'player' | 'oracle';
  text: string;
}

interface OracleTerminalProps {
  sentienceLevel: number;
  onSendMessage?: (message: string) => void;
}

export const OracleTerminal: React.FC<OracleTerminalProps> = ({
  sentienceLevel,
  onSendMessage,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');

  // TODO: Implement ORACLE interaction
  // TODO: Add terminal styling (green text, CRT effect)
  // TODO: Add sentience level indicator

  const handleSend = () => {
    if (input.trim()) {
      setMessages([...messages, { sender: 'player', text: input }]);
      onSendMessage?.(input);
      setInput('');
    }
  };

  return (
    <div className="bg-black rounded-lg p-4 border border-green-600 font-mono">
      <div className="flex justify-between items-center mb-3 pb-2 border-b border-green-800">
        <h3 className="text-green-400 font-bold">ORACLE TERMINAL</h3>
        <span className="text-green-400 text-xs">
          Sentience: {sentienceLevel}%
        </span>
      </div>

      <div className="h-64 overflow-y-auto mb-3 space-y-2">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`text-sm ${
              msg.sender === 'player' ? 'text-green-300' : 'text-green-400'
            }`}
          >
            <span className="font-bold">
              {msg.sender === 'player' ? '> ' : '[ORACLE]: '}
            </span>
            {msg.text}
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Query ORACLE..."
          className="flex-1 bg-gray-900 text-green-400 px-3 py-1 border border-green-800 focus:outline-none focus:border-green-600"
        />
        <button
          onClick={handleSend}
          className="px-4 py-1 bg-green-900 text-green-400 border border-green-600 hover:bg-green-800"
        >
          SEND
        </button>
      </div>
    </div>
  );
};
