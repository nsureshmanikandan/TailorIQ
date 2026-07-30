interface Props {
  pass1: number
  pass2: number | null
}

export default function ScoreCard({ pass1, pass2 }: Props) {
  const delta = pass2 !== null ? pass2 - pass1 : null

  function getScoreColor(score: number) {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  function getProgressColor(score: number) {
    if (score >= 80) return 'bg-green-500'
    if (score >= 60) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  return (
    <div className="flex items-center gap-8 flex-wrap">
      {/* Before */}
      <div className="text-center">
        <p className="text-xs uppercase tracking-wide text-gray-500 mb-1">Original</p>
        <p className={`text-4xl font-bold ${getScoreColor(pass1)}`}>{pass1}</p>
        <div className="w-24 h-2 bg-gray-200 rounded-full mt-2">
          <div
            className={`h-2 rounded-full ${getProgressColor(pass1)}`}
            style={{ width: `${pass1}%` }}
          />
        </div>
      </div>

      {/* Arrow */}
      <div className="text-2xl text-gray-300">→</div>

      {/* After */}
      <div className="text-center">
        <p className="text-xs uppercase tracking-wide text-gray-500 mb-1">Tailored</p>
        {pass2 !== null ? (
          <>
            <p className={`text-4xl font-bold ${getScoreColor(pass2)}`}>{pass2}</p>
            <div className="w-24 h-2 bg-gray-200 rounded-full mt-2">
              <div
                className={`h-2 rounded-full ${getProgressColor(pass2)}`}
                style={{ width: `${pass2}%` }}
              />
            </div>
          </>
        ) : (
          <>
            <p className="text-4xl font-bold text-gray-300">—</p>
            <div className="w-24 h-2 bg-gray-200 rounded-full mt-2" />
          </>
        )}
      </div>

      {/* Delta badge */}
      {delta !== null && delta > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg px-4 py-2 text-center">
          <p className="text-2xl font-bold text-green-600">+{delta}</p>
          <p className="text-xs text-green-600">improvement</p>
        </div>
      )}

      {/* Pending badge when tailored score is not yet available */}
      {pass2 === null && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 text-center">
          <p className="text-sm font-semibold text-amber-600">Pending</p>
          <p className="text-xs text-amber-500">re-run to score</p>
        </div>
      )}
    </div>
  )
}
