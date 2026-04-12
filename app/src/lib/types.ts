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
  reason_category?: string
  reasonCategory?: string
  co_number?: string
  costIncurred?: number
  billedToClient?: boolean
  marginImpact?: number
}

export interface RFI {
  id: string
  status: string
  days_open: number
  description: string
  priority?: string
  cost_impact?: boolean
  daysOpen?: number
}

export interface RootCause {
  label: string
  category?: string
  impact_dollars?: number | null
  confidence?: number | null
  evidence?: string[]
  counter_evidence?: string[]
  summary?: string
}

export interface RecoveryAction {
  id?: string
  priority?: number
  action: string
  description: string
  owner?: string
  financial_logic?: string | null
  estimated_recovery_dollars?: number | null
  amount: number
  urgency?: 'immediate' | 'this_week' | 'this_month' | 'ongoing'
  effort?: 'low' | 'medium' | 'high' | null
  time_to_cash_days?: number | null
  linked_root_cause?: string | null
  cost_to_execute_hours?: number | null
  expected_value?: number | null
  recovery_type?: 'billing' | 'change_order' | 'retention' | 'operational' | 'claim' | string | null
  probability_of_success?: number | null
  blocking_items?: string[]
  evidence_refs?: string[]
}

export interface ProfitImpact {
  current_margin_dollars: number
  projected_margin_dollars: number
  net_improvement: number
}

export interface RecoveryByTiming {
  immediate: number | null
  near_term: number | null
  long_term: number | null
}

export interface ProjectMoneyBrief {
  project_mode?: string | null
  cash_this_week?: number | null
  cash_in_30_days?: number | null
  total_recoverable?: number | null
  break_even_recovery_needed?: number | null
}

export interface Project {
  [key: string]: any
  id: string
  name: string
  sector: string
  gc_name?: string | null
  contract_value: number
  bid_margin: number
  realized_margin: number
  margin_delta: number
  severity: Severity
  alert_class?: 'hard_alert' | 'watch_signal' | null
  trigger_score?: number
  primary_trigger?: Record<string, any> | null
  supporting_triggers?: Record<string, any>[]
  fired_triggers?: Record<string, any>[]
  why_now?: string | null
  alert_state?: 'new' | 'escalated' | 'worsened' | 'ongoing' | null
  should_realert?: boolean
  project_stage?: string | null
  money_at_risk?: number
  realized_margin_dollars?: number
  current_margin_dollars?: number
  estimated_cost_total?: number
  actual_cost_total?: number
  retention_held?: number
  labor_overrun: number
  material_overrun: number
  billing_gap: number
  co_approved_value?: number
  co_pending_value?: number
  co_rejected_value?: number
  labor_cost: CostBreakdown
  material_cost: CostBreakdown
  billing_status: { percent_complete: number; percent_billed: number }
  contractValue?: number
  bidMargin?: number
  realizedMargin?: number
  marginDelta?: number
  laborOverrun?: number
  materialOverrun?: number
  billingGap?: number
  laborCost?: CostBreakdown
  materialCost?: CostBreakdown
  billingStatus?: { percentComplete: number; percentBilled: number }
  headline: string | null
  root_cause: string | null
  root_causes: RootCause[]
  rootCause?: string | null
  recovery_actions: RecoveryAction[]
  recoveryActions?: RecoveryAction[]
  primary_action?: RecoveryAction | null
  next_actions?: RecoveryAction[]
  project_mode?: string | null
  executive_brief?: string | null
  field_note_summary: string | null
  fieldNoteSummary?: string | null
  forecast_if_no_action?: string | null
  forecast_with_action?: string | null
  no_action_risk?: string | null
  action_outlook?: string | null
  total_recoverable_estimate: number | null
  profit_impact?: ProfitImpact | null
  recovery_by_timing?: RecoveryByTiming | null
  break_even_recovery_needed?: number | null
  analysis_confidence: number | null
  do_not_pursue?: Array<string | { reason?: string; action?: string }>
  blocking_items?: string[]
  money_brief?: ProjectMoneyBrief | null
  change_orders: ChangeOrder[]
  changeOrders?: ChangeOrder[]
  rfis: RFI[]
  sov_lines: SOVLine[]
  sovLines?: SOVLine[]
  labor_by_week: LaborWeek[]
  laborByWeek?: LaborWeek[]
  material_deliveries: MaterialDelivery[]
  materialDeliveries?: MaterialDelivery[]
  billing_history: BillingPeriod[]
  billingHistory?: BillingPeriod[]
  rfi_by_week: RFIWeek[]
  llm_financial_snapshot?: Record<string, any> | null
  recoverability_summary?: Record<string, any> | null
}

export interface ThisWeekPlanAction {
  day: string
  project_id: string
  project_name?: string
  action_summary: string
  owner: string
  hours_required: number
  expected_recovery: number
}

export interface PortfolioBrief {
  executive_brief: string
  optimization_available: boolean
  cash_this_week: number
  cash_in_30_days: number
  achievable_recovery: number
  theoretical_recovery: number
  top_actions: Array<RecoveryAction & { project_id?: string; project_name?: string; severity?: Severity }>
  this_week_plan: ThisWeekPlanAction[]
  owner_plan: Array<{ owner: string; hours: number }>
  projects_requiring_exec_attention: Project[]
  projects_to_deprioritize: Array<Record<string, any>>
  strategic_insights: Array<Record<string, any>>
  biggest_blockers: string[]
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
  total_recoverable?: number
  optimization_available?: boolean
  brief?: PortfolioBrief
  totalProjects?: number
  totalValue?: number
  avgBidMargin?: number
  avgRealizedMargin?: number
  flaggedCount?: number
  criticalCount?: number
  totalExposure?: number
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

export interface PipelineJob {
  id: string
  kind: string
  trigger: string
  status: 'queued' | 'running' | 'complete' | 'error'
  created_at: string
  updated_at: string
  started_at?: string | null
  completed_at?: string | null
  error?: string | null
  metadata?: Record<string, any>
  result?: PipelineResult | null
  steps?: PipelineStep[]
}

export interface UploadResult {
  status: string
  files: { name: string; size_bytes: number }[]
  available_files: string[]
  missing_required: string[]
  missing_optional: string[]
  can_run_pipeline: boolean
  active_data_dir: string
  pipeline_job?: PipelineJob | null
}

export interface HealthStatus {
  status: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}
