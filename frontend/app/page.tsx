"use client";
import { useState, useEffect, useRef } from "react";
import type { CompareRequest, CompareResponse, NoDataResponse, NavPage, StaticData } from "@/types";
import { compareUniversities, getStaticData } from "@/lib/api";

import Header from "@/components/layout/Header";
import Hero from "@/components/layout/Hero";
import Footer from "@/components/layout/Footer";
import FeatureStrip from "@/components/layout/FeatureStrip";
import PopularComparisons from "@/components/layout/PopularComparisons";
import CompareForm from "@/components/forms/CompareForm";
import LoadingPanel from "@/components/results/LoadingPanel";
import ResultsPanel from "@/components/results/ResultsPanel";
import AboutPage from "@/components/ui/AboutPage";
import FAQPage from "@/components/ui/FAQPage";
import UniversitiesPage from "@/components/ui/UniversitiesPage";

const DEFAULT_STATIC: StaticData = {
  famous_unis: {
    "Best for Computer Science": [
      "NUST — National University of Sciences & Technology, Islamabad",
      "LUMS — Lahore University of Management Sciences (SBASSE)",
      "FAST-NUCES — National University of Computer & Emerging Sciences",
      "GIKI — Ghulam Ishaq Khan Institute of Engineering Sciences & Technology",
      "ITU — Information Technology University, Lahore",
      "COMSATS University Islamabad",
      "PUCIT — Punjab University College of Information Technology, Lahore",
      "UET Lahore — University of Engineering & Technology",
      "Air University, Islamabad",
      "Bahria University, Islamabad",
    ],
    "Best for BBA / Business": [
      "LUMS — Suleman Dawood School of Business",
      "IBA Karachi — Institute of Business Administration",
      "NBS — NUST Business School, Islamabad",
      "IoBM — Institute of Business Management, Karachi",
      "LSE — Lahore School of Economics",
      "FAST School of Management",
      "Bahria University Business School",
      "COMSATS Business School",
      "UCP — University of Central Punjab, CBM",
      "Iqra University, Karachi",
    ],
    "Best for Arts / Humanities & Social Sciences": [
      "University of the Punjab, Lahore",
      "University of Karachi",
      "GCU — Government College University, Lahore",
      "Quaid-i-Azam University, Islamabad",
      "LUMS — Mushtaq Ahmad Gurmani School of Humanities & Social Sciences",
      "Kinnaird College for Women, Lahore",
      "Forman Christian College (A Chartered University), Lahore",
      "NCA — National College of Arts, Lahore",
      "BNU — Beaconhouse National University, Lahore",
      "Fatima Jinnah Women University, Rawalpindi",
    ],
  },
  popular_comparisons: [
    "NUST vs LUMS",
    "FAST-NUCES vs GIKI",
    "IBA Karachi vs LUMS",
    "NED vs UET",
    "SEECS vs IBA",
  ],
};

export default function Home() {
  const [navPage, setNavPage]     = useState<NavPage>("home");
  const [mode, setMode]           = useState<"single" | "compare">("single");
  const [staticData, setStaticData] = useState<StaticData>(DEFAULT_STATIC);
  const [loading, setLoading]     = useState(false);
  const [result, setResult] = useState<CompareResponse | NoDataResponse | null>(null);
  const [error, setError]         = useState<string | null>(null);
  const [lastReq, setLastReq]     = useState<CompareRequest | null>(null);

  // pre-fill state for popular comparison clicks
  const [prefillUni1, setPrefillUni1] = useState("");
  const [prefillUni2, setPrefillUni2] = useState("");

  const formRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getStaticData().then(setStaticData).catch(() => {});
  }, []);

  async function handleSubmit(req: CompareRequest) {
    setLoading(true);
    setResult(null);
    setError(null);
    setLastReq(req);
    try {
      const data = await compareUniversities(req);
      setResult(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function handlePopularSelect(u1: string, u2: string) {
    setMode("compare");
    setPrefillUni1(u1);
    setPrefillUni2(u2);
    setResult(null);
    setError(null);
    // scroll form into view
    setTimeout(() => formRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
  }

  function handleNav(page: NavPage) {
    setNavPage(page);
    setResult(null);
    setError(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <>
      <Header active={navPage} onNav={handleNav} />

      {/* push content below fixed header */}
      <div className="pt-16">

        {navPage === "home" && (
          <>
            <Hero mode={mode} onModeChange={setMode} />

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6">
              {/* Form card */}
              <div ref={formRef}>
                <CompareForm
                  mode={mode}
                  initialUni1={prefillUni1}
                  initialUni2={prefillUni2}
                  onSubmit={handleSubmit}
                  loading={loading}
                  error={error}
                  onDismissError={() => setError(null)}
                />
              </div>

              {/* Loading */}
              {loading && <LoadingPanel isCompare={mode === "compare"} />}

              {/* Results */}
              {result && !loading && lastReq && (
                <ResultsPanel
                  data={result}
                  uni1={lastReq.uni1}
                  uni2={lastReq.uni2}
                  onReset={() => { setResult(null); setError(null); formRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }); }}
                />
              )}

              {/* Feature strip */}
              <FeatureStrip />

              {/* Popular comparisons */}
              <PopularComparisons
                comparisons={staticData.popular_comparisons}
                onSelect={handlePopularSelect}
              />
            </main>
          </>
        )}

        {navPage === "about" && (
          <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
            <AboutPage />
          </main>
        )}

        {navPage === "faq" && (
          <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
            <FAQPage />
          </main>
        )}

        {navPage === "universities" && (
          <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
            <UniversitiesPage famousUnis={staticData.famous_unis} />
          </main>
        )}

        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <Footer />
        </div>
      </div>
    </>
  );
}
