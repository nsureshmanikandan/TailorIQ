import api from './client'

export async function downloadFile(runId: string, type: string): Promise<Blob> {
  const res = await api.get(`/downloads/${runId}/${type}`, { responseType: 'blob' })
  return res.data
}

export async function downloadCvTemplate(runId: string, templateId: string): Promise<Blob> {
  const res = await api.get(`/analysis/${runId}/cv-download`, {
    params: { template: templateId },
    responseType: 'blob',
  })
  return res.data
}

export async function downloadAll(runId: string): Promise<Blob> {
  const res = await api.get(`/downloads/${runId}/all`, { responseType: 'blob' })
  return res.data
}

export async function emailPackage(runId: string): Promise<{ message: string }> {
  const res = await api.post(`/downloads/${runId}/email`)
  return res.data
}

export function triggerDownload(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(url)
  document.body.removeChild(a)
}
