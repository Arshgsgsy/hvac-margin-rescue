'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Upload, FileArchive, CheckCircle2, X, Shield, BarChart3, Zap, FileSpreadsheet, Loader2, ChevronRight, AlertTriangle, TrendingDown, DollarSign, Building2, AlertCircle, Eye, Users, Truck, Calendar } from 'lucide-react'
import { MOCK_PROJECTS, PORTFOLIO_SUMMARY, formatCurrency, formatPercent } from '@/lib/data'
import { PipelineJob, PipelineResult, Project, UploadResult } from '@/lib/types'
import { fetchHealth, uploadDataset, waitForPipelineJob } from '@/lib/api'
import { InvestigateModal } from './investigate-modal'


interface UploadedFile {
  name: string
  size: number
  type: string
}

interface StepDef {
  id: string
  label: string
  script: string
  description: string
  duration: number
  logs: string[]
}

const STEPS: StepDef[] = [
  {
    id: '1_clean',
    label: 'Clean & Summarize',
    script: 'pipeline/1_clean/*',
    description: 'Clean raw uploads, normalize roles/categories, and generate project-level summaries',
    duration: 0,
    logs: [],
  },
  {
    id: '2_load',
    label: 'Load & Join',
    script: 'pipeline/2_load/*',
    description: 'Compare actuals vs budget and merge labor/material cost views',
    duration: 0,
    logs: [],
  },
  {
    id: 'merge',
    label: 'Merge & Enrich',
    script: 'overspend_underbill_measure.py',
    description: 'Blend billing, change orders, and RFI signals into project-level risk context',
    duration: 2200,
    logs: [
      'Calculating earned vs. billed position by project...',
      'Joining change-order exposure and commercial status...',
      'Rolling RFIs into coordination-friction signals...',
      'Writing enriched project-level dataset for flagging...',
      '[DONE] Merge & enrichment complete in 2.1s',
    ],
  },
  {
    id: 'flag',
    label: 'Portfolio Scan',
    script: '03_flag_projects.py',
    description: 'Compute variances, identify margin erosion, and rank the projects that need action',
    duration: 1400,
    logs: [
      'Computing per-project cost actuals...',
      'Computing variance: actual_cost - budget_cost per project...',
      'Computing billing gap: pct_complete - pct_billed...',
      'Computing realized margin: (contract_value - actual_cost) / contract_value...',
      'Ranking the jobs that most need intervention...',
      '[DONE] Portfolio scan complete in 1.4s',
    ],
  },
  {
    id: 'export',
    label: 'Export JSON',
    script: '04_export.py',
    description: 'Export structured project packets for the frontend and the LLM agents',
    duration: 8500,
    logs: [
      'Serializing portfolio_summary.json...',
      'Serializing flagged_projects.json...',
      'Building project packets for the LLM stage...',
      '[DONE] JSON export complete in 8.3s',
    ],
  },
  {
    id: 'agent',
    label: 'Project Recovery Analysis',
    script: 'run_batch_analysis.py',
    description: 'Diagnose each flagged job, quantify recovery actions, and write project recovery memos',
    duration: 9000,
    logs: [
      'Loading flagged projects from output_summaries/...',
      'Building hybrid packets with metrics, field notes, RFIs, and change orders...',
      'Running diagnosis + recommendation agents project by project...',
      'Saving project_analyses.json for the action-first UI...',
      '[DONE] Project recovery analysis complete',
    ],
  },
  {
    id: 'portfolio',
    label: 'Portfolio Action Plan',
    script: 'portfolio_optimizer.py',
    description: 'Turn all project actions into a cash-focused weekly operating plan',
    duration: 4200,
    logs: [
      'Flattening all project-level recovery actions...',
      'Ranking actions by expected value, urgency, and owner capacity...',
      'Producing this-week plan and cash flow projection...',
      '[DONE] Portfolio action plan ready',
    ],
  },
]

type StepStatus = 'idle' | 'running' | 'complete' | 'error'

// Time range options
const TIME_RANGES = [
  { id: '1m', label: '1 Month' },
  { id: '1q', label: '1 Quarter' },
  { id: '6m', label: '6 Months' },
  { id: '1y', label: '1 Year' },
  { id: 'custom', label: 'Custom' },
]

export function UploadPage() {
  const router = useRouter()
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadComplete, setUploadComplete] = useState(false)
  const [pipelineStarted, setPipelineStarted] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const summaryRef = useRef<HTMLDivElement>(null)

  // Pipeline state
  const [statuses, setStatuses] = useState<StepStatus[]>(STEPS.map(() => 'idle'))
  const [visibleLogs, setVisibleLogs] = useState<string[][]>(STEPS.map((): string[] => []))
  const [running, setRunning] = useState(false)
  const [done, setDone] = useState(false)
  const logRefs = useRef<(HTMLDivElement | null)[]>([])
  const runningRef = useRef(false)

  // Investigate modal
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)

  // Time range filter
  const [selectedTimeRange, setSelectedTimeRange] = useState('1y')
  const [customStartDate, setCustomStartDate] = useState('Jan 2024')
  const [customEndDate, setCustomEndDate] = useState('Dec 2025')
  const [showCustomDatePicker, setShowCustomDatePicker] = useState(false)
  const [sliderStart, setSliderStart] = useState(0)
  const [sliderEnd, setSliderEnd] = useState(24)

  useEffect(() => { return () => { runningRef.current = false } }, [])

  // Auto-scroll to summary when done
  useEffect(() => {
    if (done && summaryRef.current) {
      setTimeout(() => {
        summaryRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 500)
    }
  }, [done])

  const [backendConnected, setBackendConnected] = useState<boolean>(true)

  // Check system status on mount
  useEffect(() => {
    fetchHealth()
      .then(() => setBackendConnected(true))
      .catch(() => setBackendConnected(false))
  }, [])

  // Store actual File objects for upload
  const [actualFiles, setActualFiles] = useState<File[]>([])
  const [uploadStatus, setUploadStatus] = useState<UploadResult | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [pipelineError, setPipelineError] = useState<string | null>(null)
  const [pipelineResult, setPipelineResult] = useState<PipelineResult | null>(null)
  const [redirecting, setRedirecting] = useState(false)

  const resetWorkflow = () => {
    setFiles([])
    setActualFiles([])
    setUploadComplete(false)
    setUploadStatus(null)
    setUploadError(null)
    setPipelineStarted(false)
    setRunning(false)
    setDone(false)
    setRedirecting(false)
    setPipelineError(null)
    setPipelineResult(null)
    setStatuses(STEPS.map(() => 'idle'))
    setVisibleLogs(STEPS.map((): string[] => []))
  }

  const applyPipelineResult = useCallback((result: PipelineResult | null) => {
    if (!result?.steps) return

    setPipelineResult(result)
    setStatuses(() =>
      STEPS.map((_, index) => {
        const backendStep = result.steps[index]
        if (!backendStep) return 'idle'
        if (backendStep.status === 'complete') return 'complete'
        if (backendStep.status === 'error') return 'error'
        if (backendStep.status === 'running') return 'running'
        return 'idle'
      }),
    )
    setVisibleLogs(() =>
      STEPS.map((_, index) => result.steps[index]?.logs || []),
    )
  }, [])

  const beginUploadAndPipeline = useCallback(async (selectedFiles: File[]) => {
    if (running || done || selectedFiles.length === 0) return

    setUploadError(null)
    setPipelineError(null)
    setUploadStatus(null)
    setPipelineResult(null)
    setPipelineStarted(true)
    setRunning(true)
    runningRef.current = true
    setStatuses(STEPS.map(() => 'idle'))
    setVisibleLogs(STEPS.map((): string[] => []))
    setFiles(selectedFiles.map((file) => ({
      name: file.name,
      size: file.size,
      type: file.type || 'application/octet-stream',
    })))
    setActualFiles(selectedFiles)
    setUploadComplete(true)

    try {
      setStatuses((prev) => {
        const next = [...prev]
        next[0] = 'running'
        return next
      })
      setVisibleLogs((prev) => {
        const next = prev.map((lines) => [...lines])
        next[0] = [
          `[UPLOAD] Uploading ${selectedFiles.length} file(s) to the active dataset...`,
          '[UPLOAD] Replacing the active dataset, clearing stale outputs, and starting the backend job...',
        ]
        return next
      })

      setIsUploading(true)
      const uploadResult = await uploadDataset(selectedFiles, true)
      setIsUploading(false)
      setUploadStatus(uploadResult)

      if (!uploadResult.can_run_pipeline) {
        throw new Error(`Missing required files: ${uploadResult.missing_required.join(', ')}`)
      }

      const job = uploadResult.pipeline_job
      if (!job) {
        throw new Error('Upload succeeded, but the backend did not start a pipeline job.')
      }

      const completedJob = await waitForPipelineJob(job.id, {
        intervalMs: 1200,
        onUpdate: (nextJob: PipelineJob) => {
          if (nextJob.result) {
            applyPipelineResult(nextJob.result)
          }
        },
      })

      if (!completedJob.result) {
        throw new Error(completedJob.error || 'Pipeline job completed without a result payload.')
      }

      const result = completedJob.result
      applyPipelineResult(result)

      if (completedJob.status !== 'complete' || result.status !== 'complete') {
        const firstErrorStep = result.steps.find((step) => step.status === 'error')
        const errorMessage = firstErrorStep?.logs.find((line) => line.includes('[ERROR]')) || 'Pipeline execution failed'
        throw new Error(errorMessage)
      }

      setDone(true)
      setRedirecting(true)
      setTimeout(() => {
        router.push('/dashboard')
      }, 300)
    } catch (error) {
      setIsUploading(false)
      const message = error instanceof Error ? error.message : 'Analysis failed'
      setPipelineError(message)
      setStatuses((prev) => {
        const next = [...prev]
        const failedIndex = next.findIndex((status) => status === 'running')
        next[failedIndex >= 0 ? failedIndex : 0] = 'error'
        return next
      })
      setVisibleLogs((prev) => {
        const next = prev.map((lines) => [...lines])
        const populatedIndexes = next
          .map((lines, index) => (lines.length > 0 ? index : -1))
          .filter((index) => index >= 0)
        const targetIndex = populatedIndexes.length > 0 ? populatedIndexes[populatedIndexes.length - 1] : 0
        next[targetIndex] = [...next[targetIndex], `[ERROR] ${message}`]
        return next
      })
    } finally {
      setRunning(false)
      runningRef.current = false
    }
  }, [applyPipelineResult, done, router, running])

  const handleFiles = useCallback((fileList: FileList | null) => {
    if (!fileList) return

    const selectedFiles = Array.from(fileList).filter((file) =>
      file.name.toLowerCase().endsWith('.zip') || file.name.toLowerCase().endsWith('.csv')
    )

    if (selectedFiles.length === 0) {
      setUploadError('Only ZIP archives and CSV files are supported.')
      return
    }

    setUploadError(null)
    setPipelineError(null)
    setUploadStatus(null)
    beginUploadAndPipeline(selectedFiles)
  }, [beginUploadAndPipeline])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    handleFiles(e.dataTransfer.files)
  }, [handleFiles])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const removeFile = (index: number) => {
    setActualFiles((prev) => {
      const next = prev.filter((_, i) => i !== index)
      setFiles(next.map((file) => ({
        name: file.name,
        size: file.size,
        type: file.type || 'application/octet-stream',
      })))
      setUploadComplete(next.length > 0)
      if (next.length === 0) {
        setUploadStatus(null)
      }
      return next
    })
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const statusColor = (s: StepStatus) =>
    s === 'complete' ? '#10b981' : s === 'running' ? '#3b82f6' : s === 'error' ? '#ef4444' : '#334155'

  const completedCount = statuses.filter((s) => s === 'complete').length

  // Group projects by severity
  const criticalProjects = MOCK_PROJECTS.filter(p => p.severity === 'critical')
  const warningProjects = MOCK_PROJECTS.filter(p => p.severity === 'warning')
  const watchProjects = MOCK_PROJECTS.filter(p => p.severity === 'watch')

  // Calculate summary stats
  const totalOverrun = MOCK_PROJECTS.reduce((sum, p) => sum + p.laborOverrun + p.materialOverrun, 0)
  const totalRecovery = MOCK_PROJECTS.reduce((sum, p) => {
    return sum + (p.recoveryActions?.reduce((s, a) => s + a.amount, 0) || 0)
  }, 0)
  const avgMarginErosion = MOCK_PROJECTS.reduce((sum, p) => sum + Math.abs(p.marginDelta), 0) / MOCK_PROJECTS.length



  // Render project row
  const renderProjectRow = (project: Project) => (
    <div
      key={project.id}
      className="flex items-center gap-4 p-4 rounded-xl border border-border/50 bg-card/50 hover:bg-card transition-colors"
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-semibold text-foreground truncate">{project.name}</span>
          <span className="text-xs px-2 py-0.5 rounded bg-muted text-muted-foreground">{project.sector}</span>
        </div>
        <p className="text-sm text-muted-foreground line-clamp-1">{project.fieldNoteSummary}</p>
      </div>
      <div className="text-right flex-shrink-0">
        <div className="text-lg font-bold text-destructive">
          -{formatPercent(Math.abs(project.marginDelta))}
        </div>
        <div className="text-xs text-muted-foreground">margin erosion</div>
      </div>
      <div className="text-right flex-shrink-0">
        <div className="text-lg font-bold text-foreground">
          {formatCurrency((project.laborOverrun ?? 0) + (project.materialOverrun ?? 0))}
        </div>
        <div className="text-xs text-muted-foreground">total overrun</div>
      </div>
      <button
        onClick={() => setSelectedProject(project)}
        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors flex-shrink-0"
      >
        <Eye className="w-4 h-4" />
        <span className="text-sm font-medium">Investigate</span>
      </button>
    </div>
  )

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border/50 bg-background/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-primary/20 flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h1 className="text-foreground font-bold text-lg">MarginIQ</h1>
              <p className="text-muted-foreground text-xs">
                {done ? 'Analysis Complete' : pipelineStarted ? 'Processing...' : 'Financial Intelligence Platform'}
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="p-6">
        <div className="max-w-6xl mx-auto space-y-8">
          
          {/* Upload Section - always visible but minimized when pipeline is running */}
          {!pipelineStarted && (
            <div className="space-y-6">
              {/* Title section */}
              <div className="text-center">
                <h2 className="text-3xl font-bold text-foreground mb-3">
                  Upload Your Financial Data
                </h2>
                <p className="text-muted-foreground text-lg max-w-xl mx-auto">
                  Upload a ZIP file containing your company&apos;s financial records. Our AI will analyze margins, detect risks, and identify recovery opportunities.
                </p>
                {/* System status */}
                <div className="mt-4 flex items-center justify-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${backendConnected ? 'bg-emerald-500' : 'bg-muted-foreground animate-pulse'}`} />
                  <span className="text-xs text-muted-foreground">
                    {backendConnected ? 'System ready' : 'Initializing...'}
                  </span>
                </div>
              </div>

              {/* Upload zone */}
              <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => inputRef.current?.click()}
                className={`
                  relative rounded-2xl border-2 border-dashed p-12 text-center cursor-pointer
                  transition-all duration-300 max-w-3xl mx-auto
                  ${isDragging 
                    ? 'border-primary bg-primary/10 scale-[1.02]' 
                    : uploadComplete 
                    ? 'border-emerald-500/50 bg-emerald-500/5' 
                    : 'border-border hover:border-primary/50 hover:bg-primary/5'
                  }
                `}
              >
                <input
                  ref={inputRef}
                  type="file"
                  accept=".zip,.csv"
                  multiple
                  onChange={(e) => handleFiles(e.target.files)}
                  className="hidden"
                />

                {isUploading ? (
                  <div className="flex flex-col items-center gap-4">
                    <Loader2 className="w-12 h-12 text-primary animate-spin" />
                    <p className="text-foreground font-medium">Uploading files...</p>
                  </div>
                ) : uploadComplete ? (
                  <div className="flex flex-col items-center gap-4">
                    <CheckCircle2 className="w-12 h-12 text-emerald-500" />
                    <div>
                      <p className="text-foreground font-medium">Upload accepted</p>
                      <p className="text-muted-foreground text-sm mt-1">The backend will start the pipeline automatically.</p>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-4">
                    <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center">
                      <Upload className="w-8 h-8 text-primary" />
                    </div>
                    <div>
                      <p className="text-foreground font-medium text-lg">
                        Drop your files here, or <span className="text-primary">browse</span>
                      </p>
                      <p className="text-muted-foreground text-sm mt-2">
                        Supports ZIP archives and CSV files
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Uploaded files list */}
              {files.length > 0 && (
                <div className="space-y-2 max-w-3xl mx-auto">
                  {files.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-3 px-4 py-3 rounded-xl border border-border/50 bg-card/50"
                    >
                      <FileArchive className="w-5 h-5 text-primary" />
                      <div className="flex-1 min-w-0">
                        <p className="text-foreground text-sm font-medium truncate">{file.name}</p>
                        <p className="text-muted-foreground text-xs">{formatFileSize(file.size)}</p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          removeFile(index)
                        }}
                        className="p-1 rounded-lg hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {uploadError && (
                <div className="max-w-3xl mx-auto rounded-xl border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
                  {uploadError}
                </div>
              )}

              {uploadStatus && (
                <div className="max-w-3xl mx-auto rounded-xl border border-border/50 bg-card/50 px-4 py-3 text-sm space-y-2">
                  <div className="text-foreground">
                    Active dataset will include <span className="font-semibold">{uploadStatus.files.length}</span> accepted file(s).
                  </div>
                  {uploadStatus.missing_optional.length > 0 && (
                    <div className="text-muted-foreground">
                      Optional files missing for degraded mode: {uploadStatus.missing_optional.join(', ')}
                    </div>
                  )}
                </div>
              )}

              {/* Features */}
              <div className="grid grid-cols-3 gap-4 max-w-3xl mx-auto pt-8">
                <div className="text-center p-4">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-3">
                    <BarChart3 className="w-5 h-5 text-primary" />
                  </div>
                  <h3 className="text-foreground font-medium text-sm">Margin Analysis</h3>
                  <p className="text-muted-foreground text-xs mt-1">Identify erosion patterns</p>
                </div>
                <div className="text-center p-4">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-3">
                    <Shield className="w-5 h-5 text-primary" />
                  </div>
                  <h3 className="text-foreground font-medium text-sm">AI Root Cause</h3>
                  <p className="text-muted-foreground text-xs mt-1">Claude-powered analysis</p>
                </div>
                <div className="text-center p-4">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-3">
                    <FileSpreadsheet className="w-5 h-5 text-primary" />
                  </div>
                  <h3 className="text-foreground font-medium text-sm">Recovery Actions</h3>
                  <p className="text-muted-foreground text-xs mt-1">Prioritized recommendations</p>
                </div>
              </div>
            </div>
          )}

          {/* Pipeline Section */}
          {pipelineStarted && (
            <div className="space-y-4">
              <div>
                <h2 className="text-foreground text-xl font-semibold">Analyzing Financial Data</h2>
                <p className="text-sm mt-1 text-muted-foreground">
                  5-step data pipeline: clean, load, scan, export, analyze
                </p>
              </div>

              {pipelineError && (
                <div className="rounded-xl border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive space-y-3">
                  <div>{pipelineError}</div>
                  <button
                    type="button"
                    onClick={resetWorkflow}
                    className="inline-flex items-center gap-2 rounded-lg border border-destructive/30 px-3 py-2 text-xs font-medium text-destructive hover:bg-destructive/10 transition-colors"
                  >
                    Return to uploads
                  </button>
                </div>
              )}

              {redirecting && (
                <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 px-4 py-3 text-sm text-emerald-500">
                  Analysis complete. Opening the live dashboard for the uploaded dataset...
                </div>
              )}

              {/* Progress bar */}
              {(running || done) && (
                <div>
                  <div className="flex justify-between text-xs mb-1 text-muted-foreground">
                    <span>Progress</span>
                    <span>{completedCount} / {STEPS.length} steps</span>
                  </div>
                  <div className="h-1.5 rounded-full overflow-hidden bg-muted">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        background: 'linear-gradient(90deg, hsl(var(--primary)), hsl(var(--primary-light)))',
                        width: `${(completedCount / STEPS.length) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              )}

              {/* Steps - only running step shows logs, idle and complete are collapsed */}
              <div className="space-y-2">
                {STEPS.map((step, i) => {
                  const status = statuses[i]
                  const isRunning = status === 'running'
                  
                  return (
                    <div
                      key={step.id}
                      className={`rounded-xl border overflow-hidden transition-all duration-300 ${status === 'idle' ? 'opacity-40' : ''}`}
                      style={{
                        borderColor: statusColor(status),
                        background: status === 'complete' ? 'rgba(16,185,129,0.08)' : status === 'running' ? 'rgba(59,130,246,0.08)' : 'hsl(var(--card))',
                      }}
                    >
                      {/* Collapsed view for idle and complete steps */}
                      {!isRunning ? (
                        <div className="flex items-center gap-3 px-4 py-3">
                          <div 
                            className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0"
                            style={{ 
                              background: status === 'complete' ? '#10b981' : 'hsl(var(--muted))',
                              color: status === 'complete' ? '#fff' : 'hsl(var(--muted-foreground))'
                            }}
                          >
                            {status === 'complete' ? (
                              <CheckCircle2 className="w-4 h-4" />
                            ) : (
                              <span>{i + 1}</span>
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className={`font-semibold ${status === 'complete' ? 'text-foreground' : 'text-muted-foreground'}`}>
                                {step.label}
                              </span>
                              <code className="text-xs px-2 py-0.5 rounded font-mono bg-muted text-muted-foreground">
                                {step.script}
                              </code>
                              {status === 'complete' && (
                                <span className="text-xs text-emerald-500">done</span>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground">{step.description}</p>
                          </div>
                          <ChevronRight className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                        </div>
                      ) : (
                        <>
                          {/* Expanded view for running step only */}
                          <div className="flex items-center gap-4 px-5 py-3">
                            <div
                              className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                              style={{ background: '#3b82f6', color: '#fff' }}
                            >
                              <Loader2 className="w-4 h-4 animate-spin" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-3 flex-wrap">
                                <span className="font-semibold text-foreground">{step.label}</span>
                                <code className="text-xs px-2 py-0.5 rounded font-mono bg-muted text-muted-foreground">
                                  {step.script}
                                </code>
                                <span className="text-xs text-primary">running...</span>
                              </div>
                              <p className="text-xs mt-0.5 text-muted-foreground">{step.description}</p>
                            </div>
                          </div>

                          {visibleLogs[i].length > 0 && (
                            <div
                              ref={(el) => { logRefs.current[i] = el }}
                              className="border-t border-border/30 px-5 py-3 font-mono text-xs overflow-y-auto bg-card/50"
                              style={{ maxHeight: '180px' }}
                            >
                              {visibleLogs[i].map((line, j) => (
                                <div
                                  key={j}
                                  className="leading-relaxed"
                                  style={{
                                    color: line.startsWith('[DONE]') ? '#10b981'
                                      : line.includes('CRITICAL') ? '#ef4444'
                                      : line.includes('WARNING') ? '#f59e0b'
                                      : line.startsWith('---') ? 'hsl(var(--border))'
                                      : line.startsWith('  ') ? 'hsl(var(--muted-foreground))'
                                      : 'hsl(var(--muted-foreground))',
                                  }}
                                >
                                  {line.startsWith('[DONE]') ? '' : '> '}{line}
                                </div>
                              ))}
                              <span className="text-primary animate-pulse">|</span>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Executive Summary - shows after pipeline completes */}
          {done && !redirecting && (
            <div ref={summaryRef} className="space-y-8 pt-8 border-t border-border">
              {/* Big summary header */}
              <div className="text-center space-y-2">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/30">
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                  <span className="text-emerald-500 font-medium">Analysis Complete</span>
                </div>
                <h2 className="text-3xl font-bold text-foreground">Executive Summary</h2>
                <p className="text-muted-foreground">Portfolio health overview for CFO review</p>
              </div>

              {/* Big metrics cards - Row 1: Portfolio Value, Erosion, Exposure, Recoverable */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="rounded-2xl border border-primary/30 bg-primary/5 p-6 text-center">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-3">
                    <DollarSign className="w-6 h-6 text-primary" />
                  </div>
                  <div className="text-4xl font-bold text-foreground">{formatCurrency(PORTFOLIO_SUMMARY.totalValue)}</div>
                  <div className="text-sm text-muted-foreground mt-1">Portfolio Value</div>
                </div>

                <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-6 text-center">
                  <div className="w-12 h-12 rounded-xl bg-destructive/10 flex items-center justify-center mx-auto mb-3">
                    <TrendingDown className="w-6 h-6 text-destructive" />
                  </div>
                  <div className="text-4xl font-bold text-destructive">-{formatPercent(avgMarginErosion)}</div>
                  <div className="text-sm text-muted-foreground mt-1">Avg Margin Erosion</div>
                </div>

                <div className="rounded-2xl border border-orange-500/30 bg-orange-500/5 p-6 text-center">
                  <div className="w-12 h-12 rounded-xl bg-orange-500/10 flex items-center justify-center mx-auto mb-3">
                    <AlertTriangle className="w-6 h-6 text-orange-500" />
                  </div>
                  <div className="text-4xl font-bold text-orange-500">{formatCurrency(totalOverrun)}</div>
                  <div className="text-sm text-muted-foreground mt-1">Total Exposure</div>
                </div>

                <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-6 text-center">
                  <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center mx-auto mb-3">
                    <DollarSign className="w-6 h-6 text-emerald-500" />
                  </div>
                  <div className="text-4xl font-bold text-emerald-500">{formatCurrency(totalRecovery)}</div>
                  <div className="text-sm text-muted-foreground mt-1">Recoverable Amount</div>
                </div>
              </div>

              {/* Row 2: Projects Analyzed and Flagged Projects (with severity breakdown inside) */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="rounded-xl border border-border bg-card p-5">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <Building2 className="w-6 h-6 text-primary" />
                    </div>
                    <div>
                      <div className="text-3xl font-bold text-foreground">{PORTFOLIO_SUMMARY.totalProjects}</div>
                      <div className="text-sm text-muted-foreground">Projects Analyzed</div>
                    </div>
                  </div>
                </div>

                <div className="rounded-xl border border-border bg-card p-5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-muted flex items-center justify-center flex-shrink-0">
                        <AlertCircle className="w-6 h-6 text-muted-foreground" />
                      </div>
                      <div>
                        <div className="text-3xl font-bold text-foreground">{MOCK_PROJECTS.length}</div>
                        <div className="text-sm text-muted-foreground">Flagged Projects</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border-2 border-[#ef4444]/40 bg-[#ef4444]/10">
                        <span className="text-lg font-bold text-[#ef4444]">{criticalProjects.length}</span>
                        <span className="text-xs text-[#ef4444]">Critical</span>
                      </div>
                      <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border-2 border-[#f97316]/40 bg-[#f97316]/10">
                        <span className="text-lg font-bold text-[#f97316]">{warningProjects.length}</span>
                        <span className="text-xs text-[#f97316]">Elevated</span>
                      </div>
                      <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border-2 border-[#eab308]/40 bg-[#eab308]/10">
                        <span className="text-lg font-bold text-[#eab308]">{watchProjects.length}</span>
                        <span className="text-xs text-[#eab308]">Monitor</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* General Recommendations Section */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xl font-bold text-foreground">General Recommendations</h3>
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary/10 border border-primary/30">
                    <Zap className="w-4 h-4 text-primary" />
                    <span className="text-sm font-medium text-primary">AI-Powered Insights</span>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {/* Supply Chain / Logistics Issue */}
                  <div className="rounded-xl border border-orange-500/30 bg-orange-500/5 p-5">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center flex-shrink-0">
                        <Truck className="w-5 h-5 text-orange-500" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-foreground">Supply Chain & Delivery Issues</h4>
                        <p className="text-sm text-muted-foreground mt-1">
                          <span className="font-semibold text-orange-500">5 of 8 flagged projects</span> (Riverside Medical, Greenfield Office, Harbor Logistics, Tech Campus, Municipal Library) share this root cause pattern.
                        </p>
                        <div className="mt-3 p-3 rounded-lg bg-background/50 border border-border">
                          <p className="text-sm font-medium text-foreground">Recommended Action:</p>
                          <p className="text-sm text-muted-foreground mt-1">
                            Schedule a meeting with the logistics and procurement team to review supplier contracts, delivery SLAs, and implement better tracking mechanisms. Consider centralizing vendor management.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Coordination / Management Issue */}
                  <div className="rounded-xl border border-primary/30 bg-primary/5 p-5">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
                        <Users className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-foreground">GC Coordination Failures</h4>
                        <p className="text-sm text-muted-foreground mt-1">
                          <span className="font-semibold text-primary">4 of 8 flagged projects</span> (Lakeview Schools, Sunset Senior, Downtown Hotel, Harbor Logistics) show GC coordination issues causing rework.
                        </p>
                        <div className="mt-3 p-3 rounded-lg bg-background/50 border border-border">
                          <p className="text-sm font-medium text-foreground">Recommended Action:</p>
                          <p className="text-sm text-muted-foreground mt-1">
                            Implement weekly coordination meetings with GCs on all active projects. Consider adding contract clauses for coordination accountability and penalties.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* LLM Analysis Output */}
                <div className="rounded-xl border border-border bg-card p-5">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Zap className="w-4 h-4 text-primary" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-foreground">AI Analysis Summary</h4>
                      <p className="text-xs text-muted-foreground">Generated by Claude based on portfolio data</p>
                    </div>
                  </div>
                  <div className="rounded-lg bg-muted/30 border border-border p-4 font-mono text-sm text-foreground leading-relaxed overflow-auto max-h-80">
                    <div className="prose prose-sm prose-invert max-w-none">
                      <p className="font-semibold text-primary mb-3">Portfolio Risk Assessment</p>
                      <p className="mb-3">After analyzing 47 projects totaling $62.8M in contract value, I identified <strong>8 projects with significant margin erosion</strong> requiring immediate attention.</p>
                      
                      <p className="font-semibold text-orange-500 mb-2">Key Findings:</p>
                      <ul className="list-disc pl-5 mb-3 space-y-1">
                        <li><strong>Primary Risk Pattern:</strong> Supply chain disruptions affecting 5 projects with combined exposure of $1.2M</li>
                        <li><strong>Secondary Pattern:</strong> GC coordination failures on 4 projects causing $680K in rework costs</li>
                        <li><strong>Billing Gap Alert:</strong> 3 projects show 15%+ gap between work completed and amounts billed</li>
                        <li><strong>Overtime Exposure:</strong> 6 projects exceeding budgeted OT by 40%+ average</li>
                      </ul>
                      
                      <p className="font-semibold text-emerald-500 mb-2">Recovery Opportunities:</p>
                      <ul className="list-disc pl-5 mb-3 space-y-1">
                        <li><strong>Change Order Claims:</strong> $2.1M in documented but unbilled change orders across 6 projects</li>
                        <li><strong>Billing Acceleration:</strong> $1.8M recoverable through immediate billing of completed work</li>
                        <li><strong>Contract Renegotiation:</strong> $1.0M potential through escalation clause enforcement</li>
                      </ul>
                      
                      <p className="font-semibold text-destructive mb-2">Immediate Actions Required:</p>
                      <ol className="list-decimal pl-5 space-y-1">
                        <li>Schedule CFO review meeting for Riverside Medical ($1.02M exposure) - highest priority</li>
                        <li>Initiate change order billing process for Greenfield Office and Lakeview Schools</li>
                        <li>Convene logistics team meeting to address systemic supply chain issues</li>
                        <li>Implement weekly GC coordination calls on all flagged projects</li>
                      </ol>
                    </div>
                  </div>
                </div>
              </div>

              {/* Company Performance Metrics with Time Filter */}
              <div className="space-y-6">
                <div className="flex items-center justify-between flex-wrap gap-4">
                  <div>
                    <h3 className="text-xl font-bold text-foreground">Company Performance Metrics</h3>
                    <p className="text-sm text-muted-foreground">Track overall financial health and KPIs over time</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Calendar className="w-4 h-4 text-muted-foreground" />
                    <div className="flex items-center gap-2 bg-muted/50 rounded-lg p-1">
                      {TIME_RANGES.filter(r => r.id !== 'custom').map((range) => (
                        <button
                          key={range.id}
                          onClick={() => setSelectedTimeRange(range.id)}
                          className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                            selectedTimeRange === range.id
                              ? 'bg-primary text-primary-foreground shadow-sm'
                              : 'text-muted-foreground hover:text-foreground'
                          }`}
                        >
                          {range.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Intuitive Time Range Slider */}
                <div className="rounded-xl border border-border bg-card p-5">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-sm font-medium text-foreground">Drag to adjust date range</span>
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-muted">
                      <span className="text-sm font-medium text-foreground">{customStartDate || 'Jan 2024'}</span>
                      <span className="text-muted-foreground">—</span>
                      <span className="text-sm font-medium text-foreground">{customEndDate || 'Dec 2025'}</span>
                    </div>
                  </div>
                  
                  <div className="relative h-12 select-none">
                    {/* Track background */}
                    <div className="absolute top-1/2 -translate-y-1/2 left-0 right-0 h-2 rounded-full bg-muted" />
                    
                    {/* Active range highlight */}
                    <div 
                      className="absolute top-1/2 -translate-y-1/2 h-2 rounded-full bg-primary"
                      style={{ 
                        left: `${((sliderStart || 0) / 24) * 100}%`, 
                        right: `${100 - ((sliderEnd || 24) / 24) * 100}%` 
                      }}
                    />
                    
                    {/* Month markers */}
                    {[0, 6, 12, 18, 24].map((month) => (
                      <div 
                        key={month}
                        className="absolute top-1/2 -translate-y-1/2 w-1 h-4 bg-border rounded-full"
                        style={{ left: `${(month / 24) * 100}%`, transform: 'translate(-50%, -50%)' }}
                      />
                    ))}
                    
                    {/* Start handle */}
                    <input
                      type="range"
                      min="0"
                      max="24"
                      value={sliderStart || 0}
                      onChange={(e) => {
                        const val = parseInt(e.target.value)
                        if (val < (sliderEnd || 24)) {
                          setSliderStart(val)
                          const months = ['Jan 2024', 'Feb 2024', 'Mar 2024', 'Apr 2024', 'May 2024', 'Jun 2024', 
                                         'Jul 2024', 'Aug 2024', 'Sep 2024', 'Oct 2024', 'Nov 2024', 'Dec 2024',
                                         'Jan 2025', 'Feb 2025', 'Mar 2025', 'Apr 2025', 'May 2025', 'Jun 2025',
                                         'Jul 2025', 'Aug 2025', 'Sep 2025', 'Oct 2025', 'Nov 2025', 'Dec 2025']
                          setCustomStartDate(months[val])
                        }
                      }}
                      className="absolute top-0 left-0 w-full h-full opacity-0 cursor-grab active:cursor-grabbing z-20 pointer-events-auto"
                      style={{ 
                        clipPath: `inset(0 ${100 - ((sliderStart || 0) / 24) * 100 - 10}% 0 0)` 
                      }}
                    />
                    
                    {/* End handle */}
                    <input
                      type="range"
                      min="0"
                      max="24"
                      value={sliderEnd || 24}
                      onChange={(e) => {
                        const val = parseInt(e.target.value)
                        if (val > (sliderStart || 0)) {
                          setSliderEnd(val)
                          const months = ['Jan 2024', 'Feb 2024', 'Mar 2024', 'Apr 2024', 'May 2024', 'Jun 2024', 
                                         'Jul 2024', 'Aug 2024', 'Sep 2024', 'Oct 2024', 'Nov 2024', 'Dec 2024',
                                         'Jan 2025', 'Feb 2025', 'Mar 2025', 'Apr 2025', 'May 2025', 'Jun 2025',
                                         'Jul 2025', 'Aug 2025', 'Sep 2025', 'Oct 2025', 'Nov 2025', 'Dec 2025']
                          setCustomEndDate(months[val])
                        }
                      }}
                      className="absolute top-0 left-0 w-full h-full opacity-0 cursor-grab active:cursor-grabbing z-10 pointer-events-auto"
                      style={{ 
                        clipPath: `inset(0 0 0 ${((sliderEnd || 24) / 24) * 100 - 10}%)` 
                      }}
                    />
                    
                    {/* Visible drag handles */}
                    <div 
                      className="absolute top-1/2 -translate-y-1/2 w-5 h-5 rounded-full bg-primary border-2 border-background shadow-lg cursor-grab active:cursor-grabbing active:scale-110 transition-transform z-30 pointer-events-none"
                      style={{ left: `calc(${((sliderStart || 0) / 24) * 100}% - 10px)` }}
                    >
                      <div className="absolute inset-1 rounded-full bg-background" />
                    </div>
                    <div 
                      className="absolute top-1/2 -translate-y-1/2 w-5 h-5 rounded-full bg-primary border-2 border-background shadow-lg cursor-grab active:cursor-grabbing active:scale-110 transition-transform z-30 pointer-events-none"
                      style={{ left: `calc(${((sliderEnd || 24) / 24) * 100}% - 10px)` }}
                    >
                      <div className="absolute inset-1 rounded-full bg-background" />
                    </div>
                  </div>
                  
                  {/* Timeline labels */}
                  <div className="flex justify-between mt-2 text-xs text-muted-foreground">
                    <span>Jan 2024</span>
                    <span>Jul 2024</span>
                    <span>Jan 2025</span>
                    <span>Jul 2025</span>
                    <span>Dec 2025</span>
                  </div>
                </div>

              </div>

              {/* Biggest problem callout - moved here before projects by severity */}
              <div className="rounded-2xl border-2 border-destructive/30 bg-destructive/5 p-6">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl bg-destructive/20 flex items-center justify-center flex-shrink-0">
                    <AlertCircle className="w-6 h-6 text-destructive" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-foreground">Biggest Issue: {criticalProjects[0]?.name}</h3>
                    <p className="text-muted-foreground mt-1">{criticalProjects[0]?.rootCause}</p>
                    <div className="flex gap-4 mt-3">
                      <div>
                        <span className="text-sm text-muted-foreground">Margin Erosion: </span>
                        <span className="font-bold text-destructive">-{formatPercent(Math.abs(criticalProjects[0]?.marginDelta || 0))}</span>
                      </div>
                      <div>
                        <span className="text-sm text-muted-foreground">Total Overrun: </span>
                        <span className="font-bold text-foreground">{formatCurrency((criticalProjects[0]?.laborOverrun || 0) + (criticalProjects[0]?.materialOverrun || 0))}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Projects by severity */}
              <div className="space-y-6">
                <h3 className="text-xl font-bold text-foreground">Projects by Severity</h3>

                {/* Critical - Red */}
                {criticalProjects.length > 0 && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-red-500" />
                      <h4 className="font-semibold text-red-500">Critical - Immediate Action Required</h4>
                      <span className="text-sm text-muted-foreground">({criticalProjects.length} projects)</span>
                    </div>
                    <div className="space-y-2">
                      {criticalProjects.map(renderProjectRow)}
                    </div>
                  </div>
                )}

                {/* Elevated - Orange */}
                {warningProjects.length > 0 && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-orange-500" />
                      <h4 className="font-semibold text-orange-500">Elevated - Attention This Week</h4>
                      <span className="text-sm text-muted-foreground">({warningProjects.length} projects)</span>
                    </div>
                    <div className="space-y-2">
                      {warningProjects.map(renderProjectRow)}
                    </div>
                  </div>
                )}

                {/* Monitor - Yellow */}
                {watchProjects.length > 0 && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-yellow-500" />
                      <h4 className="font-semibold text-yellow-500">Monitor - Track for Changes</h4>
                      <span className="text-sm text-muted-foreground">({watchProjects.length} projects)</span>
                    </div>
                    <div className="space-y-2">
                      {watchProjects.map(renderProjectRow)}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Investigate Modal */}
      {selectedProject && (
        <InvestigateModal 
          project={selectedProject} 
          onClose={() => setSelectedProject(null)} 
        />
      )}
    </div>
  )
}
