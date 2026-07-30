interface Props {
  matched: string[]
  added: string[]
}

export default function KeywordPanel({ matched, added }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      {matched.map((kw) => (
        <span key={`matched-${kw}`} className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium"
          style={{ background: 'rgba(34,197,94,0.12)', color: '#4ade80', border: '1px solid rgba(34,197,94,0.2)' }}>
          {kw}
        </span>
      ))}
      {added.map((kw) => (
        <span key={`added-${kw}`} className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium"
          style={{ background: 'rgba(245,158,11,0.12)', color: '#fbbf24', border: '1px solid rgba(245,158,11,0.2)' }}>
          + {kw}
        </span>
      ))}
      {matched.length === 0 && added.length === 0 && (
        <p className="text-sm text-slate-500">No keywords to display</p>
      )}
    </div>
  )
}
