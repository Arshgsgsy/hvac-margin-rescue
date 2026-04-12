'use client'

import Link from 'next/link'
import { AlertTriangle, TrendingDown, Eye, ArrowRight } from 'lucide-react'
import type { Project } from '@/lib/types'
import { formatCurrency, formatPercent, getPriorityScore } from '@/lib/data'

interface AlertCardProps {
  project: Project
  rank?: number
}

const severityConfig = {
  critical: {
    border: 'border-red-500/40',
    badge: 'bg-red-500/15 text-red-400 border border-red-500/30',
    dot: 'bg-red-500',
    icon: AlertTriangle,
    label: 'Critical',
  },
  warning: {
    border: 'border-yellow-500/40',
    badge: 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/30',
    dot: 'bg-yellow-500',
    icon: TrendingDown,
    label: 'Warning',
  },
  watch: {
    border: 'border-blue-500/40',
    badge: 'bg-blue-500/15 text-blue-400 border border-blue-500/30',
    dot: 'bg-blue-500',
    icon: Eye,
    label: 'Watch',
  },
}

export function AlertCard({ project, rank }: AlertCardProps) {
  const cfg = severityConfig[project.severity]
  const Icon = cfg.icon
  const erosion = Math.abs(project.marginDelta) * 100
  const score = getPriorityScore(project)

  return (
    <Link href={`/projects/${project.id}`} className="block group">
      <div
        className={`rounded-2xl border ${cfg.border} p-5 flex flex-col gap-4 transition-all duration-200 group-hover:border-primary/50 group-hover:shadow-lg group-hover:shadow-primary/5`}
        style={{ background: 'rgba(255,255,255,0.03)', backdropFilter: 'blur(8px)' }}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            {rank && (
              <span className="shrink-0 w-6 h-6 rounded-full bg-muted text-muted-foreground text-xs font-bold flex items-center justify-center">
                {rank}
              </span>
            )}
            <div className="min-w-0">
              <p className="text-foreground font-semibold text-sm truncate">{project.name}</p>
              <p className="text-muted-foreground text-xs mt-0.5">{project.sector}</p>
            </div>
          </div>
          <span className={`shrink-0 px-2 py-0.5 rounded-full text-xs font-medium flex items-center gap-1 ${cfg.badge}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
            {cfg.label}
          </span>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-3 gap-3">
          <div>
            <p className="text-muted-foreground text-xs mb-0.5">Contract</p>
            <p className="text-foreground text-sm font-medium">{formatCurrency(project.contractValue)}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs mb-0.5">Bid Margin</p>
            <p className="text-foreground text-sm font-medium">{formatPercent(project.bidMargin)}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs mb-0.5">Realized</p>
            <p className={`text-sm font-medium ${project.marginDelta < -0.05 ? 'text-red-400' : project.marginDelta < -0.02 ? 'text-yellow-400' : 'text-green-400'}`}>
              {formatPercent(project.realizedMargin)}
            </p>
          </div>
        </div>

        {/* Erosion bar */}
        <div>
          <div className="flex justify-between text-xs text-muted-foreground mb-1">
            <span>Margin erosion</span>
            <span className="text-red-400 font-medium">-{erosion.toFixed(1)} pts</span>
          </div>
          <div className="h-1.5 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-red-500 to-orange-400"
              style={{ width: `${Math.min(erosion * 5, 100)}%` }}
            />
          </div>
        </div>

        {/* Primary action */}
        {project.recoveryActions && project.recoveryActions[0] && (
          <div className="rounded-xl bg-muted/50 px-4 py-3">
            <p className="text-muted-foreground text-xs mb-0.5">Top action</p>
            <p className="text-foreground text-xs">{project.recoveryActions[0].description}</p>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-1">
          <span className="text-muted-foreground text-xs">Priority score: <span className="text-foreground font-medium">{score.toFixed(0)}</span></span>
          <span className="text-primary text-xs font-medium flex items-center gap-1 group-hover:gap-2 transition-all">
            Investigate <ArrowRight className="w-3 h-3" />
          </span>
        </div>
      </div>
    </Link>
  )
}