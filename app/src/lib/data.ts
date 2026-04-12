import { Project } from './types'

export function formatCurrency(value: number): string {
  if (Math.abs(value) >= 1000000) return `$${(value / 1000000).toFixed(2)}M`
  if (Math.abs(value) >= 1000) return `$${(value / 1000).toFixed(0)}K`
  return `$${value.toFixed(0)}`
}

export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}

export function getPriorityScore(p: Project): number {
  const erosion = Math.abs(p.margin_delta) * 100
  const billing = p.billing_gap * 100 * 0.6
  const overrun = ((p.labor_overrun + p.material_overrun) / p.contract_value) * 100 * 0.4
  return erosion + billing + overrun
}

export function getSortedByPriority(projects: Project[]): Project[] {
  return [...projects].sort((a, b) => getPriorityScore(b) - getPriorityScore(a))
}
