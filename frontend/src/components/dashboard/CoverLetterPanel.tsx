import CollapsiblePanel from '../common/CollapsiblePanel'

interface Props {
  content: string
}

const ph = (text: string) => (
  <span style={{ color: '#94a3b8', fontStyle: 'italic' }}>{text}</span>
)

function formatDate() {
  return new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

export default function CoverLetterPanel({ content }: Props) {
  // Split into paragraphs, strip any lines that look like letterhead
  // (AI might or might not have included them — we always render our own)
  const bodyParagraphs = content
    .split(/\n\n+/)
    .map(p => p.trim())
    .filter(p => {
      if (!p) return false
      const lower = p.toLowerCase()
      // Skip if AI duplicated letterhead-style opening or closing we handle ourselves
      if (/^(sincerely|regards|best regards|yours truly|respectfully)/i.test(p)) return false
      if (/^dear\b/i.test(p)) return false
      if (/^subject\s*:/i.test(p)) return false
      return true
    })

  return (
    <CollapsiblePanel title="Cover Letter" defaultOpen={false}>
      <div className="flex justify-center py-4">
        {/* A4 white paper */}
        <div
          style={{
            width: '100%',
            maxWidth: '780px',
            background: '#ffffff',
            borderRadius: '4px',
            boxShadow: '0 4px 24px rgba(0,0,0,0.35), 0 1px 4px rgba(0,0,0,0.15), 0 0 0 1px rgba(0,0,0,0.08)',
            fontFamily: "'Georgia', 'Times New Roman', serif",
          }}
        >
          {/* Title bar */}
          <div style={{
            background: 'linear-gradient(135deg, #6366f1 0%, #3b82f6 100%)',
            borderRadius: '4px 4px 0 0',
            padding: '10px 32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span style={{ color: 'white', fontWeight: 600, fontSize: '12px', letterSpacing: '0.07em', textTransform: 'uppercase', fontFamily: 'Inter, sans-serif' }}>
                Cover Letter
              </span>
            </div>
            <span style={{ color: 'rgba(255,255,255,0.7)', fontSize: '11px', fontFamily: 'Inter, sans-serif' }}>AI-Generated · TailorIQ</span>
          </div>

          {/* Letter content */}
          <div style={{ padding: '48px 64px 56px' }}>

            {/* ── SENDER BLOCK ── */}
            <div style={{ marginBottom: '24px', lineHeight: 1.7, fontSize: '14px', color: '#1e293b' }}>
              <div>{ph('[Your Name]')}</div>
              <div>{ph('[Your Address]')}</div>
              <div>{ph('[City, State, ZIP Code]')}</div>
              <div>{ph('[Phone Number]')}</div>
              <div>{ph('[Email Address]')}</div>
              <div>{ph('[LinkedIn Profile]')}</div>
            </div>

            {/* ── DATE ── */}
            <div style={{ marginBottom: '20px', fontSize: '14px', color: '#334155' }}>
              {formatDate()}
            </div>

            {/* ── RECIPIENT BLOCK ── */}
            <div style={{ marginBottom: '20px', lineHeight: 1.7, fontSize: '14px', color: '#1e293b' }}>
              <div>{ph('[Hiring Manager\'s Name]')}</div>
              <div>{ph('[Job Title]')}</div>
              <div>{ph('[Company Name]')}</div>
              <div>{ph('[Company Address]')}</div>
              <div>{ph('[City, State, ZIP Code]')}</div>
            </div>

            {/* ── SUBJECT ── */}
            <div style={{ marginBottom: '20px', fontSize: '14px', fontWeight: 700, color: '#1e293b', textDecoration: 'underline' }}>
              Subject: Application for {ph('[Job Title]')}
            </div>

            {/* ── SALUTATION ── */}
            <div style={{ marginBottom: '18px', fontSize: '14px', fontWeight: 600, color: '#1e293b' }}>
              Dear {ph('[Hiring Manager\'s Name]')},
            </div>

            {/* ── BODY PARAGRAPHS (AI-generated) ── */}
            {bodyParagraphs.map((para, i) => (
              <p key={i} style={{
                fontSize: '14px',
                color: '#334155',
                lineHeight: 1.85,
                textAlign: 'justify',
                marginBottom: i < bodyParagraphs.length - 1 ? '18px' : 0,
                whiteSpace: 'pre-wrap',
              }}>
                {para}
              </p>
            ))}

            {/* ── CLOSING ── */}
            <div style={{ marginTop: '28px', fontSize: '14px', color: '#1e293b', lineHeight: 1.9 }}>
              <div>Sincerely,</div>
              <div style={{ marginTop: '40px', fontWeight: 600 }}>{ph('[Your Name]')}</div>
            </div>
          </div>

          {/* Footer */}
          <div style={{
            borderTop: '1px solid #e2e8f0',
            padding: '10px 32px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: '#f8fafc',
            borderRadius: '0 0 4px 4px',
            fontFamily: 'Inter, sans-serif',
          }}>
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
