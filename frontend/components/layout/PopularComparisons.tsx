"use client";

interface PopularComparisonsProps {
  comparisons: string[];
  onSelect: (uni1: string, uni2: string) => void;
}

export default function PopularComparisons({ comparisons, onSelect }: PopularComparisonsProps) {
  function handleClick(pair: string) {
    const parts = pair.split(" vs ");
    if (parts.length === 2) onSelect(parts[0].trim(), parts[1].trim());
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="font-bold text-gray-900 text-sm">
          Popular Pakistani University Comparisons
        </div>
        <button className="text-xs text-gray-500 bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded-full transition font-medium">
          View all
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {comparisons.map((pair) => (
          <button
            key={pair}
            onClick={() => handleClick(pair)}
            className="flex items-center gap-1 px-3 py-1.5 rounded-full border border-gray-200 bg-gray-50 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 text-gray-700 text-xs font-semibold transition"
          >
            {pair} <span className="text-gray-400">›</span>
          </button>
        ))}
      </div>
    </div>
  );
}
