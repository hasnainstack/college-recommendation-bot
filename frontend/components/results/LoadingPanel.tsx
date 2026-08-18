"use client";
import { useEffect, useState } from "react";

const STEPS = [
  "Finding university information…",
  "Collecting student discussions…",
  "Analysing student sentiment…",
  "Comparing universities…",
  "Almost ready…",
];

export default function LoadingPanel({ isCompare }: { isCompare: boolean }) {
  const steps = isCompare ? STEPS : [...STEPS.slice(0, 3), "Preparing insights…", STEPS[4]];
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setIdx(i => Math.min(i + 1, steps.length - 1)), 2200);
    return () => clearInterval(id);
  }, [steps.length]);

  const pct = Math.round(((idx + 1) / steps.length) * 100);

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-10 text-center max-w-2xl mx-auto">
      <div
        className="w-10 h-10 rounded-full border-4 border-gray-200 border-t-blue-600 mx-auto mb-5"
        style={{ animation: "spin 0.8s linear infinite" }}
      />
      <p className="font-semibold text-gray-800 text-base mb-4">{steps[idx]}</p>
      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden max-w-xs mx-auto">
        <div
          className="h-full bg-blue-600 rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
