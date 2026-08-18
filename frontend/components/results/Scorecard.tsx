import type { UniversityData } from "@/types";

const CATS = [
  { label: "Overall",      key: "overall_score"      },
  { label: "Academics",    key: "academic_score"      },
  { label: "Student Life", key: "student_life_score"  },
  { label: "Value / Cost", key: "value_score"         },
  { label: "Career",       key: "career_score"        },
  { label: "Satisfaction", key: "satisfaction_score"  },
] as const;

function safe(v: unknown) {
  const n = Number(v);
  return isFinite(n) ? Math.max(0, Math.min(10, n)) : 0;
}

function Bar({ score }: { score: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className="h-full bg-blue-600 rounded-full" style={{ width: `${score * 10}%` }} />
      </div>
      <span className="text-blue-600 font-bold text-sm w-10 text-right">{score.toFixed(1)}</span>
    </div>
  );
}

export default function Scorecard({ unis, fallbacks }: { unis: UniversityData[]; fallbacks: string[] }) {
  if (unis.length === 2) {
    const n1 = unis[0].name || fallbacks[0];
    const n2 = unis[1].name || fallbacks[1];
    return (
      <div className="overflow-x-auto mb-6">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-gray-50">
              <th className="text-left px-4 py-3 font-bold text-gray-700 border-b-2 border-gray-200">Category</th>
              <th className="text-left px-4 py-3 font-bold text-gray-700 border-b-2 border-gray-200">{n1}</th>
              <th className="text-left px-4 py-3 font-bold text-gray-700 border-b-2 border-gray-200">{n2}</th>
            </tr>
          </thead>
          <tbody>
            {CATS.map(({ label, key }) => {
              const s1 = safe(unis[0][key]);
              const s2 = safe(unis[1][key]);
              return (
                <tr key={key} className="border-b border-gray-50 hover:bg-gray-50/50">
                  <td className="px-4 py-3 text-gray-700 font-medium">{label}</td>
                  <td className="px-4 py-3"><span className="text-blue-600 font-bold">{s1.toFixed(1)}</span><span className="text-gray-400">/10</span></td>
                  <td className="px-4 py-3"><span className="text-blue-600 font-bold">{s2.toFixed(1)}</span><span className="text-gray-400">/10</span></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
  }

  const u = unis[0];
  return (
    <div className="space-y-3 mb-6">
      {CATS.map(({ label, key }) => (
        <div key={key}>
          <div className="flex justify-between text-sm mb-1">
            <span className="font-semibold text-gray-700">{label}</span>
          </div>
          <Bar score={safe(u[key])} />
        </div>
      ))}
    </div>
  );
}
