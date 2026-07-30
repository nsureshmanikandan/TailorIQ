import CollapsiblePanel from '../common/CollapsiblePanel'

interface Props {
  content: string
}

export default function CoverLetterPanel({ content }: Props) {
  return (
    <CollapsiblePanel title="Cover Letter" defaultOpen={false}>
      <div className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">
        {content}
      </div>
    </CollapsiblePanel>
  )
}
