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
      {/* Header row: label + action button */}
      <div className="flex items-center justify-between mb-3" style={{ minHeight: '28px' }}>
        <h3 className="section-label" style={{ marginBottom: 0 }}>Job Description</h3>
        {mode === 'text' ? (
          <button onClick={handleSubmitText} disabled={loading}
            className="text-sm px-4 py-1.5 rounded-lg font-semibold transition-all disabled:opacity-50 shadow-md"
            style={{ background: 'linear-gradient(to right, #6366f1, #3b82f6)', color: '#fff' }}>
            {loading ? 'Saving...' : saved ? 'Saved ✓' : 'Save JD'}
          </button>
        ) : (
          <button onClick={handleSubmitUrl} disabled={loading}
            className="text-sm px-4 py-1.5 rounded-lg font-semibold transition-all disabled:opacity-50 shadow-md"
            style={{ background: 'linear-gradient(to right, #6366f1, #3b82f6)', color: '#fff' }}>
            {loading ? 'Fetching...' : saved ? 'Fetched ✓' : 'Fetch JD'}
          </button>
        )}
      </div>

      {/* Tab switcher — indigo */}
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
        <div className="relative flex flex-col flex-1 min-h-0">
          <span className="absolute top-2.5 right-3 text-xs z-10 pointer-events-none select-none" style={{ color: '#475569' }}>
            {text.length}/50,000
          </span>
          <textarea
            value={text}
            onChange={(e) => { setText(e.target.value); setSaved(false) }}
            placeholder="Paste the job description here..."
            className="input-field text-sm resize-none flex-1 min-h-0"
            style={{
              paddingRight: '5.5rem',
              background: 'rgba(99,102,241,0.08)',
              borderColor: 'rgba(99,102,241,0.35)',
            }}
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
            style={{ background: 'rgba(99,102,241,0.08)', borderColor: 'rgba(99,102,241,0.35)' }}
          />
        </div>
      )}
    </div>
  )
}
