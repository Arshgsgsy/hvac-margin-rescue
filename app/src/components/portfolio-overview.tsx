import { PortfolioSummary } from '@/lib/types'
import { formatCurrency, formatPercent } from '@/lib/data'

interface Props {
  summary: PortfolioSummary
}

export default function PortfolioOverview({ summary }: Props) {
  const cards = [
    {
      label: 'Total Portfolio Value',
      value: formatCurrency(summary.totalValue),
      sub: `${summary.totalProjects} active projects`,
      color: '#3b82f6',
    },
    {
      label: 'Avg Realized Margin',
      value: formatPercent(summary.avgRealizedMargin),
      sub: `Bid avg: ${formatPercent(summary.avgBidMargin)}`,
      color: summary.avgRealizedMargin < summary.avgBidMargin - 0.02 ? '#f59e0b' : '#10b981',
    },
    {
      label: 'Flagged Projects',
      value: summary.flaggedCount.toString(),
      sub: `${summary.criticalCount} critical`,
      color: '#ef4444',
    },
    {
      label: 'Total Exposure',
      value: formatCurrency(summary.totalExposure),
      sub: 'Labor + material overruns',
      color: '#f59e0b',
    },
  ]

  return (
    <div>
      <h2 className="text-white font-semibold text-lg mb-4">Portfolio Health</h2>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {cards.map((card) => (
          <div key={card.label} className="rounded-lg p-5 border" style={{ background: '#111827', borderColor: '#1e3a5f' }}>
            <p className="text-xs mb-2" style={{ color: '#64748b' }}>{card.label}</p>
            <p className="text-2xl font-bold mb-1" style={{ color: card.color }}>{card.value}</p>
            <p className="text-xs" style={{ color: '#475569' }}>{card.sub}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
