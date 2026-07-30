interface Props {
  pass1: number
  pass2: number | null
}

function getColor(score: number) {
  if (score >= 80) return { stroke: '#22c55e', text: '#22c55e', bg: 'rgba(34,197,94,0.12)', border: 'rgba(34,197,94,0.25)', delta: '#22c55e' }
  if (score >= 60) return { stroke: '#f59e0b', text: '#f59e0b', bg: 'rgba(245,158,11,0.12)', border: 'rgba(245,158,11,0.25)', delta: '#f59e0b' }
  return { stroke: '#ef4444', text: '#ef4444', bg: 'rgba(239,68,68,0.12)', border: 'rgba(239,68,68,0.25)', delta: '#ef4444' }
}

function CircleScore({ score, label, dim = false }: { score: number; label: string; dim?: boolean }) {
  const R = 38
  const CIRC = 2 * Math.PI * R
  const fill = dim ? 0 : (score / 100) * CIRC
  const c = getColor(score)

  return (
    <div className="flex flex-col items-center gap-1.5">
      <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">{label}</p>
      <div className="relative">
        <svg width="100" height="100" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r={R} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="8" />
          {!dim && (
            <circle
              cx="50" cy="50" r={R}
              fill="none"
              stroke={c.stroke}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={`${fill} ${CIRC}`}
              transform="rotate(-90 50 50)"
              style={{ transition: 'stroke-dasharray 0.6s ease' }}
            />
          )}
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          {dim
            ? <span className="text-2xl font-bold text-slate-600">—</span>
            : <span className="text-2xl font-bold" style={{ color: c.text }}>{score}</span>
          }
        </div>
      </div>
    </div>
  )
}

export default function ScoreCard({ pass1, pass2 }: Props) {
  const delta = pass2 !== null ? pass2 - pass1 : null
  const c2 = pass2 !== null ? getColor(pass2) : null

  return (
    <div className="flex items-center gap-6 flex-wrap">
      <CircleScore score={pass1} label="Original" />

      {/* Arrow */}
      <div className="flex flex-col items-center gap-1">
        <svg className="w-8 h-8" style={{ color: '#6366f1' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
        </svg>
        {delta !== null && delta > 0 && (
          <span className="text-xs font-bold rounded-full px-2 py-0.5" style={{ color: '#22c55e', background: 'rgba(34,197,94,0.12)', border: '1px solid rgba(34,197,94,0.25)' }}>
            +{delta}
          </span>
        )}
      </div>

      <CircleScore score={pass2 ?? 0} label="Tailored" dim={pass2 === null} />

      {pass2 === null && (
        <div className="rounded-xl px-4 py-3 text-center" style={{ background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)' }}>
          <p className="text-sm font-bold" style={{ color: '#f59e0b' }}>Pending</p>
          <p className="text-xs mt-0.5" style={{ color: '#d97706' }}>re-run to score</p>
        </div>
      )}

      {delta !== null && delta > 0 && (
        <div className="rounded-xl px-4 py-3 text-center" style={{ background: c2?.bg, border: `1px solid ${c2?.border}` }}>
          <p className="text-2xl font-bold" style={{ color: c2?.text }}>+{delta}</p>
          <p className="text-xs mt-0.5" style={{ color: c2?.delta }}>pts improvement</p>
        </div>
      )}
    </div>
  )
}
