/**
 * TypeScript types — MUST mirror docs/API_CONTRACT.md exactly.
 * Contract change = update contract + backend schemas.py + this file in ONE PR.
 * NOTE: Profile intentionally has NO gender field — anti-bias by design.
 */

export type Region = "hanoi" | "hcm" | "danang" | "other" | "all";
export type RouteType = "university" | "college" | "vocational" | "certificate";
export type Phase = "warmup" | "interests" | "abilities" | "constraints" | "wrapup";

// ---------- Profile ----------

export interface ProfileSkill {
  name: string;
  level: string;
  source_quote: string;
}

export interface Constraints {
  region_pref: string | null;
  study_budget: string | null;
  study_duration_pref: string | null;
  notes: string;
}

export interface EvidenceQuote {
  turn: number;
  quote: string;
  mapped_to: string;
}

export interface Profile {
  session_id: string;
  dimensions: Record<string, number>; // ky_thuat, phan_tich, sang_tao, xa_hoi, quan_ly (0..1)
  skills: ProfileSkill[];
  interests: string[];
  constraints: Constraints;
  evidence_quotes: EvidenceQuote[];
  completeness: number;
}

// ---------- Chat ----------

export interface ChatResponse {
  reply: string;
  phase: Phase;
  turn: number;
  done: boolean;
  profile: Profile;
}

// ---------- Recommendations ----------

export interface Why {
  from_you: { quote: string; reason: string }[];
  from_market: { stat: string; stat_key: string }[];
  counterfactual: string;
}

export interface MarketStats {
  demand_count_90d: number;
  salary_p25_trieu: number | null;
  salary_p50_trieu: number | null;
  salary_p75_trieu: number | null;
  trend_pct: number | null;
  salary_sample_count?: number;
  low_confidence?: boolean;
  top_regions: string[];
  top_skills: string[];
  source_note: string;
}

export interface Route {
  type: RouteType;
  label: string;
  detail: string;
  first_steps: string[];
}

export interface Recommendation {
  career_id: string;
  title: string;
  match_score: number;
  is_stretch: boolean;
  why: Why;
  market: MarketStats;
  routes: Route[]; // luôn ≥2, ≥1 ngoài đại học (BE đảm bảo)
  skill_roadmap: { skill: string; status: string }[];
}

export interface RecommendationResponse {
  generated_at: string;
  disclaimer: string;
  recommendations: Recommendation[];
  stretch: Recommendation;
}

// ---------- Market ----------

export interface MarketOverview {
  region: Region;
  postings_count: number;
  window_days: number;
  updated_at: string;
  source_note?: string;
  rising_careers: { career_id: string; title: string; trend_pct: number; demand_count: number; low_confidence?: boolean }[];
  top_paying: { career_id: string; title: string; salary_p50_trieu: number }[];
}

export interface SkillGapItem {
  skill: string;
  gap_score: number;
  demand_count: number;
  trend_pct: number | null;
  low_confidence?: boolean;
  related_careers: string[];
}

export interface SkillGapResponse {
  region: Region;
  skills: SkillGapItem[];
  source_note?: string;
}

export interface CareerDetail {
  career_id: string;
  title: string;
  description: string;
  market: MarketStats;
  routes: Route[];
}
