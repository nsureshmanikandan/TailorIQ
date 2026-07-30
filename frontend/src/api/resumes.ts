import api from './client'

export interface ResumeUploadResponse {
  resume_id: string
  raw_text_preview?: string
}

export async function uploadResume(file: File): Promise<ResumeUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await api.post('/resumes/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export async function pasteResumeText(text: string): Promise<{ resume_id: string }> {
  const res = await api.post('/resumes/text', { text })
  return res.data
}

export async function submitJDText(text: string): Promise<{ jd_id: string }> {
  const res = await api.post('/jobs/text', { text })
  return res.data
}

export async function submitJDUrl(url: string): Promise<{ jd_id: string; extracted_text_preview: string }> {
  const res = await api.post('/jobs/url', { url })
  return res.data
}
