'use client'

import { useState, useEffect, useRef } from 'react'
import { CheckCircle2, Circle, Loader2, Terminal, ChevronRight, Zap, ArrowRight, AlertTriangle, TrendingDown, Eye } from 'lucide-react'
import { MOCK_PROJECTS, PORTFOLIO_SUMMARY, formatCurrency, formatPercent, getSortedByPriority } from '@/lib/data'
import Link from 'next/link'

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
    description: 'Normalize dates, resolve role name variants, standardize labor log fields across 1.2M rows',
    duration: 3200,
    logs: [
      'Loading source CSVs from hvac_data/...',
      'Parsing labor_logs_all.csv (1,247,832 rows)...',
      'Parsing contracts_all.csv (405 rows)...',
      'Parsing billing_history_all.csv (6,479 rows)...',
      'Parsing change_orders_all.csv (4,255 rows)...',
      'Parsing rfis_all.csv (22,065 rows)...',
      'Parsing field_notes_all.csv (103,676 rows)...',
      'Normalizing date formats: found 7 format variants...',
      'Mapping role name variants via role_mapping.json...',
      '  Resolved 23 variants -> 8 canonical roles',
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
    description: 'Load all cleaned parquet/CSV into DuckDB, build pre-aggregated project-level views',
    duration: 2800,
    logs: [
      'Initializing DuckDB (in-memory + persist mode)...',
      'Creating schema: labor_logs, contracts, billing, change_orders, rfis...',
      'Loading cleaned_labor_logs.parquet -> labor_logs (1.2M rows)...',
      'Loading contracts_all.csv -> contracts (405 rows)...',
      'Loading billing_history_all.csv -> billing_history (6,479 rows)...',
      'Loading change_orders_all.csv -> change_orders (4,255 rows)...',
      'Loading sov_all.csv -> sov (6,075 rows)...',
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
    description: 'Compute variances across all 405 projects, identify margin erosion, rank by severity score',
    duration: 2200,
    logs: [
      'Computing per-project cost actuals...',
      'Formula: Labor = (hours_st + hours_ot x 1.5) x rate x burden',
      'Joining actuals to contract budgets (sov_budget_all)...',
      'Computing variance: actual_cost - budget_cost per project...',
      'Computing billing gap: pct_complete - pct_billed...',
      'Computing realized margin per project...',
      'Flagging projects where realized < bid_margin - 0.05...',
      '-------------------------------------------',
      '  CRITICAL (erosion > 8%):  4 projects',
      '  WARNING  (erosion 5-8%):  3 projects',
      '  WATCH    (erosion 3-5%):  1 project',
      '  Total flagged: 8 / 47 active projects',
      '  Total exposure: $17.7M at risk',
      '-------------------------------------------',
      'Ranking projects by priority score...',
      '[DONE] Portfolio scan complete in 2.1s',
    ],
  },
  {
    id: 'export',
    label: 'Export JSON',
    script: '04_export.py',
    description: 'Serialize portfolio summary and per-project detail bundles for the dashboard',
    duration: 1400,
    logs: [
      'Serializing portfolio_summary.json...',
      '  totalProjects: 47, totalValue: $62.8M',
      '  avgBidMargin: 13.8%, avgRealizedMargin: 9.4%',
      'Serializing flagged_projects.json (8 records)...',
      'Creating output/project_details/ directory...',
      'Exporting PRJ-2021-260.json (Riverside Medical)...',
      'Exporting PRJ-2022-118.json (Greenfield Office Tower)...',
      'Exporting PRJ-2022-334.json (Westside K-12)...',
      'Exporting PRJ-2023-077.json (Harbor Logistics)...',
      'Exporting PRJ-2022-491.json (St. Agnes Hospital)...',
      'Exporting PRJ-2023-155.json (Luxe Hotel Chain)...',
      'Exporting PRJ-2023-288.json (Downtown Mixed-Use)...',
      'Exporting PRJ-2023-401.json (Federal Courthouse)...',
      '[DONE] 10 JSON files written to pipeline/output/',
    ],
  },
  {
    id: 'agent',
    label: 'LLM Root Cause Analysis',
    script: '05_agent.py + Claude Haiku',
    description: 'Send each flagged project context to Claude â€" root cause identification + dollar-quantified recovery actions',
    duration: 8500,
    logs: [
      'Loading flagged projects from pipeline/output/...',
      'Building context bundles (cost + field notes + COs + RFIs)...',
      'Sending PRJ-2021-260 to Claude Haiku...',
      '  [Riverside Medical] Root cause: BMS coordination + undocumented COs',
      '  Recovery potential: $1.02M',
      'Sending PRJ-2022-118 to Claude Haiku...',
      '  [Greenfield Office] Root cause: Chiller delay standby + submittal rework',
      '  Recovery potential: $1.09M',
      'Sending PRJ-2022-334 to Claude Haiku...',
      '  [Westside K-12] Root cause: Abatement discovery + compressed schedule',
      '  Recovery potential: $534K',
      'Sending PRJ-2023-077 to Claude Haiku...',
      '  [Harbor Logistics] Root cause: Unbudgeted lift equipment + OT',
      '  Recovery potential: $247K',
      'Sending PRJ-2022-491 to Claude Haiku...',
      '  [St. Agnes Hospital] Root cause: Infection control premium + refrigerant delta',
      '  Recovery potential: $541K',
      'Sending PRJ-2023-155 to Claude Haiku...',
      '  [Luxe Hotel] Root cause: Overnight premium + work stoppages',
      '  Recovery potential: $673K',
      'Sending PRJ-2023-288 to Claude Haiku...',
      '  [Downtown Mixed-Use] Root cause: BIM clash redesign cycles + facade delay',
      '  Recovery potential: $262K',
      'Sending PRJ-2023-401 to Claude Haiku...',
      '  [Federal Courthouse] Root cause: Security clearance standby',
      '  Recovery potential: $251K',
      '-------------------------------------------',
      '  Total recoverable: ~$4.63M across 8 projects',
      '  Analysis complete. Dashboard ready.',
      '-------------------------------------------',
      '[DONE] All 8 projects analyzed in 8.3s',
    ],
  },
]

type StepStatus = 'idle' | 'running' | 'complete'

const SEVERITY_ICON = { critical: AlertTriangle, warning: TrendingDown, watch: Eye }
const SEVERITY_COLOR = { critical: 'text-red-400', warning: 'text-yellow-400', watch: 'text-blue-400' }
const SEVERITY_BADGE = {
  critical: 'bg-red-500/15 text-red-400 border-red-500/30',
  warning: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
  watch: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
}

export function Tab5Pipeline() {
  const [statuses, setStatuses] = useState<StepStatus[]>(STEPS.map(() => 'idle'))
  const [visibleLogs, setVisibleLogs] = useState<string[][]>(STEPS.map(() => []))
  const [running, setRunning] = useState(false)
  const [done, setDone] = useState(false)
  const [expandedStep, setExpandedStep] = useState<number | null>(null)
  const top5 = getSortedByPriority(MOCK_PROJECTS).slice(0, 5)
  const logRefs = useRef<(HTMLDivElement | null)[]>([])
  const runningRef = useRef(false)

  useEffect(() => { return () => { runningRef.current = false } }, [])

  const runPipeline = async () => {
    if (running || done) return
    setRunning(true)
    runningRef.current = true
    setExpandedStep(0)

    for (let i = 0; i < STEPS.length; i++) {
      if (!runningRef.current) break
      const step = STEPS[i]
      setExpandedStep(i)
      setStatuses(prev => { const n = [...prev]; n[i] = 'running'; return n })

      const delay = step.duration / step.logs.length
      for (let j = 0; j < step.logs.length; j++) {
        if (!runningRef.current) break
        await new Promise(r => setTimeout(r, delay))
        setVisibleLogs(prev => {
          const n = prev.map(l => [...l])
          n[i] = step.logs.slice(0, j + 1)
          return n
        })
        const el = logRefs.current[i]
        if (el) el.scrollTop = el.scrollHeight
      }

      await new Promise(r => setTimeout(r, 200))
      setStatuses(prev => { const n = [...prev]; n[i] = 'complete'; return n })
    }

    setRunning(false)
    setDone(true)
    setExpandedStep(null)
  }

  const completedCount = statuses.filter(s => s === 'complete').length
  const progress = (completedCount / STEPS.length) * 100

  const logColor = (line: string) => {
    if (line.startsWith('[DONE]')) return 'text-emerald-400'
    if (line.includes('CRITICAL')) return 'text-red-400'
    if (line.includes('WARNING')) return 'text-yellow-400'
    if (line.startsWith('---')) return 'text-border'
    if (line.startsWith('  [')) return 'text-blue-300'
    if (line.startsWith('  Recovery')) return 'text-emerald-400'
    if (line.startsWith('  Total recoverable')) return 'text-emerald-300 font-semibold'
    if (line.startsWith('  ')) return 'text-muted-foreground'
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
            5-step automated pipeline: ingests 1.46M records, aggregates via DuckDB, flags margin erosion, and runs Claude AI root cause analysis across the full portfolio.
          </p>
        </div>
        <button
          onClick={runPipeline}
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
      </div>

      {/* Progress bar */}
      {(running || done) && (
        <div>
          <div className="flex justify-between text-xs text-muted-foreground mb-1.5">
            <span>Pipeline progress</span>
            <span>{completedCount} / {STEPS.length} steps complete</span>
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
      <div className="space-y-2">
        {STEPS.map((step, i) => {
          const status = statuses[i]
          const isExpanded = expandedStep === i
          const hasLogs = visibleLogs[i].length > 0

          return (
            <div
              key={step.id}
              className={`rounded-2xl border overflow-hidden transition-all duration-300 ${
                status === 'complete' ? 'border-emerald-500/30'
                : status === 'running' ? 'border-primary/50 shadow-lg shadow-primary/10'
                : 'border-border/50'
              }`}
              style={{
                background: status === 'complete' ? 'rgba(16,185,129,0.04)'
                  : status === 'running' ? 'rgba(59,130,246,0.06)'
                  : 'rgba(255,255,255,0.02)',
                opacity: status === 'idle' && running ? 0.45 : 1,
              }}
            >
              {/* Step header â€" clickable to expand logs */}
              <button
                className="w-full flex items-center gap-4 px-5 py-4 text-left"
                onClick={() => hasLogs && setExpandedStep(isExpanded ? null : i)}
              >
                {/* Status icon */}
                <div className="shrink-0 w-8 h-8 rounded-full flex items-center justify-center">
                  {status === 'complete' ? (
                    <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                  ) : status === 'running' ? (
                    <Loader2 className="w-6 h-6 text-primary animate-spin" />
                  ) : (
                    <div className="w-6 h-6 rounded-full border-2 border-border flex items-center justify-center">
                      <span className="text-muted-foreground text-xs font-bold">{i + 1}</span>
                    </div>
                  )}
                </div>

                {/* Step info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`font-semibold text-sm ${status === 'idle' ? 'text-muted-foreground' : 'text-foreground'}`}>
                      {step.label}
                    </span>
                    <code className="text-xs px-2 py-0.5 rounded-md bg-muted text-muted-foreground font-mono">
                      {step.script}
                    </code>
                    {status === 'running' && (
                      <span className="text-xs text-primary animate-pulse">running...</span>
                    )}
                    {status === 'complete' && (
                      <span className="text-xs text-emerald-400">done</span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">{step.description}</p>
                </div>

                {/* Expand chevron */}
                {hasLogs && (
                  <ChevronRight className={`w-4 h-4 text-muted-foreground shrink-0 transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}`} />
                )}
              </button>

              {/* Terminal log output */}
              {isExpanded && hasLogs && (
                <div
                  ref={el => { logRefs.current[i] = el }}
                  className="border-t border-border/30 px-5 py-3 font-mono text-xs overflow-y-auto"
                  style={{ background: 'rgba(0,0,0,0.4)', maxHeight: 200 }}
                >
                  {visibleLogs[i].map((line, j) => (
                    <div key={j} className={`leading-relaxed ${logColor(line)}`}>
                      {!line.startsWith('[DONE]') && !line.startsWith('---') && (
                        <span className="text-border mr-1">{'>'}</span>
                      )}
                      {line}
                    </div>
                  ))}
                  {status === 'running' && (
                    <span className="text-primary animate-pulse">|</span>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Results summary + top 5 critical projects */}
      {done && (
        <div className="space-y-4">
            {/* KPI bar */}
            <div className="rounded-2xl border border-emerald-500/30 p-5" style={{ background: 'rgba(16,185,129,0.05)' }}>
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <h3 className="text-foreground font-semibold">Pipeline Complete - Results Ready</h3>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { label: 'Projects Scanned', value: '405' },
                  { label: 'Flagged', value: `${PORTFOLIO_SUMMARY.flaggedCount}` },
                  { label: 'Critical', value: `${PORTFOLIO_SUMMARY.criticalCount}`, alert: true },
                  { label: 'Recovery Opportunity', value: formatCurrency(PORTFOLIO_SUMMARY.flaggedCount * 280000), alert: true },
                ].map(s => (
                  <div key={s.label} className="rounded-xl bg-black/20 border border-border/30 px-4 py-3">
                    <p className="text-muted-foreground text-xs mb-1">{s.label}</p>
                    <p className={`text-xl font-bold ${s.alert ? 'text-emerald-400' : 'text-foreground'}`}>{s.value}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Top 5 critical projects */}
            <div className="rounded-2xl border border-border/50 overflow-hidden" style={{ background: 'rgba(255,255,255,0.02)' }}>
              <div className="px-5 py-4 border-b border-border/50 flex items-center justify-between">
                <div>
                  <h3 className="text-foreground font-semibold">Immediate Action Required</h3>
                  <p className="text-muted-foreground text-xs mt-0.5">Top 5 projects ranked by margin erosion severity - investigate these first</p>
                </div>
                <span className="text-xs text-muted-foreground">sorted by priority score</span>
              </div>

              <div className="divide-y divide-border/30">
                {top5.map((project, i) => {
                  const Icon = SEVERITY_ICON[project.severity]
                  const erosion = Math.abs(project.marginDelta) * 100
                  const recovery = project.recoveryActions?.reduce((s, a) => s + a.amount, 0) ?? 0
                  return (
                    <div key={project.id} className={`flex items-center gap-4 px-5 py-4 hover:bg-muted/10 transition-colors ${project.severity === 'critical' ? 'bg-red-500/5' : ''}`}>
                      {/* Rank */}
                      <div className="w-7 h-7 rounded-full bg-muted flex items-center justify-center shrink-0">
                        <span className="text-xs font-bold text-muted-foreground">#{i + 1}</span>
                      </div>

                      {/* Severity icon */}
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${project.severity === 'critical' ? 'bg-red-500/10' : project.severity === 'warning' ? 'bg-yellow-500/10' : 'bg-blue-500/10'}`}>
                        <Icon className={`w-4 h-4 ${SEVERITY_COLOR[project.severity]}`} />
                      </div>

                      {/* Project info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="text-foreground text-sm font-semibold truncate">{project.name}</p>
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${SEVERITY_BADGE[project.severity]}`}>
                            {project.severity}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 mt-1 flex-wrap">
                          <span className="text-muted-foreground text-xs">{project.sector}</span>
                          <span className="text-muted-foreground text-xs">{formatCurrency(project.contractValue)}</span>
                          <span className="text-red-400 text-xs font-medium">-{erosion.toFixed(1)} pts margin erosion</span>
                          <span className="text-xs text-muted-foreground">
                            Bid <span className="text-foreground">{formatPercent(project.bidMargin)}</span>
                            {' -> '}
                            Realized <span className="text-red-400">{formatPercent(project.realizedMargin)}</span>
                          </span>
                        </div>
                        {/* Erosion bar */}
                        <div className="mt-2 h-1 rounded-full bg-muted overflow-hidden w-48">
                          <div className="h-full rounded-full bg-gradient-to-r from-red-500 to-orange-400" style={{ width: `${Math.min(erosion * 5, 100)}%` }} />
                        </div>
                      </div>

                      {/* Recovery + action */}
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
        </div>
      )}
    </div>
  )
}
