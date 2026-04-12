import { Project } from './types'

export function buildProjectContext(project: Project): string {
  const pct = (n: number) => `${(n * 100).toFixed(1)}%`
  const usd = (n: number) => n >= 1000000 ? `$${(n / 1000000).toFixed(2)}M` : `$${(n / 1000).toFixed(0)}K`

  return `PROJECT: ${project.id} -- ${project.name}
SECTOR: ${project.sector}
CONTRACT VALUE: ${usd(project.contract_value)}

MARGIN ANALYSIS
  Bid Margin:      ${pct(project.bid_margin)}
  Realized Margin: ${pct(project.realized_margin)}
  Margin Erosion:  ${pct(Math.abs(project.margin_delta))} below bid
  Severity:        ${project.severity.toUpperCase()}

COST BREAKDOWN
  Labor    -- Budget: ${usd(project.labor_cost.budget)} | Actual: ${usd(project.labor_cost.actual)} | Overrun: ${usd(project.labor_overrun)}
  Material -- Budget: ${usd(project.material_cost.budget)} | Actual: ${usd(project.material_cost.actual)} | Overrun: ${usd(project.material_overrun)}

BILLING STATUS
  % Complete: ${pct(project.billing_status.percent_complete)}
  % Billed:   ${pct(project.billing_status.percent_billed)}
  Billing Gap: ${pct(project.billing_gap)} (${usd(project.contract_value * project.billing_gap)} unbilled)

FIELD NOTES
${project.field_note_summary ?? 'None available.'}

CHANGE ORDERS (${project.change_orders?.length ?? 0})
${project.change_orders?.map(co => `  ${co.id} [${co.status.toUpperCase()}] ${usd(co.amount)} -- ${co.description}`).join('\n') ?? '  None'}

OPEN RFIs
${project.rfis?.filter(r => r.status === 'open').map(r => `  ${r.id} -- open ${r.days_open}d -- ${r.description}`).join('\n') ?? '  None'}
`
}
