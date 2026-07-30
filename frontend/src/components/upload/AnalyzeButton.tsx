import { useAnalysisStore } from '../../store/analysisStore'
import { startAnalysis, getAnalysisResult, getAnalysisStatus } from '../../api/analysis'

export default function AnalyzeButton() {
  const { resumeId, jdId, phase, setPhase, setRunId, setResult, setError, setProgress, setPipelinePhase } =
    useAnalysisStore()

  const canAnalyze = resumeId && jdId && phase !== 'analyzing'

  async function handleAnalyze() {
    if (!resumeId || !jdId) return
    setPhase('analyzing')
    setProgress(0)
    setPipelinePhase('phase_1')

    try {
      const { run_id } = await startAnalysis({ resume_id: resumeId, jd_id: jdId })
      setRunId(run_id)

      // Poll for completion
      let completed = false
      while (!completed) {
        await new Promise((r) => setTimeout(r, 2000))
        const status = await getAnalysisStatus(run_id)
        setProgress(status.progress_pct ?? 0)
        if (status.current_phase) setPipelinePhase(status.current_phase)

        if (status.status === 'completed' || status.status === 'partial') {
          setPipelinePhase('completed')
          const result = await getAnalysisResult(run_id)
          setResult(result)
          completed = true
        } else if (status.status === 'failed') {
          setPipelinePhase('failed')
          setError('Analysis failed. Please check your inputs and try again.')
          completed = true
        }
      }
    } catch (err: any) {
      setPipelinePhase('failed')
      setError(err.message || 'Analysis failed. Please try again.')
    }
  }

  return (
    <button onClick={handleAnalyze} disabled={!canAnalyze} className="btn-primary text-lg px-10 py-4">
      {phase === 'analyzing' ? 'Analysing...' : 'Analyse & Tailor'}
    </button>
  )
}
