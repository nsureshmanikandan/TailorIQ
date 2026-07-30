import { CategoryScore } from '../../api/analysis'

interface Props {
  pass1Categories: CategoryScore[]
  pass2Categories: CategoryScore[]
}

const CATEGORY_LABELS: Record<string, string> = {
  hard_skill_overlap: 'Hard Skill Overlap',
  title_seniority_alignment: 'Title & Seniority',
  keyword_phrase_match: 'Keyword Match',
  achievement_relevance: 'Achievement Relevance',
}

export default function CategoryBreakdown({ pass1Categories, pass2Categories }: Props) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {pass1Categories.map((cat, i) => {
        const after = pass2Categories[i]
        const delta = after ? after.score - cat.score : 0
        const label = CATEGORY_LABELS[cat.category] || cat.category

        return (
          <div key={cat.category} className="bg-gray-50 rounded-lg p-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">{label}</span>
              <span className="text-xs text-gray-500">{Math.round(cat.weight * 100)}% weight</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-500 w-8">{cat.score}</span>
              <div className="flex-1 h-2 bg-gray-200 rounded-full relative">
                <div
                  className="absolute h-2 bg-gray-400 rounded-full opacity-50"
                  style={{ width: `${cat.score}%` }}
                />
                <div
                  className="absolute h-2 bg-brand-500 rounded-full"
                  style={{ width: `${after?.score ?? cat.score}%` }}
                />
              </div>
              <span className="text-sm font-medium text-brand-600 w-8">
                {after?.score ?? cat.score}
              </span>
              {delta > 0 && (
                <span className="text-xs text-green-600 font-medium">+{delta}</span>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
