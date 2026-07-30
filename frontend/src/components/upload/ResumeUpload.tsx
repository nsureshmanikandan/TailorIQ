import { useState, useRef, ChangeEvent } from 'react'
import { uploadResume, pasteResumeText } from '../../api/resumes'
import { useAnalysisStore } from '../../store/analysisStore'

export default function ResumeUpload() {
  const [mode, setMode] = useState<'upload' | 'paste'>('upload')
  const [text, setText] = useState('')
  const [fileName, setFileName] = useState('')
  const [uploading, setUploading] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)
  const { setResumeId, setPhase } = useAnalysisStore()

  async function handleFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > 5 * 1024 * 1024) { alert('File must be under 5 MB'); return }
    const ext = file.name.split('.').pop()?.toLowerCase()
    if (!['pdf', 'docx'].includes(ext || '')) { alert('Only PDF and DOCX files are accepted'); return }
    setUploading(true)
    setPhase('uploading')
    try {
      const res = await uploadResume(file)
      setResumeId(res.resume_id)
      setFileName(file.name)
    } catch { alert('Upload failed') }
    finally { setUploading(false); setPhase('idle') }
  }

  async function handlePaste() {
    if (!text.trim() || text.length > 50000) { alert('Resume text must be between 1 and 50,000 characters'); return }
    setUploading(true)
    setPhase('uploading')
    try {
      const res = await pasteResumeText(text)
      setResumeId(res.resume_id)
    } catch { alert('Failed to save resume text') }
    finally { setUploading(false); setPhase('idle') }
  }

  const pills = ['Match Scoring', 'Gap Analysis', 'Keyword Boost', 'Cover Letter', 'Interview Prep']

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center flex-wrap gap-2 mb-3" style={{ minHeight: '28px' }}>
        <h3 className="section-label" style={{ marginBottom: 0 }}>Resume</h3>
        <div className="flex flex-wrap gap-1.5">
          {pills.map((f) => (
            <span key={f} className="flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-full"
              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8' }}>
              <span className="w-1.5 h-1.5 rounded-full inline-block flex-shrink-0" style={{ background: '#6366f1' }} />
              {f}
            </span>
          ))}
        </div>
      </div>

      {/* Tab switcher — dark */}
      <div className="flex gap-1 mb-3 p-1 rounded-lg w-fit" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.07)' }}>
        {(['upload', 'paste'] as const).map((m) => (
          <button key={m} onClick={() => setMode(m)}
            className="text-sm px-4 py-1.5 rounded-md font-medium transition-all"
            style={mode === m
              ? { background: '#6366f1', color: '#fff' }
              : { color: '#64748b' }}>
            {m === 'upload' ? 'Upload File' : 'Paste Text'}
          </button>
        ))}
      </div>

      {mode === 'upload' ? (
        <div
          onClick={() => fileRef.current?.click()}
          className="rounded-xl cursor-pointer transition-all flex-1 flex flex-col items-center justify-center"
          style={{ border: '2px dashed rgba(99,102,241,0.45)', background: 'rgba(99,102,241,0.08)', minHeight: '180px' }}
          onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(99,102,241,0.7)'; (e.currentTarget as HTMLDivElement).style.background = 'rgba(99,102,241,0.14)' }}
          onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(99,102,241,0.45)'; (e.currentTarget as HTMLDivElement).style.background = 'rgba(99,102,241,0.08)' }}
        >
          <input ref={fileRef} type="file" accept=".pdf,.docx" onChange={handleFile} className="hidden" />
          {fileName ? (
            <div className="flex flex-col items-center gap-2">
              <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ background: 'rgba(34,197,94,0.15)' }}>
                <svg className="w-5 h-5" style={{ color: '#22c55e' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p className="text-sm font-semibold" style={{ color: '#22c55e' }}>{fileName}</p>
            </div>
          ) : (
            <div className="text-center px-6">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-3" style={{ background: 'rgba(99,102,241,0.12)' }}>
                <svg className="w-6 h-6" style={{ color: '#818cf8' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
              </div>
              <p className="text-sm font-medium text-slate-300">Drop your resume here or click to browse</p>
              <p className="text-xs mt-1 text-slate-500">PDF or DOCX · max 5 MB</p>
            </div>
          )}
          {uploading && <p className="text-xs mt-2 font-medium" style={{ color: '#818cf8' }}>Uploading…</p>}
        </div>
      ) : (
        <div className="flex flex-col flex-1 min-h-0">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste your resume text here..."
            className="input-field font-mono text-sm resize-none flex-1 min-h-0"
            maxLength={50000}
          />
          <div className="flex justify-between items-center mt-2">
            <span className="text-xs text-slate-500">{text.length}/50,000</span>
            <button onClick={handlePaste} disabled={uploading} className="btn-secondary text-sm">
              {uploading ? 'Saving...' : 'Save Text'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
