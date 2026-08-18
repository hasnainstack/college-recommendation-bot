export const SCORE_CATEGORIES = [
  { label: "Overall", key: "overall_score" },
  { label: "Academics", key: "academic_score" },
  { label: "Student Life", key: "student_life_score" },
  { label: "Value / Cost", key: "value_score" },
  { label: "Career", key: "career_score" },
  { label: "Satisfaction", key: "satisfaction_score" },
] as const;

export const WINNER_LABELS: Record<string, string> = {
  overall: "🏆 Best overall",
  academics: "📚 Best for academics",
  student_life: "🎉 Best student life",
  value: "💰 Best value",
  career: "💼 Best for careers",
};

export const NAV_ITEMS = [
  { id: "home", label: "🏠 Home" },
  { id: "about", label: "ℹ️ About Us" },
  { id: "faq", label: "❓ FAQ" },
  { id: "universities", label: "🎓 Famous Universities" },
] as const;

export const STUDY_LEVELS = ["", "Undergraduate", "Graduate", "PhD"];
export const CAMPUS_PRIORITIES = ["", "Low", "Medium", "High"];
export const INTL_SUPPORT_OPTIONS = ["", "Not important", "Important", "Very important"];

export const LOADING_STEPS = [
  "🔎 Finding university information…",
  "💬 Collecting student discussions…",
  "🧠 Analysing student sentiment…",
  "✨ Almost ready…",
];
