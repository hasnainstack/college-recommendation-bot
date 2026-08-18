import type { UniversityData } from "@/types";

export default function UniversityCard({ u, fallback }: { u: UniversityData; fallback: string }) {
  const name = u.name || fallback;
  return (
    <div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-4">
        <div>
          <h4 className="font-bold text-gray-900 text-sm mb-2">What students like</h4>
          <ul className="space-y-1 mb-4">
            {(u.likes ?? []).map((item, i) => (
              <li key={i} className="text-sm text-gray-600 flex gap-2">
                <span className="text-blue-500 shrink-0">•</span>{item}
              </li>
            ))}
          </ul>
          <h4 className="font-bold text-gray-900 text-sm mb-1">Academic experience</h4>
          <p className="text-sm text-gray-600 leading-relaxed mb-4">{u.academic_experience || "—"}</p>
          <h4 className="font-bold text-gray-900 text-sm mb-1">Career / internships</h4>
          <p className="text-sm text-gray-600 leading-relaxed">{u.career_internships || "—"}</p>
        </div>
        <div>
          <h4 className="font-bold text-gray-900 text-sm mb-2">Common complaints</h4>
          <ul className="space-y-1 mb-4">
            {(u.complaints ?? []).map((item, i) => (
              <li key={i} className="text-sm text-gray-600 flex gap-2">
                <span className="text-red-400 shrink-0">•</span>{item}
              </li>
            ))}
          </ul>
          <h4 className="font-bold text-gray-900 text-sm mb-1">Housing / cost</h4>
          <p className="text-sm text-gray-600 leading-relaxed mb-4">{u.housing_cost || "—"}</p>
          <h4 className="font-bold text-gray-900 text-sm mb-1">Student life</h4>
          <p className="text-sm text-gray-600 leading-relaxed">{u.student_life || "—"}</p>
        </div>
      </div>
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
        <strong>Things prospective students should know about {name}:</strong>
        <p className="mt-1">{u.things_to_know || "—"}</p>
      </div>
    </div>
  );
}
