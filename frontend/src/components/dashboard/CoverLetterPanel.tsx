import CollapsiblePanel from '../common/CollapsiblePanel'

interface Props {
  content: string
}

export default function CoverLetterPanel({ content }: Props) {
  return (
    <CollapsiblePanel title="Cover Letter" defaultOpen={false}>
      <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap leading-relaxed">
        {content}
      </div>
    </CollapsiblePanel>
  )
}
