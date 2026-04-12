'use client'

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Project } from '@/lib/types'

interface Props {
  project: Project
}

export default function CostBreakdown({ project }: Props) {
  const data = [
    { name: 'Labor', Budget: project.laborCost.budget, Actual: project.laborCost.actual },
    { name: 'Material', Budget: project.materialCost.budget, Actual: project.materialCost.actual },
  ]

  const fmt = (v: number) => v >= 1000000 ? `$${(v / 1000000).toFixed(1)}M` : `$${(v / 1000).toFixed(0)}K`

  return (
    <div>
      <div style={{ height: 200 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} barCategoryGap="30%">
            <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={{ stroke: '#1e3a5f' }} tickLine={false} />
            <YAxis tickFormatter={fmt} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip
              formatter={(value: number) => [fmt(value), '']}
              contentStyle={{ background: '#1a2235', border: '1px solid #1e3a5f', borderRadius: 6 }}
              labelStyle={{ color: '#94a3b8' }}
              itemStyle={{ color: '#94a3b8' }}
            />
            <Bar dataKey="Budget" fill="#1d4ed8" radius={[3, 3, 0, 0]} />
            <Bar dataKey="Actual" radius={[3, 3, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={index} fill={entry.Actual > entry.Budget ? '#ef4444' : '#10b981'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="flex justify-center gap-6 mt-2">
        {[['#1d4ed8', 'Budget'], ['#ef4444', 'Actual (over)'], ['#10b981', 'Actual (under)']].map(([c, l]) => (
          <div key={l} className="flex items-center gap-1.5 text-xs" style={{ color: '#64748b' }}>
            <span className="inline-block w-3 h-3 rounded-sm" style={{ background: c as string }} />
            {l}
          </div>
        ))}
      </div>
    </div>
  )
}
