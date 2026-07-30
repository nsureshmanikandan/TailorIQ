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
    if (!text.trim() || text.length > 50000) {
      alert('JD text must be between 1 and 50,000 characters')
      return
    }
    setLoading(true)
    setPhase('uploading')
    try {
      const res = await submitJDText(text)
      setJdId(res.jd_id)
      setSaved(true)
    } catch {
      alert('Failed to save JD')
    } finally {
      setLoading(false)
      setPhase('idle')
    }
  }

  async function handleSubmitUrl() {
    if (!url.trim()) {
      alert('Please enter a URL')
      return
    }
    setLoading(true)
    setPhase('uploading')
    try {
      const res = await submitJDUrl(url)
      setJdId(res.jd_id)
      setSaved(true)
    } catch {
      alert('Could not fetch JD from URL. Please paste the text instead.')
    } finally {
      setLoading(false)
      setPhase('idle')
    }
  }

  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">
        Job Description
      </h3>

      <div className="flex gap-2 mb-3">
        <button
          onClick={() => { setMode('text'); setSaved(false) }}
          className={`text-sm px-3 py-1 rounded ${mode === 'text' ? 'bg-brand-100 text-brand-700' : 'text-gray-500 hover:text-gray-700'}`}
        >
          Paste Text
        </button>
        <button
          onClick={() => { setMode('url'); setSaved(false) }}
          className={`text-sm px-3 py-1 rounded ${mode === 'url' ? 'bg-brand-100 text-brand-700' : 'text-gray-500 hover:text-gray-700'}`}
        >
          From URL
        </button>
      </div>

      {mode === 'text' ? (
        <div>
          <textarea
            value={text}
            onChange={(e) => { setText(e.target.value); setSaved(false) }}
            rows={8}
            placeholder="Paste the job description here..."
            className="input-field text-sm resize-y"
            maxLength={50000}
          />
          <div className="flex justify-between items-center mt-2">
            <span className="text-xs text-gray-400">{text.length}/50,000</span>
            <button onClick={handleSubmitText} disabled={loading} className="btn-secondary text-sm">
              {loading ? 'Saving...' : saved ? 'Saved ✓' : 'Save JD'}
            </button>
          </div>
        </div>
      ) : (
        <div>
          <input
            type="url"
            value={url}
            onChange={(e) => { setUrl(e.target.value); setSaved(false) }}
            placeholder="https://example.com/job/12345"
            className="input-field text-sm"
          />
          <div className="flex justify-end mt-2">
            <button onClick={handleSubmitUrl} disabled={loading} className="btn-secondary text-sm">
              {loading ? 'Fetching...' : saved ? 'Fetched ✓' : 'Fetch JD'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
