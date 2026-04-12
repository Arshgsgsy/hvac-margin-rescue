'use client'

import { TrendingDown, Brain, Zap, BarChart3, FileSearch, MessageSquare } from 'lucide-react'

const features = [
  {
    icon: TrendingDown,
    title: 'Margin Erosion Detection',
    description: 'Automatically flags projects where realized margin has dropped more than 3 points below bid â€” before the billing cycle closes.',
    accent: 'text-red-400',
    bg: 'bg-red-500/10',
    size: 'col-span-2',
  },
  {
    icon: Brain,
    title: 'AI Root Cause Analysis',
    description: 'Claude Haiku analyzes field notes, change orders, and cost data to surface the exact driver of margin erosion.',
    accent: 'text-blue-400',
    bg: 'bg-blue-500/10',
    size: 'col-span-1',
  },
  {
    icon: FileSearch,
    title: 'Billing Gap Identification',
    description: 'Compares billings to percent-complete, surfacing unbilled work that drains cash flow.',
    accent: 'text-yellow-400',
    bg: 'bg-yellow-500/10',
    size: 'col-span-1',
  },
  {
    icon: Zap,
    title: 'Instant Recovery Actions',
    description: 'Prioritized, actionable recovery steps generated for each flagged project â€” CO submissions, labor adjustments, vendor renegotiations.',
    accent: 'text-green-400',
    bg: 'bg-green-500/10',
    size: 'col-span-1',
  },
  {
    icon: BarChart3,
    title: 'Portfolio Visibility',
    description: 'Real-time view across all active contracts â€” margin trends, overrun rates, and risk concentration by project type.',
    accent: 'text-purple-400',
    bg: 'bg-purple-500/10',
    size: 'col-span-1',
  },
  {
    icon: MessageSquare,
    title: 'Conversational Drill-Down',
    description: 'Ask any question about a project in plain English. Get answers grounded in your actual cost data.',
    accent: 'text-cyan-400',
    bg: 'bg-cyan-500/10',
    size: 'col-span-2',
  },
]

export function FeatureBento() {
  return (
    <section className="w-full px-6 py-16">
      <div className="mb-10 text-center">
        <p className="text-xs font-semibold tracking-widest uppercase text-primary mb-3">What this platform does</p>
        <h2 className="text-3xl md:text-4xl font-bold text-foreground">
          From raw cost data to <span className="text-primary">CFO-ready insight</span>
        </h2>
        <p className="mt-3 text-muted-foreground max-w-xl mx-auto text-sm">
          Six capabilities working together to protect margin, accelerate billing, and eliminate surprises.
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {features.map((f) => {
          const Icon = f.icon
          return (
            <div
              key={f.title}
              className={`${f.size === 'col-span-2' ? 'md:col-span-2' : ''} rounded-2xl border border-border/50 p-6 flex flex-col gap-4`}
              style={{
                background: 'rgba(255,255,255,0.03)',
                backdropFilter: 'blur(8px)',
              }}
            >
              <div className={`w-10 h-10 rounded-xl ${f.bg} flex items-center justify-center`}>
                <Icon className={`w-5 h-5 ${f.accent}`} />
              </div>
              <div>
                <h3 className="text-foreground font-semibold mb-1">{f.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{f.description}</p>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}