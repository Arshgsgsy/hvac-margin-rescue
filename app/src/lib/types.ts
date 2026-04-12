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
  budgetedCost?: number
  actualCost?: number
}

export interface BillingPeriod {
  period_end: string
  period_total: number
  cumulative_billed: number
  retention_held: number
  status: string
  month?: string
  billed?: number
  actualCost?: number
}

export interface RFIWeek {
  week: string
  rfi_count: number
  weeklyCost?: number
}

export interface ChangeOrder {
  id: string
  description: string
  amount: number
  status: string
  reason_category: string
  reasonCategory: string
  co_number: string
  costIncurred: number
  billedToClient: boolean
  marginImpact: number
}

export interface RFI {
  id: string
  status: string
  days_open: number
  description: string
  priority: string
  cost_impact: boolean
  daysOpen: number
}

export interface RecoveryAction {
  description: string
  amount: number
  priority: string
  category: string
}

export interface Project {
  [key: string]: any
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
  contractValue: number
  bidMargin: number
  realizedMargin: number
  marginDelta: number
  laborOverrun: number
  materialOverrun: number
  billingGap: number
  laborCost: CostBreakdown
  materialCost: CostBreakdown
  billingStatus: { percentComplete: number; percentBilled: number }
  root_cause: string | null
  root_causes: string[] | null
  rootCause: string | null
  recovery_actions: RecoveryAction[] | null
  recoveryActions: RecoveryAction[] | null
  field_note_summary: string | null
  fieldNoteSummary: string | null
  change_orders: ChangeOrder[]
  changeOrders: ChangeOrder[]
  rfis: RFI[]
  sov_lines: SOVLine[]
  sovLines: SOVLine[]
  labor_by_week: LaborWeek[]
  laborByWeek: LaborWeek[]
  material_deliveries: MaterialDelivery[]
  materialDeliveries: MaterialDelivery[]
  billing_history: BillingPeriod[]
  billingHistory: BillingPeriod[]
  rfi_by_week: RFIWeek[]
  total_recoverable_estimate: number | null
  analysis_confidence: string | null
  headline: string | null
}

export interface PortfolioSummary {
  [key: string]: any
  total_projects: number
  total_value: number
  avg_bid_margin: number
  avg_realized_margin: number
  flagged_count: number
  critical_count: number
  total_exposure: number
  total_recoverable: number
  totalProjects: number
  totalValue: number
  avgBidMargin: number
  avgRealizedMargin: number
  flaggedCount: number
  criticalCount: number
  totalExposure: number
  data_availability: {
    available_features: string[]
    missing_features: string[]
    degraded_mode: boolean
  }
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
  degraded_mode?: boolean
  data_dir?: string
  available_files?: string[]
  missing_optional?: string[]
  summary?: PortfolioSummary | null
  flagged_projects?: Array<{ project_id: string; project_name: string; severity: Severity }>
}

export interface UploadResult {
  status: string
  files: { name: string; size_bytes: number }[]
  available_files: string[]
  missing_required: string[]
  missing_optional: string[]
  can_run_pipeline: boolean
  active_data_dir: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}
