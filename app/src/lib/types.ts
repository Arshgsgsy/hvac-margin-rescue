export type Severity = 'critical' | 'warning' | 'watch'

export interface RecoveryAction {
  description: string
  amount: number
  priority: 'high' | 'medium' | 'low'
  category: 'billing' | 'change_order' | 'labor' | 'material' | 'renegotiation'
}

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
  budgetedCost: number
  actualCost: number
  condition: 'Good' | 'Damaged' | 'Partial' | 'Reordered'
  date: string
}

export interface BillingMonth {
  month: string
  billed: number
  actualCost: number
}

export interface RFIWeek {
  week: string
  rfiCount: number
  weeklyCost: number
}

export interface ChangeOrder {
  id: string
  description: string
  costIncurred: number
  billedToClient: boolean
  status: string
  marginImpact: number
}

export interface Project {
  id: string
  name: string
  sector: string
  contractValue: number
  bidMargin: number
  realizedMargin: number
  marginDelta: number
  severity: Severity
  laborOverrun: number
  materialOverrun: number
  billingGap: number
  laborCost: CostBreakdown
  materialCost: CostBreakdown
  billingStatus: { percentComplete: number; percentBilled: number }
  rootCause?: string
  recoveryActions?: RecoveryAction[]
  fieldNoteSummary?: string
  changeOrders?: ChangeOrder[]
  rfis?: { id: string; status: string; daysOpen: number; description: string }[]
  sovLines?: SOVLine[]
  laborByWeek?: LaborWeek[]
  materialDeliveries?: MaterialDelivery[]
  billingHistory?: BillingMonth[]
  rfiByWeek?: RFIWeek[]
}

export interface PortfolioSummary {
  totalProjects: number
  totalValue: number
  avgBidMargin: number
  avgRealizedMargin: number
  flaggedCount: number
  criticalCount: number
  totalExposure: number
}

export type PipelineStepStatus = 'idle' | 'running' | 'complete' | 'error'

export interface PipelineStep {
  id: string
  label: string
  description: string
  script: string
  logs: string[]
  status: PipelineStepStatus
  duration?: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}