import { useEffect, useRef, useState } from 'react'
import { useAnalysisStore } from '../../store/analysisStore'

const PHASE_STEPS = [
  {
    key: 'phase_1',
    label: 'Parsing Resume & JD',
    agents: ['ResumeParser', 'JDParser'],
    hint: '~15 sec',
    targetPct: 10,
  },
  {
    key: 'phase_2',
    label: 'Scoring & Gap Analysis',
    agents: ['MatchScoring', 'GapAnalysis', 'ATSCheck'],
    hint: '~30 sec',
    targetPct: 30,
  },
  {
    key: 'phase_3',
    label: 'Tailoring Your Resume',
    agents: ['ResumeTailoring', 'ClaimVerification'],
    hint: '~60–90 sec',
    targetPct: 55,
  },
  {
    key: 'phase_4',
    label: 'Generating Cover Letter & Interview Guide',
    agents: ['CoverLetter', 'InterviewPrep'],
    hint: '~30 sec',
    targetPct: 75,
  },
  {
    key: 'phase_5',
    label: 'Packaging Documents',
    agents: ['PackageGeneration'],
    hint: '~5 sec',
    targetPct: 90,
  },
]

const PHASE_INDEX: Record<string, number> = {
  phase_1: 0,
  phase_2: 1,
  phase_3: 2,
  phase_4: 3,
  phase_5: 4,
  completed: 5,
  partial: 5,
}

export default function LoadingState() {
  const { pipelinePhase, error, phase } = useAnalysisStore()
  const [displayPct, setDisplayPct] = useState(0)
  const animRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const targetRef = useRef(0)

  // Compute the target % based on the current pipeline phase
  const phaseIdx = PHASE_INDEX[pipelinePhase ?? 'phase_1'] ?? 0
  const currentStep = PHASE_STEPS[Math.min(phaseIdx, PHASE_STEPS.length - 1)]
  const targetPct = pipelinePhase === 'completed' || pipelinePhase === 'partial'
    ? 100
    : currentStep?.targetPct ?? 5

  // Smoothly animate displayPct toward targetPct
  useEffect(() => {
    targetRef.current = targetPct
    if (animRef.current) clearInterval(animRef.current)

    animRef.current = setInterval(() => {
      setDisplayPct((prev) => {
        const diff = targetRef.current - prev
        if (Math.abs(diff) < 0.5) return targetRef.current
        // Fast jump if we're behind, slow creep if we're close
        return prev + Math.max(0.3, diff * 0.06)
      })
    }, 200)

    return () => {
      if (animRef.current) clearInterval(animRef.current)
    }
  }, [targetPct])

  const isFailed = phase === 'error' || pipelinePhase === 'failed'

  if (isFailed) {
    return (
      <div className="card py-8" style={{ borderColor: 'rgba(239,68,68,0.25)', background: 'rgba(239,68,68,0.06)' }}>
        <div className="max-w-lg mx-auto text-center">
          <div className="flex justify-center mb-4">
            <div className="w-14 h-14 rounded-full flex items-center justify-center" style={{ background: 'rgba(239,68,68,0.15)' }}>
              <svg className="w-7 h-7" style={{ color: '#ef4444' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
              </svg>
            </div>
          </div>
          <h3 className="text-lg font-semibold text-red-400 mb-2">Analysis Failed</h3>
          <p className="text-sm text-red-300 mb-4">{error ?? 'Something went wrong. Please try again.'}</p>
          <p className="text-xs text-red-400">Tip: Ensure your resume and job description contain enough text, then re-run.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="card py-10">
      <div className="max-w-lg mx-auto">
        <div className="flex justify-center mb-6">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full" style={{ background: 'rgba(99,102,241,0.15)' }}>
            <svg className="animate-spin h-7 w-7" style={{ color: '#818cf8' }} fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        </div>

        <h3 className="text-lg font-medium text-white text-center mb-1">Analysing your resume…</h3>
        {currentStep && (
          <p className="text-sm text-center mb-5 font-medium" style={{ color: '#818cf8' }}>
            {currentStep.label}
            <span className="ml-2 text-xs text-slate-500 font-normal">({currentStep.hint})</span>
          </p>
        )}

        <div className="mb-6">
          <div className="h-2.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.07)' }}>
            <div className="h-2.5 rounded-full transition-none" style={{ width: `${Math.max(displayPct, 3)}%`, background: 'linear-gradient(90deg,#6366f1,#60a5fa)' }} />
          </div>
          <p className="text-xs text-slate-500 text-center mt-1">{Math.round(displayPct)}%</p>
        </div>

        <div className="space-y-3">
          {PHASE_STEPS.map((step, index) => {
            let status: 'done' | 'active' | 'pending' = 'pending'
            if (index < phaseIdx) status = 'done'
            else if (index === phaseIdx) status = 'active'

            return (
              <div key={step.key} className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-0.5">
                  {status === 'done' && (
                    <div className="w-6 h-6 rounded-full flex items-center justify-center" style={{ background: 'rgba(34,197,94,0.15)' }}>
                      <svg className="w-3.5 h-3.5" style={{ color: '#22c55e' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  )}
                  {status === 'active' && (
                    <div className="w-6 h-6 rounded-full flex items-center justify-center" style={{ background: 'rgba(99,102,241,0.2)' }}>
                      <div className="w-3 h-3 rounded-full animate-pulse" style={{ background: '#818cf8' }} />
                    </div>
                  )}
                  {status === 'pending' && (
                    <div className="w-6 h-6 rounded-full flex items-center justify-center" style={{ background: 'rgba(255,255,255,0.05)' }}>
                      <div className="w-2 h-2 rounded-full" style={{ background: 'rgba(255,255,255,0.2)' }} />
                    </div>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium leading-tight" style={{ color: status === 'done' ? '#22c55e' : status === 'active' ? '#a5b4fc' : '#475569' }}>
                    {step.label}
                  </p>
                  <p className="text-xs mt-0.5" style={{ color: status === 'active' ? '#64748b' : '#334155' }}>
                    {step.agents.join(' · ')}
                  </p>
                </div>

                <span className="text-xs font-mono flex-shrink-0 mt-0.5" style={{ color: status === 'done' ? '#22c55e' : status === 'active' ? '#818cf8' : '#334155' }}>
                  {index + 1}/5
                </span>
              </div>
            )
          })}
        </div>

        <p className="text-center text-xs text-slate-600 mt-6">Total time: 2–4 minutes. Please keep this tab open.</p>
      </div>
    </div>
  )
}
