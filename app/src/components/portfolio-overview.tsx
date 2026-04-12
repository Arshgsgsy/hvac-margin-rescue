import { PortfolioSummary } from '@/lib/types'
import { formatCurrency, formatPercent } from '@/lib/data'

interface Props {
  summary: PortfolioSummary
}

export default function PortfolioOverview({ summary }: Props) {
  const cards = [
    {
      label: 'Total Portfolio Value',
      value: formatCurrency(summary.total_value),
      sub: `${summary.total_projects} active projects`,
      color: '#3b82f6',
    },
    {
      label: 'Avg Realized Margin',
      value: formatPercent(summary.avg_realized_margin),
      sub: `Bid avg: ${formatPercent(summary.avg_bid_margin)}`,
      color: summary.avg_realized_margin < summary.avg_bid_margin - 0.02 ? '#f59e0b' : '#10b981',
    },
    {
      label: 'Flagged Projects',
      value: summary.flagged_count.toString(),
      sub: `${summary.critical_count} critical`,
      color: '#ef4444',
    },
    {
      label: 'Total Exposure',
      value: formatCurrency(summary.total_exposure),
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
