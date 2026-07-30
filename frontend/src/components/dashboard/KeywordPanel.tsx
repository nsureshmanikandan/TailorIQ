interface Props {
  matched: string[]
  added: string[]
}

export default function KeywordPanel({ matched, added }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      {matched.map((kw) => (
        <span
          key={`matched-${kw}`}
          className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800"
        >
          {kw}
        </span>
      ))}
      {added.map((kw) => (
        <span
          key={`added-${kw}`}
          className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800"
        >
          + {kw}
        </span>
      ))}
      {matched.length === 0 && added.length === 0 && (
        <p className="text-sm text-gray-400">No keywords to display</p>
      )}
    </div>
  )
}
