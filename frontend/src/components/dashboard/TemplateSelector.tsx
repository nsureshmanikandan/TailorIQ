import { useState } from 'react'
import { TEMPLATES, TemplateDefinition } from './templateDefinitions'
import { downloadCvTemplate, triggerDownload } from '../../api/downloads'
import { useAnalysisStore } from '../../store/analysisStore'
import '../../styles/cv-templates.css'

// Scaled-down live preview using the actual tmpl-X CSS classes
function MiniCVPreview({ tpl }: { tpl: TemplateDefinition }) {
  const SCALE = 0.40
  const INV = `${(100 / SCALE).toFixed(1)}%`

  const isTwo = tpl.layout === 'two-column'

  return (
    <div style={{ height: '160px', position: 'relative', overflow: 'hidden', background: 'white' }}>
      <div style={{ position: 'absolute', top: 0, left: 0, transformOrigin: 'top left', transform: `scale(${SCALE})`, width: INV, height: INV }}>
        {isTwo ? (
          <div className={`cv-preview tmpl-${tpl.id}`} style={{ display: 'flex', minHeight: '400px', fontSize: '13px' }}>
            <div className="cv-sidebar">
              <div className="cv-name">SURESH M.</div>
              <div className="cv-designation">AI Architect</div>
              <div className="cv-section">
                <div className="cv-section-heading">SKILLS</div>
                <div className="cv-section-body">{'Azure OpenAI\nLangGraph\nFastAPI\nDocker'}</div>
              </div>
              <div className="cv-section">
                <div className="cv-section-heading">CERTS</div>
                <div className="cv-section-body">{'AZ-305\nAZ-204'}</div>
              </div>
            </div>
            <div className="cv-main-col">
              <div className="cv-section">
                <div className="cv-section-heading">SUMMARY</div>
                <div className="cv-section-body">23yr AI Architect. Fortune 500. 5 production agentic platforms. $10M+ savings.</div>
              </div>
              <div className="cv-section">
                <div className="cv-section-heading">EXPERIENCE</div>
                <div className="cv-section-body">{'Technical Program Manager\nAccenture · Jul 2008 – Present'}</div>
              </div>
            </div>
          </div>
        ) : (
          <div className={`cv-preview tmpl-${tpl.id}`} style={{ fontSize: '13px', lineHeight: '1.5' }}>
            <div className="cv-preview-header">
              {tpl.id === 'tech_pro' && <div className="cv-prompt">user@tailoriq:~$ cat resume.txt</div>}
              <div className="cv-name">SURESH MANIKANDAN</div>
              <div className="cv-designation">Senior Enterprise AI Architect</div>
              <div className="cv-contact">Chennai · suresh@email.com · +91 98765 43210</div>
              {tpl.id === 'corporate_blue'     && <div className="cv-divider" />}
              {tpl.id === 'green_professional' && <div className="cv-accent-bar" />}
              {tpl.id === 'elegant_serif'      && <div className="cv-orn">— ✦ —</div>}
            </div>
            <div className="cv-preview-body">
              <div className="cv-section">
                <div className="cv-section-heading">PROFESSIONAL SUMMARY</div>
                <div className="cv-section-body">Senior AI Architect, 23 years. Fortune 500 AI/ML delivery. Expert in Azure OpenAI, LangGraph, RAG pipelines.</div>
              </div>
              <div className="cv-section">
                <div className="cv-section-heading">EXPERIENCE</div>
                <div className="cv-section-body">{'Technical Program Manager — Accenture\nJul 2008 – Present · Chennai'}</div>
              </div>
              <div className="cv-section">
                <div className="cv-section-heading">CORE SKILLS</div>
                <div className="cv-section-body">Azure OpenAI · LangGraph · FastAPI · Docker · PostgreSQL</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function TemplateSelector({ runId }: { runId: string }) {
  const { selectedTemplate, setSelectedTemplate } = useAnalysisStore()
  const [downloading, setDownloading] = useState(false)
  const [dlError, setDlError] = useState<string | null>(null)

  async function handleDownload() {
    setDownloading(true)
    setDlError(null)
    try {
      const blob = await downloadCvTemplate(runId, selectedTemplate)
      triggerDownload(blob, `cv_${selectedTemplate}.docx`)
    } catch {
      setDlError('Download failed — please try again')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div>
      {/* Template card grid */}
      <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-5 gap-3 mb-5">
        {TEMPLATES.map((tpl) => {
          const isSelected = selectedTemplate === tpl.id
          return (
            <button
              key={tpl.id}
              onClick={() => setSelectedTemplate(tpl.id)}
              className={`relative text-left rounded-xl border-2 overflow-hidden transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-indigo-400 ${
                isSelected
                  ? 'border-indigo-500 shadow-lg shadow-indigo-100 scale-[1.02]'
                  : 'border-gray-200 hover:border-indigo-300 hover:shadow-md'
              }`}
            >
              {/* Live mini CV preview */}
              <MiniCVPreview tpl={tpl} />

              {/* Label */}
              <div className="px-2.5 pb-2.5">
                <p className="text-xs font-semibold text-gray-800 leading-tight">{tpl.name}</p>
                <p className="text-[10px] text-gray-400 mt-0.5 leading-tight">{tpl.description}</p>
              </div>

              {/* Selected checkmark */}
              {isSelected && (
                <div className="absolute top-2 right-2 w-5 h-5 bg-indigo-500 rounded-full flex items-center justify-center shadow">
                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              )}

              {/* Two-column badge */}
              {tpl.layout === 'two-column' && (
                <div className="absolute bottom-8 right-1.5">
                  <span className="text-[8px] bg-gray-100 text-gray-500 rounded px-1 py-0.5">2-col</span>
                </div>
              )}
            </button>
          )
        })}
      </div>

      {/* Action row */}
      <div className="flex items-center gap-3 flex-wrap">
        <button
          onClick={handleDownload}
          disabled={downloading}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold px-5 py-2.5 rounded-lg text-sm transition-colors shadow-sm"
        >
          {downloading ? (
            <>
              <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              Generating…
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download DOCX
            </>
          )}
        </button>

        <span className="text-sm text-gray-500">
          Selected:{' '}
          <span className="font-semibold text-gray-700">
            {TEMPLATES.find((t) => t.id === selectedTemplate)?.name ?? selectedTemplate}
          </span>
        </span>

        {dlError && (
          <span className="text-sm text-red-600">{dlError}</span>
        )}
      </div>
    </div>
  )
}
