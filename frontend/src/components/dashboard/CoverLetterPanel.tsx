import CollapsiblePanel from '../common/CollapsiblePanel'

interface Props {
  content: string
}

function classifyLine(line: string): 'subject' | 'dear' | 'closing' | 'signature' | 'header' | 'blank' | 'body' {
  const t = line.trim()
  if (!t) return 'blank'
  if (/^subject\s*:/i.test(t)) return 'subject'
  if (/^(re\s*:|ref\s*:)/i.test(t)) return 'subject'
  if (/^dear\b/i.test(t)) return 'dear'
  if (/^(sincerely|regards|best regards|yours truly|respectfully|warm regards|kind regards)\b/i.test(t)) return 'closing'
  // lines after closing that look like a signature (short lines, no punctuation sentence)
  return 'body'
}

export default function CoverLetterPanel({ content }: Props) {
  // Split into paragraph blocks
  const rawParagraphs = content.split(/\n\n+/).map(p => p.trim()).filter(Boolean)

  // If no paragraphs, fall back to line-split
  const paragraphs = rawParagraphs.length ? rawParagraphs : content.split('\n').filter(l => l.trim())

  let pastClosing = false

  return (
    <CollapsiblePanel title="Cover Letter" defaultOpen={false}>
      <div className="flex justify-center py-4">
        {/* A4-like white paper */}
        <div
          className="w-full"
          style={{
            maxWidth: '780px',
            background: '#ffffff',
            borderRadius: '4px',
            boxShadow: '0 4px 6px -1px rgba(0,0,0,0.3), 0 2px 4px -1px rgba(0,0,0,0.2), 0 0 0 1px rgba(0,0,0,0.08)',
          }}
        >
          {/* Document top bar — like Word's title bar */}
          <div
            style={{
              background: 'linear-gradient(135deg, #6366f1 0%, #3b82f6 100%)',
              borderRadius: '4px 4px 0 0',
              padding: '10px 32px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span style={{ color: 'white', fontWeight: 600, fontSize: '13px', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                Cover Letter
              </span>
            </div>
            <span style={{ color: 'rgba(255,255,255,0.75)', fontSize: '11px' }}>AI-Generated · TailorIQ</span>
          </div>

          {/* Paper body — letter margins */}
          <div style={{ padding: '48px 64px 56px', fontFamily: "'Georgia', 'Times New Roman', serif" }}>

            {paragraphs.map((para, i) => {
              const firstLine = para.split('\n')[0]
              const kind = classifyLine(firstLine)

              if (kind === 'subject') {
                return (
                  <div key={i} style={{ marginBottom: '20px' }}>
                    <p style={{ fontSize: '14px', fontWeight: 700, color: '#1e293b', textDecoration: 'underline', lineHeight: 1.6 }}>
                      {para}
                    </p>
                  </div>
                )
              }

              if (kind === 'dear') {
                return (
                  <div key={i} style={{ marginBottom: '20px' }}>
                    <p style={{ fontSize: '14px', fontWeight: 600, color: '#1e293b', lineHeight: 1.6 }}>{para}</p>
                  </div>
                )
              }

              if (kind === 'closing') {
                pastClosing = true
                return (
                  <div key={i} style={{ marginTop: '28px', marginBottom: '4px' }}>
                    <p style={{ fontSize: '14px', color: '#1e293b', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{para}</p>
                  </div>
                )
              }

              if (pastClosing) {
                // Signature block
                return (
                  <div key={i} style={{ marginTop: '4px' }}>
                    <p style={{ fontSize: '14px', fontWeight: 600, color: '#1e293b', lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>{para}</p>
                  </div>
                )
              }

              // Body paragraph
              return (
                <div key={i} style={{ marginBottom: '18px' }}>
                  <p style={{ fontSize: '14px', color: '#334155', lineHeight: 1.85, textAlign: 'justify', whiteSpace: 'pre-wrap' }}>
                    {para}
                  </p>
                </div>
              )
            })}
          </div>

          {/* Document footer */}
          <div
            style={{
              borderTop: '1px solid #e2e8f0',
              padding: '10px 32px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              background: '#f8fafc',
              borderRadius: '0 0 4px 4px',
            }}
          >
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>Generated by TailorIQ · AI Resume Optimizer</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#6366f1' }} />
              <span style={{ fontSize: '11px', color: '#6366f1', fontWeight: 600 }}>AI-Tailored</span>
            </div>
          </div>
        </div>
      </div>
    </CollapsiblePanel>
  )
}
