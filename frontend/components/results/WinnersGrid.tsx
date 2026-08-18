import type { Winners } from "@/types";

const LABELS: Record<keyof Winners, string> = {
  overall:      "Best overall",
  academics:    "Best academics",
  student_life: "Best student life",
  value:        "Best value",
  career:       "Best careers",
};

export default function WinnersGrid({ winners }: { winners: Winners }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
      {(Object.keys(LABELS) as (keyof Winners)[]).map((key) => (
        <div key={key} className="bg-white border border-gray-100 rounded-xl p-3 text-center shadow-sm">
          <p className="text-xs text-gray-400 mb-1">{LABELS[key]}</p>
          <p className="font-bold text-gray-900 text-xs leading-snug">{winners[key] ?? "—"}</p>
        </div>
      ))}
    </div>
  );
}
