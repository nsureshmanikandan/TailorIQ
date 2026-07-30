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
      <h3 className="section-label">Resume</h3>

      <div className="flex gap-1.5 mb-3 bg-gray-100 p-1 rounded-lg w-fit">
        <button
          onClick={() => setMode('upload')}
          className={`text-sm px-4 py-1.5 rounded-md font-medium transition-all ${
            mode === 'upload'
              ? 'bg-white text-indigo-700 shadow-sm'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Upload File
        </button>
        <button
          onClick={() => setMode('paste')}
          className={`text-sm px-4 py-1.5 rounded-md font-medium transition-all ${
            mode === 'paste'
              ? 'bg-white text-indigo-700 shadow-sm'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Paste Text
        </button>
      </div>

      {mode === 'upload' ? (
        <div
          onClick={() => fileRef.current?.click()}
          className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center cursor-pointer hover:border-indigo-400 hover:bg-indigo-50/40 transition-all group"
        >
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx"
            onChange={handleFile}
            className="hidden"
          />
          {fileName ? (
            <div className="flex flex-col items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p className="text-sm text-green-700 font-semibold">{fileName}</p>
            </div>
          ) : (
            <>
              <div className="w-12 h-12 rounded-xl bg-indigo-50 group-hover:bg-indigo-100 flex items-center justify-center mx-auto mb-3 transition-colors">
                <svg className="w-6 h-6 text-indigo-400 group-hover:text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
              </div>
              <p className="text-gray-600 text-sm font-medium">Drop your resume here or click to browse</p>
              <p className="text-gray-400 text-xs mt-1">PDF or DOCX · max 5 MB</p>
            </>
          )}
          {uploading && (
            <p className="text-xs text-indigo-500 mt-2 font-medium">Uploading…</p>
          )}
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
