import { useState } from 'react'
import { submitJDText, submitJDUrl } from '../../api/resumes'
import { useAnalysisStore } from '../../store/analysisStore'

export default function JDInput() {
  const [mode, setMode] = useState<'text' | 'url'>('text')
  const [text, setText] = useState('')
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [saved, setSaved] = useState(false)
  const { setJdId, setPhase } = useAnalysisStore()

  async function handleSubmitText() {
    if (!text.trim() || text.length > 50000) { alert('JD text must be between 1 and 50,000 characters'); return }
    setLoading(true); setPhase('uploading')
    try { const res = await submitJDText(text); setJdId(res.jd_id); setSaved(true) }
    catch { alert('Failed to save JD') }
    finally { setLoading(false); setPhase('idle') }
  }

  async function handleSubmitUrl() {
    if (!url.trim()) { alert('Please enter a URL'); return }
    setLoading(true); setPhase('uploading')
    try { const res = await submitJDUrl(url); setJdId(res.jd_id); setSaved(true) }
    catch { alert('Could not fetch JD from URL. Please paste the text instead.') }
    finally { setLoading(false); setPhase('idle') }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header row: label + char count + action button */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="section-label" style={{ marginBottom: 0 }}>Job Description</h3>
        <div className="flex items-center gap-2">
          {mode === 'text' && (
            <span className="text-xs text-slate-500">{text.length}/50,000</span>
          )}
          {mode === 'text' ? (
            <button onClick={handleSubmitText} disabled={loading} className="btn-secondary text-sm">
              {loading ? 'Saving...' : saved ? 'Saved ✓' : 'Save JD'}
            </button>
          ) : (
            <button onClick={handleSubmitUrl} disabled={loading} className="btn-secondary text-sm">
              {loading ? 'Fetching...' : saved ? 'Fetched ✓' : 'Fetch JD'}
            </button>
          )}
        </div>
      </div>

      {/* Tab switcher — dark */}
      <div className="flex gap-1 mb-3 p-1 rounded-lg w-fit" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.07)' }}>
        {([['text', 'Paste Text'], ['url', 'From URL']] as const).map(([m, label]) => (
          <button key={m} onClick={() => { setMode(m); setSaved(false) }}
            className="text-sm px-4 py-1.5 rounded-md font-medium transition-all"
            style={mode === m
              ? { background: '#6366f1', color: '#fff' }
              : { color: '#64748b' }}>
            {label}
          </button>
        ))}
      </div>

      {mode === 'text' ? (
        <div className="flex flex-col flex-1 min-h-0">
          <textarea
            value={text}
            onChange={(e) => { setText(e.target.value); setSaved(false) }}
            placeholder="Paste the job description here..."
            className="input-field text-sm resize-none flex-1 min-h-0"
            maxLength={50000}
          />
        </div>
      ) : (
        <div className="flex flex-col flex-1 min-h-0">
          <input
            type="url"
            value={url}
            onChange={(e) => { setUrl(e.target.value); setSaved(false) }}
            placeholder="https://example.com/job/12345"
            className="input-field text-sm"
          />
        </div>
      )}
    </div>
  )
}
