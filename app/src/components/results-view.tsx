'use client'

import { useState } from 'react'
import { MOCK_PROJECTS, formatCurrency, formatPercent } from '@/lib/data'
import { Project } from '@/lib/types'
import { AlertTriangle, AlertCircle, Eye, ChevronRight, BarChart3, TrendingDown, DollarSign } from 'lucide-react'

interface ResultsViewProps {
  onInvestigate: (project: Project) => void
}

export function ResultsView({ onInvestigate }: ResultsViewProps) {
  // Group projects by severity
  const criticalProjects = MOCK_PROJECTS.filter(p => p.severity === 'critical')
  const warningProjects = MOCK_PROJECTS.filter(p => p.severity === 'warning')
  const watchProjects = MOCK_PROJECTS.filter(p => p.severity === 'watch')

  const totalExposure = MOCK_PROJECTS.reduce((sum, p) => sum + p.laborOverrun + p.materialOverrun, 0)

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border/50 bg-background/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-primary/20 flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h1 className="text-foreground font-bold text-lg">MarginIQ</h1>
              <p className="text-muted-foreground text-xs">Analysis Complete</p>
            </div>
          </div>
          <div className="flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">Projects Analyzed:</span>
              <span className="text-foreground font-semibold">{MOCK_PROJECTS.length}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">Total Exposure:</span>
              <span className="text-red-400 font-semibold">{formatCurrency(totalExposure)}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {/* Summary cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-5">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              <span className="text-red-400 font-semibold text-sm uppercase tracking-wide">Critical</span>
            </div>
            <p className="text-3xl font-bold text-foreground">{criticalProjects.length}</p>
            <p className="text-muted-foreground text-sm mt-1">Immediate action required</p>
          </div>
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-5">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="w-5 h-5 text-amber-400" />
              <span className="text-amber-400 font-semibold text-sm uppercase tracking-wide">Elevated</span>
            </div>
            <p className="text-3xl font-bold text-foreground">{warningProjects.length}</p>
            <p className="text-muted-foreground text-sm mt-1">Needs attention this week</p>
          </div>
          <div className="rounded-xl border border-blue-500/30 bg-blue-500/5 p-5">
            <div className="flex items-center gap-2 mb-2">
              <Eye className="w-5 h-5 text-blue-400" />
              <span className="text-blue-400 font-semibold text-sm uppercase tracking-wide">Monitor</span>
            </div>
            <p className="text-3xl font-bold text-foreground">{watchProjects.length}</p>
            <p className="text-muted-foreground text-sm mt-1">Track for changes</p>
          </div>
        </div>

        {/* Critical Projects Section */}
        {criticalProjects.length > 0 && (
          <section>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <h2 className="text-lg font-bold text-foreground">Critical Projects</h2>
              <span className="text-muted-foreground text-sm">({criticalProjects.length} projects)</span>
            </div>
            <div className="space-y-3">
              {criticalProjects.map(project => (
                <ProjectRow key={project.id} project={project} onInvestigate={onInvestigate} />
              ))}
            </div>
          </section>
        )}

        {/* Elevated Projects Section */}
        {warningProjects.length > 0 && (
          <section>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-3 h-3 rounded-full bg-amber-500" />
              <h2 className="text-lg font-bold text-foreground">Elevated Projects</h2>
              <span className="text-muted-foreground text-sm">({warningProjects.length} projects)</span>
            </div>
            <div className="space-y-3">
              {warningProjects.map(project => (
                <ProjectRow key={project.id} project={project} onInvestigate={onInvestigate} />
              ))}
            </div>
          </section>
        )}

        {/* Monitor Projects Section */}
        {watchProjects.length > 0 && (
          <section>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-3 h-3 rounded-full bg-blue-500" />
              <h2 className="text-lg font-bold text-foreground">Monitor Projects</h2>
              <span className="text-muted-foreground text-sm">({watchProjects.length} projects)</span>
            </div>
            <div className="space-y-3">
              {watchProjects.map(project => (
                <ProjectRow key={project.id} project={project} onInvestigate={onInvestigate} />
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  )
}

interface ProjectRowProps {
  project: Project
  onInvestigate: (project: Project) => void
}

function ProjectRow({ project, onInvestigate }: ProjectRowProps) {
  const severityColors = {
    critical: 'border-red-500/30 bg-red-500/5 hover:border-red-500/50',
    warning: 'border-amber-500/30 bg-amber-500/5 hover:border-amber-500/50',
    watch: 'border-blue-500/30 bg-blue-500/5 hover:border-blue-500/50',
  }

  const totalOverrun = project.laborOverrun + project.materialOverrun

  return (
    <div className={`rounded-xl border p-5 transition-all duration-200 ${severityColors[project.severity]}`}>
      <div className="flex items-start justify-between gap-4">
        {/* Project info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="font-semibold text-foreground truncate">{project.name}</h3>
            <span className="text-xs px-2 py-0.5 rounded bg-muted text-muted-foreground">{project.sector}</span>
          </div>
          <p className="text-sm text-muted-foreground line-clamp-1">{project.fieldNoteSummary}</p>
        </div>

        {/* Metrics */}
        <div className="flex items-center gap-6 shrink-0">
          <div className="text-right">
            <div className="flex items-center gap-1 text-red-400">
              <TrendingDown className="w-4 h-4" />
              <span className="font-semibold">{formatPercent(Math.abs(project.marginDelta))}</span>
            </div>
            <p className="text-xs text-muted-foreground">Margin erosion</p>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-1 text-foreground">
              <DollarSign className="w-4 h-4 text-muted-foreground" />
              <span className="font-semibold">{formatCurrency(totalOverrun)}</span>
            </div>
            <p className="text-xs text-muted-foreground">Total overrun</p>
          </div>
          <button
            onClick={() => onInvestigate(project)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary/10 hover:bg-primary/20 text-primary font-medium text-sm transition-colors"
          >
            Investigate
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
