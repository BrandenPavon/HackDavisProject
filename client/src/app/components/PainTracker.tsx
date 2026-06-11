import { useState } from 'react';
import { Frown, Meh, Smile } from 'lucide-react';

interface PainTrackerProps {
  onPainLogged?: () => void;
}

export default function PainTracker({ onPainLogged }: PainTrackerProps) {
  const [painLevel, setPainLevel] = useState<number | null>(null);

  const handlePainSelect = (value: number) => {
    setPainLevel(value);
    onPainLogged?.();
  };

  const painLevels = [
    { value: 1, label: 'Minimal', icon: Smile, color: 'text-green-500' },
    { value: 2, label: 'Mild', icon: Smile, color: 'text-green-400' },
    { value: 3, label: 'Moderate', icon: Meh, color: 'text-yellow-500' },
    { value: 4, label: 'Severe', icon: Frown, color: 'text-orange-500' },
    { value: 5, label: 'Extreme', icon: Frown, color: 'text-red-500' },
  ];

  return (
    <div className="bg-white rounded-lg p-4 shadow">
      <h3 className="font-semibold mb-3">How's your pain today?</h3>
      <div className="flex justify-between gap-2">
        {painLevels.map(({ value, label, icon: Icon, color }) => (
          <button
            key={value}
            onClick={() => handlePainSelect(value)}
            className={`flex-1 flex flex-col items-center gap-2 p-3 rounded-lg border-2 transition-all ${
              painLevel === value
                ? 'border-blue-500 bg-blue-50'
                : painLevel !== null
                ? 'border-gray-200 opacity-40'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <Icon className={`w-6 h-6 ${color}`} />
            <span className="text-xs text-center">{label}</span>
            <span className="text-xs font-semibold text-gray-500">{value}</span>
          </button>
        ))}
      </div>
      {painLevel && (
        <p className="text-sm text-gray-600 mt-3 text-center">
          Pain level recorded: {painLevel}/5
        </p>
      )}
    </div>
  );
}
