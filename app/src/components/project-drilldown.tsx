'use client'

import { useState, useRef } from 'react'
import { Project, ChatMessage } from '@/lib/types'
import { formatCurrency, formatPercent } from '@/lib/data'
import { API_BASE } from '@/lib/api'
import CostBreakdown from '@/components/charts/cost-breakdown'

interface Props {
  project: Project
}

const severityStyle: Record<string, { text: string; bg: string }> = {
  critical: { text: '#f87171', bg: '#7f1d1d' },
  warning: { text: '#fbbf24', bg: '#78350f' },
  watch: { text: '#60a5fa', bg: '#1e3a5f' },
}

export default function ProjectDrilldown({ project }: Props) {
  const cfg = severityStyle[project.severity] ?? severityStyle.watch
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const chatRef = useRef<HTMLDivElement>(null)

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
        next[next.length - 1] = { ...next[next.length - 1], content: 'Error: Could not reach agent. Ensure the FastAPI backend is running.' }
        return next
      })
    }

    setLoading(false)
  }

  const SUGGESTED = [
    'Why did the margin erode on this project?',
    'What are the highest-priority recovery actions?',
    'How much can we recover from change orders?',
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-lg border p-6" style={{ background: '#111827', borderColor: '#1e3a5f' }}>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ background: cfg.bg, color: cfg.text }}>
                {project.severity.toUpperCase()}
              </span>
              <code className="text-xs font-mono" style={{ color: '#64748b' }}>{project.id}</code>
              <span className="text-xs px-2 py-0.5 rounded" style={{ background: '#1e293b', color: '#64748b' }}>{project.sector}</span>
            </div>
            <h1 className="text-2xl font-bold text-white">{project.name}</h1>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4 mt-4 sm:grid-cols-4">
          {[
            { label: 'Contract Value', value: formatCurrency(project.contract_value), color: '#94a3b8' },
            { label: 'Bid Margin', value: formatPercent(project.bid_margin), color: '#94a3b8' },
            { label: 'Realized Margin', value: formatPercent(project.realized_margin), color: cfg.text },
            { label: 'Erosion', value: `-${formatPercent(Math.abs(project.margin_delta))}`, color: cfg.text },
          ].map((s) => (
            <div key={s.label} className="rounded p-3" style={{ background: '#1a2235' }}>
              <p className="text-xs mb-1" style={{ color: '#475569' }}>{s.label}</p>
              <p className="text-xl font-bold" style={{ color: s.color }}>{s.value}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Cost Breakdown */}
        <div className="rounded-lg border p-5" style={{ background: '#111827', borderColor: '#1e3a5f' }}>
          <h2 className="text-white font-semibold mb-4">Cost Breakdown</h2>
          <CostBreakdown project={project} />
          <div className="mt-4 p-3 rounded" style={{ background: '#1a2235' }}>
            <div className="flex justify-between text-sm mb-1">
              <span style={{ color: '#64748b' }}>% Complete</span>
              <span className="font-mono" style={{ color: '#94a3b8' }}>{formatPercent(project.billing_status.percent_complete)}</span>
            </div>
            <div className="flex justify-between text-sm mb-2">
              <span style={{ color: '#64748b' }}>% Billed</span>
              <span className="font-mono" style={{ color: '#f59e0b' }}>{formatPercent(project.billing_status.percent_billed)}</span>
            </div>
            <div className="flex justify-between text-sm border-t pt-2" style={{ borderColor: '#1e3a5f' }}>
              <span className="font-medium" style={{ color: '#fbbf24' }}>Billing Gap</span>
              <span className="font-bold font-mono" style={{ color: '#fbbf24' }}>
                {formatCurrency(project.contract_value * project.billing_gap)} unbilled
              </span>
            </div>
          </div>
        </div>

        {/* Root Cause */}
        <div className="rounded-lg border p-5" style={{ background: '#111827', borderColor: '#1e3a5f' }}>
          <h2 className="text-white font-semibold mb-4">Root Cause Analysis</h2>
          {project.headline && (
            <p className="text-sm font-medium mb-3" style={{ color: '#f59e0b' }}>{project.headline}</p>
          )}
          {project.root_causes && project.root_causes.length > 0 ? (
            <ul className="space-y-2">
              {project.root_causes.map((cause, i) => (
                <li key={i} className="text-sm leading-relaxed flex items-start gap-2" style={{ color: '#94a3b8' }}>
                  <span style={{ color: '#f87171' }}>•</span>
                  {cause}
                </li>
              ))}
            </ul>
          ) : project.root_cause ? (
            <p className="text-sm leading-relaxed" style={{ color: '#94a3b8' }}>{project.root_cause}</p>
          ) : (
            <p className="text-sm" style={{ color: '#475569' }}>Ask the agent below for analysis.</p>
          )}
          {project.analysis_confidence && (
            <p className="text-xs mt-3" style={{ color: '#64748b' }}>
              Confidence: <span style={{ color: '#60a5fa' }}>{project.analysis_confidence}</span>
            </p>
          )}
          {project.field_note_summary && (
            <div className="mt-4 p-3 rounded border-l-2" style={{ background: '#1a2235', borderColor: '#3b82f6' }}>
              <p className="text-xs font-semibold mb-1" style={{ color: '#60a5fa' }}>Field Notes</p>
              <p className="text-xs leading-relaxed" style={{ color: '#64748b' }}>{project.field_note_summary}</p>
            </div>
          )}
        </div>
      </div>

      {/* Change Orders + RFIs */}
      {((project.change_orders?.length ?? 0) > 0 || (project.rfis?.length ?? 0) > 0) && (
        <div className="grid gap-6 lg:grid-cols-2">
          {(project.change_orders?.length ?? 0) > 0 && (
            <div className="rounded-lg border p-5" style={{ background: '#111827', borderColor: '#1e3a5f' }}>
              <h2 className="text-white font-semibold mb-4">Change Orders</h2>
              <div className="space-y-2">
                {project.change_orders!.map((co) => (
                  <div key={co.id} className="flex justify-between items-start text-sm p-2 rounded" style={{ background: '#1a2235' }}>
                    <div>
                      <code className="text-xs font-mono" style={{ color: '#60a5fa' }}>{co.id}</code>
                      <p className="text-xs mt-0.5" style={{ color: '#94a3b8' }}>{co.description}</p>
                      <span className="text-xs" style={{ color: co.status.toLowerCase() === 'approved' ? '#4ade80' : '#f59e0b' }}>
                        {co.status}
                      </span>
                    </div>
                    <span className="font-mono font-semibold" style={{ color: '#fbbf24' }}>
                      {formatCurrency(co.amount)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {(project.rfis?.length ?? 0) > 0 && (
            <div className="rounded-lg border p-5" style={{ background: '#111827', borderColor: '#1e3a5f' }}>
              <h2 className="text-white font-semibold mb-4">RFIs</h2>
              <div className="space-y-2">
                {project.rfis!.map((rfi) => (
                  <div key={rfi.id} className="flex justify-between items-start text-sm p-2 rounded" style={{ background: '#1a2235' }}>
                    <div>
                      <code className="text-xs font-mono" style={{ color: '#60a5fa' }}>{rfi.id}</code>
                      <p className="text-xs mt-0.5" style={{ color: '#94a3b8' }}>{rfi.description}</p>
                    </div>
                    <span className="text-xs font-medium" style={{ color: rfi.status === 'open' ? '#f87171' : '#4ade80' }}>
                      {rfi.status === 'open' ? `open ${rfi.days_open}d` : 'closed'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Agent Chat */}
      <div className="rounded-lg border" style={{ background: '#111827', borderColor: '#1e3a5f' }}>
        <div className="px-5 py-4 border-b" style={{ borderColor: '#1e3a5f' }}>
          <h2 className="text-white font-semibold">Ask the Recovery Agent</h2>
          <p className="text-xs mt-0.5" style={{ color: '#64748b' }}>
            Powered by Claude Haiku. Ask about root causes, recovery strategy, or specific cost items.
          </p>
        </div>

        <div ref={chatRef} className="p-5 space-y-4 overflow-y-auto" style={{ minHeight: '120px', maxHeight: '360px' }}>
          {messages.length === 0 && (
            <div className="space-y-2">
              <p className="text-xs" style={{ color: '#475569' }}>Suggested questions:</p>
              {SUGGESTED.map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="text-xs px-3 py-2 rounded border block w-full text-left"
                  style={{ borderColor: '#1e3a5f', color: '#64748b', background: '#1a2235' }}
                >
                  {q}
                </button>
              ))}
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
              <div
                className="max-w-prose text-sm px-4 py-3 rounded-lg leading-relaxed whitespace-pre-wrap"
                style={{
                  background: msg.role === 'user' ? '#1d4ed8' : '#1a2235',
                  color: msg.role === 'user' ? '#fff' : '#94a3b8',
                  maxWidth: '85%',
                }}
              >
                {msg.content || (loading && i === messages.length - 1 ? '...' : '')}
              </div>
            </div>
          ))}
        </div>

        <div className="px-5 pb-4 flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask about this project..."
            className="flex-1 text-sm px-3 py-2 rounded border outline-none"
            style={{ background: '#1a2235', borderColor: '#1e3a5f', color: '#f1f5f9' }}
          />
          <button
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            className="px-4 py-2 text-sm font-semibold rounded"
            style={{
              background: loading || !input.trim() ? '#1e3a5f' : '#1d4ed8',
              color: loading || !input.trim() ? '#64748b' : '#fff',
              cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? '...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  )
}
