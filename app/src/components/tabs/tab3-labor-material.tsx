'use client'

import { useState } from 'react'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import { MOCK_PROJECTS, formatCurrency } from '@/lib/data'
import { ChevronDown } from 'lucide-react'

const CONDITION_COLORS: Record<string, string> = {
  Good: '#22c55e',
  Damaged: '#ef4444',
  Partial: '#f59e0b',
  Reordered: '#a855f7',
}

export function Tab3LaborMaterial() {
  const [selectedId, setSelectedId] = useState(MOCK_PROJECTS[0].id)
  const project = MOCK_PROJECTS.find(p => p.id === selectedId)!
  const laborData = project.laborByWeek ?? []
  const materials = project.materialDeliveries ?? []

  const conditionCounts = materials.reduce<Record<string, number>>((acc, m) => {
    acc[m.condition] = (acc[m.condition] ?? 0) + 1
    return acc
  }, {})
  const pieData = Object.entries(conditionCounts).map(([name, value]) => ({ name, value }))

  const materialOverruns = [...materials]
    .filter(m => m.actualCost > m.budgetedCost)
    .sort((a, b) => (b.actualCost - b.budgetedCost) - (a.actualCost - a.budgetedCost))
    .slice(0, 5)

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <label className="text-muted-foreground text-sm font-medium whitespace-nowrap">Analyze project:</label>
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

      {/* Labor stacked area */}
      <div className="rounded-2xl border border-border/50 p-6" style={{ background: 'rgba(255,255,255,0.03)' }}>
        <div className="mb-4">
          <h3 className="text-foreground font-semibold">Labor: Regular vs Overtime by Week</h3>
          <p className="text-muted-foreground text-xs mt-0.5">Red area = overtime. Peaks show where overtime destroyed budget.</p>
        </div>
        <div style={{ height: 220 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={laborData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2a3a" />
              <XAxis dataKey="week" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tickFormatter={v => `$${(v/1000).toFixed(0)}K`} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip formatter={(v: number) => formatCurrency(v)} />
              <Legend wrapperStyle={{ fontSize: '12px', color: '#64748b' }} />
              <Area type="monotone" dataKey="regular" name="Regular Labor" stackId="1" stroke="#3b82f6" fill="#1e3a5f" />
              <Area type="monotone" dataKey="overtime" name="Overtime" stackId="1" stroke="#ef4444" fill="#7f1d1d" fillOpacity={0.8} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Material panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pie chart */}
        <div className="rounded-2xl border border-border/50 p-6" style={{ background: 'rgba(255,255,255,0.03)' }}>
          <h3 className="text-foreground font-semibold mb-4">Material Condition on Delivery</h3>
          {pieData.length > 0 ? (
            <div style={{ height: 200 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" outerRadius={75} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={CONDITION_COLORS[entry.name] ?? '#64748b'} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-muted-foreground text-sm">No delivery data for this project.</p>
          )}
        </div>

        {/* Price spikes */}
        <div className="rounded-2xl border border-border/50 p-6" style={{ background: 'rgba(255,255,255,0.03)' }}>
          <h3 className="text-foreground font-semibold mb-4">Top Material Cost Overruns</h3>
          {materialOverruns.length > 0 ? (
            <div className="space-y-3">
              {materialOverruns.map((m, i) => {
                const over = m.actualCost - m.budgetedCost
                const pct = ((over / m.budgetedCost) * 100).toFixed(0)
                return (
                  <div key={i} className="flex items-center justify-between gap-4">
                    <div className="min-w-0">
                      <p className="text-foreground text-xs font-medium truncate">{m.description}</p>
                      <p className="text-muted-foreground text-xs">Budget: {formatCurrency(m.budgetedCost)}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-red-400 text-sm font-semibold">+{formatCurrency(over)}</p>
                      <p className="text-red-400/70 text-xs">+{pct}%</p>
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="text-muted-foreground text-sm">No material overruns for this project.</p>
          )}
        </div>
      </div>
    </div>
  )
}