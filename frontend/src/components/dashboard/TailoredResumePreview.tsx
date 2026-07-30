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

// Section names already rendered in the header block — skip them from body
const HEADER_SECTIONS = new Set([
  'HEADER', 'CONTACT', 'CONTACT INFORMATION', 'CONTACT DETAILS',
])

const TWO_COLUMN_TEMPLATES = new Set(['executive_dark', 'two_column_split'])

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

  // Split sections into sidebar vs main for two-column templates
  const sidebarSections = isTwoCol
    ? resume.sections.filter((s) => SIDEBAR_SECTIONS.has(s.section_name.toUpperCase()))
    : []
  const mainSections = isTwoCol
    ? resume.sections.filter((s) => !SIDEBAR_SECTIONS.has(s.section_name.toUpperCase()))
    : resume.sections.filter((s) => !HEADER_SECTIONS.has(s.section_name.toUpperCase()))

  const totalKeywords = resume.keywords_added?.length ?? 0
  const totalChanges = resume.sections.reduce((n, s) => n + (s.changes_made?.length ?? 0), 0)

  return (
    <div>
      {/* ── Styled CV Preview ── */}
      <div className={`cv-preview tmpl-${selectedTemplate} border border-gray-200 shadow-sm`}>
        {isTwoCol ? (
          // Two-column layout
          <>
            <div className="cv-sidebar">
              <div className="cv-name">{candidateName}</div>
              {designation && <div className="cv-designation">{designation}</div>}
              {sidebarSections.map((sec) => (
                <div key={sec.section_name} className="cv-section">
                  <div className="cv-section-heading">{sec.section_name.toUpperCase()}</div>
                  <div className="cv-section-body">{sec.content}</div>
                </div>
              ))}
            </div>
            <div className="cv-main-col">
              {mainSections.map((sec) => (
                <CVSection key={sec.section_name} section={sec} />
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
              {mainSections.map((sec) => (
                <CVSection key={sec.section_name} section={sec} />
              ))}
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
              {resume.sections.map((sec) => {
                const hasChanges = sec.changes_made?.length > 0
                const hasKw = sec.keywords_added?.length > 0
                if (!hasChanges && !hasKw) return null
                return (
                  <div key={sec.section_name}>
                    <p className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-1">
                      {sec.section_name}
                    </p>
                    {hasKw && (
                      <div className="flex flex-wrap gap-1 mb-1">
                        {sec.keywords_added.map((kw) => (
                          <span key={kw} className="cv-keyword-badge">+{kw}</span>
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

// ── Header block: handles both plain and colored-header templates ──
function HeaderBlock({
  template, name, designation, contact,
}: {
  template: string; name: string; designation: string; contact: string
}) {
  // Elegant serif gets an ornament divider
  const isSerif = template === 'elegant_serif'
  // Corporate blue gets a gradient divider
  const isCorporate = template === 'corporate_blue'
  // Green professional gets an accent bar
  const isGreen = template === 'green_professional'
  // Tech Pro gets a prompt line
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

// ── Individual section ──
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
