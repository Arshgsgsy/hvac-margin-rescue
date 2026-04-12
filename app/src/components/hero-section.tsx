'use client'

import Link from 'next/link'
import { Project, PortfolioSummary } from '@/lib/types'
import { formatCurrency, formatPercent } from '@/lib/data'

interface Props {
  projects: Project[]
  portfolio: PortfolioSummary | null
}

export default function HeroSection({ projects, portfolio }: Props) {
  const criticalCount = projects.filter((p) => p.severity === 'critical').length
  const totalRecovery = projects.flatMap((p) => p.recovery_actions ?? []).reduce((s, a) => s + a.amount, 0)

  return (
    <section className="relative w-full overflow-hidden rounded-2xl mx-auto" style={{ background: 'hsl(var(--background))' }}>
      <div className="absolute inset-0 z-0">
        <svg width="100%" height="100%" viewBox="0 0 1220 700" fill="none" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice">
          <g>
            {[...Array(35)].map((_, i) =>
              [...Array(20)].map((_, j) => (
                <rect key={`${i}-${j}`} x={-20 + i * 36} y={9 + j * 36} width="35.6" height="35.6"
                  stroke="hsl(var(--foreground))" strokeOpacity="0.06" strokeWidth="0.4" strokeDasharray="2 2" />
              ))
            )}
            {[[700,81],[200,153],[1020,153],[125,225],[1095,225],[950,297],[230,333],[520,405],[770,405]].map(([x,y],i) => (
              <rect key={i} x={x} y={y} width="36" height="36" fill="hsl(var(--foreground))" fillOpacity="0.06" />
            ))}
          </g>
          <g filter="url(#glow1)">
            <path d="M1447 -87V-149H1770V1249H466V894C1008 894 1447 455 1447 -87Z" fill="url(#grad1)" />
          </g>
          <g filter="url(#glow2)" style={{ mixBlendMode: 'lighten' }}>
            <path d="M1567 -231V-293H1890V1105H586V750C1128 750 1567 311 1567 -231Z" fill="url(#grad2)" />
          </g>
          <defs>
            <filter id="glow1" x="147" y="-468" width="1942" height="2036" filterUnits="userSpaceOnUse" colorInterpolationFilters="sRGB">
              <feGaussianBlur stdDeviation="159" result="blur" />
            </filter>
            <filter id="glow2" x="427" y="-452" width="1623" height="1717" filterUnits="userSpaceOnUse" colorInterpolationFilters="sRGB">
              <feGaussianBlur stdDeviation="80" result="blur" />
            </filter>
            <linearGradient id="grad1" x1="1118" y1="-149" x2="1118" y2="1249" gradientUnits="userSpaceOnUse">
              <stop stopColor="hsl(var(--primary-dark))" />
              <stop offset="0.58" stopColor="hsl(var(--primary-light))" />
              <stop offset="1" stopColor="hsl(var(--primary))" />
            </linearGradient>
            <linearGradient id="grad2" x1="1238" y1="-293" x2="1238" y2="1105" gradientUnits="userSpaceOnUse">
              <stop stopColor="hsl(var(--primary-dark))" />
              <stop offset="0.58" stopColor="hsl(var(--primary-light))" />
              <stop offset="1" stopColor="hsl(var(--primary))" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      <div className="relative z-10 flex flex-col items-start px-8 pt-28 pb-20 max-w-3xl">
        <div className="flex items-center gap-2 mb-6 px-3 py-1.5 rounded-full border text-xs font-medium"
          style={{ borderColor: 'hsl(var(--border))', background: 'hsl(var(--secondary))', color: 'hsl(var(--muted-foreground))' }}>
          <span className="w-1.5 h-1.5 rounded-full bg-destructive animate-pulse inline-block" />
          {criticalCount} critical projects identified -- AI analysis complete
        </div>

        <h1 className="text-4xl md:text-5xl lg:text-6xl font-semibold text-foreground leading-tight mb-5">
          Your HVAC Portfolio<br />
          <span style={{ color: 'hsl(var(--primary-light))' }}>Has a Margin Problem.</span>
        </h1>

        <p className="text-muted-foreground text-base md:text-lg leading-relaxed mb-8 max-w-xl">
          {criticalCount} critical projects are eroding profit right now.
          The AI has diagnosed the root causes and identified{' '}
          <span className="text-foreground font-semibold">{formatCurrency(totalRecovery)}</span>{' '}
          in recoverable value -- with a ranked action plan waiting for you.
        </p>

        <div className="flex items-center gap-4">
          <a href="#priority-queue"
            className="px-6 py-2.5 rounded-full text-sm font-semibold transition-all"
            style={{ background: 'hsl(var(--foreground))', color: 'hsl(var(--background))' }}>
            View Priority Actions
          </a>
          <a href="#all-projects"
            className="px-6 py-2.5 rounded-full text-sm font-medium border transition-all"
            style={{ borderColor: 'hsl(var(--border))', color: 'hsl(var(--muted-foreground))' }}>
            Full Portfolio
          </a>
        </div>
      </div>

      {portfolio && (
        <div className="relative z-10 mx-8 mb-8 rounded-xl border px-6 py-4 grid grid-cols-2 gap-4 md:grid-cols-4"
          style={{ background: 'rgba(255,255,255,0.03)', borderColor: 'hsl(var(--border))', backdropFilter: 'blur(8px)' }}>
          {[
            { label: 'Portfolio Value', value: formatCurrency(portfolio.total_value), note: `${portfolio.total_projects} projects` },
            { label: 'Avg Realized Margin', value: formatPercent(portfolio.avg_realized_margin), note: `Bid avg ${formatPercent(portfolio.avg_bid_margin)}` },
            { label: 'Flagged', value: `${portfolio.flagged_count} Projects`, note: `${portfolio.critical_count} critical` },
            { label: 'Recovery Potential', value: formatCurrency(totalRecovery), note: 'AI-identified' },
          ].map((s) => (
            <div key={s.label}>
              <p className="text-xs mb-1" style={{ color: 'hsl(var(--muted-foreground))' }}>{s.label}</p>
              <p className="text-xl font-bold text-foreground">{s.value}</p>
              <p className="text-xs mt-0.5" style={{ color: 'hsl(var(--muted-foreground))' }}>{s.note}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
