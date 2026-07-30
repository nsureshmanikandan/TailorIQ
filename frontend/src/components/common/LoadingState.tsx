import { useEffect, useRef, useState } from 'react'
import { useAnalysisStore } from '../../store/analysisStore'

const PHASE_STEPS = [
  {
    key: 'phase_1',
    label: 'Parsing Resume & JD',
    agents: ['ResumeParser', 'JDParser'],
    targetPct: 10,
  },
  {
    key: 'phase_2',
    label: 'Scoring & Gap Analysis',
    agents: ['MatchScoring', 'GapAnalysis', 'ATSCheck'],
    targetPct: 30,
  },
  {
    key: 'phase_3',
    label: 'Tailoring Your Resume',
    agents: ['ResumeTailoring', 'ClaimVerification'],
    targetPct: 55,
  },
  {
    key: 'phase_4',
    label: 'Generating Cover Letter & Interview Guide',
    agents: ['CoverLetter', 'InterviewPrep'],
    targetPct: 75,
  },
  {
    key: 'phase_5',
    label: 'Packaging Documents',
    agents: ['PackageGeneration'],
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

function fmtMs(ms: number): string {
  const s = Math.floor(ms / 1000)
  if (s < 60) return `${s}s`
  return `${Math.floor(s / 60)}m ${s % 60}s`
}

export default function LoadingState() {
  const { pipelinePhase, error, phase } = useAnalysisStore()
  const [displayPct, setDisplayPct] = useState(0)
  const animRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const targetRef = useRef(0)

  // ── Timing ──────────────────────────────────────────────────────────
  const overallStart = useRef(Date.now())
  const phaseTimesRef = useRef<Record<string, { start: number; end?: number }>>({})
  const prevPhaseIdx = useRef(-1)
  const [phaseTimes, setPhaseTimes] = useState<Record<string, { start: number; end?: number }>>({})
  const [tick, setTick] = useState(0)

  // Tick every second for live timers
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 1000)
    return () => clearInterval(id)
  }, [])

  const phaseIdx = PHASE_INDEX[pipelinePhase ?? 'phase_1'] ?? 0
  const currentStep = PHASE_STEPS[Math.min(phaseIdx, PHASE_STEPS.length - 1)]
  const isDone = pipelinePhase === 'completed' || pipelinePhase === 'partial'
  const targetPct = isDone ? 100 : currentStep?.targetPct ?? 5

  // Record start/end time when phase transitions
  useEffect(() => {
    const now = Date.now()
    const prev = prevPhaseIdx.current

    if (prev >= 0 && prev < PHASE_STEPS.length) {
      const prevKey = PHASE_STEPS[prev].key
      if (phaseTimesRef.current[prevKey] && !phaseTimesRef.current[prevKey].end) {
        phaseTimesRef.current[prevKey].end = now
      }
    }

    if (phaseIdx >= 0 && phaseIdx < PHASE_STEPS.length) {
      const currKey = PHASE_STEPS[phaseIdx].key
      if (!phaseTimesRef.current[currKey]) {
        phaseTimesRef.current[currKey] = { start: now }
      }
    }

    prevPhaseIdx.current = phaseIdx
    setPhaseTimes({ ...phaseTimesRef.current })
  }, [phaseIdx])

  // Smooth progress bar animation
  useEffect(() => {
    targetRef.current = targetPct
    if (animRef.current) clearInterval(animRef.current)
    animRef.current = setInterval(() => {
      setDisplayPct((prev) => {
        const diff = targetRef.current - prev
        if (Math.abs(diff) < 0.5) return targetRef.current
        return prev + Math.max(0.3, diff * 0.06)
      })
    }, 200)
    return () => { if (animRef.current) clearInterval(animRef.current) }
  }, [targetPct])

  const overallElapsed = fmtMs(Date.now() - overallStart.current)
  // suppress tick unused warning
  void tick

  function phaseTimer(key: string, status: 'done' | 'active' | 'pending'): string | null {
    const pt = phaseTimes[key]
    if (!pt) return null
    const end = pt.end ?? Date.now()
    return fmtMs(end - pt.start)
  }

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
          <p className="text-sm text-red-300 mb-2">{error ?? 'Something went wrong. Please try again.'}</p>
          <p className="text-xs font-mono" style={{ color: '#ef4444' }}>Failed after {overallElapsed}</p>
          <p className="text-xs text-red-400 mt-2">Tip: Ensure your resume and job description contain enough text, then re-run.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="card py-10">
      <div className="max-w-lg mx-auto">

        {/* Spinner */}
        <div className="flex justify-center mb-6">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full" style={{ background: 'rgba(99,102,241,0.15)' }}>
            <svg className="animate-spin h-7 w-7" style={{ color: '#818cf8' }} fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        </div>

        {/* Title + active phase */}
        <h3 className="text-lg font-medium text-white text-center mb-1">Analyzing your resume…</h3>
        {currentStep && (
          <p className="text-sm text-center mb-5 font-medium" style={{ color: '#818cf8' }}>
            {currentStep.label}
          </p>
        )}

        {/* Progress bar */}
        <div className="mb-6">
          <div className="h-2.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.07)' }}>
            <div className="h-2.5 rounded-full transition-none"
              style={{ width: `${Math.max(displayPct, 3)}%`, background: 'linear-gradient(90deg,#6366f1,#60a5fa)' }} />
          </div>
          <p className="text-xs text-slate-500 text-center mt-1">{Math.round(displayPct)}%</p>
        </div>

        {/* Phase steps with live timers */}
        <div className="space-y-3">
          {PHASE_STEPS.map((step, index) => {
            let status: 'done' | 'active' | 'pending' = 'pending'
            if (index < phaseIdx) status = 'done'
            else if (index === phaseIdx) status = 'active'

            const timer = phaseTimer(step.key, status)

            return (
              <div key={step.key} className="flex items-start gap-3">
                {/* Status icon */}
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

                {/* Label + agents */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium leading-tight"
                    style={{ color: status === 'done' ? '#22c55e' : status === 'active' ? '#a5b4fc' : '#475569' }}>
                    {step.label}
                  </p>
                  <p className="text-xs mt-0.5" style={{ color: status === 'active' ? '#64748b' : '#334155' }}>
                    {step.agents.join(' · ')}
                  </p>
                </div>

                {/* Right column: step number + elapsed time */}
                <div className="flex flex-col items-end flex-shrink-0 mt-0.5 gap-0.5">
                  <span className="text-xs font-mono"
                    style={{ color: status === 'done' ? '#22c55e' : status === 'active' ? '#818cf8' : '#334155' }}>
                    {index + 1}/5
                  </span>
                  {timer && (
                    <span className="text-xs font-mono tabular-nums"
                      style={{ color: status === 'done' ? '#16a34a' : '#6366f1' }}>
                      ⏱ {timer}
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Overall elapsed */}
        <div className="mt-6 flex items-center justify-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: '#6366f1' }} />
          <p className="text-xs font-mono tabular-nums" style={{ color: '#475569' }}>
            Elapsed: <span style={{ color: '#818cf8' }}>{overallElapsed}</span>
          </p>
        </div>

      </div>
    </div>
  )
}
