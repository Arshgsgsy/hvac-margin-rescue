'use client'

import { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import { MOCK_PROJECTS, formatCurrency, formatPercent } from '@/lib/data'
import { ChevronDown } from 'lucide-react'

const CustomTip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="rounded-lg p-3 text-xs border border-border bg-card shadow-xl">
      <p className="font-semibold text-foreground mb-1">{d.name}</p>
      <p className="text-muted-foreground">Budgeted: <span className="text-foreground">{formatCurrency(d.budgeted)}</span></p>
      <p className="text-muted-foreground">Actual: <span className={d.actual > d.budgeted ? 'text-red-400' : 'text-green-400'}>{formatCurrency(d.actual)}</span></p>
      <p className="text-muted-foreground">Variance: <span className={d.variance < 0 ? 'text-red-400' : 'text-green-400'}>{formatCurrency(Math.abs(d.variance))} {d.variance < 0 ? 'over' : 'under'}</span></p>
    </div>
  )
}

export function Tab2SOV() {
  const [selectedId, setSelectedId] = useState(MOCK_PROJECTS[0].id)
  const project = MOCK_PROJECTS.find(p => p.id === selectedId)!
  const sovData = (project.sovLines ?? []).map(s => ({
    name: s.name.length > 22 ? s.name.slice(0, 22) + '...' : s.name,
    fullName: s.name,
    budgeted: s.budgeted,
    actual: s.actual,
    variance: s.budgeted - s.actual,
    variancePct: ((s.actual - s.budgeted) / s.budgeted * 100).toFixed(1),
  })).sort((a, b) => a.variance - b.variance)

  return (
    <div className="space-y-6">
      {/* Project selector */}
      <div className="flex items-center gap-3">
        <label className="text-muted-foreground text-sm font-medium whitespace-nowrap">Drill into project:</label>
        <div className="relative">
          <select
            value={selectedId}
            onChange={e => setSelectedId(e.target.value)}
            className="appearance-none bg-card border border-border text-foreground text-sm rounded-xl px-4 py-2 pr-9 focus:outline-none focus:ring-2 focus:ring-primary/50 cursor-pointer"
          >
            {MOCK_PROJECTS.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          <ChevronDown className="absolute right-2.5 top-2.5 w-4 h-4 text-muted-foreground pointer-events-none" />
        </div>
      </div>

      {/* Waterfall / grouped bar */}
      <div className="rounded-2xl border border-border/50 p-6" style={{ background: 'rgba(255,255,255,0.03)' }}>
        <div className="mb-4">
          <h3 className="text-foreground font-semibold">SOV Variance â€” Budget vs Actual</h3>
          <p className="text-muted-foreground text-xs mt-0.5">Worst overruns sorted to top. Red = over budget.</p>
        </div>
        <div style={{ height: 280 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={sovData} layout="vertical" barCategoryGap="20%">
              <XAxis type="number" tickFormatter={v => `$${(v/1000).toFixed(0)}K`} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" width={160} tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTip />} />
              <Bar dataKey="budgeted" name="Budgeted" fill="#1e3a5f" radius={[0, 2, 2, 0]} />
              <Bar dataKey="actual" name="Actual" radius={[0, 2, 2, 0]}>
                {sovData.map((entry, i) => (
                  <Cell key={i} fill={entry.actual > entry.budgeted ? '#ef4444' : '#22c55e'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Budget vs Actuals table */}
      <div className="rounded-2xl border border-border/50 overflow-hidden" style={{ background: 'rgba(255,255,255,0.03)' }}>
        <div className="px-6 py-4 border-b border-border/50">
          <h3 className="text-foreground font-semibold">Budget vs Actuals Detail</h3>
          <p className="text-muted-foreground text-xs mt-0.5">Sorted by variance (worst first)</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border/50">
                {['SOV Line Item', 'Budgeted', 'Actual Cost', 'Variance ($)', 'Variance (%)'].map(h => (
                  <th key={h} className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sovData.map((row, i) => (
                <tr key={i} className="border-b border-border/30 hover:bg-muted/20 transition-colors">
                  <td className="px-6 py-3 text-foreground font-medium">{row.fullName}</td>
                  <td className="px-6 py-3 text-muted-foreground">{formatCurrency(row.budgeted)}</td>
                  <td className="px-6 py-3">
                    <span className={row.actual > row.budgeted ? 'text-red-400 font-medium' : 'text-green-400'}>
                      {formatCurrency(row.actual)}
                    </span>
                  </td>
                  <td className="px-6 py-3">
                    <span className={row.variance < 0 ? 'text-red-400 font-medium' : 'text-green-400'}>
                      {row.variance < 0 ? '-' : '+'}{formatCurrency(Math.abs(row.variance))}
                    </span>
                  </td>
                  <td className="px-6 py-3">
                    <span className={parseFloat(row.variancePct) > 0 ? 'text-red-400 font-medium' : 'text-green-400'}>
                      {parseFloat(row.variancePct) > 0 ? '+' : ''}{row.variancePct}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}