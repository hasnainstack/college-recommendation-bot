"use client";
import { useState } from "react";

const FAQS = [
  { q: "Where does the data come from?",        a: "Live discussions and reviews pulled from Reddit, analysed with Gemini AI." },
  { q: "Are the scores official rankings?",     a: "No — scores are AI-generated estimates based on Reddit sentiment, not official rankings." },
  { q: "Is it free to use?",                    a: "Yes, 100% free and no sign-up is required." },
  { q: "Can I compare more than two universities?", a: "Not yet — comparing more than two universities at once is coming soon." },
  { q: "How accurate are the results?",         a: "Accuracy depends on how much relevant Reddit discussion exists for a university, so results for less-discussed schools may be less reliable." },
];

export default function FAQPage() {
  const [open, setOpen] = useState<number | null>(null);
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 sm:p-8 max-w-2xl mx-auto">
      <h2 className="text-2xl font-extrabold text-gray-900 mb-5">Frequently Asked Questions</h2>
      <div className="space-y-3">
        {FAQS.map((faq, i) => (
          <div key={i} className="border border-gray-200 rounded-xl overflow-hidden">
            <button
              onClick={() => setOpen(open === i ? null : i)}
              className="w-full flex items-center justify-between px-4 py-3.5 bg-white hover:bg-gray-50 text-left text-sm font-semibold text-gray-800 transition"
            >
              <span>{faq.q}</span>
              <span className="text-gray-400 text-xs ml-4 shrink-0">{open === i ? "▲" : "▼"}</span>
            </button>
            {open === i && (
              <div className="px-4 py-3 bg-gray-50 border-t border-gray-100 text-sm text-gray-600 leading-relaxed">
                {faq.a}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
