import api from './client'

export interface RunAnalysisRequest {
  resume_id: string
  jd_id: string
}

export interface AnalysisStatus {
  run_id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'partial'
  current_phase?: string
  progress_pct?: number
}

export interface CategoryScore {
  category: string
  score: number
  weight: number
  reasoning: string
  matched_items: string[]
  missing_items: string[]
}

export interface ScoreOutput {
  overall_score: number
  category_scores: CategoryScore[]
  matched_keywords: string[]
  missing_keywords: string[]
  skills_gap: string[]
  certification_gap: string[]
  achievement_gap: string[]
}

export interface AnalysisResult {
  run_id: string
  status: string
  pass1_score: ScoreOutput | null
  pass2_score: ScoreOutput | null
  gap_report: any
  ats_report: any
  parsed_resume: any
  tailored_resume: any
  cover_letter: any
  interview_guide: any
  total_tokens_used: number
  total_cost_usd: number
}

export async function startAnalysis(data: RunAnalysisRequest): Promise<{ run_id: string }> {
  const res = await api.post('/analysis/run', data)
  return res.data
}

export async function getAnalysisStatus(runId: string): Promise<AnalysisStatus> {
  const res = await api.get(`/analysis/${runId}/status`)
  return res.data
}

export async function getAnalysisResult(runId: string): Promise<AnalysisResult> {
  const res = await api.get(`/analysis/${runId}`)
  return res.data
}
