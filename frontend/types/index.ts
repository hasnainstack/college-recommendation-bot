export interface Filters {
  program: string;
  budget: string;
  career_goal: string;
  study_level: string;
  campus_priority: string;
  international_support: string;
}

export interface CompareRequest {
  uni1: string;
  uni2?: string;
  filters: Filters;
}

export interface UniversityData {
  name: string;
  overall_score: number;
  academic_score: number;
  student_life_score: number;
  value_score: number;
  career_score: number;
  satisfaction_score: number;
  strengths: string[];
  weaknesses: string[];
  likes: string[];
  complaints: string[];
  academic_experience: string;
  housing_cost: string;
  student_life: string;
  career_internships: string;
  things_to_know: string;
}

export interface Winners {
  overall: string;
  academics: string;
  student_life: string;
  value: string;
  career: string;
}

export interface RedditSource {
  title: string;
  url: string;
  subreddit: string;
}

export interface NoDataResponse {
  mode: "no_data";
  university: string;
  message: string;
  posts_analyzed: 0;
}

export interface CompareResponse {
  mode: "single" | "compare";
  universities: UniversityData[];
  winners?: Winners;
  comparison_summary?: string | null;
  recommendation: string;
  confidence: "low" | "medium" | "high";
  posts_analyzed: number;
  data_date: string;
  reddit_sources?: RedditSource[];
}

export interface StaticData {
  famous_unis: Record<string, string[]>;
  popular_comparisons: string[];
}

export type NavPage = "home" | "about" | "faq" | "universities";
