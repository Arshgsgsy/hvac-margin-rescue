'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { Upload, FileArchive, CheckCircle2, X, ArrowRight, Shield, BarChart3, Zap, FileSpreadsheet, Loader2, ChevronRight } from 'lucide-react'

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
    id: 'clean',
    label: 'Data Cleaning',
    script: '01_clean.py',
    description: 'Normalize dates, map role name variants, standardize labor log fields',
    duration: 3200,
    logs: [
      'Loading source CSVs from hvac_data/...',
      'Parsing labor_logs_all.csv (1,247,832 rows)...',
      'Parsing contracts_all.csv (312 rows)...',
      'Parsing billing_history_all.csv (8,941 rows)...',
      'Parsing change_orders_all.csv (2,204 rows)...',
      'Parsing rfis_all.csv (1,876 rows)...',
      'Parsing field_notes_all.csv (4,312 rows)...',
      'Normalizing date formats: found 7 format variants...',
      'Mapping role name variants via role_mapping.json...',
      '  Resolved 23 variants to 8 canonical roles',
      'Flagging overtime rows (hours > 8): 184,211 rows',
      'Computing burden multiplier per role...',
      'Calculating effective hourly cost per row...',
      'Writing cleaned_labor_logs.parquet...',
      '[DONE] 1,247,832 rows cleaned in 3.1s',
    ],
  },
  {
    id: 'load',
    label: 'Load to DuckDB',
    script: '02_load_duckdb.py',
    description: 'Load all cleaned data into DuckDB, build pre-aggregated project-level tables',
    duration: 2800,
    logs: [
      'Initializing DuckDB (in-memory + persist mode)...',
      'Creating schema: labor_logs, contracts, billing, change_orders, rfis...',
      'Loading cleaned_labor_logs.parquet -> labor_logs table...',
      'Loading contracts_all.csv -> contracts table...',
      'Loading billing_history_all.csv -> billing_history table...',
      'Loading change_orders_all.csv -> change_orders table...',
      'Loading sov_all.csv -> sov table...',
      'Running aggregation: project-level labor cost sums...',
      'Running aggregation: material cost by project...',
      'Running aggregation: billing totals by project...',
      'Building project_summary materialized view...',
      '[DONE] All tables loaded, 6 views created in 2.6s',
    ],
  },
  {
    id: 'flag',
    label: 'Portfolio Scan',
    script: '03_flag_projects.py',
    description: 'Compute variances, identify margin erosion, rank by severity',
    duration: 2200,
    logs: [
      'Computing per-project cost actuals...',
      'Formula: Labor Cost = (hours_st + hours_ot x 1.5) x hourly_rate x burden_multiplier',
      'Joining actuals to contract budgets...',
      'Computing variance: actual_cost - budget_cost per project...',
      'Computing billing gap: pct_complete - pct_billed...',
      'Computing realized margin: (contract_value - actual_cost) / contract_value...',
      'Flagging projects where realized_margin < bid_margin - 0.05...',
      '-------------------------------------------',
      '  CRITICAL (margin erosion > 8%): 4 projects',
      '  WARNING  (margin erosion 5-8%): 3 projects',
      '  WATCH    (margin erosion 3-5%): 1 project',
      '  Total flagged: 8 / 47 projects',
      '  Total exposure: $1.62M in overruns',
      '-------------------------------------------',
      'Ranking projects by severity score...',
      '[DONE] Portfolio scan complete in 2.1s',
    ],
  },
  {
    id: 'export',
    label: 'Export JSON',
    script: '04_export.py',
    description: 'Export portfolio summary and per-project detail to JSON for the frontend',
    duration: 1400,
    logs: [
      'Serializing portfolio_summary.json...',
      '  totalProjects: 47, totalValue: $62.8M',
      '  avgBidMargin: 13.8%, avgRealizedMargin: 9.4%',
      'Serializing flagged_projects.json (8 records)...',
      'Creating output/project_details/ directory...',
      'Exporting PRJ-2021-260.json...',
      'Exporting PRJ-2022-118.json...',
      'Exporting PRJ-2022-309.json...',
      'Exporting PRJ-2023-044.json...',
      'Exporting PRJ-2023-187.json...',
      'Exporting PRJ-2023-291.json...',
      'Exporting PRJ-2024-033.json...',
      'Exporting PRJ-2024-112.json...',
      '[DONE] 10 JSON files written to pipeline/output/',
    ],
  },
  {
    id: 'agent',
    label: 'LLM Root Cause Analysis',
    script: '05_extract_text.py + Claude',
    description: 'Send each flagged project to Claude for root cause analysis and recovery recommendations',
    duration: 8500,
    logs: [
      'Loading flagged projects from pipeline/output/...',
      'Building context bundles (cost data + field notes + COs + RFIs)...',
      'Sending PRJ-2021-260 to Claude Haiku...',
      '  [Riverside Medical] Root cause identified: BMS coordination + undocumented COs',
      '  Recovery potential: $1.02M',
      'Sending PRJ-2022-118 to Claude Haiku...',
      '  [Greenfield Office] Root cause identified: Supply chain delay + GC rework',
      '  Recovery potential: $1.32M',
      'Sending PRJ-2022-309 to Claude Haiku...',
      '  [Lakeview Schools] Root cause identified: Underbid OT + asbestos delays',
      '  Recovery potential: $765K',
      'Sending PRJ-2023-044 to Claude Haiku...',
      '  [Harbor Logistics] Root cause identified: GC coordination failures',
      '  Recovery potential: $295K',
      'Sending PRJ-2023-187 to Claude Haiku...',
      '  [Sunset Senior] Root cause identified: Design revisions at 60% complete',
      '  Recovery potential: $717K',
      'Sending PRJ-2023-291 to Claude Haiku...',
      '  [Downtown Hotel] Root cause identified: Occupied building constraints',
      '  Recovery potential: $330K',
      'Sending PRJ-2024-033 to Claude Haiku...',
      '  [Tech Campus] Root cause identified: Unscoped IT coordination overhead',
      '  Recovery potential: $327K',
      'Sending PRJ-2024-112 to Claude Haiku...',
      '  [Municipal Library] Root cause identified: Prevailing wage audit gap',
      '  Recovery potential: $148K',
      '-------------------------------------------',
      '  Total recoverable: ~$4.92M across 8 projects',
      '  Analysis complete. Dashboard ready.',
      '-------------------------------------------',
      '[DONE] All 8 projects analyzed in 8.3s',
    ],
  },
]

type StepStatus = 'idle' | 'running' | 'complete'

interface UploadPageProps {
  onComplete: () => void
}

export function UploadPage({ onComplete }: UploadPageProps) {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadComplete, setUploadComplete] = useState(false)
  const [pipelineStarted, setPipelineStarted] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  // Pipeline state
  const [statuses, setStatuses] = useState<StepStatus[]>(STEPS.map(() => 'idle'))
  const [visibleLogs, setVisibleLogs] = useState<string[][]>(STEPS.map(() => []))
  const [running, setRunning] = useState(false)
  const [done, setDone] = useState(false)
  const logRefs = useRef<(HTMLDivElement | null)[]>([])
  const runningRef = useRef(false)

  useEffect(() => { return () => { runningRef.current = false } }, [])

  const runPipeline = async () => {
    if (running || done) return
    setPipelineStarted(true)
    setRunning(true)
    runningRef.current = true

    for (let i = 0; i < STEPS.length; i++) {
      if (!runningRef.current) break
      const step = STEPS[i]
      setStatuses((prev) => { const n = [...prev]; n[i] = 'running'; return n })

      const delay = step.duration / step.logs.length
      for (let j = 0; j < step.logs.length; j++) {
        if (!runningRef.current) break
        await new Promise((r) => setTimeout(r, delay))
        setVisibleLogs((prev) => {
          const n = prev.map((l) => [...l])
          n[i] = step.logs.slice(0, j + 1)
          return n
        })
        const el = logRefs.current[i]
        if (el) el.scrollTop = el.scrollHeight
      }

      await new Promise((r) => setTimeout(r, 150))
      setStatuses((prev) => { const n = [...prev]; n[i] = 'complete'; return n })
    }

    setRunning(false)
    setDone(true)
    setTimeout(onComplete, 1000)
  }

  const handleFiles = useCallback((fileList: FileList | null) => {
    if (!fileList) return
    
    const newFiles: UploadedFile[] = []
    for (let i = 0; i < fileList.length; i++) {
      const file = fileList[i]
      if (file.name.endsWith('.zip') || file.name.endsWith('.csv') || file.name.endsWith('.xlsx') || file.name.endsWith('.json')) {
        newFiles.push({
          name: file.name,
          size: file.size,
          type: file.type || 'application/zip'
        })
      }
    }
    
    if (newFiles.length > 0) {
      setIsUploading(true)
      setTimeout(() => {
        setFiles(prev => [...prev, ...newFiles])
        setIsUploading(false)
        setUploadComplete(true)
      }, 1500)
    }
  }, [])

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
    setFiles(prev => prev.filter((_, i) => i !== index))
    if (files.length === 1) {
      setUploadComplete(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const statusColor = (s: StepStatus) =>
    s === 'complete' ? '#10b981' : s === 'running' ? '#3b82f6' : '#334155'

  const completedCount = statuses.filter((s) => s === 'complete').length

  // If pipeline started, show pipeline view
  if (pipelineStarted) {
    return (
      <div className="min-h-screen bg-background text-foreground flex flex-col">
        {/* Header */}
        <header className="border-b border-border/50 bg-background/80 backdrop-blur-sm">
          <div className="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-primary/20 flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h1 className="text-foreground font-bold text-lg">MarginIQ</h1>
                <p className="text-muted-foreground text-xs">Processing your data...</p>
              </div>
            </div>
          </div>
        </header>

        {/* Pipeline content */}
        <main className="flex-1 p-6">
          <div className="max-w-4xl mx-auto space-y-6">
            <div>
              <h2 className="text-foreground text-xl font-semibold">Analyzing Financial Data</h2>
              <p className="text-sm mt-1 text-muted-foreground">
                5-step data pipeline: clean data, load DuckDB, scan portfolio, export JSON, LLM analysis
              </p>
            </div>

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

            {done && (
              <div className="rounded-xl p-4 border text-center bg-emerald-500/10 border-emerald-500/30">
                <p className="text-sm font-semibold text-emerald-500">
                  Pipeline complete. Loading dashboard...
                </p>
              </div>
            )}
          </div>
        </main>
      </div>
    )
  }

  // Upload view
  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Header */}
      <header className="border-b border-border/50 bg-background/80 backdrop-blur-sm">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-primary/20 flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h1 className="text-foreground font-bold text-lg">MarginIQ</h1>
              <p className="text-muted-foreground text-xs">Financial Intelligence Platform</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-3xl">
          {/* Title section */}
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-foreground mb-3">
              Upload Your Financial Data
            </h2>
            <p className="text-muted-foreground text-lg max-w-xl mx-auto">
              Upload a ZIP file containing your company&apos;s financial records. Our AI will analyze margins, detect risks, and identify recovery opportunities.
            </p>
          </div>

          {/* Upload zone */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => inputRef.current?.click()}
            className={`
              relative rounded-2xl border-2 border-dashed p-12 text-center cursor-pointer
              transition-all duration-300
              ${isDragging 
                ? 'border-primary bg-primary/10 scale-[1.02]' 
                : uploadComplete 
                  ? 'border-emerald-500/50 bg-emerald-500/5' 
                  : 'border-border hover:border-primary/50 hover:bg-muted/30'
              }
            `}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".zip,.csv,.xlsx,.json"
              multiple
              onChange={(e) => handleFiles(e.target.files)}
              className="hidden"
            />

            {isUploading ? (
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-primary/20 flex items-center justify-center animate-pulse">
                  <Upload className="w-8 h-8 text-primary" />
                </div>
                <p className="text-foreground font-semibold">Processing files...</p>
                <div className="w-48 h-1.5 rounded-full bg-muted overflow-hidden">
                  <div className="h-full bg-primary rounded-full animate-[loading_1.5s_ease-in-out_infinite]" style={{ width: '60%' }} />
                </div>
              </div>
            ) : uploadComplete && files.length > 0 ? (
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 flex items-center justify-center">
                  <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                </div>
                <div>
                  <p className="text-foreground font-semibold text-lg">Files Ready</p>
                  <p className="text-muted-foreground text-sm mt-1">
                    {files.length} file{files.length > 1 ? 's' : ''} uploaded successfully
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center">
                  <FileArchive className="w-8 h-8 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-foreground font-semibold text-lg">
                    Drop your ZIP file here
                  </p>
                  <p className="text-muted-foreground text-sm mt-1">
                    or click to browse
                  </p>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <FileSpreadsheet className="w-3.5 h-3.5" />
                  <span>Supports: ZIP, CSV, XLSX, JSON</span>
                </div>
              </div>
            )}
          </div>

          {/* Uploaded files list */}
          {files.length > 0 && (
            <div className="mt-6 space-y-2">
              {files.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between px-4 py-3 rounded-xl bg-card border border-border/50"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <FileArchive className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <p className="text-foreground text-sm font-medium">{file.name}</p>
                      <p className="text-muted-foreground text-xs">{formatFileSize(file.size)}</p>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      removeFile(index)
                    }}
                    className="p-1.5 rounded-lg hover:bg-muted transition-colors"
                  >
                    <X className="w-4 h-4 text-muted-foreground" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Analyze button - runs pipeline automatically */}
          <div className="mt-8 flex justify-center">
            <button
              onClick={runPipeline}
              disabled={files.length === 0}
              className={`
                flex items-center gap-2 px-8 py-3.5 rounded-xl text-sm font-semibold
                transition-all duration-200
                ${files.length > 0
                  ? 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-lg shadow-primary/25'
                  : 'bg-muted text-muted-foreground cursor-not-allowed'
                }
              `}
            >
              <Zap className="w-4 h-4" />
              Analyze Financial Data
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Features */}
          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              {
                icon: BarChart3,
                title: 'Margin Analysis',
                description: 'Identify margin erosion across your entire portfolio'
              },
              {
                icon: Zap,
                title: 'AI Root Cause',
                description: 'Claude AI identifies why costs exceeded budgets'
              },
              {
                icon: Shield,
                title: 'Recovery Actions',
                description: 'Get dollar-quantified recommendations to recover losses'
              }
            ].map((feature) => (
              <div
                key={feature.title}
                className="flex items-start gap-3 p-4 rounded-xl bg-card/50 border border-border/30"
              >
                <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                  <feature.icon className="w-4 h-4 text-primary" />
                </div>
                <div>
                  <p className="text-foreground text-sm font-semibold">{feature.title}</p>
                  <p className="text-muted-foreground text-xs mt-0.5">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Security note */}
          <div className="mt-8 flex items-center justify-center gap-2 text-xs text-muted-foreground">
            <Shield className="w-3.5 h-3.5" />
            <span>Your data is processed securely and never stored permanently</span>
          </div>
        </div>
      </main>
    </div>
  )
}
