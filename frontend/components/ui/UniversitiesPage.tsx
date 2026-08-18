interface UniversitiesPageProps {
  famousUnis: Record<string, string[]>;
}

export default function UniversitiesPage({ famousUnis }: UniversitiesPageProps) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 sm:p-8 max-w-2xl mx-auto">
      <h2 className="text-2xl font-extrabold text-gray-900 mb-1">Famous Universities in Pakistan</h2>
      <p className="text-xs text-gray-400 mb-6">
        Commonly cited reputation by field — not an official ranking. Always verify on the university&apos;s official site.
      </p>
      {Object.entries(famousUnis).map(([category, unis]) => (
        <div key={category} className="mb-7">
          <p className="font-bold text-gray-800 text-sm mb-3">{category}</p>
          <div className="space-y-2">
            {unis.map((uni, i) => (
              <div key={i} className="flex gap-2 items-start bg-gray-50 border border-gray-100 rounded-xl px-3 py-2 text-sm text-gray-700">
                <span className="text-blue-600 font-bold shrink-0">{i + 1}.</span>
                <span>{uni}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
