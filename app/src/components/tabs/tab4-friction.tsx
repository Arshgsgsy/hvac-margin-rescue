'use client'

import { useState } from 'react'
import {
  ComposedChart, Bar, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts'
import { formatCurrency } from '@/lib/data'
import { Project } from '@/lib/types'
import { ChevronDown } from 'lucide-react'

interface Props {
  projects: Project[]
}

const CustomTip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg p-3 text-xs border border-border bg-card shadow-xl">
      <p className="font-semibold text-foreground mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.color }}>
          {p.name}: {p.name === 'RFIs' ? p.value : formatCurrency(p.value)}
        </p>
      ))}
    </div>
  )
}

export function Tab4Friction({ projects }: Props) {
  const [selectedId, setSelectedId] = useState(projects[0]?.id ?? '')
  const project = projects.find(p => p.id === selectedId)

  if (!project || projects.length === 0) {
    return <p className="text-muted-foreground text-sm py-8">No data available. Run the pipeline first.</p>
  }

  const rfiData = (project.rfi_by_week ?? []).map(r => ({
    week: r.week,
    rfiCount: r.rfi_count,
  }))
  const changeOrders = project.change_orders ?? []
  const fieldNotes = project.field_note_summary ?? 'No field notes available for this project.'

  const pendingCOs = changeOrders.filter(co => co.status.toLowerCase() !== 'approved')
  const approvedCOs = changeOrders.filter(co => co.status.toLowerCase() === 'approved')

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <label className="text-muted-foreground text-sm font-medium whitespace-nowrap">Select project:</label>
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

      {/* RFI volume chart */}
      {rfiData.length > 0 && (
        <div className="rounded-2xl border border-border/50 p-6" style={{ background: 'rgba(255,255,255,0.03)' }}>
          <div className="mb-4">
            <h3 className="text-foreground font-semibold">RFI Volume by Week</h3>
            <p className="text-muted-foreground text-xs mt-0.5">Spikes in RFIs indicate coordination issues and potential cost drivers.</p>
          </div>
          <div style={{ height: 240 }}>
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={rfiData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2a3a" />
                <XAxis dataKey="week" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#f59e0b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTip />} />
                <Legend wrapperStyle={{ fontSize: '12px', color: '#64748b' }} />
                <Bar dataKey="rfiCount" name="RFIs" fill="#1e3a5f" radius={[2, 2, 0, 0]} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Change Order Tracker */}
        <div className="rounded-2xl border border-border/50 overflow-hidden" style={{ background: 'rgba(255,255,255,0.03)' }}>
          <div className="px-6 py-4 border-b border-border/50">
            <h3 className="text-foreground font-semibold">Change Order Tracker</h3>
            <p className="text-muted-foreground text-xs mt-0.5">
              <span className="text-yellow-400 font-semibold">{pendingCOs.length} pending/rejected</span> of {changeOrders.length} total COs
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border/30">
                  {['CO #', 'Description', 'Amount', 'Status', 'Category'].map(h => (
                    <th key={h} className="px-4 py-2 text-left font-semibold text-muted-foreground uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {changeOrders.map((co, i) => (
                  <tr key={i} className={`border-b border-border/20 hover:bg-muted/10 transition-colors ${co.status.toLowerCase() !== 'approved' ? 'bg-yellow-500/5' : ''}`}>
                    <td className="px-4 py-2.5 text-muted-foreground font-mono">{co.id}</td>
                    <td className="px-4 py-2.5 text-foreground max-w-[180px]">
                      <span className="line-clamp-2">{co.description}</span>
                    </td>
                    <td className="px-4 py-2.5 text-foreground font-medium">{formatCurrency(co.amount)}</td>
                    <td className="px-4 py-2.5">
                      {co.status.toLowerCase() === 'approved' ? (
                        <span className="px-2 py-0.5 rounded-full bg-green-500/15 text-green-400 text-xs font-medium border border-green-500/30">Approved</span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full bg-yellow-500/15 text-yellow-400 text-xs font-bold border border-yellow-500/30">{co.status}</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-muted-foreground">{co.reason_category}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Field Notes + RFIs Feed */}
        <div className="rounded-2xl border border-border/50 p-6" style={{ background: 'rgba(255,255,255,0.03)' }}>
          <div className="mb-4">
            <h3 className="text-foreground font-semibold">Field Notes & RFIs</h3>
            <p className="text-muted-foreground text-xs mt-0.5">Qualitative site report and RFI activity</p>
          </div>
          <div className="h-[280px] overflow-y-auto rounded-xl bg-black/30 border border-border/30 p-4">
            <div className="flex gap-2 mb-3">
              <div className="w-2 h-2 rounded-full bg-yellow-400 mt-1 shrink-0" />
              <p className="text-yellow-100/80 text-xs font-mono leading-relaxed whitespace-pre-line">{fieldNotes}</p>
            </div>
            {(project.rfis ?? []).map((rfi, i) => (
              <div key={i} className="flex gap-2 mb-2">
                <div className={`w-2 h-2 rounded-full mt-1 shrink-0 ${rfi.status === 'open' ? 'bg-red-400' : 'bg-green-400'}`} />
                <p className="text-foreground/70 text-xs font-mono">
                  <span className="text-muted-foreground">[{rfi.id}] </span>
                  {rfi.description}
                  <span className={`ml-2 ${rfi.status === 'open' ? 'text-red-400' : 'text-green-400'}`}>
                    {rfi.status === 'open' ? `OPEN - ${rfi.days_open}d` : 'CLOSED'}
                  </span>
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
