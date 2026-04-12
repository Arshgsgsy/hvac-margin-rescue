'use client'

import Link from 'next/link'
import { Project } from '@/lib/types'
import { getSortedByPriority, formatCurrency, formatPercent } from '@/lib/data'

interface Props {
  projects: Project[]
}

const RANK_STYLES = [
  { badge: 'bg-destructive/20 text-destructive border-destructive/30', ring: 'hsl(var(--destructive))' },
  { badge: 'bg-orange-500/20 text-orange-400 border-orange-500/30', ring: '#f97316' },
  { badge: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30', ring: '#eab308' },
]

export default function PriorityQueue({ projects }: Props) {
  const ranked = getSortedByPriority(projects)
  const top3 = ranked.slice(0, 3)

  return (
    <section id="priority-queue" className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <p className="text-xs font-semibold tracking-widest uppercase mb-1" style={{ color: 'hsl(var(--primary))' }}>
            CFO Action Queue
          </p>
          <h2 className="text-2xl md:text-3xl font-semibold text-foreground">
            Address These Three Projects First
          </h2>
          <p className="text-muted-foreground text-sm mt-1">
            Ranked by margin erosion severity, billing gap, and recovery urgency. Start here.
          </p>
        </div>
        <a href="#all-projects" className="text-sm hidden md:block" style={{ color: 'hsl(var(--primary))' }}>
          View all {projects.length} flagged &rarr;
        </a>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {top3.map((project, i) => {
          const style = RANK_STYLES[i]
          const topAction = project.recovery_actions?.[0]
          const totalRecovery = project.recovery_actions?.reduce((s, a) => s + a.amount, 0) ?? 0

          return (
            <div key={project.id}
              className="rounded-2xl border flex flex-col overflow-hidden"
              style={{
                background: 'rgba(255,255,255,0.03)',
                borderColor: `${style.ring}40`,
                backdropFilter: 'blur(8px)',
                boxShadow: `0 0 0 1px ${style.ring}20`,
              }}>
              <div className="p-5 pb-4 flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${style.badge}`}>
                      #{i + 1} Priority
                    </span>
                    <span className="text-xs" style={{ color: 'hsl(var(--muted-foreground))' }}>{project.sector}</span>
                  </div>
                  <p className="font-semibold text-foreground text-sm leading-snug">{project.name}</p>
                  <code className="text-xs mt-1 block" style={{ color: 'hsl(var(--muted-foreground))' }}>{project.id}</code>
                </div>
              </div>

              <div className="px-5 pb-4">
                <div className="flex justify-between text-xs mb-1.5" style={{ color: 'hsl(var(--muted-foreground))' }}>
                  <span>Margin erosion</span>
                  <span className="font-bold" style={{ color: style.ring }}>
                    -{formatPercent(Math.abs(project.margin_delta))}
                  </span>
                </div>
                <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'hsl(var(--border))' }}>
                  <div className="h-full rounded-full transition-all"
                    style={{ width: `${Math.min(Math.abs(project.margin_delta) * 500, 100)}%`, background: style.ring }} />
                </div>
                <div className="flex justify-between text-xs mt-1.5">
                  <span style={{ color: 'hsl(var(--muted-foreground))' }}>Realized: {formatPercent(project.realized_margin)}</span>
                  <span style={{ color: 'hsl(var(--muted-foreground))' }}>Bid: {formatPercent(project.bid_margin)}</span>
                </div>
              </div>

              {topAction && (
                <div className="mx-5 mb-4 p-3 rounded-lg" style={{ background: 'hsl(var(--secondary))' }}>
                  <p className="text-xs font-semibold mb-1" style={{ color: 'hsl(var(--primary))' }}>Immediate Action</p>
                  <p className="text-xs text-foreground leading-relaxed">{topAction.description}</p>
                </div>
              )}

              <div className="mt-auto px-5 pb-5 flex items-center justify-between">
                <div>
                  <p className="text-xs" style={{ color: 'hsl(var(--muted-foreground))' }}>Recovery potential</p>
                  <p className="text-lg font-bold" style={{ color: '#4ade80' }}>{formatCurrency(totalRecovery)}</p>
                </div>
                <Link href={`/projects/${project.id}`}
                  className="text-xs px-4 py-2 rounded-full font-semibold transition-all"
                  style={{ background: 'hsl(var(--foreground))', color: 'hsl(var(--background))' }}>
                  Investigate
                </Link>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
