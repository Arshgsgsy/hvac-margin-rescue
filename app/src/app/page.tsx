'use client'

import { useState, useEffect } from 'react'
import { Tab1Executive } from '@/components/tabs/tab1-executive'
import { Tab2SOV } from '@/components/tabs/tab2-sov'
import { Tab3LaborMaterial } from '@/components/tabs/tab3-labor-material'
import { Tab4Friction } from '@/components/tabs/tab4-friction'
import { Tab5Pipeline } from '@/components/tabs/tab5-pipeline'
import { formatCurrency, formatPercent } from '@/lib/data'
import { fetchPortfolioSummary, fetchProjects } from '@/lib/api'
import { Project, PortfolioSummary } from '@/lib/types'
import { BarChart3, Layers, Hammer, AlertOctagon, ChevronRight, Terminal, Loader2 } from 'lucide-react'

const TABS = [
  { id: 'pipeline', label: 'Agent Pipeline', icon: Terminal, sub: 'How the data gets here' },
  { id: 'executive', label: 'Executive Portfolio View', icon: BarChart3, sub: 'Where is the bleed?' },
  { id: 'sov', label: 'SOV Variance Drill-Down', icon: Layers, sub: 'What part of the project failed?' },
  { id: 'labor', label: 'Labor & Material Root Causes', icon: Hammer, sub: 'Why did it cost more?' },
  { id: 'friction', label: 'Operational Friction', icon: AlertOctagon, sub: 'What went wrong on site?' },
]

export default function Home() {
  const [activeTab, setActiveTab] = useState('pipeline')
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null)
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)

  const loadData = async () => {
    setLoading(true)
    try {
      const [summary, projs] = await Promise.all([
        fetchPortfolioSummary(),
        fetchProjects(),
      ])
      setPortfolio(summary)
      setProjects(projs)
    } catch {
      // Data not available yet (pipeline hasn't run)
    }
    setLoading(false)
  }

  useEffect(() => { loadData() }, [])

  const erosion = portfolio ? portfolio.avg_bid_margin - portfolio.avg_realized_margin : 0

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Top bar */}
      <header className="border-b border-border/50 bg-background/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-[1400px] mx-auto px-6 h-14 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-primary/20 flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-primary" />
            </div>
            <div>
              <span className="text-foreground font-semibold text-sm">Margin Variance Intelligence</span>
              <span className="text-muted-foreground text-xs ml-2 hidden sm:inline">HVAC Portfolio Dashboard</span>
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs">
            {portfolio && (
              <>
                <div className="hidden md:flex items-center gap-2">
                  <span className="text-muted-foreground">Portfolio:</span>
                  <span className="text-foreground font-medium">{formatCurrency(portfolio.total_value)}</span>
                </div>
                <div className="hidden md:flex items-center gap-2">
                  <span className="text-muted-foreground">Margin gap:</span>
                  <span className="text-red-400 font-semibold">{formatPercent(erosion)}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                  <span className="text-red-400 font-medium">{portfolio.critical_count} Critical</span>
                </div>
              </>
            )}
          </div>
        </div>
      </header>

      <div className="flex flex-1 max-w-[1400px] mx-auto w-full">
        {/* Sidebar */}
        <aside className="w-64 shrink-0 border-r border-border/50 py-6 px-3 hidden lg:block">
          <p className="text-muted-foreground text-xs font-semibold uppercase tracking-widest px-3 mb-3">Analysis Views</p>
          <nav className="space-y-1">
            {TABS.map(tab => {
              const Icon = tab.icon
              const active = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full text-left px-3 py-3 rounded-xl transition-all duration-150 flex items-start gap-3 group ${
                    active ? 'bg-primary/10 border border-primary/30' : 'hover:bg-muted/30 border border-transparent'
                  }`}
                >
                  <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${active ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'}`} />
                  <div className="min-w-0">
                    <p className={`text-sm font-medium leading-tight ${active ? 'text-foreground' : 'text-muted-foreground group-hover:text-foreground'}`}>
                      {tab.label}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5 leading-tight">{tab.sub}</p>
                  </div>
                  {active && <ChevronRight className="w-3 h-3 text-primary mt-1 ml-auto shrink-0" />}
                </button>
              )
            })}
          </nav>

          {/* Summary box */}
          {portfolio && (
            <div className="mx-3 mt-8 rounded-xl border border-red-500/30 bg-red-500/5 p-4">
              <p className="text-red-400 text-xs font-semibold uppercase tracking-wide mb-3">Recovery Opportunity</p>
              <p className="text-foreground text-xl font-bold">{formatCurrency(
                portfolio.flagged_count * 280000
              )}</p>
              <p className="text-muted-foreground text-xs mt-1">Estimated recoverable across {portfolio.flagged_count} flagged projects</p>
            </div>
          )}
        </aside>

        {/* Mobile tab bar */}
        <div className="lg:hidden border-b border-border/50 w-full">
          <div className="flex overflow-x-auto px-4 py-2 gap-2">
            {TABS.map(tab => {
              const Icon = tab.icon
              const active = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    active ? 'bg-primary/20 text-primary border border-primary/30' : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {tab.label.split(' ').slice(0, 2).join(' ')}
                </button>
              )
            })}
          </div>
        </div>

        {/* Main content */}
        <main className="flex-1 overflow-auto p-6">
          <div className="mb-6">
            {(() => {
              const tab = TABS.find(t => t.id === activeTab)!
              const Icon = tab.icon
              return (
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center">
                    <Icon className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <h1 className="text-xl font-bold text-foreground">{tab.label}</h1>
                    <p className="text-muted-foreground text-sm">{tab.sub}</p>
                  </div>
                </div>
              )
            })()}
          </div>

          {activeTab === 'pipeline' && <Tab5Pipeline portfolio={portfolio} onPipelineComplete={loadData} />}
          {activeTab === 'executive' && (
            loading ? <LoadingState /> : <Tab1Executive projects={projects} portfolio={portfolio} />
          )}
          {activeTab === 'sov' && (
            loading ? <LoadingState /> : <Tab2SOV projects={projects} />
          )}
          {activeTab === 'labor' && (
            loading ? <LoadingState /> : <Tab3LaborMaterial projects={projects} />
          )}
          {activeTab === 'friction' && (
            loading ? <LoadingState /> : <Tab4Friction projects={projects} />
          )}
        </main>
      </div>
    </div>
  )
}

function LoadingState() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="text-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin mx-auto mb-3" />
        <p className="text-muted-foreground text-sm">Loading data...</p>
        <p className="text-muted-foreground text-xs mt-1">Run the pipeline first if no data is available.</p>
      </div>
    </div>
  )
}
