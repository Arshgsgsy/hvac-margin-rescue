'use client'

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  LineChart, Line, CartesianGrid, Legend, ReferenceLine,
} from 'recharts'
import { MOCK_PROJECTS, PORTFOLIO_SUMMARY, formatCurrency, formatPercent, getSortedByPriority } from '@/lib/data'
import { TrendingDown, DollarSign, AlertTriangle, FileWarning } from 'lucide-react'

const CustomBarTip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="rounded-lg p-3 text-xs border border-border bg-card shadow-xl">
      <p className="font-semibold text-foreground mb-1">{d.name}</p>
      <p className="text-muted-foreground">Bid: <span className="text-foreground">{formatPercent(d.bidRaw)}</span></p>
      <p className="text-muted-foreground">Realized: <span className="text-red-400">{formatPercent(d.realizedRaw)}</span></p>
      <p className="text-muted-foreground">Variance: <span className="text-red-400">{formatCurrency(d.varianceDollars)}</span></p>
    </div>
  )
}

const CustomLineTip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg p-3 text-xs border border-border bg-card shadow-xl">
      <p className="font-semibold text-foreground mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.color }}>{p.name}: {formatCurrency(p.value)}</p>
      ))}
    </div>
  )
}

export function Tab1Executive() {
  const sorted = getSortedByPriority(MOCK_PROJECTS)
  const bottom10 = [...MOCK_PROJECTS]
    .sort((a, b) => a.marginDelta - b.marginDelta)
    .slice(0, 8)
    .map((p) => ({
      name: p.name.length > 28 ? p.name.slice(0, 28) + '...' : p.name,
      fullName: p.name,
      bidRaw: p.bidMargin,
      realizedRaw: p.realizedMargin,
      bid: +(p.bidMargin * 100).toFixed(1),
      realized: +(p.realizedMargin * 100).toFixed(1),
      varianceDollars: Math.abs(p.marginDelta) * p.contractValue,
      severity: p.severity,
    }))

  const totalUnbilledCOs = MOCK_PROJECTS.flatMap(p => p.changeOrders ?? [])
    .filter(co => !co.billedToClient)
    .reduce((sum, co) => sum + co.costIncurred, 0)

  const totalMarginVariance = MOCK_PROJECTS.reduce(
    (sum, p) => sum + p.marginDelta * p.contractValue, 0
  )

  const allBillingData = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'].map((month) => {
    let billed = 0
    let cost = 0
    MOCK_PROJECTS.forEach((p) => {
      const m = (p.billingHistory ?? []).find((b) => b.month === month)
      if (m) { billed += m.billed; cost += m.actualCost }
    })
    return { month, billed, cost }
  }).filter(d => d.billed > 0 || d.cost > 0)

  const severityColor: Record<string, string> = {
    critical: '#ef4444',
    warning: '#f59e0b',
    watch: '#3b82f6',
  }

  return (
    <div className="space-y-6">
      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          {
            label: 'Avg Bid Margin',
            value: formatPercent(PORTFOLIO_SUMMARY.avgBidMargin),
            sub: 'Portfolio target',
            icon: TrendingDown,
            color: 'text-blue-400',
            bg: 'bg-blue-500/10',
          },
          {
            label: 'Avg Realized Margin',
            value: formatPercent(PORTFOLIO_SUMMARY.avgRealizedMargin),
            sub: `${formatPercent((PORTFOLIO_SUMMARY.avgBidMargin - PORTFOLIO_SUMMARY.avgRealizedMargin))} below bid`,
            icon: TrendingDown,
            color: 'text-red-400',
            bg: 'bg-red-500/10',
            alert: true,
          },
          {
            label: 'Total Margin Variance',
            value: formatCurrency(Math.abs(totalMarginVariance)),
            sub: 'Across flagged projects',
            icon: DollarSign,
            color: 'text-red-400',
            bg: 'bg-red-500/10',
            alert: true,
          },
          {
            label: 'Unbilled Change Orders',
            value: formatCurrency(totalUnbilledCOs),
            sub: 'Not yet billed to client',
            icon: FileWarning,
            color: 'text-yellow-400',
            bg: 'bg-yellow-500/10',
            alert: true,
          },
        ].map((kpi) => {
          const Icon = kpi.icon
          return (
            <div key={kpi.label} className={`rounded-2xl border p-5 ${kpi.alert ? 'border-red-500/30' : 'border-border/50'}`}
              style={{ background: 'rgba(255,255,255,0.03)' }}>
              <div className="flex items-center justify-between mb-3">
                <p className="text-muted-foreground text-xs font-medium uppercase tracking-wide">{kpi.label}</p>
                <div className={`w-8 h-8 rounded-lg ${kpi.bg} flex items-center justify-center`}>
                  <Icon className={`w-4 h-4 ${kpi.color}`} />
                </div>
              </div>
              <p className={`text-2xl font-bold ${kpi.alert ? 'text-red-400' : 'text-foreground'}`}>{kpi.value}</p>
              <p className="text-muted-foreground text-xs mt-1">{kpi.sub}</p>
            </div>
          )
        })}
      </div>

      {/* Bottom bleeders chart */}
      <div className="rounded-2xl border border-border/50 p-6" style={{ background: 'rgba(255,255,255,0.03)' }}>
        <div className="mb-4">
          <h3 className="text-foreground font-semibold">Bottom Margin Bleeders</h3>
          <p className="text-muted-foreground text-xs mt-0.5">Projects with largest bid-to-realized margin gap. Hover for dollar impact.</p>
        </div>
        <div style={{ height: 280 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={bottom10} layout="vertical" barCategoryGap="20%">
              <XAxis type="number" tickFormatter={(v) => `${v}%`} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" width={180} tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomBarTip />} />
              <Bar dataKey="bid" name="Bid" fill="#1e3a5f" radius={[0, 2, 2, 0]} />
              <Bar dataKey="realized" name="Realized" radius={[0, 2, 2, 0]}>
                {bottom10.map((entry, i) => (
                  <Cell key={i} fill={severityColor[entry.severity]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="flex gap-5 mt-2 justify-end">
          {[['#1e3a5f', 'Bid Margin'], ['#ef4444', 'Critical'], ['#f59e0b', 'Warning'], ['#3b82f6', 'Watch']].map(([c, l]) => (
            <div key={l} className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="inline-block w-3 h-2 rounded-sm" style={{ background: c as string }} />{l}
            </div>
          ))}
        </div>
      </div>

      {/* Billing vs Cost line chart */}
      <div className="rounded-2xl border border-border/50 p-6" style={{ background: 'rgba(255,255,255,0.03)' }}>
        <div className="mb-4">
          <h3 className="text-foreground font-semibold">Portfolio Cash Flow Health</h3>
          <p className="text-muted-foreground text-xs mt-0.5">Total billing vs total actual costs across all flagged projects. Gap below the line = cash flow pressure.</p>
        </div>
        <div style={{ height: 220 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={allBillingData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2a3a" />
              <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomLineTip />} />
              <Legend wrapperStyle={{ fontSize: '12px', color: '#64748b' }} />
              <Line type="monotone" dataKey="billed" name="Total Billed" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="cost" name="Actual Cost" stroke="#ef4444" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}