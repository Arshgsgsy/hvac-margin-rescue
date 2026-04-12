'use client'

import { useState, useRef, useCallback, useMemo } from 'react'
import Link from 'next/link'
import {
  CheckCircle2,
  Loader2,
  Terminal,
  ChevronRight,
  Zap,
  Upload,
  AlertTriangle,
  TrendingDown,
  Eye,
  ArrowRight,
} from 'lucide-react'
import { formatCurrency, formatPercent, getSortedByPriority } from '@/lib/data'
import { PortfolioSummary, PipelineStep, Project } from '@/lib/types'
import { uploadFiles, runPipeline } from '@/lib/api'

interface Props {
  portfolio: PortfolioSummary | null
  projects: Project[]
  onPipelineComplete: () => void
}

const SEVERITY_ICON = { critical: AlertTriangle, warning: TrendingDown, watch: Eye }
const SEVERITY_COLOR = { critical: 'text-red-400', warning: 'text-yellow-400', watch: 'text-blue-400' }
const SEVERITY_BADGE = {
  critical: 'bg-red-500/15 text-red-400 border-red-500/30',
  warning: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
  watch: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
}

export function Tab5Pipeline({ portfolio, projects, onPipelineComplete }: Props) {
  const [uploading, setUploading] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<{ name: string; size_bytes: number }[]>([])
  const [running, setRunning] = useState(false)
  const [done, setDone] = useState(false)
  const [steps, setSteps] = useState<PipelineStep[]>([])
  const [expandedStep, setExpandedStep] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const top5 = useMemo(() => getSortedByPriority(projects).slice(0, 5), [projects])

  const handleUpload = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return
    setUploading(true)
    setError(null)
    try {
      const result = await uploadFiles(files)
      setUploadedFiles(result.files)
    } catch (e: any) {
      setError(`Upload failed: ${e.message}`)
    }
    setUploading(false)
  }, [])

  const handleRunPipeline = useCallback(async () => {
    if (running || done) return
    setRunning(true)
    setError(null)
    try {
      const result = await runPipeline()
      setSteps(result.steps)
      setDone(result.status === 'complete')
      if (result.status === 'complete') {
        onPipelineComplete()
      }
      if (result.status === 'error') {
        setError('Pipeline completed with errors. Check step logs.')
      }
    } catch (e: any) {
      setError(`Pipeline failed: ${e.message}`)
    }
    setRunning(false)
  }, [running, done, onPipelineComplete])

  const completedCount = steps.filter(s => s.status === 'complete').length
  const progress = steps.length > 0 ? (completedCount / steps.length) * 100 : 0

  const logColor = (line: string) => {
    if (line.startsWith('[OK]')) return 'text-emerald-400'
    if (line.startsWith('[ERROR]')) return 'text-red-400'
    if (line.startsWith('[TIMEOUT]')) return 'text-red-400'
    return 'text-slate-400'
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Terminal className="w-4 h-4 text-primary" />
            <p className="text-xs font-semibold uppercase tracking-widest text-primary">Backend Pipeline</p>
          </div>
          <p className="text-muted-foreground text-sm max-w-lg">
            Upload CSV data files, then run the 5-step automated pipeline: clean, aggregate, flag, score, and export for LLM analysis.
          </p>
        </div>
      </div>

      {/* File Upload */}
      <div className="rounded-2xl border border-border/50 p-6" style={{ background: 'rgba(255,255,255,0.03)' }}>
        <h3 className="text-foreground font-semibold mb-3 flex items-center gap-2">
          <Upload className="w-4 h-4" /> Upload CSV Data
        </h3>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".csv"
          onChange={e => handleUpload(e.target.files)}
          className="hidden"
        />
        <div className="flex items-center gap-3">
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="px-4 py-2 rounded-xl text-sm font-medium border border-border hover:bg-muted/30 transition-all"
          >
            {uploading ? 'Uploading...' : 'Choose CSV Files'}
          </button>
          {uploadedFiles.length > 0 && (
            <span className="text-emerald-400 text-xs">{uploadedFiles.length} files uploaded</span>
          )}
        </div>
        {uploadedFiles.length > 0 && (
          <div className="mt-3 space-y-1">
            {uploadedFiles.map(f => (
              <div key={f.name} className="text-xs text-muted-foreground flex items-center gap-2">
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                {f.name} ({(f.size_bytes / 1024 / 1024).toFixed(1)}MB)
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Run Pipeline */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleRunPipeline}
          disabled={running || done}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
            done ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 cursor-default'
            : running ? 'bg-primary/10 text-primary border border-primary/30 cursor-not-allowed'
            : 'bg-primary text-white hover:bg-primary/90 shadow-lg shadow-primary/20 cursor-pointer'
          }`}
        >
          {done ? (
            <><CheckCircle2 className="w-4 h-4" /> Complete</>
          ) : running ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> Running...</>
          ) : (
            <><Zap className="w-4 h-4" /> Run Pipeline</>
          )}
        </button>
        {error && <span className="text-red-400 text-xs">{error}</span>}
      </div>

      {/* Progress bar */}
      {steps.length > 0 && (
        <div>
          <div className="flex justify-between text-xs text-muted-foreground mb-1.5">
            <span>Pipeline progress</span>
            <span>{completedCount} / {steps.length} steps complete</span>
          </div>
          <div className="h-1.5 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{ width: `${progress}%`, background: 'linear-gradient(90deg, hsl(var(--primary-dark)), hsl(var(--primary)), hsl(var(--primary-light)))' }}
            />
          </div>
        </div>
      )}

      {/* Steps */}
      {steps.length > 0 && (
        <div className="space-y-2">
          {steps.map((step, i) => {
            const isExpanded = expandedStep === i
            const hasLogs = step.logs.length > 0

            return (
              <div
                key={step.id}
                className={`rounded-2xl border overflow-hidden transition-all duration-300 ${
                  step.status === 'complete' ? 'border-emerald-500/30'
                  : step.status === 'error' ? 'border-red-500/30'
                  : 'border-border/50'
                }`}
                style={{
                  background: step.status === 'complete' ? 'rgba(16,185,129,0.04)'
                    : step.status === 'error' ? 'rgba(239,68,68,0.06)'
                    : 'rgba(255,255,255,0.02)',
                }}
              >
                <button
                  className="w-full flex items-center gap-4 px-5 py-4 text-left"
                  onClick={() => hasLogs && setExpandedStep(isExpanded ? null : i)}
                >
                  <div className="shrink-0 w-8 h-8 rounded-full flex items-center justify-center">
                    {step.status === 'complete' ? (
                      <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                    ) : step.status === 'error' ? (
                      <span className="w-6 h-6 rounded-full bg-red-500/20 flex items-center justify-center text-red-400 text-xs font-bold">!</span>
                    ) : (
                      <div className="w-6 h-6 rounded-full border-2 border-border flex items-center justify-center">
                        <span className="text-muted-foreground text-xs font-bold">{i + 1}</span>
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`font-semibold text-sm ${step.status === 'idle' ? 'text-muted-foreground' : 'text-foreground'}`}>
                        {step.label}
                      </span>
                      {step.status === 'complete' && step.duration !== undefined && (
                        <span className="text-xs text-emerald-400">{step.duration}s</span>
                      )}
                      {step.status === 'error' && (
                        <span className="text-xs text-red-400">failed</span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">{step.description}</p>
                  </div>
                  {hasLogs && (
                    <ChevronRight className={`w-4 h-4 text-muted-foreground shrink-0 transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}`} />
                  )}
                </button>

                {isExpanded && hasLogs && (
                  <div className="border-t border-border/30 px-5 py-3 font-mono text-xs overflow-y-auto" style={{ background: 'rgba(0,0,0,0.4)', maxHeight: 200 }}>
                    {step.logs.map((line, j) => (
                      <div key={j} className={`leading-relaxed ${logColor(line)}`}>
                        <span className="text-border mr-1">{'>'}</span>
                        {line}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Results summary */}
      {done && portfolio && (
        <div className="space-y-4">
          <div className="rounded-2xl border border-emerald-500/30 p-6" style={{ background: 'rgba(16,185,129,0.05)' }}>
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <h3 className="text-foreground font-semibold">Pipeline Complete — Results Ready</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {(() => {
                // Calculate actual recovery opportunity from project data
                const totalRecovery = projects.reduce((sum, p) => {
                  const projectRecovery = p.total_recoverable_estimate ??
                    (p.recovery_actions?.reduce((s, a) => s + a.amount, 0) ?? 0)
                  return sum + projectRecovery
                }, 0)
                return [
                  { label: 'Projects Scanned', value: `${portfolio.total_projects}` },
                  { label: 'Flagged', value: `${portfolio.flagged_count}` },
                  { label: 'Critical', value: `${portfolio.critical_count}`, alert: true },
                  { label: 'Recovery Opportunity', value: formatCurrency(totalRecovery > 0 ? totalRecovery : portfolio.total_exposure * 0.3), alert: true },
                ]
              })().map(s => (
                <div key={s.label} className="rounded-xl bg-black/20 border border-border/30 px-4 py-3">
                  <p className="text-muted-foreground text-xs mb-1">{s.label}</p>
                  <p className={`text-xl font-bold ${s.alert ? 'text-emerald-400' : 'text-foreground'}`}>{s.value}</p>
                </div>
              ))}
            </div>
            <p className="text-muted-foreground text-xs mt-4">
              Switch to the <span className="text-foreground font-medium">Executive Portfolio View</span> tab to explore findings.
            </p>
          </div>

          {top5.length > 0 && (
            <div className="rounded-2xl border border-border/50 overflow-hidden" style={{ background: 'rgba(255,255,255,0.02)' }}>
              <div className="px-5 py-4 border-b border-border/50 flex items-center justify-between">
                <div>
                  <h3 className="text-foreground font-semibold">Immediate Action Required</h3>
                  <p className="text-muted-foreground text-xs mt-0.5">Top 5 projects ranked by margin erosion severity — investigate these first</p>
                </div>
                <span className="text-xs text-muted-foreground">sorted by priority score</span>
              </div>

              <div className="divide-y divide-border/30">
                {top5.map((project, i) => {
                  const Icon = SEVERITY_ICON[project.severity]
                  const erosion = Math.abs(project.margin_delta) * 100
                  const recovery = project.recovery_actions?.reduce((s, a) => s + a.amount, 0) ?? 0
                  return (
                    <div key={project.id} className={`flex items-center gap-4 px-5 py-4 hover:bg-muted/10 transition-colors ${project.severity === 'critical' ? 'bg-red-500/5' : ''}`}>
                      <div className="w-7 h-7 rounded-full bg-muted flex items-center justify-center shrink-0">
                        <span className="text-xs font-bold text-muted-foreground">#{i + 1}</span>
                      </div>

                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${project.severity === 'critical' ? 'bg-red-500/10' : project.severity === 'warning' ? 'bg-yellow-500/10' : 'bg-blue-500/10'}`}>
                        <Icon className={`w-4 h-4 ${SEVERITY_COLOR[project.severity]}`} />
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="text-foreground text-sm font-semibold truncate">{project.name}</p>
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${SEVERITY_BADGE[project.severity]}`}>
                            {project.severity}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 mt-1 flex-wrap">
                          <span className="text-muted-foreground text-xs">{project.sector}</span>
                          <span className="text-muted-foreground text-xs">{formatCurrency(project.contract_value)}</span>
                          <span className="text-red-400 text-xs font-medium">-{erosion.toFixed(1)} pts margin erosion</span>
                          <span className="text-xs text-muted-foreground">
                            Bid <span className="text-foreground">{formatPercent(project.bid_margin)}</span>
                            {' → '}
                            Realized <span className="text-red-400">{formatPercent(project.realized_margin)}</span>
                          </span>
                        </div>
                        <div className="mt-2 h-1 rounded-full bg-muted overflow-hidden w-48">
                          <div className="h-full rounded-full bg-gradient-to-r from-red-500 to-orange-400" style={{ width: `${Math.min(erosion * 5, 100)}%` }} />
                        </div>
                      </div>

                      <div className="text-right shrink-0">
                        {recovery > 0 && (
                          <p className="text-emerald-400 text-sm font-bold">{formatCurrency(recovery)}</p>
                        )}
                        <p className="text-muted-foreground text-xs mb-2">recovery potential</p>
                        <Link
                          href={`/projects/${project.id}`}
                          className="inline-flex items-center gap-1 text-xs text-primary font-medium hover:gap-2 transition-all"
                        >
                          Investigate <ArrowRight className="w-3 h-3" />
                        </Link>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
