import { useState } from 'react'
import { TEMPLATES } from './templateDefinitions'
import { downloadCvTemplate, triggerDownload } from '../../api/downloads'
import { useAnalysisStore } from '../../store/analysisStore'

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
              {/* Accent stripe */}
              <div
                className="h-2 w-full"
                style={{ background: tpl.accentColor }}
              />

              {/* Mini CV preview */}
              <div className="p-2.5 bg-white">
                {/* Simulated name bar */}
                <div
                  className="h-2 rounded mb-1.5 w-3/4"
                  style={{ background: tpl.headerBg ?? tpl.headingColor, opacity: 0.9 }}
                />
                {/* Simulated heading */}
                <div
                  className="h-1.5 rounded mb-1 w-1/2"
                  style={{ background: tpl.headingColor, opacity: 0.7 }}
                />
                {/* Simulated body lines */}
                <div className="space-y-1">
                  <div className="h-1 rounded bg-gray-200 w-full" />
                  <div className="h-1 rounded bg-gray-200 w-5/6" />
                  <div className="h-1 rounded bg-gray-200 w-4/6" />
                </div>
                {/* Second heading */}
                <div
                  className="h-1.5 rounded mt-2 mb-1 w-2/5"
                  style={{ background: tpl.headingColor, opacity: 0.7 }}
                />
                <div className="space-y-1">
                  <div className="h-1 rounded bg-gray-200 w-full" />
                  <div className="h-1 rounded bg-gray-200 w-3/4" />
                </div>
              </div>

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
