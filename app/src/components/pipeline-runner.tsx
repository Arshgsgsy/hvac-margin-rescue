'use client'

import { useState, useEffect, useRef } from 'react'

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

interface Props {
  onComplete: () => void
}

export default function PipelineRunner({ onComplete }: Props) {
  const [statuses, setStatuses] = useState<StepStatus[]>(STEPS.map(() => 'idle'))
  const [visibleLogs, setVisibleLogs] = useState<string[][]>(STEPS.map((): string[] => []))
  const [running, setRunning] = useState(false)
  const [done, setDone] = useState(false)
  const logRefs = useRef<(HTMLDivElement | null)[]>([])
  const runningRef = useRef(false)

  useEffect(() => { return () => { runningRef.current = false } }, [])

  const runPipeline = async () => {
    if (running || done) return
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

  const statusColor = (s: StepStatus) =>
    s === 'complete' ? '#10b981' : s === 'running' ? '#3b82f6' : '#334155'

  const completedCount = statuses.filter((s) => s === 'complete').length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-white text-xl font-semibold">Pipeline Monitor</h2>
          <p className="text-sm mt-1" style={{ color: '#64748b' }}>
            5-step data pipeline: clean data, load DuckDB, scan portfolio, export JSON, LLM analysis
          </p>
        </div>
        <button
          onClick={runPipeline}
          disabled={running || done}
          className="px-5 py-2.5 rounded text-sm font-semibold"
          style={{
            background: running || done ? '#1e3a5f' : '#1d4ed8',
            color: running || done ? '#64748b' : '#fff',
            cursor: running || done ? 'not-allowed' : 'pointer',
          }}
        >
          {done ? 'Complete â€” Loading Dashboard...' : running ? 'Running...' : 'Run Pipeline'}
        </button>
      </div>

      {(running || done) && (
        <div>
          <div className="flex justify-between text-xs mb-1" style={{ color: '#64748b' }}>
            <span>Progress</span>
            <span>{completedCount} / {STEPS.length} steps</span>
          </div>
          <div className="h-1.5 rounded-full overflow-hidden" style={{ background: '#1e293b' }}>
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                background: 'linear-gradient(90deg, #1d4ed8, #3b82f6)',
                width: `${(completedCount / STEPS.length) * 100}%`,
              }}
            />
          </div>
        </div>
      )}

      <div className="space-y-3">
        {STEPS.map((step, i) => {
          const status = statuses[i]
          return (
            <div
              key={step.id}
              className="rounded-lg border overflow-hidden"
              style={{
                borderColor: statusColor(status),
                background: status === 'complete' ? '#052e16' : status === 'running' ? '#0c1d3d' : '#111827',
                opacity: status === 'idle' && running ? 0.5 : 1,
                transition: 'all 0.3s',
              }}
            >
              <div className="flex items-center gap-4 px-5 py-3">
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                  style={{ background: statusColor(status), color: '#fff' }}
                >
                  {status === 'complete' ? (
                    <svg width="14" height="14" fill="none" stroke="white" strokeWidth="2.5" viewBox="0 0 24 24">
                      <path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  ) : status === 'running' ? (
                    <span
                      style={{
                        display: 'inline-block',
                        width: 12,
                        height: 12,
                        border: '2px solid white',
                        borderTopColor: 'transparent',
                        borderRadius: '50%',
                        animation: 'spin 0.7s linear infinite',
                      }}
                    />
                  ) : (
                    <span style={{ color: '#64748b' }}>{i + 1}</span>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="font-semibold text-white">{step.label}</span>
                    <code
                      className="text-xs px-2 py-0.5 rounded font-mono"
                      style={{ background: '#0a0f1e', color: '#64748b' }}
                    >
                      {step.script}
                    </code>
                    {status === 'running' && (
                      <span className="text-xs" style={{ color: '#3b82f6' }}>running...</span>
                    )}
                    {status === 'complete' && (
                      <span className="text-xs" style={{ color: '#10b981' }}>done</span>
                    )}
                  </div>
                  <p className="text-xs mt-0.5" style={{ color: '#64748b' }}>{step.description}</p>
                </div>
              </div>

              {(status === 'running' || status === 'complete') && visibleLogs[i].length > 0 && (
                <div
                  ref={(el) => { logRefs.current[i] = el }}
                  className="border-t px-5 py-3 font-mono text-xs overflow-y-auto"
                  style={{ borderColor: '#0a0f1e', background: '#060d1a', maxHeight: '180px', color: '#94a3b8' }}
                >
                  {visibleLogs[i].map((line, j) => (
                    <div
                      key={j}
                      className="leading-relaxed"
                      style={{
                        color: line.startsWith('[DONE]') ? '#10b981'
                          : line.includes('CRITICAL') ? '#ef4444'
                          : line.includes('WARNING') ? '#f59e0b'
                          : line.startsWith('---') ? '#1e3a5f'
                          : line.startsWith('  ') ? '#94a3b8'
                          : '#64748b',
                      }}
                    >
                      {line.startsWith('[DONE]') ? '' : '> '}{line}
                    </div>
                  ))}
                  {status === 'running' && (
                    <span style={{ color: '#3b82f6', animation: 'pulse 1s infinite' }}>|</span>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {done && (
        <div className="rounded-lg p-4 border text-center" style={{ background: '#052e16', borderColor: '#10b981' }}>
          <p className="text-sm font-semibold" style={{ color: '#4ade80' }}>
            Pipeline complete. Loading dashboard...
          </p>
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
