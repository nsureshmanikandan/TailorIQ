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
    if (file.size > 5 * 1024 * 1024) {
      alert('File must be under 5 MB')
      return
    }
    const ext = file.name.split('.').pop()?.toLowerCase()
    if (!['pdf', 'docx'].includes(ext || '')) {
      alert('Only PDF and DOCX files are accepted')
      return
    }
    setUploading(true)
    setPhase('uploading')
    try {
      const res = await uploadResume(file)
      setResumeId(res.resume_id)
      setFileName(file.name)
    } catch {
      alert('Upload failed')
    } finally {
      setUploading(false)
      setPhase('idle')
    }
  }

  async function handlePaste() {
    if (!text.trim() || text.length > 50000) {
      alert('Resume text must be between 1 and 50,000 characters')
      return
    }
    setUploading(true)
    setPhase('uploading')
    try {
      const res = await pasteResumeText(text)
      setResumeId(res.resume_id)
    } catch {
      alert('Failed to save resume text')
    } finally {
      setUploading(false)
      setPhase('idle')
    }
  }

  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">Resume</h3>

      <div className="flex gap-2 mb-3">
        <button
          onClick={() => setMode('upload')}
          className={`text-sm px-3 py-1 rounded ${mode === 'upload' ? 'bg-brand-100 text-brand-700' : 'text-gray-500 hover:text-gray-700'}`}
        >
          Upload File
        </button>
        <button
          onClick={() => setMode('paste')}
          className={`text-sm px-3 py-1 rounded ${mode === 'paste' ? 'bg-brand-100 text-brand-700' : 'text-gray-500 hover:text-gray-700'}`}
        >
          Paste Text
        </button>
      </div>

      {mode === 'upload' ? (
        <div
          onClick={() => fileRef.current?.click()}
          className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-brand-400 transition-colors"
        >
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx"
            onChange={handleFile}
            className="hidden"
          />
          {fileName ? (
            <p className="text-sm text-brand-600 font-medium">{fileName} ✓</p>
          ) : (
            <>
              <p className="text-gray-500 text-sm">
                Drop your resume here or click to browse
              </p>
              <p className="text-gray-400 text-xs mt-1">PDF or DOCX, max 5 MB</p>
            </>
          )}
          {uploading && <p className="text-xs text-brand-500 mt-2">Uploading...</p>}
        </div>
      ) : (
        <div>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={8}
            placeholder="Paste your resume text here..."
            className="input-field font-mono text-sm resize-y"
            maxLength={50000}
          />
          <div className="flex justify-between items-center mt-2">
            <span className="text-xs text-gray-400">{text.length}/50,000</span>
            <button onClick={handlePaste} disabled={uploading} className="btn-secondary text-sm">
              {uploading ? 'Saving...' : 'Save Text'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
