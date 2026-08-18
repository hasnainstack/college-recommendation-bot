"use client";
import { useState } from "react";
import type { CompareResponse, NoDataResponse } from "@/types";
import WinnersGrid from "./WinnersGrid";
import Scorecard from "./Scorecard";
import UniversityCard from "./UniversityCard";

interface ResultsPanelProps {
  data: CompareResponse | NoDataResponse;
  uni1: string;
  uni2?: string;
  onReset: () => void;
}

export default function ResultsPanel({ data, uni1, uni2, onReset }: ResultsPanelProps) {
  const [tab, setTab] = useState(0);

  if (data.mode === "no_data") {
    return (
      <div className="bg-white rounded-2xl shadow-md border border-gray-100 p-10 max-w-2xl mx-auto mt-6 flex flex-col items-center text-center gap-4">
        <h2 className="text-xl font-bold text-gray-800">No Reddit Data Found</h2>
        <p className="text-sm text-gray-500 max-w-sm">{data.message}</p>
        <p className="text-xs text-gray-400">Try a more widely discussed university, or be the first to post about it on Reddit!</p>
        <button
          onClick={onReset}
          className="mt-2 px-5 py-2 rounded-full bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 transition-colors"
        >
          Try Another University
        </button>
      </div>
    );
  }

  const compareData = data as CompareResponse;
  const unis = compareData.universities ?? [];
  const isCompare = compareData.mode === "compare" && unis.length === 2;
  const name1 = unis[0]?.name || uni1;
  const name2 = unis[1]?.name || uni2 || "University 2";

  return (
    <div className="bg-white rounded-2xl shadow-md border border-gray-100 p-6 sm:p-8 max-w-2xl mx-auto mt-6">

      <h2 className="text-2xl font-extrabold text-gray-900 mb-6">
        {isCompare ? `${name1} vs ${name2}` : `${name1} — Analysis`}
      </h2>

      {isCompare && compareData.winners && (
        <>
          <p className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-3">Overall Winners</p>
          <WinnersGrid winners={compareData.winners} />
        </>
      )}

      <p className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">Scorecard</p>
      <p className="text-xs text-gray-400 mb-4">
        AI-generated estimates based on Reddit discussions — not official rankings.
      </p>
      <Scorecard unis={unis} fallbacks={[uni1, uni2 ?? "University 2"]} />

      {compareData.comparison_summary && (
        <>
          <hr className="border-gray-100 my-6" />
          <p className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-2">AI Comparison Summary</p>
          <p className="text-sm text-gray-600 leading-relaxed">{compareData.comparison_summary}</p>
        </>
      )}

      <hr className="border-gray-100 my-6" />
      <p className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-4">What Students Say</p>

      {isCompare ? (
        <>
          <div className="flex border-b border-gray-200 mb-5">
            {[name1, name2].map((n, i) => (
              <button
                key={i}
                onClick={() => setTab(i)}
                className={`px-4 py-2.5 text-sm font-semibold border-b-2 -mb-px transition-colors
                  ${tab === i
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-400 hover:text-gray-700"
                  }`}
              >
                {n}
              </button>
            ))}
          </div>
          <UniversityCard u={unis[tab]} fallback={tab === 0 ? uni1 : (uni2 ?? "University 2")} />
        </>
      ) : unis[0] ? (
        <UniversityCard u={unis[0]} fallback={uni1} />
      ) : (
        <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
          No university data was returned. Please try again.
        </p>
      )}

      {compareData.recommendation && (
        <>
          <hr className="border-gray-100 my-6" />
          <p className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-2">AI Recommendation</p>
          <div className="bg-blue-50 border border-blue-100 rounded-xl px-4 py-3 text-sm text-blue-800 leading-relaxed">
            {compareData.recommendation}
          </div>
        </>
      )}

      <hr className="border-gray-100 my-6" />
      <p className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-3">Sources &amp; Transparency</p>
      <ul className="space-y-1 text-sm text-gray-600 mb-4">
        <li><span className="font-semibold">Platform:</span> Reddit</li>
        <li><span className="font-semibold">Discussions analysed:</span> ~{compareData.posts_analyzed}</li>
        <li><span className="font-semibold">Data collected:</span> {compareData.data_date}</li>
        <li><span className="font-semibold">AI confidence:</span> {compareData.confidence}</li>
        <li className="text-gray-400">Reddit opinions are anecdotal and may not represent all students.</li>
      </ul>

      {compareData.reddit_sources && compareData.reddit_sources.length > 0 && (
        <div className="mb-4">
          <p className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-2">Reddit Posts Referenced</p>
          <ul className="space-y-1.5">
            {compareData.reddit_sources.map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-xs">
                <span className="text-gray-400 mt-0.5 shrink-0">r/{s.subreddit}</span>
                <a href={s.url} target="_blank" rel="noopener noreferrer"
                  className="text-blue-600 hover:underline line-clamp-1">
                  {s.title}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="border-l-4 border-blue-600 bg-gray-50 rounded-r-xl px-4 py-3 text-xs text-gray-500 leading-relaxed">
        <strong className="text-gray-700">Disclaimer:</strong> AI-generated insights are intended to help with
        research and comparison. Student reviews are subjective and may not represent the overall university
        experience. Always verify tuition, admission requirements, rankings, and official policies through the
        university&apos;s official website.
      </div>
    </div>
  );
}
