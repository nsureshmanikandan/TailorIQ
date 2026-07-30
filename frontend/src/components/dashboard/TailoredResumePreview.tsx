import { useState } from 'react'
import '../../styles/cv-templates.css'

interface Section {
  section_name: string
  content: string
  changes_made: string[]
  keywords_added: string[]
}

interface ParsedContact {
  email?: string
  phone?: string
  location?: string
  linkedin_url?: string
}

interface ParsedResume {
  candidate_name?: string
  current_title?: string
  contact_info?: ParsedContact
}

interface Props {
  resume: { sections: Section[]; full_text?: string; keywords_added: string[] }
  parsedResume?: ParsedResume | null
  selectedTemplate: string
}

// Section headers that belong in the sidebar for two-column templates
const SIDEBAR_SECTIONS = new Set([
  'SKILLS', 'CORE SKILLS', 'TECHNICAL SKILLS', 'KEY SKILLS',
  'CORE COMPETENCIES', 'CERTIFICATIONS', 'LANGUAGES', 'INTERESTS',
])

// Section names already rendered in the header block — always skip from body
const HEADER_SECTIONS = new Set([
  'HEADER', 'CONTACT', 'CONTACT INFORMATION', 'CONTACT DETAILS',
])

// Known section headings for full_text detection
const KNOWN_HEADINGS = new Set([
  'PROFESSIONAL SUMMARY', 'EXECUTIVE SUMMARY', 'SUMMARY', 'OBJECTIVE', 'PROFILE',
  'CAREER OBJECTIVE', 'PROFESSIONAL PROFILE',
  'CORE SKILLS', 'TECHNICAL SKILLS', 'KEY SKILLS', 'SKILLS', 'CORE SKILLS & TECHNOLOGIES',
  'CORE COMPETENCIES', 'SKILLS & EXPERTISE', 'AREAS OF EXPERTISE',
  'WORK EXPERIENCE', 'PROFESSIONAL EXPERIENCE', 'EXPERIENCE', 'EMPLOYMENT HISTORY',
  'EDUCATION', 'ACADEMIC BACKGROUND', 'ACADEMIC QUALIFICATIONS',
  'CERTIFICATIONS', 'PROFESSIONAL CERTIFICATIONS', 'LICENSES & CERTIFICATIONS',
  'KEY ACHIEVEMENTS', 'ACHIEVEMENTS', 'ACCOMPLISHMENTS', 'AWARDS',
  'PROJECTS', 'KEY PROJECTS', 'NOTABLE PROJECTS', 'SELECTED PROJECTS',
  'LEADERSHIP', 'LEADERSHIP & MANAGEMENT',
  'PUBLICATIONS', 'SPEAKING ENGAGEMENTS', 'PROFESSIONAL AFFILIATIONS',
  'VOLUNTEER', 'VOLUNTEER EXPERIENCE', 'LANGUAGES', 'INTERESTS', 'REFERENCES',
])

const TWO_COLUMN_TEMPLATES = new Set(['executive_dark', 'two_column_split'])

// ── Full-text line-by-line renderer ──────────────────────────────────────────
// Used when sections are missing names or poorly structured.
// Detects ALL-CAPS headings and renders them with proper .cv-section-heading style.
function FullTextRenderer({
  fullText,
  candidateName,
}: {
  fullText: string
  candidateName: string
}) {
  const candidateUpper = candidateName.toUpperCase().replace(/\s+/g, '')
  // Also match partial name forms (first+last without middle, etc.)
  const candidateWords = new Set(candidateName.toUpperCase().split(/\s+/).filter(Boolean))

  interface Segment { heading: string; body: string[] }
  const segments: Segment[] = []
  let current: Segment = { heading: '', body: [] }
  let skip = false  // inside HEADER / CONTACT section — skip until next real heading

  for (const raw of fullText.split('\n')) {
    const t = raw.trim()
    if (!t) continue
    // Skip candidate name line (already shown in HeaderBlock)
    // Match: exact name, name with different spacing, or a short line made entirely of name words
    const tUpper = t.toUpperCase()
    const tCompact = tUpper.replace(/\s+/g, '')
    const isNameLine =
      tCompact === candidateUpper ||
      (t.length <= 60 && tUpper.split(/\s+/).every((w) => candidateWords.has(w)))
    if (isNameLine) continue
    // Skip contact/header lines that duplicate the HeaderBlock (email, phone, linkedin, location separators)
    if (!skip) {
      const isContactLine =
        tUpper.includes('@') ||
        /\+\d{1,3}[-\s]?\d/.test(t) ||
        tUpper.includes('LINKEDIN') ||
        (t.includes('|') && t.split('|').length >= 3 && t.length < 200)
      if (isContactLine && (current.heading === '' || HEADER_SECTIONS.has(current.heading.toUpperCase()))) {
        continue
      }
    }

    // Detect section headings: known list OR all-uppercase line (3–70 chars)
    const isHeading =
      KNOWN_HEADINGS.has(tUpper) ||
      (t === t.toUpperCase() && t.length > 2 && t.length <= 70 && /[A-Z]/.test(t))

    if (isHeading) {
      if (HEADER_SECTIONS.has(tUpper)) {
        skip = true
        continue
      }
      skip = false
      // Save current segment before starting a new one
      if (current.body.length > 0 || current.heading) {
        segments.push(current)
      }
      current = { heading: t, body: [] }
    } else if (!skip) {
      current.body.push(t)
    }
  }
  // Push last segment
  if (current.body.length > 0 || current.heading) {
    segments.push(current)
  }

  return (
    <>
      {segments.map((seg, i) => (
        <div key={i} className="cv-section">
          {seg.heading && (
            <div className="cv-section-heading">{seg.heading.toUpperCase()}</div>
          )}
          {seg.body.length > 0 && (
            <div className="cv-section-body">{seg.body.join('\n')}</div>
          )}
        </div>
      ))}
    </>
  )
}

export default function TailoredResumePreview({ resume, parsedResume, selectedTemplate }: Props) {
  const [showChanges, setShowChanges] = useState(false)

  const candidateName = parsedResume?.candidate_name ?? 'Candidate'
  const designation = parsedResume?.current_title ?? ''
  const contact = parsedResume?.contact_info
  const contactLine = [
    contact?.location,
    contact?.email,
    contact?.phone,
    contact?.linkedin_url,
  ].filter(Boolean).join('  ·  ')

  const isTwoCol = TWO_COLUMN_TEMPLATES.has(selectedTemplate)

  // Safe section name getter (handles null/undefined from LLM)
  const secName = (s: Section) => (s.section_name || '').toUpperCase().trim()

  // Split sections for two-column layout
  const sidebarSections = isTwoCol
    ? resume.sections.filter((s) => SIDEBAR_SECTIONS.has(secName(s)))
    : []
  const mainSections = isTwoCol
    ? resume.sections.filter((s) => !SIDEBAR_SECTIONS.has(secName(s)))
    : resume.sections.filter((s) => !HEADER_SECTIONS.has(secName(s)))

  // Decide whether sections are well-structured enough to render directly.
  // "Well-structured" = at least 2 non-header sections with actual names.
  const namedSections = mainSections.filter((s) => secName(s).length > 0)
  const sectionsWellStructured = namedSections.length >= 2

  const totalKeywords = resume.keywords_added?.length ?? 0
  const totalChanges = resume.sections.reduce((n, s) => n + (s.changes_made?.length ?? 0), 0)

  return (
    <div>
      {/* ── Styled CV Preview ── */}
      <div className={`cv-preview tmpl-${selectedTemplate} border border-gray-200 shadow-sm`}>
        {isTwoCol ? (
          // Two-column layout — always uses sections
          <>
            <div className="cv-sidebar">
              <div className="cv-name">{candidateName}</div>
              {designation && <div className="cv-designation">{designation}</div>}
              {sidebarSections.map((sec, i) => (
                <div key={`${secName(sec)}-${i}`} className="cv-section">
                  <div className="cv-section-heading">{secName(sec)}</div>
                  <div className="cv-section-body">{sec.content}</div>
                </div>
              ))}
            </div>
            <div className="cv-main-col">
              {mainSections.map((sec, i) => (
                <CVSection key={`${secName(sec)}-${i}`} section={sec} />
              ))}
            </div>
          </>
        ) : (
          // Single-column layout
          <>
            <HeaderBlock
              template={selectedTemplate}
              name={candidateName}
              designation={designation}
              contact={contactLine}
            />
            <div className="cv-preview-body">
              {sectionsWellStructured
                ? namedSections.map((sec, i) => (
                    <CVSection key={`${secName(sec)}-${i}`} section={sec} />
                  ))
                : resume.full_text
                  ? <FullTextRenderer fullText={resume.full_text} candidateName={candidateName} />
                  : mainSections.map((sec, i) => (
                      <CVSection key={`${secName(sec)}-${i}`} section={sec} />
                    ))
              }
            </div>
          </>
        )}
      </div>

      {/* ── Changes summary toggle ── */}
      {(totalChanges > 0 || totalKeywords > 0) && (
        <div className="mt-4">
          <button
            onClick={() => setShowChanges(!showChanges)}
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
          >
            <svg
              className={`w-4 h-4 transition-transform ${showChanges ? 'rotate-90' : ''}`}
              fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
            {totalChanges} tailoring change{totalChanges !== 1 ? 's' : ''}
            {totalKeywords > 0 && ` · ${totalKeywords} keyword${totalKeywords !== 1 ? 's' : ''} added`}
          </button>

          {showChanges && (
            <div className="mt-3 space-y-3 border-l-2 border-indigo-100 pl-4">
              {resume.sections.map((sec, i) => {
                const hasChanges = sec.changes_made?.length > 0
                const hasKw = sec.keywords_added?.length > 0
                if (!hasChanges && !hasKw) return null
                return (
                  <div key={`change-${i}-${sec.section_name ?? ''}`}>
                    <p className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-1">
                      {sec.section_name}
                    </p>
                    {hasKw && (
                      <div className="flex flex-wrap gap-1 mb-1">
                        {sec.keywords_added.map((kw, ki) => (
                          <span key={`kw-${ki}-${kw}`} className="cv-keyword-badge">+{kw}</span>
                        ))}
                      </div>
                    )}
                    {hasChanges && (
                      <ul className="space-y-0.5">
                        {sec.changes_made.map((ch, i) => (
                          <li key={i} className="text-xs text-gray-500">— {ch}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Header block ──────────────────────────────────────────────────────────────
function HeaderBlock({
  template, name, designation, contact,
}: {
  template: string; name: string; designation: string; contact: string
}) {
  const isSerif = template === 'elegant_serif'
  const isCorporate = template === 'corporate_blue'
  const isGreen = template === 'green_professional'
  const isTech = template === 'tech_pro'

  return (
    <div className="cv-preview-header">
      {isTech && <div className="cv-prompt">user@tailoriq:~$ cat resume.txt</div>}
      <div className="cv-name">{name}</div>
      {designation && <div className="cv-designation">{designation}</div>}
      {contact && <div className="cv-contact">{contact}</div>}
      {isSerif && <div className="cv-orn">— ✦ —</div>}
      {isCorporate && <div className="cv-divider" />}
      {isGreen && <div className="cv-accent-bar" />}
    </div>
  )
}

// ── Individual section (used for well-structured section arrays) ──────────────
function CVSection({ section }: { section: Section }) {
  if (!section.section_name && !section.content) return null
  return (
    <div className="cv-section">
      {section.section_name && (
        <div className="cv-section-heading">{section.section_name.toUpperCase()}</div>
      )}
      {section.content && (
        <div className="cv-section-body">{section.content}</div>
      )}
    </div>
  )
}
