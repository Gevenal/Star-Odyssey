import React from 'react';

interface TimeDisplayProps {
  day: number;
  turn: number;
  timeOfDay: string;
}

export const TimeDisplay: React.FC<TimeDisplayProps> = ({ day, turn, timeOfDay }) => {
  // TODO: Add visual clock/timeline
  // TODO: Add animations on time change

  return (
    <div className="bg-gray-900 rounded-lg p-4 text-center">
      <div className="text-gray-400 text-xs uppercase mb-1">Mission Time</div>
      <div className="text-white text-2xl font-bold">Day {day}</div>
      <div className="text-gray-400 text-sm mt-1">
        Turn {turn} • {timeOfDay}
      </div>
    </div>
  );
};
