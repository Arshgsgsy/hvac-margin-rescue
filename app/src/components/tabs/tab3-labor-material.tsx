'use client'

import { useState } from 'react'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import { formatCurrency } from '@/lib/data'
import { Project } from '@/lib/types'
import { ChevronDown } from 'lucide-react'

interface Props {
  projects: Project[]
}

const CONDITION_COLORS: Record<string, string> = {
  Good: '#22c55e',
  Damaged: '#ef4444',
  Partial: '#f59e0b',
  Reordered: '#a855f7',
}

export function Tab3LaborMaterial({ projects }: Props) {
  const [selectedId, setSelectedId] = useState(projects[0]?.id ?? '')
  const project = projects.find(p => p.id === selectedId)

  if (!project || projects.length === 0) {
    return <p className="text-muted-foreground text-sm py-8">No data available. Run the pipeline first.</p>
  }

  const laborData = project.labor_by_week ?? []
  const materials = project.material_deliveries ?? []

  const conditionCounts = materials.reduce<Record<string, number>>((acc, m) => {
    const cond = m.condition.includes('Partial') ? 'Partial'
      : m.condition.includes('Damaged') ? 'Damaged'
      : m.condition.includes('Reorder') ? 'Reordered'
      : 'Good'
    acc[cond] = (acc[cond] ?? 0) + 1
    return acc
  }, {})
  const pieData = Object.entries(conditionCounts).map(([name, value]) => ({ name, value }))

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
            {projects.map(p => (
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

        <div className="rounded-2xl border border-border/50 p-6" style={{ background: 'rgba(255,255,255,0.03)' }}>
          <h3 className="text-foreground font-semibold mb-4">Material Deliveries</h3>
          {materials.length > 0 ? (
            <div className="space-y-3">
              {materials.slice(0, 8).map((m, i) => (
                <div key={i} className="flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <p className="text-foreground text-xs font-medium truncate">{m.description}</p>
                    <p className="text-muted-foreground text-xs">{m.date} | {m.vendor}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-foreground text-sm font-semibold">{formatCurrency(m.total_cost)}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-sm">No material deliveries for this project.</p>
          )}
        </div>
      </div>
    </div>
  )
}
