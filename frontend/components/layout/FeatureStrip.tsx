const FEATURES = [
  { bg: "bg-purple-100", color: "text-purple-600", title: "Real Student Reviews",    desc: "Live opinions from Reddit communities" },
  { bg: "bg-green-100",  color: "text-green-600",  title: "Side-by-Side Comparison", desc: "Compare key aspects that matter to you" },
  { bg: "bg-yellow-100", color: "text-yellow-600", title: "AI-Powered Insights",     desc: "Smart summaries with pros, cons & takeaways" },
  { bg: "bg-pink-100",   color: "text-pink-600",   title: "100% Free to Use",        desc: "No sign-up required, always free" },
];

export default function FeatureStrip() {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
        {FEATURES.map((f) => (
          <div key={f.title} className="flex flex-col items-center text-center gap-3">
            <div className={`w-12 h-12 rounded-full ${f.bg} ${f.color} flex items-center justify-center text-xl font-bold`}>
              {f.title[0]}
            </div>
            <div>
              <p className="font-bold text-gray-900 text-sm">{f.title}</p>
              <p className="text-gray-400 text-xs mt-0.5 leading-relaxed">{f.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
