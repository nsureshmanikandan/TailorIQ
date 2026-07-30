import { useAuthStore } from '../store/authStore'
import { useAnalysisStore } from '../store/analysisStore'
import ResumeUpload from '../components/upload/ResumeUpload'
import JDInput from '../components/upload/JDInput'
import ScoreCard from '../components/dashboard/ScoreCard'
import CategoryBreakdown from '../components/dashboard/CategoryBreakdown'
import KeywordPanel from '../components/dashboard/KeywordPanel'
import TailoredResumePreview from '../components/dashboard/TailoredResumePreview'
import TemplateSelector from '../components/dashboard/TemplateSelector'
import CoverLetterPanel from '../components/dashboard/CoverLetterPanel'
import InterviewGuidePanel from '../components/dashboard/InterviewGuidePanel'
import DownloadActions from '../components/dashboard/DownloadActions'
import AnalyzeButton from '../components/upload/AnalyzeButton'
import LoadingState from '../components/common/LoadingState'

const FEATURE_PILLS = ['Match Scoring', 'Gap Analysis', 'Keyword Boost', 'Cover Letter', 'Interview Prep']

export default function Dashboard() {
  const { userEmail, logout } = useAuthStore()
  const { phase, result, selectedTemplate } = useAnalysisStore()

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #080d1a 0%, #0d1635 50%, #080d1a 100%)' }}>

      {/* Header — dark glass */}
      <header className="sticky top-0 z-50 border-b border-white/5" style={{ background: 'rgba(8,13,26,0.85)', backdropFilter: 'blur(12px)' }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: 'linear-gradient(135deg, #6366f1, #3b82f6)' }}>
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h1 className="text-xl font-bold text-white tracking-tight">TailorIQ</h1>
            <span className="hidden sm:inline-block text-xs font-semibold px-2.5 py-0.5 rounded-full" style={{ background: 'rgba(99,102,241,0.15)', color: '#a5b4fc', border: '1px solid rgba(99,102,241,0.3)' }}>
              AI Resume
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="hidden sm:inline text-sm text-slate-400">{userEmail}</span>
            <button
              onClick={logout}
              className="text-sm font-semibold text-slate-300 hover:text-white transition-colors px-3 py-1.5 rounded-lg"
              style={{ border: '1px solid rgba(255,255,255,0.1)' }}
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-5 pb-14">
        {/* Badge pill */}
        <div className="inline-flex items-center gap-2 mb-5 px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider"
          style={{ background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.3)', color: '#a5b4fc' }}>
          <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
          AI-Powered Resume Optimizer
        </div>

        {/* Main headline */}
        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white leading-tight mb-3">
          Tailor Your <span style={{ background: 'linear-gradient(90deg, #6366f1, #60a5fa)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>Resume</span> with AI
        </h2>
        <p className="text-slate-400 text-base sm:text-lg mb-6 max-w-2xl">
          Actionable score, gap analysis, and AI-tailored sections in seconds.
        </p>

        {/* Feature capability pills */}
        <div className="flex flex-wrap gap-2 mb-0">
          {FEATURE_PILLS.map((f) => (
            <span key={f} className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full"
              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8' }}>
              <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ background: '#6366f1' }} />
              {f}
            </span>
          ))}
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-4 pb-12">

        {/* Input Section */}
        <section className="rounded-2xl p-6" style={{ background: 'rgba(15,23,41,0.9)', border: '1px solid rgba(255,255,255,0.07)' }}>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ResumeUpload />
            <JDInput />
          </div>
          <div className="mt-6 flex justify-center">
            <AnalyzeButton />
          </div>
        </section>

        {/* Loading / Error */}
        {(phase === 'analyzing' || phase === 'error') && <LoadingState />}

        {/* Results */}
        {result && (
          <>
            {/* Score + Downloads */}
            <section className="card">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <ScoreCard
                  pass1={result.pass1_score?.overall_score ?? 0}
                  pass2={result.pass2_score?.overall_score ?? null}
                />
                <DownloadActions runId={result.run_id} />
              </div>
            </section>

            {/* Category Breakdown */}
            {result.pass1_score && result.pass2_score && (
              <section className="card">
                <h3 className="text-base font-semibold text-white mb-4">Category Breakdown</h3>
                <CategoryBreakdown
                  pass1Categories={result.pass1_score.category_scores}
                  pass2Categories={result.pass2_score.category_scores}
                />
              </section>
            )}

            {/* Keywords */}
            {result.pass2_score && (
              <section className="card">
                <h3 className="text-base font-semibold text-white mb-4">Keywords</h3>
                <KeywordPanel
                  matched={result.pass1_score?.matched_keywords ?? []}
                  added={
                    result.pass2_score.matched_keywords.filter(
                      (k) => !result.pass1_score?.matched_keywords.includes(k)
                    )
                  }
                />
              </section>
            )}

            {/* Tailored Resume */}
            <section className="card">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-base font-semibold text-white">Tailored Resume</h3>
                {result.tailored_resume && (
                  <span className="text-xs px-2 py-1 rounded" style={{ color: '#94a3b8', background: 'rgba(255,255,255,0.05)' }}>
                    {selectedTemplate.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                  </span>
                )}
              </div>

              {result.tailored_resume ? (
                <>
                  <TemplateSelector runId={result.run_id} />
                  <div className="mt-6">
                    <TailoredResumePreview
                      resume={result.tailored_resume}
                      parsedResume={result.parsed_resume ?? null}
                      selectedTemplate={selectedTemplate}
                    />
                  </div>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 border-2 border-dashed rounded-xl" style={{ borderColor: 'rgba(255,255,255,0.08)', background: 'rgba(255,255,255,0.02)' }}>
                  <svg className="w-12 h-12 mb-3" style={{ color: '#334155' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="text-sm font-medium text-slate-500">Tailored CV not yet generated</p>
                  <p className="text-xs text-slate-600 mt-1">Run analysis again to unlock template selection and CV download.</p>
                </div>
              )}
            </section>

            {/* Cover Letter */}
            {result.cover_letter && (
              <CoverLetterPanel content={result.cover_letter.content} />
            )}

            {/* Interview Guide */}
            {result.interview_guide && (
              <InterviewGuidePanel guide={result.interview_guide} />
            )}
          </>
        )}
      </main>
    </div>
  )
}
