import { Project } from './types'

export function buildProjectContext(project: Project): string {
  const pct = (n: number) => `${(n * 100).toFixed(1)}%`
  const usd = (n: number) => n >= 1000000 ? `$${(n / 1000000).toFixed(2)}M` : `$${(n / 1000).toFixed(0)}K`

  return `PROJECT: ${project.id} -- ${project.name}
SECTOR: ${project.sector}
CONTRACT VALUE: ${usd(project.contractValue)}

MARGIN ANALYSIS
  Bid Margin:      ${pct(project.bidMargin)}
  Realized Margin: ${pct(project.realizedMargin)}
  Margin Erosion:  ${pct(Math.abs(project.marginDelta))} below bid
  Severity:        ${project.severity.toUpperCase()}

COST BREAKDOWN
  Labor    -- Budget: ${usd(project.laborCost.budget)} | Actual: ${usd(project.laborCost.actual)} | Overrun: ${usd(project.laborOverrun)}
  Material -- Budget: ${usd(project.materialCost.budget)} | Actual: ${usd(project.materialCost.actual)} | Overrun: ${usd(project.materialOverrun)}

BILLING STATUS
  % Complete: ${pct(project.billingStatus.percentComplete)}
  % Billed:   ${pct(project.billingStatus.percentBilled)}
  Billing Gap: ${pct(project.billingGap)} (${usd(project.contractValue * project.billingGap)} unbilled)

FIELD NOTES
${project.fieldNoteSummary ?? 'None available.'}

CHANGE ORDERS (${project.changeOrders?.length ?? 0})
${project.changeOrders?.map(co => `  ${co.id} [${co.status.toUpperCase()}] ${usd(co.costIncurred)} -- ${co.description}`).join('\n') ?? '  None'}

OPEN RFIs
${project.rfis?.filter(r => r.status === 'open').map(r => `  ${r.id} -- open ${r.daysOpen}d -- ${r.description}`).join('\n') ?? '  None'}
`
}
