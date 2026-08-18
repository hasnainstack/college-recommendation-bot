"use client";
import { useState } from "react";
import type { CompareRequest, Filters } from "@/types";

const STUDY_LEVELS    = ["", "Undergraduate", "Graduate", "PhD"];
const CAMPUS_OPTS     = ["", "Low", "Medium", "High"];
const INTL_OPTS       = ["", "Not important", "Important", "Very important"];

const EMPTY_FILTERS: Filters = {
  program: "", budget: "", career_goal: "",
  study_level: "", campus_priority: "", international_support: "",
};

interface CompareFormProps {
  mode: "single" | "compare";
  initialUni1?: string;
  initialUni2?: string;
  onSubmit: (req: CompareRequest) => void;
  loading: boolean;
  error: string | null;
  onDismissError: () => void;
}

export default function CompareForm({
  mode, initialUni1 = "", initialUni2 = "",
  onSubmit, loading, error, onDismissError,
}: CompareFormProps) {
  const [uni1, setUni1]       = useState(initialUni1);
  const [uni2, setUni2]       = useState(initialUni2);
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [prefsOpen, setPrefsOpen] = useState(false);
  const [formErr, setFormErr] = useState("");

  if (initialUni1 !== uni1 && initialUni1) setUni1(initialUni1);
  if (initialUni2 !== uni2 && initialUni2) setUni2(initialUni2);

  function setF(k: keyof Filters, v: string) {
    setFilters(p => ({ ...p, [k]: v }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormErr("");
    if (!uni1.trim()) { setFormErr("Please enter a university name."); return; }
    if (mode === "compare" && !uni2.trim()) { setFormErr("Please enter the second university name."); return; }
    onSubmit({ uni1: uni1.trim(), uni2: mode === "compare" ? uni2.trim() : undefined, filters });
  }

  const inputCls = "w-full pl-4 pr-4 py-3 rounded-xl border border-gray-200 bg-white text-gray-900 text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition";
  const selectCls = "w-full px-3 py-2.5 rounded-xl border border-gray-200 bg-white text-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition";

  return (
    <div className="bg-white rounded-2xl shadow-md p-6 sm:p-8 max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} noValidate>

        <div className="flex items-center gap-3 mb-4">
          <span className="w-7 h-7 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center shrink-0">1</span>
          <span className="font-bold text-gray-900 text-base">Enter University Name{mode === "compare" ? "s" : ""}</span>
        </div>

        <div className="relative mb-3">
          <input
            className={inputCls}
            type="text"
            placeholder="Enter university name (e.g. Harvard University)"
            value={uni1}
            onChange={e => setUni1(e.target.value)}
          />
        </div>

        {mode === "compare" && (
          <div className="relative mb-3">
            <input
              className={inputCls}
              type="text"
              placeholder="Enter second university name (e.g. Stanford University)"
              value={uni2}
              onChange={e => setUni2(e.target.value)}
            />
          </div>
        )}

        <div className="flex items-center gap-3 mt-6 mb-3">
          <span className="w-7 h-7 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center shrink-0">2</span>
          <span className="font-bold text-gray-900 text-base">Personalise Your Results</span>
          <span className="text-gray-400 text-sm">(Optional)</span>
        </div>

        <div className="border border-gray-200 rounded-xl overflow-hidden mb-6">
          <button
            type="button"
            onClick={() => setPrefsOpen(o => !o)}
            className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition text-sm font-medium text-gray-700"
          >
            <span>Choose preferences to get more relevant insights</span>
            <span className="text-gray-400 text-xs">{prefsOpen ? "▲" : "▼"}</span>
          </button>

          {prefsOpen && (
            <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4 bg-white">
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Intended program / degree</label>
                <input className={selectCls} type="text" placeholder="e.g. Computer Science"
                  value={filters.program} onChange={e => setF("program", e.target.value)} />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Study level</label>
                <select className={selectCls} value={filters.study_level} onChange={e => setF("study_level", e.target.value)}>
                  {STUDY_LEVELS.map(l => <option key={l} value={l}>{l || "Select…"}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Budget / tuition range</label>
                <input className={selectCls} type="text" placeholder="e.g. Under $20,000/yr"
                  value={filters.budget} onChange={e => setF("budget", e.target.value)} />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Campus life priority</label>
                <select className={selectCls} value={filters.campus_priority} onChange={e => setF("campus_priority", e.target.value)}>
                  {CAMPUS_OPTS.map(l => <option key={l} value={l}>{l || "Select…"}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Career goal</label>
                <input className={selectCls} type="text" placeholder="e.g. Software Engineer"
                  value={filters.career_goal} onChange={e => setF("career_goal", e.target.value)} />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">International student support</label>
                <select className={selectCls} value={filters.international_support} onChange={e => setF("international_support", e.target.value)}>
                  {INTL_OPTS.map(l => <option key={l} value={l}>{l || "Select…"}</option>)}
                </select>
              </div>
            </div>
          )}
        </div>

        {formErr && (
          <p className="text-red-600 text-sm mb-3 bg-red-50 border border-red-200 rounded-xl px-4 py-2">{formErr}</p>
        )}

        {error && (
          <div className="flex items-start justify-between gap-3 bg-red-50 border border-red-200 rounded-xl px-4 py-3 mb-4 text-sm text-red-700">
            <span>Warning: {error}</span>
            <button type="button" onClick={onDismissError} className="text-red-400 hover:text-red-600 shrink-0 font-bold">x</button>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed text-white font-bold rounded-xl py-4 flex flex-col items-center gap-0.5 transition shadow-lg shadow-blue-200"
        >
          <span className="flex items-center gap-2 text-base">
            {loading
              ? <><span className="inline-block w-4 h-4 border-2 border-white/40 border-t-white rounded-full" style={{ animation: "spin 0.7s linear infinite" }} /> Analyzing…</>
              : <>{mode === "compare" ? "Compare Universities" : "Get Insights"}</>
            }
          </span>
          {!loading && (
            <span className="text-blue-200 text-xs font-normal">Get AI-powered analysis and real student opinions</span>
          )}
        </button>
      </form>
    </div>
  );
}
