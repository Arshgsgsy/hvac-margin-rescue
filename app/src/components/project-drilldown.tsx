'use client'

import { useMemo, useRef, useState, type ReactNode } from 'react'
import {
  Clock3,
  DollarSign,
  Gavel,
  Loader2,
  ShieldAlert,
  Sparkles,
  Target,
  TrendingUp,
} from 'lucide-react'

import type { ChatMessage, Project, RecoveryAction, RootCause } from '@/lib/types'
import { formatCurrency, formatPercent } from '@/lib/data'
import { API_BASE } from '@/lib/api'
import CostBreakdown from '@/components/charts/cost-breakdown'

interface Props {
  project: Project
}

const severityStyle: Record<string, { text: string; bg: string; border: string }> = {
  critical: { text: '#fca5a5', bg: 'rgba(127,29,29,0.55)', border: 'rgba(248,113,113,0.25)' },
  warning: { text: '#fcd34d', bg: 'rgba(120,53,15,0.55)', border: 'rgba(251,191,36,0.25)' },
  watch: { text: '#93c5fd', bg: 'rgba(30,58,95,0.55)', border: 'rgba(96,165,250,0.25)' },
}

export default function ProjectDrilldown({ project }: Props) {
  const cfg = severityStyle[project.severity] ?? severityStyle.watch
  const billingDataAvailable = project.billing_data_available !== false
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const chatRef = useRef<HTMLDivElement>(null)

  const actionQueue = useMemo(() => {
    const primary = project.primary_action ? [project.primary_action] : []
    const next = project.next_actions ?? []
    const remainder = project.recovery_actions ?? []
    const queue = [...primary, ...next]
    remainder.forEach((action) => {
      if (!queue.find((item) => item.id === action.id || item.action === action.action)) {
        queue.push(action)
      }
    })
    return queue.slice(0, 5)
  }, [project])

  const primaryAction = actionQueue[0]
  const rootCauses = (project.root_causes ?? []) as RootCause[]

  const sendMessage = async (question?: string) => {
    const q = question ?? input.trim()
    if (!q || loading) return
    if (!question) setInput('')

    const userMsg: ChatMessage = { role: 'user', content: q, timestamp: Date.now() }
    setMessages((prev) => [...prev, userMsg])
    setLoading(true)

    const assistantMsg: ChatMessage = { role: 'assistant', content: '', timestamp: Date.now() }
    setMessages((prev) => [...prev, assistantMsg])

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: project.id, question: q }),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)

      const reader = res.body?.getReader()
      const decoder = new TextDecoder()
      if (!reader) throw new Error('No stream')

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        setMessages((prev) => {
          const next = [...prev]
          next[next.length - 1] = { ...next[next.length - 1], content: next[next.length - 1].content + chunk }
          return next
        })
        if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight
      }
    } catch {
      setMessages((prev) => {
        const next = [...prev]
        next[next.length - 1] = { ...next[next.length - 1], content: 'Error: Could not reach the recovery agent. Ensure the FastAPI backend is running.' }
        return next
      })
    }

    setLoading(false)
  }

  const suggested = [
    'Give me the strongest commercial recovery case on this job.',
    'What should we do this week to convert the most cash?',
    'What action should we not spend time on here?',
  ]

  return (
    <div className="space-y-6">
      <section className="rounded-[28px] border p-7" style={{ background: 'linear-gradient(145deg, #0d1728, #081120)', borderColor: '#14304f' }}>
        <div className="flex items-start justify-between gap-5 flex-wrap">
          <div className="space-y-3 max-w-4xl">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="text-xs font-bold px-3 py-1 rounded-full" style={{ background: cfg.bg, color: cfg.text, border: `1px solid ${cfg.border}` }}>
                {project.severity.toUpperCase()}
              </span>
              <span className="text-xs px-3 py-1 rounded-full border border-white/10 text-slate-300">
                {project.project_mode?.replace('_', ' ') || 'recovery memo'}
              </span>
              <span className="text-xs px-3 py-1 rounded-full border border-white/10 text-slate-300">
                {project.project_stage}
              </span>
              <code className="text-xs font-mono text-slate-500">{project.id}</code>
            </div>
            <div>
              <h1 className="text-3xl md:text-4xl font-semibold text-white">{project.name}</h1>
              <p className="text-slate-300 text-base mt-3 leading-relaxed">
                {project.executive_brief || project.headline}
              </p>
            </div>
          </div>
          <div className="rounded-[24px] border border-cyan-300/20 bg-cyan-400/5 p-5 min-w-[280px] max-w-sm">
            <p className="text-xs uppercase tracking-[0.2em] text-cyan-200 mb-2">Primary Move</p>
            <p className="text-sm font-medium text-white leading-relaxed">
              {primaryAction?.action || 'No primary action surfaced yet.'}
            </p>
            {primaryAction?.estimated_recovery_dollars ? (
              <p className="text-emerald-300 text-lg font-semibold mt-4">
                {formatCurrency(primaryAction.estimated_recovery_dollars)}
              </p>
            ) : null}
            <p className="text-xs text-slate-400 mt-1">
              {primaryAction?.owner || 'Owner not assigned'} · {primaryAction?.urgency?.replace('_', ' ') || 'this month'}
            </p>
          </div>
        </div>

        <div className="grid gap-4 mt-7 md:grid-cols-2 xl:grid-cols-5">
          <MetricPill
            icon={<DollarSign className="w-4 h-4 text-cyan-200" />}
            label="Current Margin Dollars"
            value={formatCurrency(project.profit_impact?.current_margin_dollars ?? project.current_margin_dollars ?? 0)}
          />
          <MetricPill
            icon={<TrendingUp className="w-4 h-4 text-emerald-200" />}
            label="Net Improvement"
            value={formatCurrency(project.profit_impact?.net_improvement ?? project.total_recoverable_estimate ?? 0)}
          />
          <MetricPill
            icon={<Clock3 className="w-4 h-4 text-blue-200" />}
            label="Cash In 30 Days"
            value={formatCurrency(project.money_brief?.cash_in_30_days ?? 0)}
          />
          <MetricPill
            icon={<Target className="w-4 h-4 text-amber-200" />}
            label="Break-Even Need"
            value={formatCurrency(project.break_even_recovery_needed ?? 0)}
          />
          <MetricPill
            icon={<Sparkles className="w-4 h-4 text-violet-200" />}
            label="Confidence"
            value={`${((project.analysis_confidence ?? 0) * 100).toFixed(0)}%`}
          />
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-[28px] border border-white/10 bg-white/5 p-6 space-y-5">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-cyan-300 mb-1">Do This Next</p>
            <h2 className="text-2xl font-semibold text-white">Recovery Action Queue</h2>
          </div>
          {actionQueue.length > 0 ? (
            <div className="space-y-4">
              {actionQueue.map((action, index) => (
                <ActionQueueRow key={action.id ?? `${action.action}-${index}`} action={action} index={index + 1} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-400">No action queue is available yet for this project.</p>
          )}
        </div>

        <div className="space-y-6">
          <section className="rounded-[28px] border border-white/10 bg-white/5 p-6 space-y-4">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-cyan-300 mb-1">Outcome</p>
              <h2 className="text-2xl font-semibold text-white">If We Wait Vs. If We Move</h2>
            </div>
            <OutcomeCard
              title="If We Wait"
              tone="risk"
              body={project.no_action_risk || 'No downside forecast provided.'}
            />
            <OutcomeCard
              title="If We Move"
              tone="upside"
              body={project.action_outlook || 'No action forecast provided.'}
            />
          </section>

          {!!project.blocking_items?.length && (
            <section className="rounded-[28px] border border-white/10 bg-white/5 p-6 space-y-4">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-cyan-300 mb-1">Blockers</p>
                <h2 className="text-2xl font-semibold text-white">What Needs Clearing</h2>
              </div>
              <div className="space-y-3">
                {project.blocking_items.map((item, index) => (
                  <div key={index} className="rounded-2xl border border-amber-400/20 bg-amber-400/5 px-4 py-3 text-sm text-amber-100">
                    {item}
                  </div>
                ))}
              </div>
            </section>
          )}

          {!!project.do_not_pursue?.length && (
            <section className="rounded-[28px] border border-white/10 bg-white/5 p-6 space-y-4">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-cyan-300 mb-1">Do Not Chase</p>
                <h2 className="text-2xl font-semibold text-white">Low-Value Work To Skip</h2>
              </div>
              <div className="space-y-3">
                {project.do_not_pursue.map((item, index) => (
                  <div key={index} className="rounded-2xl border border-white/10 bg-slate-950/35 px-4 py-3 text-sm text-slate-300">
                    {typeof item === 'string' ? item : item.reason || item.action || 'Deprioritized item'}
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1fr_0.95fr]">
        <div className="rounded-[28px] border border-white/10 bg-white/5 p-6 space-y-5">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-cyan-300 mb-1">Why The System Believes This</p>
            <h2 className="text-2xl font-semibold text-white">Evidence And Drivers</h2>
          </div>
          {rootCauses.length > 0 ? (
            <div className="space-y-4">
              {rootCauses.map((cause, index) => (
                <RootCauseCard key={`${cause.label}-${index}`} cause={cause} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-400">No structured root causes were available for this job.</p>
          )}

          {project.field_note_summary && (
            <div className="rounded-[24px] border border-blue-400/20 bg-blue-400/5 p-5">
              <p className="text-xs uppercase tracking-[0.2em] text-blue-200 mb-2">Field Notes Signal</p>
              <p className="text-sm leading-relaxed text-slate-200">{project.field_note_summary}</p>
            </div>
          )}
        </div>

        <div className="rounded-[28px] border border-white/10 bg-white/5 p-6 space-y-5">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-cyan-300 mb-1">Supporting Numbers</p>
            <h2 className="text-2xl font-semibold text-white">Cost And Commercial Detail</h2>
          </div>
          <div className="rounded-[24px] border border-white/10 bg-slate-950/30 p-5">
            <h3 className="text-white font-semibold mb-4">Cost Breakdown</h3>
            <CostBreakdown project={project} />
            <div className="grid gap-3 mt-5 sm:grid-cols-3">
              <SupportMetric label="% Complete" value={formatPercent(project.billing_status.percent_complete)} />
              <SupportMetric
                label="% Billed"
                value={billingDataAvailable ? formatPercent(project.billing_status.percent_billed) : 'N/A'}
              />
              <SupportMetric
                label="Billing Gap"
                value={billingDataAvailable ? formatCurrency(project.contract_value * (project.billing_gap ?? 0)) : 'Unavailable'}
              />
            </div>
          </div>

          {((project.change_orders?.length ?? 0) > 0 || (project.rfis?.length ?? 0) > 0) && (
            <div className="grid gap-4 lg:grid-cols-2">
              {(project.change_orders?.length ?? 0) > 0 && (
                <div className="rounded-[24px] border border-white/10 bg-slate-950/30 p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <Gavel className="w-4 h-4 text-cyan-200" />
                    <h3 className="text-white font-semibold">Commercial Paper</h3>
                  </div>
                  <div className="space-y-3">
                    {project.change_orders.slice(0, 6).map((co) => (
                      <div key={co.id} className="rounded-2xl border border-white/10 bg-white/5 p-3">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <code className="text-xs text-cyan-200">{co.id}</code>
                            <p className="text-sm text-white mt-1">{co.description}</p>
                            <p className="text-xs text-slate-400 mt-1">{co.status}</p>
                          </div>
                          <span className="text-sm font-semibold text-amber-200">{formatCurrency(co.amount)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {(project.rfis?.length ?? 0) > 0 && (
                <div className="rounded-[24px] border border-white/10 bg-slate-950/30 p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <ShieldAlert className="w-4 h-4 text-cyan-200" />
                    <h3 className="text-white font-semibold">Coordination Friction</h3>
                  </div>
                  <div className="space-y-3">
                    {project.rfis.slice(0, 6).map((rfi) => (
                      <div key={rfi.id} className="rounded-2xl border border-white/10 bg-white/5 p-3">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <code className="text-xs text-cyan-200">{rfi.id}</code>
                            <p className="text-sm text-white mt-1">{rfi.description}</p>
                          </div>
                          <span className="text-xs text-slate-300">
                            {rfi.status === 'open' ? `open ${rfi.days_open ?? 0}d` : rfi.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </section>

      <section className="rounded-[28px] border border-white/10 bg-white/5 overflow-hidden">
        <div className="px-6 py-5 border-b border-white/10">
          <h2 className="text-white font-semibold text-2xl">Ask For Proof Or Alternatives</h2>
          <p className="text-sm text-slate-400 mt-1">
            Use the agent for negotiation prep, backup evidence, or alternative recovery paths. The memo above should already tell you what to do first.
          </p>
        </div>

        <div ref={chatRef} className="p-6 space-y-4 overflow-y-auto" style={{ minHeight: '120px', maxHeight: '360px' }}>
          {messages.length === 0 && (
            <div className="space-y-2">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Suggested prompts</p>
              {suggested.map((question) => (
                <button
                  key={question}
                  onClick={() => sendMessage(question)}
                  className="text-sm px-4 py-3 rounded-2xl border border-white/10 block w-full text-left bg-slate-950/35 text-slate-300 hover:border-cyan-300/40 transition-colors"
                >
                  {question}
                </button>
              ))}
            </div>
          )}

          {messages.map((msg, index) => (
            <div key={index} className={msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
              <div
                className="max-w-prose text-sm px-4 py-3 rounded-2xl leading-relaxed whitespace-pre-wrap"
                style={{
                  background: msg.role === 'user' ? '#155e75' : '#111827',
                  color: msg.role === 'user' ? '#ecfeff' : '#cbd5e1',
                  maxWidth: '85%',
                }}
              >
                {msg.content || (loading && index === messages.length - 1 ? <Loader2 className="w-4 h-4 animate-spin" /> : '')}
              </div>
            </div>
          ))}
        </div>

        <div className="px-6 pb-6 flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask for evidence, alternatives, or negotiation prep..."
            className="flex-1 text-sm px-4 py-3 rounded-2xl border outline-none bg-slate-950/35 border-white/10 text-slate-100"
          />
          <button
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            className="px-5 py-3 text-sm font-semibold rounded-2xl"
            style={{
              background: loading || !input.trim() ? '#1e293b' : '#155e75',
              color: loading || !input.trim() ? '#64748b' : '#ecfeff',
              cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? '...' : 'Ask'}
          </button>
        </div>
      </section>
    </div>
  )
}

function MetricPill({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
      <div className="flex items-center gap-2 text-slate-300 text-xs uppercase tracking-[0.14em] mb-2">
        {icon}
        <span>{label}</span>
      </div>
      <p className="text-xl font-semibold text-white">{value}</p>
    </div>
  )
}

function ActionQueueRow({ action, index }: { action: RecoveryAction; index: number }) {
  return (
    <div className="rounded-[24px] border border-white/10 bg-slate-950/30 p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="flex gap-4">
          <div className="w-9 h-9 rounded-2xl bg-cyan-400/10 border border-cyan-300/20 text-cyan-200 flex items-center justify-center font-semibold text-sm shrink-0">
            {index}
          </div>
          <div>
            <p className="text-white font-medium leading-relaxed">{action.action}</p>
            {action.financial_logic && (
              <p className="text-sm text-slate-400 mt-2 leading-relaxed">{action.financial_logic}</p>
            )}
          </div>
        </div>
        <div className="text-right shrink-0">
          <p className="text-lg font-semibold text-emerald-300">
            {formatCurrency(action.expected_value ?? action.estimated_recovery_dollars ?? action.amount ?? 0)}
          </p>
          <p className="text-xs text-slate-400">expected value</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mt-4 text-xs">
        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-slate-200">{action.owner || 'Owner TBD'}</span>
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
            {formatCurrency(action.estimated_recovery_dollars)} gross
          </span>
        )}
      </div>

      {!!action.blocking_items?.length && (
        <div className="mt-4 rounded-2xl border border-amber-400/20 bg-amber-400/5 px-4 py-3">
          <p className="text-xs uppercase tracking-[0.18em] text-amber-200 mb-2">Blocking Items</p>
          <p className="text-sm text-amber-100">{action.blocking_items.join(' · ')}</p>
        </div>
      )}
    </div>
  )
}

function OutcomeCard({ title, body, tone }: { title: string; body: string; tone: 'risk' | 'upside' }) {
  const palette = tone === 'risk'
    ? { border: 'rgba(248,113,113,0.2)', background: 'rgba(127,29,29,0.18)', text: '#fecaca' }
    : { border: 'rgba(74,222,128,0.2)', background: 'rgba(20,83,45,0.18)', text: '#bbf7d0' }

  return (
    <div className="rounded-[24px] p-5 border" style={{ borderColor: palette.border, background: palette.background }}>
      <p className="text-xs uppercase tracking-[0.18em] mb-2" style={{ color: palette.text }}>{title}</p>
      <p className="text-sm leading-relaxed text-slate-100">{body}</p>
    </div>
  )
}

function RootCauseCard({ cause }: { cause: RootCause }) {
  return (
    <div className="rounded-[24px] border border-white/10 bg-slate-950/30 p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-white font-medium">{cause.label}</p>
          {cause.category && <p className="text-xs uppercase tracking-[0.18em] text-slate-500 mt-1">{cause.category}</p>}
        </div>
        {typeof cause.impact_dollars === 'number' && (
          <span className="text-sm font-semibold text-amber-200">{formatCurrency(cause.impact_dollars)}</span>
        )}
      </div>
      {cause.summary && <p className="text-sm text-slate-300 mt-3 leading-relaxed">{cause.summary}</p>}
      {!!cause.evidence?.length && (
        <div className="mt-4 space-y-2">
          {cause.evidence.slice(0, 2).map((evidence, index) => (
            <div key={index} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-300">
              {evidence}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function SupportMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
      <p className="text-xs uppercase tracking-[0.14em] text-slate-400 mb-1">{label}</p>
      <p className="text-base font-semibold text-white">{value}</p>
    </div>
  )
}
