import { create } from 'zustand'
import { AnalysisResult } from '../api/analysis'

type Phase = 'idle' | 'uploading' | 'analyzing' | 'completed' | 'error'

interface AnalysisState {
  phase: Phase
  resumeId: string | null
  jdId: string | null
  runId: string | null
  result: AnalysisResult | null
  error: string | null
  progress: number
  pipelinePhase: string | null
  selectedTemplate: string

  setPhase: (phase: Phase) => void
  setResumeId: (id: string) => void
  setJdId: (id: string) => void
  setRunId: (id: string) => void
  setResult: (result: AnalysisResult) => void
  setError: (error: string) => void
  setProgress: (progress: number) => void
  setPipelinePhase: (phase: string | null) => void
  setSelectedTemplate: (templateId: string) => void
  reset: () => void
}

export const useAnalysisStore = create<AnalysisState>((set) => ({
  phase: 'idle',
  resumeId: null,
  jdId: null,
  runId: null,
  result: null,
  error: null,
  progress: 0,
  pipelinePhase: null,
  selectedTemplate: 'ats_classic',

  setPhase: (phase) => set({ phase }),
  setResumeId: (id) => set({ resumeId: id }),
  setJdId: (id) => set({ jdId: id }),
  setRunId: (id) => set({ runId: id }),
  setResult: (result) => set({ result, phase: 'completed' }),
  setError: (error) => set({ error, phase: 'error' }),
  setProgress: (progress) => set({ progress }),
  setPipelinePhase: (pipelinePhase) => set({ pipelinePhase }),
  setSelectedTemplate: (selectedTemplate) => set({ selectedTemplate }),
  reset: () =>
    set({
      phase: 'idle',
      resumeId: null,
      jdId: null,
      runId: null,
      result: null,
      error: null,
      progress: 0,
      pipelinePhase: null,
      selectedTemplate: 'ats_classic',
    }),
}))
