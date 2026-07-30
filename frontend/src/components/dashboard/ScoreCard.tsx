interface Props {
  pass1: number
  pass2: number | null
}

function getColor(score: number) {
  if (score >= 80) return { stroke: '#16a34a', text: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200', label: 'text-green-600' }
  if (score >= 60) return { stroke: '#d97706', text: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200', label: 'text-amber-600' }
  return { stroke: '#dc2626', text: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200', label: 'text-red-600' }
}

function CircleScore({ score, label, dim = false }: { score: number; label: string; dim?: boolean }) {
  const R = 38
  const CIRC = 2 * Math.PI * R
  const fill = dim ? 0 : (score / 100) * CIRC
  const c = getColor(score)

  return (
    <div className="flex flex-col items-center gap-1.5">
      <p className="text-xs font-semibold uppercase tracking-widest text-gray-400">{label}</p>
      <div className="relative">
        <svg width="100" height="100" viewBox="0 0 100 100">
          {/* Track */}
          <circle cx="50" cy="50" r={R} fill="none" stroke="#e5e7eb" strokeWidth="8" />
          {/* Progress */}
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
            ? <span className="text-2xl font-bold text-gray-300">—</span>
            : <span className={`text-2xl font-bold ${c.text}`}>{score}</span>
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
        <svg className="w-8 h-8 text-indigo-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
        </svg>
        {delta !== null && delta > 0 && (
          <span className="text-xs font-bold text-green-600 bg-green-50 border border-green-200 rounded-full px-2 py-0.5">
            +{delta}
          </span>
        )}
      </div>

      <CircleScore score={pass2 ?? 0} label="Tailored" dim={pass2 === null} />

      {/* Pending badge */}
      {pass2 === null && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-center">
          <p className="text-sm font-bold text-amber-600">Pending</p>
          <p className="text-xs text-amber-500 mt-0.5">re-run to score</p>
        </div>
      )}

      {/* Delta card */}
      {delta !== null && delta > 0 && (
        <div className={`${c2?.bg} border ${c2?.border} rounded-xl px-4 py-3 text-center`}>
          <p className={`text-2xl font-bold ${c2?.text}`}>+{delta}</p>
          <p className={`text-xs ${c2?.label} mt-0.5`}>pts improvement</p>
        </div>
      )}
    </div>
  )
}
