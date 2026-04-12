export type Severity = 'critical' | 'warning' | 'watch'

export interface CostBreakdown {
  budget: number
  actual: number
}

export interface SOVLine {
  name: string
  budgeted: number
  actual: number
}

export interface LaborWeek {
  week: string
  regular: number
  overtime: number
}

export interface MaterialDelivery {
  description: string
  total_cost: number
  date: string
  condition: string
  vendor: string
}

export interface BillingPeriod {
  period_end: string
  period_total: number
  cumulative_billed: number
  retention_held: number
  status: string
}

export interface RFIWeek {
  week: string
  rfi_count: number
}

export interface ChangeOrder {
  id: string
  description: string
  amount: number
  status: string
  reason_category: string
}

export interface RFI {
  id: string
  status: string
  days_open: number
  description: string
  priority: string
  cost_impact: boolean
}

export interface Project {
  id: string
  name: string
  sector: string
  contract_value: number
  bid_margin: number
  realized_margin: number
  margin_delta: number
  severity: Severity
  labor_overrun: number
  material_overrun: number
  billing_gap: number
  labor_cost: CostBreakdown
  material_cost: CostBreakdown
  billing_status: { percent_complete: number; percent_billed: number }
  root_cause?: string | null
  root_causes?: string[] | null
  recovery_actions?: { description: string; amount: number; priority: string; category: string }[] | null
  field_note_summary?: string | null
  change_orders?: ChangeOrder[]
  rfis?: RFI[]
  sov_lines?: SOVLine[]
  labor_by_week?: LaborWeek[]
  material_deliveries?: MaterialDelivery[]
  billing_history?: BillingPeriod[]
  rfi_by_week?: RFIWeek[]
  total_recoverable_estimate?: number | null
  analysis_confidence?: string | null
  headline?: string | null
}

export interface PortfolioSummary {
  total_projects: number
  total_value: number
  avg_bid_margin: number
  avg_realized_margin: number
  flagged_count: number
  critical_count: number
  total_exposure: number
  total_recoverable?: number
}

export type PipelineStepStatus = 'idle' | 'running' | 'complete' | 'error'

export interface PipelineStep {
  id: string
  label: string
  description: string
  status: PipelineStepStatus
  duration?: number
  logs: string[]
}

export interface PipelineResult {
  status: string
  total_duration_seconds: number
  steps: PipelineStep[]
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}
