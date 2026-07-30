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

export default function Dashboard() {
  const { userEmail, logout } = useAuthStore()
  const { phase, result, selectedTemplate } = useAnalysisStore()

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200/80 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-sm flex-shrink-0">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">
              TailorIQ
            </h1>
            <span className="hidden sm:inline-block text-xs font-medium text-indigo-400 bg-indigo-50 px-2 py-0.5 rounded-full border border-indigo-100">
              AI Resume
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="hidden sm:inline text-sm text-gray-400">{userEmail}</span>
            <button
              onClick={logout}
              className="text-sm font-medium text-gray-500 hover:text-indigo-600 transition-colors px-3 py-1.5 rounded-lg hover:bg-indigo-50"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Input Section */}
        <section className="card border-0 shadow-md bg-gradient-to-br from-white to-indigo-50/40 ring-1 ring-indigo-100">
          <div className="mb-6">
            <div className="inline-flex items-center gap-2 bg-indigo-50 border border-indigo-100 text-indigo-600 text-xs font-semibold uppercase tracking-widest px-3 py-1 rounded-full mb-3">
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              Step 1 — Input
            </div>
            <h2 className="text-2xl font-bold text-gray-900">
              Analyse &amp; Tailor Your Resume
            </h2>
            <p className="text-sm text-gray-500 mt-1">Upload your resume and paste the job description. Our AI does the rest.</p>
          </div>
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
                <h3 className="text-lg font-semibold mb-4">Category Breakdown</h3>
                <CategoryBreakdown
                  pass1Categories={result.pass1_score.category_scores}
                  pass2Categories={result.pass2_score.category_scores}
                />
              </section>
            )}

            {/* Keywords */}
            {result.pass2_score && (
              <section className="card">
                <h3 className="text-lg font-semibold mb-4">Keywords</h3>
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

            {/* Tailored Resume — Template Selector + Preview */}
            <section className="card">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-lg font-semibold text-gray-800">Tailored Resume</h3>
                {result.tailored_resume && (
                  <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">
                    {selectedTemplate.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                  </span>
                )}
              </div>

              {result.tailored_resume ? (
                <>
                  {/* Template picker */}
                  <TemplateSelector runId={result.run_id} />

                  {/* Visual CV preview — rerenders instantly on card click */}
                  <div className="mt-6">
                    <TailoredResumePreview
                      resume={result.tailored_resume}
                      parsedResume={result.parsed_resume ?? null}
                      selectedTemplate={selectedTemplate}
                    />
                  </div>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 border-2 border-dashed border-gray-200 rounded-xl bg-gray-50">
                  <svg className="w-12 h-12 text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="text-sm font-medium text-gray-500">Tailored CV not yet generated</p>
                  <p className="text-xs text-gray-400 mt-1">
                    The pipeline stopped before completing tailoring. Run analysis again to unlock template selection and CV download.
                  </p>
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
