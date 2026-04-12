'use client'

import { useState } from 'react'
import { Tab1Executive } from '@/components/tabs/tab1-executive'
import { Tab2SOV } from '@/components/tabs/tab2-sov'
import { Tab3LaborMaterial } from '@/components/tabs/tab3-labor-material'
import { Tab4Friction } from '@/components/tabs/tab4-friction'
import { Tab5Pipeline } from '@/components/tabs/tab5-pipeline'
import { PORTFOLIO_SUMMARY, formatCurrency, formatPercent } from '@/lib/data'
import { BarChart3, Layers, Hammer, AlertOctagon, ChevronRight, Terminal } from 'lucide-react'

const TABS = [
  { id: 'pipeline', label: 'Agent Pipeline', icon: Terminal, sub: 'How the data gets here' },
  { id: 'executive', label: 'Executive Portfolio View', icon: BarChart3, sub: 'Where is the bleed?' },
  { id: 'sov', label: 'SOV Variance Drill-Down', icon: Layers, sub: 'What part of the project failed?' },
  { id: 'labor', label: 'Labor & Material Root Causes', icon: Hammer, sub: 'Why did it cost more?' },
  { id: 'friction', label: 'Operational Friction', icon: AlertOctagon, sub: 'What went wrong on site?' },
]

export default function Home() {
  const [activeTab, setActiveTab] = useState('pipeline')
  const erosion = PORTFOLIO_SUMMARY.avgBidMargin - PORTFOLIO_SUMMARY.avgRealizedMargin

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
            <div className="hidden md:flex items-center gap-2">
              <span className="text-muted-foreground">Portfolio:</span>
              <span className="text-foreground font-medium">{formatCurrency(PORTFOLIO_SUMMARY.totalValue)}</span>
            </div>
            <div className="hidden md:flex items-center gap-2">
              <span className="text-muted-foreground">Margin gap:</span>
              <span className="text-red-400 font-semibold">{formatPercent(erosion)}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
              <span className="text-red-400 font-medium">{PORTFOLIO_SUMMARY.criticalCount} Critical</span>
            </div>
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
          <div className="mx-3 mt-8 rounded-xl border border-red-500/30 bg-red-500/5 p-4">
            <p className="text-red-400 text-xs font-semibold uppercase tracking-wide mb-3">Recovery Opportunity</p>
            <p className="text-foreground text-xl font-bold">{formatCurrency(
              PORTFOLIO_SUMMARY.flaggedCount * 280000
            )}</p>
            <p className="text-muted-foreground text-xs mt-1">Estimated recoverable across {PORTFOLIO_SUMMARY.flaggedCount} flagged projects</p>
          </div>
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

          {activeTab === 'pipeline' && <Tab5Pipeline />}
          {activeTab === 'executive' && <Tab1Executive />}
          {activeTab === 'sov' && <Tab2SOV />}
          {activeTab === 'labor' && <Tab3LaborMaterial />}
          {activeTab === 'friction' && <Tab4Friction />}
        </main>
      </div>
    </div>
  )
}