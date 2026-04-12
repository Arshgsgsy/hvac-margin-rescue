'use client'

import { useState } from 'react'
import { Project } from '@/lib/types'
import { formatCurrency, formatPercent } from '@/lib/data'
import { 
  X, AlertTriangle, ListChecks, BarChart3, TrendingDown, DollarSign, ArrowRight, CheckCircle2,
  LayoutDashboard, Layers, Users, AlertCircle, FileText
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

interface InvestigateModalProps {
  project: Project
  onClose: () => void
}

type TabType = 'recommendation' | 'breakdown' | 'charts'
type SideTabType = 'executive' | 'sov' | 'labor' | 'friction' | null

export function InvestigateModal({ project, onClose }: InvestigateModalProps) {
  const [activeTab, setActiveTab] = useState<TabType>('recommendation')
  const [activeSideTab, setActiveSideTab] = useState<SideTabType>(null)

  const tabs: { id: TabType; label: string }[] = [
    { id: 'recommendation', label: 'Recommendation' },
    { id: 'breakdown', label: 'Breakdown' },
    { id: 'charts', label: 'Charts' },
  ]

  // Side navigation tabs - advanced views
  const sideTabs: { id: SideTabType; label: string; icon: React.ReactNode; description: string }[] = [
    { id: 'executive', label: 'Executive', icon: <LayoutDashboard className="w-5 h-5" />, description: 'Portfolio View' },
    { id: 'sov', label: 'SOV', icon: <Layers className="w-5 h-5" />, description: 'Variance Drill-down' },
    { id: 'labor', label: 'Labor', icon: <Users className="w-5 h-5" />, description: 'Cost Analysis' },
    { id: 'friction', label: 'Friction', icon: <AlertCircle className="w-5 h-5" />, description: 'Issue Tracker' },
  ]

  const severityConfig = {
    critical: { color: '#ef4444', label: 'Critical', bg: 'bg-red-500/10', border: 'border-red-500/30' },
    warning: { color: '#f59e0b', label: 'Elevated', bg: 'bg-amber-500/10', border: 'border-amber-500/30' },
    watch: { color: '#3b82f6', label: 'Monitor', bg: 'bg-blue-500/10', border: 'border-blue-500/30' },
  }

  const config = severityConfig[project.severity]
  const totalOverrun = project.laborOverrun + project.materialOverrun

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal with side navigation */}
      <div className="relative flex w-full max-w-5xl max-h-[85vh]">
        {/* Side navigation - small square tiles */}
        <div className="flex flex-col gap-2 mr-3">
          {sideTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveSideTab(activeSideTab === tab.id ? null : tab.id)}
              className={`w-16 h-16 rounded-xl border flex flex-col items-center justify-center gap-1 transition-all duration-200 ${
                activeSideTab === tab.id
                  ? 'bg-primary border-primary text-primary-foreground scale-105 shadow-lg'
                  : 'bg-card/90 border-border/50 text-muted-foreground hover:bg-card hover:border-primary/50 hover:text-foreground'
              }`}
              title={`${tab.label}: ${tab.description}`}
            >
              {tab.icon}
              <span className="text-[10px] font-medium">{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Main modal content */}
        <div className="flex-1 bg-card border border-border rounded-2xl shadow-2xl overflow-hidden flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-border/50">
            <div className="flex items-center gap-3">
              <div 
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: config.color }}
              />
              <div>
                <h2 className="text-lg font-bold text-foreground">{project.name}</h2>
                <p className="text-sm text-muted-foreground">{project.sector} | {project.id}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-muted transition-colors"
            >
              <X className="w-5 h-5 text-muted-foreground" />
            </button>
          </div>

          {/* Main 3 Tabs */}
          <div className="flex gap-2 px-6 py-3 border-b border-border/50 bg-muted/30">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => { setActiveTab(tab.id); setActiveSideTab(null) }}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === tab.id && !activeSideTab
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {/* Show side tab content if active */}
            {activeSideTab === 'executive' && (
              <ExecutiveView project={project} />
            )}
            {activeSideTab === 'sov' && (
              <SOVView project={project} />
            )}
            {activeSideTab === 'labor' && (
              <LaborView project={project} />
            )}
            {activeSideTab === 'friction' && (
              <FrictionView project={project} />
            )}
            
            {/* Show main tab content if no side tab active */}
            {!activeSideTab && activeTab === 'recommendation' && (
              <RecommendationTab project={project} config={config} totalOverrun={totalOverrun} />
            )}
            {!activeSideTab && activeTab === 'breakdown' && (
              <BreakdownTab project={project} totalOverrun={totalOverrun} />
            )}
            {!activeSideTab && activeTab === 'charts' && (
              <ChartsTab project={project} />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// Advanced Side Views
function ExecutiveView({ project }: { project: Project }) {
  const totalOverrun = project.laborOverrun + project.materialOverrun
  const recoveryPotential = project.recoveryActions.reduce((sum, a) => sum + a.amount, 0)
  
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <LayoutDashboard className="w-5 h-5 text-primary" />
        <h3 className="text-lg font-bold text-foreground">Executive Portfolio View</h3>
      </div>
      
      {/* Key Metrics Grid */}
      <div className="grid grid-cols-4 gap-4">
        <div className="rounded-xl border border-border p-4 text-center">
          <p className="text-2xl font-bold text-foreground">{formatCurrency(project.contractValue)}</p>
          <p className="text-xs text-muted-foreground mt-1">Contract Value</p>
        </div>
        <div className="rounded-xl border border-border p-4 text-center">
          <p className="text-2xl font-bold text-foreground">{formatPercent(project.bidMargin)}</p>
          <p className="text-xs text-muted-foreground mt-1">Bid Margin</p>
        </div>
        <div className="rounded-xl border border-border p-4 text-center">
          <p className="text-2xl font-bold text-red-400">{formatPercent(project.realizedMargin)}</p>
          <p className="text-xs text-muted-foreground mt-1">Realized Margin</p>
        </div>
        <div className="rounded-xl border border-border p-4 text-center">
          <p className="text-2xl font-bold text-amber-400">{formatCurrency(totalOverrun)}</p>
          <p className="text-xs text-muted-foreground mt-1">Total Overrun</p>
        </div>
      </div>

      {/* Summary */}
      <div className="rounded-xl border border-border p-5">
        <h4 className="font-semibold text-foreground mb-3">Executive Summary</h4>
        <p className="text-sm text-muted-foreground leading-relaxed">
          {project.name} is currently experiencing a margin erosion of {formatPercent(Math.abs(project.marginDelta))} 
          from the original bid margin of {formatPercent(project.bidMargin)}. The project has accumulated 
          {formatCurrency(totalOverrun)} in cost overruns primarily due to {project.rootCause.toLowerCase()}.
          Recovery potential is estimated at {formatCurrency(recoveryPotential)} through recommended actions.
        </p>
      </div>

      {/* Timeline Status */}
      <div className="rounded-xl border border-border p-5">
        <h4 className="font-semibold text-foreground mb-3">Completion Status</h4>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-muted-foreground">Project Progress</span>
              <span className="font-medium text-foreground">{formatPercent(project.billingStatus.percentComplete)}</span>
            </div>
            <div className="h-3 rounded-full bg-muted overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-primary to-emerald-500 rounded-full"
                style={{ width: `${project.billingStatus.percentComplete * 100}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function SOVView({ project }: { project: Project }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <Layers className="w-5 h-5 text-primary" />
        <h3 className="text-lg font-bold text-foreground">SOV Variance Drill-down</h3>
      </div>

      {/* SOV Lines Table */}
      <div className="rounded-xl border border-border overflow-hidden">
        <table className="w-full">
          <thead className="bg-muted/50">
            <tr>
              <th className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground">Line Item</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-muted-foreground">Budgeted</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-muted-foreground">Actual</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-muted-foreground">Variance</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-muted-foreground">%</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {project.sovLines.map((line, i) => {
              const variance = line.actual - line.budgeted
              const variancePct = line.budgeted > 0 ? (variance / line.budgeted) : 0
              return (
                <tr key={i} className="hover:bg-muted/30">
                  <td className="px-4 py-3 text-sm text-foreground">{line.name}</td>
                  <td className="px-4 py-3 text-sm text-right text-muted-foreground">{formatCurrency(line.budgeted)}</td>
                  <td className="px-4 py-3 text-sm text-right text-foreground">{formatCurrency(line.actual)}</td>
                  <td className={`px-4 py-3 text-sm text-right font-medium ${variance > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                    {variance > 0 ? '+' : ''}{formatCurrency(variance)}
                  </td>
                  <td className={`px-4 py-3 text-sm text-right ${variancePct > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                    {variancePct > 0 ? '+' : ''}{formatPercent(variancePct)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function LaborView({ project }: { project: Project }) {
  const laborData = project.laborByWeek.map(week => ({
    name: week.week,
    Regular: week.regular,
    Overtime: week.overtime,
    Total: week.regular + week.overtime,
  }))

  const totalRegular = project.laborByWeek.reduce((sum, w) => sum + w.regular, 0)
  const totalOvertime = project.laborByWeek.reduce((sum, w) => sum + w.overtime, 0)
  const overtimeRatio = totalOvertime / (totalRegular + totalOvertime)

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <Users className="w-5 h-5 text-primary" />
        <h3 className="text-lg font-bold text-foreground">Labor & Material Cost Analysis</h3>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-xl border border-border p-4">
          <p className="text-xs text-muted-foreground mb-1">Labor Budget</p>
          <p className="text-xl font-bold text-foreground">{formatCurrency(project.laborCost.budget)}</p>
        </div>
        <div className="rounded-xl border border-border p-4">
          <p className="text-xs text-muted-foreground mb-1">Labor Actual</p>
          <p className="text-xl font-bold text-red-400">{formatCurrency(project.laborCost.actual)}</p>
        </div>
        <div className="rounded-xl border border-border p-4">
          <p className="text-xs text-muted-foreground mb-1">Overtime Ratio</p>
          <p className="text-xl font-bold text-amber-400">{formatPercent(overtimeRatio)}</p>
        </div>
      </div>

      {/* Labor by Week Chart */}
      <div className="rounded-xl border border-border p-5">
        <h4 className="font-semibold text-foreground mb-4">Weekly Labor Breakdown</h4>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={laborData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="name" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }} />
              <YAxis tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
              <Tooltip
                contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px' }}
                formatter={(value: number) => formatCurrency(value)}
              />
              <Legend />
              <Bar dataKey="Regular" stackId="labor" fill="#10b981" radius={[0, 0, 0, 0]} />
              <Bar dataKey="Overtime" stackId="labor" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

function FrictionView({ project }: { project: Project }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <AlertCircle className="w-5 h-5 text-primary" />
        <h3 className="text-lg font-bold text-foreground">Friction Log & Issue Tracker</h3>
      </div>

      {/* Field Notes */}
      <div className="rounded-xl border border-border p-5">
        <h4 className="font-semibold text-foreground mb-3">Field Notes Summary</h4>
        <p className="text-sm text-muted-foreground leading-relaxed">{project.fieldNoteSummary}</p>
      </div>

      {/* Change Orders */}
      <div>
        <h4 className="font-semibold text-foreground mb-3">Change Orders</h4>
        <div className="space-y-2">
          {project.changeOrders.map((co) => (
            <div key={co.id} className="flex items-center justify-between p-4 rounded-xl border border-border bg-card">
              <div className="flex items-center gap-3">
                <FileText className="w-4 h-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium text-foreground">{co.description}</p>
                  <p className="text-xs text-muted-foreground">{co.id}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className={`text-xs px-2 py-1 rounded ${
                  co.status === 'approved' ? 'bg-emerald-500/20 text-emerald-400' :
                  co.status === 'pending' ? 'bg-amber-500/20 text-amber-400' :
                  'bg-muted text-muted-foreground'
                }`}>
                  {co.status}
                </span>
                <span className="text-sm font-semibold text-foreground">{formatCurrency(co.costIncurred)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Root Cause */}
      <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-5">
        <h4 className="font-semibold text-foreground mb-2 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          Identified Root Cause
        </h4>
        <p className="text-sm text-muted-foreground">{project.rootCause}</p>
      </div>
    </div>
  )
}

interface TabProps {
  project: Project
  config?: { color: string; label: string; bg: string; border: string }
  totalOverrun?: number
}

function RecommendationTab({ project, config, totalOverrun }: TabProps) {
  return (
    <div className="space-y-6">
      {/* Critical Issue Summary */}
      <div className={`rounded-xl p-5 ${config?.bg} border ${config?.border}`}>
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 mt-0.5" style={{ color: config?.color }} />
          <div>
            <h3 className="font-semibold text-foreground mb-2">Root Cause Analysis</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">{project.rootCause}</p>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-xl border border-border p-4 text-center">
          <TrendingDown className="w-5 h-5 mx-auto mb-2 text-red-400" />
          <p className="text-2xl font-bold text-foreground">{formatPercent(Math.abs(project.marginDelta))}</p>
          <p className="text-xs text-muted-foreground mt-1">Margin Erosion</p>
        </div>
        <div className="rounded-xl border border-border p-4 text-center">
          <DollarSign className="w-5 h-5 mx-auto mb-2 text-amber-400" />
          <p className="text-2xl font-bold text-foreground">{formatCurrency(totalOverrun || 0)}</p>
          <p className="text-xs text-muted-foreground mt-1">Total Overrun</p>
        </div>
        <div className="rounded-xl border border-border p-4 text-center">
          <CheckCircle2 className="w-5 h-5 mx-auto mb-2 text-emerald-400" />
          <p className="text-2xl font-bold text-foreground">
            {formatCurrency(project.recoveryActions.reduce((sum, a) => sum + a.amount, 0))}
          </p>
          <p className="text-xs text-muted-foreground mt-1">Recovery Potential</p>
        </div>
      </div>

      {/* Recovery Actions */}
      <div>
        <h3 className="flex items-center gap-2 font-semibold text-foreground mb-4">
          <ListChecks className="w-5 h-5 text-primary" />
          Recommended Actions
        </h3>
        <div className="space-y-3">
          {project.recoveryActions.map((action, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-4 rounded-xl border border-border bg-card hover:bg-muted/30 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${
                  action.priority === 'high' ? 'bg-red-500' : 
                  action.priority === 'medium' ? 'bg-amber-500' : 'bg-blue-500'
                }`} />
                <div>
                  <p className="text-sm font-medium text-foreground">{action.description}</p>
                  <p className="text-xs text-muted-foreground capitalize">{action.priority} priority | {action.category.replace('_', ' ')}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm font-semibold text-emerald-400">+{formatCurrency(action.amount)}</span>
                <ArrowRight className="w-4 h-4 text-muted-foreground" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function BreakdownTab({ project, totalOverrun }: TabProps) {
  return (
    <div className="space-y-6">
      {/* Field Notes Summary */}
      <div className="rounded-xl border border-border p-5">
        <h3 className="font-semibold text-foreground mb-3">Field Notes Summary</h3>
        <p className="text-sm text-muted-foreground leading-relaxed">{project.fieldNoteSummary}</p>
      </div>

      {/* Cost Breakdown */}
      <div>
        <h3 className="font-semibold text-foreground mb-4">Cost Breakdown</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="rounded-xl border border-border p-4">
            <p className="text-sm text-muted-foreground mb-1">Labor Cost</p>
            <div className="flex items-baseline justify-between">
              <span className="text-lg font-bold text-foreground">{formatCurrency(project.laborCost.actual)}</span>
              <span className="text-sm text-red-400">+{formatCurrency(project.laborOverrun)}</span>
            </div>
            <div className="mt-2 h-2 rounded-full bg-muted overflow-hidden">
              <div 
                className="h-full bg-red-500 rounded-full"
                style={{ width: `${Math.min((project.laborCost.actual / project.laborCost.budget) * 100, 100)}%` }}
              />
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Budget: {formatCurrency(project.laborCost.budget)}
            </p>
          </div>
          <div className="rounded-xl border border-border p-4">
            <p className="text-sm text-muted-foreground mb-1">Material Cost</p>
            <div className="flex items-baseline justify-between">
              <span className="text-lg font-bold text-foreground">{formatCurrency(project.materialCost.actual)}</span>
              <span className="text-sm text-red-400">+{formatCurrency(project.materialOverrun)}</span>
            </div>
            <div className="mt-2 h-2 rounded-full bg-muted overflow-hidden">
              <div 
                className="h-full bg-amber-500 rounded-full"
                style={{ width: `${Math.min((project.materialCost.actual / project.materialCost.budget) * 100, 100)}%` }}
              />
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Budget: {formatCurrency(project.materialCost.budget)}
            </p>
          </div>
        </div>
      </div>

      {/* Billing Status */}
      <div className="rounded-xl border border-border p-5">
        <h3 className="font-semibold text-foreground mb-3">Billing Status</h3>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-muted-foreground">% Complete</span>
              <span className="font-medium text-foreground">{formatPercent(project.billingStatus.percentComplete)}</span>
            </div>
            <div className="h-2 rounded-full bg-muted overflow-hidden">
              <div 
                className="h-full bg-emerald-500 rounded-full"
                style={{ width: `${project.billingStatus.percentComplete * 100}%` }}
              />
            </div>
          </div>
          <div className="flex-1">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-muted-foreground">% Billed</span>
              <span className="font-medium text-foreground">{formatPercent(project.billingStatus.percentBilled)}</span>
            </div>
            <div className="h-2 rounded-full bg-muted overflow-hidden">
              <div 
                className="h-full bg-blue-500 rounded-full"
                style={{ width: `${project.billingStatus.percentBilled * 100}%` }}
              />
            </div>
          </div>
        </div>
        <p className="text-sm text-amber-400 mt-3">
          Billing gap: {formatPercent(project.billingGap)} ({formatCurrency(project.contractValue * project.billingGap)} unbilled)
        </p>
      </div>

      {/* Change Orders */}
      <div>
        <h3 className="font-semibold text-foreground mb-4">Change Orders</h3>
        <div className="space-y-2">
          {project.changeOrders.map((co) => (
            <div key={co.id} className="flex items-center justify-between p-3 rounded-lg border border-border bg-card">
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-muted-foreground">{co.id}</span>
                <span className="text-sm text-foreground">{co.description}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className={`text-xs px-2 py-0.5 rounded ${
                  co.status === 'approved' ? 'bg-emerald-500/20 text-emerald-400' :
                  co.status === 'pending' ? 'bg-amber-500/20 text-amber-400' :
                  'bg-muted text-muted-foreground'
                }`}>
                  {co.status}
                </span>
                <span className="text-sm font-medium text-foreground">{formatCurrency(co.costIncurred)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function ChartsTab({ project }: TabProps) {
  // SOV data for chart
  const sovData = project.sovLines.map(line => ({
    name: line.name.length > 12 ? line.name.substring(0, 12) + '...' : line.name,
    Budget: line.budgeted,
    Actual: line.actual,
  }))

  // Labor by week data
  const laborData = project.laborByWeek.map(week => ({
    name: week.week,
    Regular: week.regular,
    Overtime: week.overtime,
  }))

  return (
    <div className="space-y-8">
      {/* SOV Budget vs Actual */}
      <div>
        <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-primary" />
          Budget vs Actual by Category
        </h3>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={sovData} margin={{ top: 10, right: 10, left: 10, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis 
                dataKey="name" 
                tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis 
                tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                }}
                labelStyle={{ color: 'hsl(var(--foreground))' }}
                formatter={(value: number) => formatCurrency(value)}
              />
              <Legend />
              <Bar dataKey="Budget" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Actual" fill="#ef4444" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Labor Breakdown by Week */}
      <div>
        <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-primary" />
          Weekly Labor Cost (Regular vs Overtime)
        </h3>
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={laborData} margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis 
                dataKey="name" 
                tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
              />
              <YAxis 
                tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                }}
                labelStyle={{ color: 'hsl(var(--foreground))' }}
                formatter={(value: number) => formatCurrency(value)}
              />
              <Legend />
              <Bar dataKey="Regular" stackId="labor" fill="#10b981" radius={[0, 0, 0, 0]} />
              <Bar dataKey="Overtime" stackId="labor" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
