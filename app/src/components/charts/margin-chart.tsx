'use client'

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts'
import { Project } from '@/lib/types'

interface Props {
  projects: Project[]
}

const colorMap: Record<string, string> = {
  critical: '#ef4444',
  warning: '#f59e0b',
  watch: '#3b82f6',
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="rounded p-3 text-xs border" style={{ background: '#1a2235', borderColor: '#1e3a5f' }}>
      <p className="font-semibold text-white mb-1">{d.name}</p>
      <p style={{ color: '#64748b' }}>Bid: {d.bid}%</p>
      <p style={{ color: colorMap[d.severity] }}>Realized: {d.realized}%</p>
      <p style={{ color: '#f87171' }}>Erosion: -{(d.bid - d.realized).toFixed(1)}%</p>
    </div>
  )
}

export default function MarginChart({ projects }: Props) {
  const data = [...projects]
    .sort((a, b) => a.realized_margin - b.realized_margin)
    .map((p) => ({
      id: p.id.replace('PRJ-', ''),
      name: p.name,
      bid: +(p.bid_margin * 100).toFixed(1),
      realized: +(p.realized_margin * 100).toFixed(1),
      severity: p.severity,
    }))

  return (
    <div className="rounded-lg border p-5" style={{ background: '#111827', borderColor: '#1e3a5f' }}>
      <div style={{ height: 240 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} barCategoryGap="25%">
            <XAxis dataKey="id" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={{ stroke: '#1e3a5f' }} tickLine={false} />
            <YAxis tickFormatter={(v) => `${v}%`} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} domain={[0, 20]} />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={13.8} stroke="#334155" strokeDasharray="4 2" label={{ value: 'Bid avg', fill: '#475569', fontSize: 10 }} />
            <Bar dataKey="bid" fill="#1e3a5f" radius={[2, 2, 0, 0]} />
            <Bar dataKey="realized" radius={[2, 2, 0, 0]}>
              {data.map((entry, i) => (
                <Cell key={i} fill={colorMap[entry.severity]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="flex justify-center gap-6 mt-2">
        {[['#1e3a5f', 'Bid margin'], ['#ef4444', 'Critical'], ['#f59e0b', 'Warning'], ['#3b82f6', 'Watch']].map(([c, l]) => (
          <div key={l} className="flex items-center gap-1.5 text-xs" style={{ color: '#64748b' }}>
            <span className="inline-block w-3 h-3 rounded-sm" style={{ background: c as string }} />
            {l}
          </div>
        ))}
      </div>
    </div>
  )
}
