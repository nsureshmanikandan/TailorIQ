import { downloadFile, downloadAll, emailPackage, triggerDownload } from '../../api/downloads'

interface Props {
  runId: string
}

export default function DownloadActions({ runId }: Props) {
  async function handleDownload(type: string, filename: string) {
    const blob = await downloadFile(runId, type)
    triggerDownload(blob, filename)
  }

  async function handleDownloadAll() {
    const blob = await downloadAll(runId)
    triggerDownload(blob, 'TailorIQ_Complete_Package.zip')
  }

  async function handleEmail() {
    await emailPackage(runId)
    alert('Package sent to your registered email')
  }

  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() => handleDownload('resume-docx', 'Tailored_Resume.docx')}
        className="btn-secondary text-sm"
      >
        Resume DOCX
      </button>
      <button
        onClick={() => handleDownload('resume-pdf', 'Tailored_Resume.pdf')}
        className="btn-secondary text-sm"
      >
        Resume PDF
      </button>
      <button
        onClick={() => handleDownload('cover-letter-docx', 'Cover_Letter.docx')}
        className="btn-secondary text-sm"
      >
        Cover Letter
      </button>
      <button onClick={handleDownloadAll} className="btn-primary text-sm">
        Download All
      </button>
      <button onClick={handleEmail} className="btn-secondary text-sm">
        📧 Email
      </button>
    </div>
  )
}
