'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import {
  ArrowLeft,
  ArrowRight,
  BriefcaseBusiness,
  Clock3,
  DollarSign,
  Loader2,
  ShieldAlert,
  Sparkles,
} from 'lucide-react'

import { fetchPortfolioSummary, fetchProjects } from '@/lib/api'
import { formatCurrency, formatPercent, getSortedByPriority } from '@/lib/data'
import type { PortfolioBrief, PortfolioSummary, Project, RecoveryAction, ThisWeekPlanAction } from '@/lib/types'

export default function DashboardPage() {
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null)
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    Promise.all([fetchPortfolioSummary(), fetchProjects()])
      .then(([summary, flaggedProjects]) => {
        if (cancelled) return
        setPortfolio(summary)
        setProjects(flaggedProjects)
      })
      .catch((err) => {
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Failed to load recovery command center.')
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  const fallbackProjects = useMemo(() => getSortedByPriority(projects), [projects])
  const brief: PortfolioBrief | undefined = portfolio?.brief
  const rankedProjects = useMemo(() => {
    if (!brief?.projects_requiring_exec_attention?.length) {
      return fallbackProjects
    }

    const seen = new Set<string>()
    return [...brief.projects_requiring_exec_attention, ...fallbackProjects].filter((project) => {
      if (seen.has(project.id)) {
        return false
      }
      seen.add(project.id)
      return true
    })
  }, [brief?.projects_requiring_exec_attention, fallbackProjects])

  const topProjects = brief?.projects_requiring_exec_attention?.length
    ? brief.projects_requiring_exec_attention
    : fallbackProjects.slice(0, 5)
  const criticalProjects = rankedProjects.filter((project) => project.severity === 'critical').slice(0, 3)

  const topActions = brief?.top_actions?.length
    ? brief.top_actions
    : fallbackProjects
        .flatMap((project) =>
          (project.recovery_actions ?? []).map((action) => ({
            ...action,
            project_id: project.id,
            project_name: project.name,
            severity: project.severity,
          }))
        )
        .sort(
          (a, b) =>
            (b.expected_value ?? b.estimated_recovery_dollars ?? b.amount ?? 0) -
            (a.expected_value ?? a.estimated_recovery_dollars ?? a.amount ?? 0)
        )
        .slice(0, 6)

  const thisWeekPlan = brief?.this_week_plan ?? []
  const ownerPlan = brief?.owner_plan ?? []
  const blockers = brief?.biggest_blockers ?? []

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#07111f' }}>
        <Loader2 className="w-8 h-8 text-cyan-300 animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6" style={{ background: '#07111f' }}>
        <div className="max-w-xl rounded-3xl border border-red-500/30 bg-red-500/5 p-6 text-center">
          <p className="text-red-300 font-semibold">Recovery command center unavailable</p>
          <p className="text-slate-300 text-sm mt-2">{error}</p>
          <Link href="/" className="inline-flex items-center gap-2 mt-5 text-sm text-cyan-300">
            <ArrowLeft className="w-4 h-4" />
            Upload a dataset
          </Link>
        </div>
      </div>
    )
  }

  if (!portfolio || projects.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6" style={{ background: '#07111f' }}>
        <div className="max-w-xl rounded-3xl border border-white/10 bg-white/5 p-6 text-center">
          <p className="text-white font-semibold">No recovery queue is available yet.</p>
          <p className="text-slate-400 text-sm mt-2">Upload a dataset and run the pipeline to generate the action plan.</p>
          <Link href="/" className="inline-flex items-center gap-2 mt-5 text-sm text-cyan-300">
            <ArrowLeft className="w-4 h-4" />
            Upload a dataset
          </Link>
        </div>
      </div>
    )
  }

  return (
    <main className="min-h-screen px-6 py-8" style={{ background: 'radial-gradient(circle at top left, rgba(17,94,89,0.2), transparent 28%), #07111f' }}>
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <Link href="/" className="inline-flex items-center gap-2 text-sm" style={{ color: '#94a3b8' }}>
            <ArrowLeft className="w-4 h-4" />
            Upload another dataset
          </Link>
          {portfolio.data_availability?.degraded_mode && (
            <div className="rounded-full border border-yellow-500/30 bg-yellow-500/10 px-4 py-2 text-xs text-yellow-200">
              Running in degraded mode. Missing optional sources: {portfolio.data_availability.missing_features.join(', ')}
            </div>
          )}
        </div>

        <section className="rounded-[32px] border border-cyan-400/20 overflow-hidden" style={{ background: 'linear-gradient(135deg, rgba(14,27,47,0.95), rgba(4,11,23,0.96))' }}>
          <div className="grid gap-8 px-8 py-10 lg:grid-cols-[1.4fr_0.9fr]">
            <div className="space-y-6">
              <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-xs text-cyan-200">
                <Sparkles className="w-3.5 h-3.5" />
                Solution-first portfolio brief
              </div>
              <div className="space-y-3">
                <h1 className="text-4xl md:text-5xl font-semibold text-white leading-tight">
                  Recover cash now.
                  <br />
                  Protect what margin is still left.
                </h1>
                <p className="text-slate-300 text-base md:text-lg max-w-3xl leading-relaxed">
                  {brief?.executive_brief || 'The system has already ranked the highest-payoff moves. Start with the action queue below, not the raw data.'}
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <MetricCard
                  icon={<Clock3 className="w-5 h-5 text-cyan-200" />}
                  label="Cash This Week"
                  value={formatCurrency(brief?.cash_this_week ?? 0)}
                  note="Fastest collectible recovery"
                />
                <MetricCard
                  icon={<DollarSign className="w-5 h-5 text-emerald-200" />}
                  label="Cash In 30 Days"
                  value={formatCurrency(brief?.cash_in_30_days ?? 0)}
                  note="Immediate + near-term plan"
                />
                <MetricCard
                  icon={<BriefcaseBusiness className="w-5 h-5 text-blue-200" />}
                  label="Achievable Recovery"
                  value={formatCurrency(brief?.achievable_recovery ?? portfolio.total_recoverable ?? 0)}
                  note={brief?.optimization_available ? 'Probability-weighted plan' : 'Derived from project queue'}
                />
                <MetricCard
                  icon={<ShieldAlert className="w-5 h-5 text-amber-200" />}
                  label="Critical Jobs"
                  value={`${portfolio.critical_count}`}
                  note={`${portfolio.flagged_count} flagged projects total`}
                />
              </div>
            </div>

            <div className="rounded-[28px] border border-white/10 bg-white/5 p-6 space-y-5">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-cyan-300 mb-1">What To Push First</p>
                <h2 className="text-2xl font-semibold text-white">Top Executive Moves</h2>
              </div>
              <div className="space-y-3">
                {topActions.slice(0, 3).map((action, index) => (
                  <ActionBriefCard key={`${action.project_id ?? 'portfolio'}-${index}`} action={action} compact />
                ))}
              </div>
              <div className="rounded-2xl border border-white/10 bg-slate-950/40 p-4">
                <p className="text-sm text-slate-300">
                  Portfolio value {formatCurrency(portfolio.total_value)} across {portfolio.total_projects} jobs. Average realized margin is{' '}
                  <span className="text-white font-medium">{formatPercent(portfolio.avg_realized_margin)}</span>.
                </p>
              </div>
            </div>
          </div>
        </section>

        {criticalProjects.length > 0 && (
          <section className="space-y-5">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-cyan-300 mb-1">Critical Now</p>
              <h2 className="text-2xl font-semibold text-white">Top 3 Most Critical Projects</h2>
              <p className="text-slate-400 text-sm mt-1">
                Critical is assigned in the flagging stage from margin deterioration. Within that set, these are ranked by
                the strongest recovery move and how fast it turns into cash.
              </p>
            </div>
            <div className="grid gap-4 xl:grid-cols-3">
              {criticalProjects.map((project) => (
                <ProjectMemoCard key={`critical-${project.id}`} project={project} />
              ))}
            </div>
          </section>
        )}

        <section className="grid gap-6 xl:grid-cols-[1.35fr_0.9fr]">
          <div className="rounded-[28px] border border-white/10 bg-white/5 p-6 space-y-5">
            <div className="flex items-end justify-between gap-4 flex-wrap">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-cyan-300 mb-1">Action Queue</p>
                <h2 className="text-2xl font-semibold text-white">Highest-Value Moves</h2>
                <p className="text-slate-400 text-sm mt-1">
                  Ordered by expected recovery, urgency, and how quickly the team can turn them into money.
                </p>
              </div>
            </div>
            <div className="space-y-3">
              {topActions.slice(0, 6).map((action, index) => (
                <ActionBriefCard key={`${action.project_id ?? 'portfolio'}-${index}-expanded`} action={action} />
              ))}
            </div>
          </div>

          <div className="space-y-6">
            <section className="rounded-[28px] border border-white/10 bg-white/5 p-6 space-y-4">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-cyan-300 mb-1">This Week</p>
                <h2 className="text-2xl font-semibold text-white">Owner Plan</h2>
              </div>
              {thisWeekPlan.length > 0 ? (
                <div className="space-y-3">
                  {thisWeekPlan.slice(0, 5).map((item, index) => (
                    <WeekPlanRow key={`${item.project_id}-${index}`} item={item} />
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-400">
                  No explicit weekly plan was produced, so the queue above is acting as the default operating plan.
                </p>
              )}

              {ownerPlan.length > 0 && (
                <div className="grid gap-3 pt-2">
                  {ownerPlan.map((owner) => (
                    <div key={owner.owner} className="rounded-2xl border border-white/10 bg-slate-950/30 px-4 py-3 flex items-center justify-between">
                      <span className="text-sm text-slate-300">{owner.owner}</span>
                      <span className="text-sm font-medium text-white">{owner.hours.toFixed(0)} hrs</span>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="rounded-[28px] border border-white/10 bg-white/5 p-6 space-y-4">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-cyan-300 mb-1">Blockers</p>
                <h2 className="text-2xl font-semibold text-white">What Could Slow Recovery</h2>
              </div>
              <div className="space-y-3">
                {blockers.length > 0 ? (
                  blockers.slice(0, 4).map((blocker, index) => (
                    <div key={index} className="rounded-2xl border border-amber-400/20 bg-amber-400/5 px-4 py-3 text-sm text-amber-100">
                      {blocker}
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-slate-400">
                    No portfolio-level blockers were surfaced. The remaining work is execution discipline.
                  </p>
                )}
              </div>
            </section>
          </div>
        </section>

        <section className="space-y-5">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-cyan-300 mb-1">Project Memos</p>
            <h2 className="text-2xl font-semibold text-white">Projects That Need Decisions</h2>
            <p className="text-slate-400 text-sm mt-1">
              Each card leads with the money move, not the dashboard metrics. Open the recovery memo for evidence and support detail.
            </p>
          </div>
          <div className="grid gap-4 xl:grid-cols-2">
            {topProjects.map((project) => (
              <ProjectMemoCard key={project.id} project={project} />
            ))}
          </div>
        </section>
      </div>
    </main>
  )
}

function MetricCard({ icon, label, value, note }: { icon: ReactNode; label: string; value: string; note: string }) {
  return (
    <div className="rounded-[24px] border border-white/10 bg-white/5 p-5">
      <div className="w-10 h-10 rounded-2xl bg-white/10 flex items-center justify-center mb-4">
        {icon}
      </div>
      <p className="text-slate-400 text-xs uppercase tracking-[0.16em] mb-2">{label}</p>
      <p className="text-2xl font-semibold text-white">{value}</p>
      <p className="text-sm text-slate-400 mt-1">{note}</p>
    </div>
  )
}

function ActionBriefCard({
  action,
  compact = false,
}: {
  action: RecoveryAction & { project_id?: string; project_name?: string }
  compact?: boolean
}) {
  return (
    <div className={`rounded-[24px] border border-white/10 bg-slate-950/35 ${compact ? 'p-4' : 'p-5'} space-y-3`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-cyan-300 mb-1">
            {action.owner || 'Assigned owner'}
            {action.project_name ? ` · ${action.project_name}` : ''}
          </p>
          <p className={`${compact ? 'text-sm' : 'text-base'} text-white font-medium leading-relaxed`}>
            {action.action}
          </p>
        </div>
        <div className="text-right shrink-0">
          <p className="text-emerald-300 font-semibold">
            {formatCurrency(action.expected_value ?? action.estimated_recovery_dollars ?? action.amount ?? 0)}
          </p>
          <p className="text-xs text-slate-400">expected value</p>
        </div>
      </div>
      {!compact && action.financial_logic && (
        <p className="text-sm text-slate-400 leading-relaxed">{action.financial_logic}</p>
      )}
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-slate-200">
          {action.urgency?.replace('_', ' ') || 'this month'}
        </span>
        {typeof action.time_to_cash_days === 'number' && (
          <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-slate-200">
            {action.time_to_cash_days} days to cash
          </span>
        )}
        {typeof action.estimated_recovery_dollars === 'number' && (
          <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-slate-200">
            {formatCurrency(action.estimated_recovery_dollars)} gross upside
          </span>
        )}
      </div>
    </div>
  )
}

function WeekPlanRow({ item }: { item: ThisWeekPlanAction }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-950/30 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-cyan-300 mb-1">{item.day}</p>
          <p className="text-sm font-medium text-white">{item.action_summary}</p>
          <p className="text-xs text-slate-400 mt-1">
            {item.project_name || item.project_id} · {item.owner}
          </p>
        </div>
        <div className="text-right shrink-0">
          <p className="text-sm font-semibold text-emerald-300">{formatCurrency(item.expected_recovery)}</p>
          <p className="text-xs text-slate-400">{item.hours_required.toFixed(0)} hrs</p>
        </div>
      </div>
    </div>
  )
}

function ProjectMemoCard({ project }: { project: Project }) {
  const primaryAction = project.primary_action ?? project.recovery_actions?.[0]

  return (
    <Link href={`/projects/${project.id}`} className="block group">
      <div className="rounded-[28px] border border-white/10 bg-white/5 p-6 h-full transition-all duration-200 group-hover:border-cyan-300/40 group-hover:bg-white/[0.07]">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-cyan-300 mb-2">{project.project_mode?.replace('_', ' ') || 'recovery memo'}</p>
            <h3 className="text-xl font-semibold text-white">{project.name}</h3>
            <p className="text-sm text-slate-400 mt-1">
              {project.id} · {project.sector} · {project.project_stage}
            </p>
          </div>
          <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-200">
            {project.severity}
          </span>
        </div>

        <div className="grid gap-3 sm:grid-cols-3 mt-6">
          <MiniMetric label="Cash This Week" value={formatCurrency(project.money_brief?.cash_this_week ?? 0)} />
          <MiniMetric label="30-Day Recovery" value={formatCurrency(project.money_brief?.cash_in_30_days ?? 0)} />
          <MiniMetric label="Break Even Need" value={formatCurrency(project.break_even_recovery_needed ?? 0)} />
        </div>

        <div className="rounded-2xl border border-cyan-300/20 bg-cyan-400/5 p-4 mt-5">
          <p className="text-xs uppercase tracking-[0.18em] text-cyan-200 mb-1">Primary Move</p>
          <p className="text-sm text-white font-medium leading-relaxed">
            {primaryAction?.action || 'Open the memo to review the recommended action queue.'}
          </p>
          {primaryAction?.estimated_recovery_dollars ? (
            <p className="text-xs text-slate-300 mt-2">
              {formatCurrency(primaryAction.estimated_recovery_dollars)} opportunity · {primaryAction.owner}
            </p>
          ) : null}
        </div>

        <p className="text-sm text-slate-300 leading-relaxed mt-5">
          {project.executive_brief || project.headline}
        </p>

        <div className="flex items-center justify-between pt-5 mt-5 border-t border-white/10">
          <div>
            <p className="text-xs text-slate-400">Projected improvement</p>
            <p className="text-lg font-semibold text-emerald-300">
              {formatCurrency(project.profit_impact?.net_improvement ?? project.total_recoverable_estimate ?? 0)}
            </p>
          </div>
          <span className="inline-flex items-center gap-2 text-sm text-cyan-200 font-medium group-hover:gap-3 transition-all">
            Open recovery memo
            <ArrowRight className="w-4 h-4" />
          </span>
        </div>
      </div>
    </Link>
  )
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-950/30 px-4 py-3">
      <p className="text-xs uppercase tracking-[0.14em] text-slate-400 mb-1">{label}</p>
      <p className="text-lg font-semibold text-white">{value}</p>
    </div>
  )
}
