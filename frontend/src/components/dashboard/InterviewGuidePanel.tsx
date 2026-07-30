import CollapsiblePanel from '../common/CollapsiblePanel'

interface Question {
  question: string
  category: string
  star_skeleton?: { situation: string; task: string; action: string; result: string }
  note?: string
}

interface Guide {
  behavioral_questions: Question[]
  technical_questions: Question[]
  preparation_tips: string[]
}

interface Props {
  guide: Guide
}

export default function InterviewGuidePanel({ guide }: Props) {
  return (
    <CollapsiblePanel title="Interview Preparation Guide" defaultOpen={false}>
      <div className="space-y-6">
        {/* Behavioral */}
        <div>
          <h4 className="font-semibold text-gray-800 mb-3">
            Behavioral Questions ({guide.behavioral_questions.length})
          </h4>
          <div className="space-y-4">
            {guide.behavioral_questions.map((q, i) => (
              <QuestionCard key={i} q={q} index={i + 1} />
            ))}
          </div>
        </div>

        {/* Technical */}
        <div>
          <h4 className="font-semibold text-gray-800 mb-3">
            Technical Questions ({guide.technical_questions.length})
          </h4>
          <div className="space-y-4">
            {guide.technical_questions.map((q, i) => (
              <QuestionCard key={i} q={q} index={i + 1} />
            ))}
          </div>
        </div>

        {/* Tips */}
        {guide.preparation_tips.length > 0 && (
          <div>
            <h4 className="font-semibold text-gray-800 mb-2">Preparation Tips</h4>
            <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
              {guide.preparation_tips.map((tip, i) => (
                <li key={i}>{tip}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </CollapsiblePanel>
  )
}

function QuestionCard({ q, index }: { q: Question; index: number }) {
  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <p className="text-sm font-medium text-gray-800">
        {index}. {q.question}
      </p>
      {q.star_skeleton && (
        <div className="mt-2 text-xs text-gray-600 space-y-1 pl-4 border-l-2 border-brand-200">
          <p><strong>S:</strong> {q.star_skeleton.situation}</p>
          <p><strong>T:</strong> {q.star_skeleton.task}</p>
          <p><strong>A:</strong> {q.star_skeleton.action}</p>
          <p><strong>R:</strong> {q.star_skeleton.result}</p>
        </div>
      )}
      {q.note && (
        <p className="mt-2 text-xs text-amber-600 italic">{q.note}</p>
      )}
    </div>
  )
}
