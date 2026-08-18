"use client";

interface HeroProps {
  mode: "single" | "compare";
  onModeChange: (m: "single" | "compare") => void;
}

export default function Hero({ mode, onModeChange }: HeroProps) {
  return (
    <section className="bg-gray-100 pt-10 pb-8 px-4 text-center">
      <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight leading-tight mb-3">
        <span className="text-gray-900">University </span>
        <span className="text-blue-600">Comparison Bot</span>
      </h1>

      <p className="text-gray-500 text-base sm:text-lg max-w-xl mx-auto mb-8 leading-relaxed">
        Compare universities using real student experiences, reviews, and AI-powered insights from{" "}
        <span className="text-orange-600 font-semibold">Reddit.</span>
      </p>

      <div className="inline-flex gap-3 flex-wrap justify-center">
        <button
          onClick={() => onModeChange("single")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-full font-semibold text-sm transition-all
            ${mode === "single"
              ? "bg-blue-600 text-white shadow-lg shadow-blue-200"
              : "bg-white text-gray-600 border border-gray-300 hover:border-blue-400 hover:text-blue-600"
            }`}
        >
          Single University Analysis
        </button>
        <button
          onClick={() => onModeChange("compare")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-full font-semibold text-sm transition-all
            ${mode === "compare"
              ? "bg-blue-600 text-white shadow-lg shadow-blue-200"
              : "bg-white text-gray-600 border border-gray-300 hover:border-blue-400 hover:text-blue-600"
            }`}
        >
          Compare Two Universities
        </button>
      </div>
    </section>
  );
}
