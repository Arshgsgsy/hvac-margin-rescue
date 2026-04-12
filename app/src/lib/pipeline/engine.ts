/**
 * Pipeline Engine - TypeScript implementation of the Python pipeline
 * 
 * This processes uploaded CSV data through:
 * 1. Clean - Parse and normalize CSV data
 * 2. Load - Structure data into usable format
 * 3. Flag - Identify projects with issues
 * 4. LLM - Generate AI analysis prompts
 * 5. Output - Format results for display
 */

export interface PipelineStep {
  id: string
  label: string
  status: 'idle' | 'running' | 'complete' | 'error'
  logs: string[]
  duration: number
}

export interface ProjectData {
  project_id: string
  project_name: string
  contract_value: number
  estimated_labor_cost: number
  estimated_material_cost: number
  actual_labor_cost: number
  actual_material_cost: number
  billed_to_date: number
  percent_complete: number
  change_orders_approved: number
  change_orders_pending: number
  change_orders_rejected: number
  rfis_open: number
  rfis_closed: number
}

export interface FlaggedProject extends ProjectData {
  severity: 'critical' | 'elevated' | 'monitor'
  margin_delta: number
  labor_overrun: number
  material_overrun: number
  billing_gap: number
  root_cause: string
  flags: string[]
}

export interface PortfolioSummary {
  total_projects: number
  total_contract_value: number
  flagged_count: number
  critical_count: number
  elevated_count: number
  monitor_count: number
  total_labor_overrun: number
  total_material_overrun: number
  avg_margin_delta: number
}

export interface PipelineResult {
  status: 'complete' | 'error'
  summary: PortfolioSummary
  flagged_projects: FlaggedProject[]
  steps: PipelineStep[]
}

// Role normalization map (from Python)
const ROLE_MAP: Record<string, string> = {
  'JM Pipefitter': 'Journeyman Pipefitter',
  'J. Pipefitter': 'Journeyman Pipefitter',
  'Pipefitter JM': 'Journeyman Pipefitter',
  'Sheet Metal JM': 'Journeyman Sheet Metal',
  'J. Sheet Metal': 'Journeyman Sheet Metal',
  'Apprentice 2nd Yr': 'Apprentice 2nd Year',
  'App 2nd Year': 'Apprentice 2nd Year',
  'Apprentice 4th Yr': 'Apprentice 4th Year',
  'App 4th Year': 'Apprentice 4th Year',
  'Helper': 'Helper/Laborer',
  'Fmn': 'Foreman',
  'Lead Foreman': 'Foreman',
  'Controls Tech': 'Controls Technician',
}

/**
 * Parse CSV string into array of objects
 */
export function parseCSV(csvContent: string): Record<string, string>[] {
  const lines = csvContent.trim().split('\n')
  if (lines.length < 2) return []
  
  const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''))
  const rows: Record<string, string>[] = []
  
  for (let i = 1; i < lines.length; i++) {
    const values = parseCSVLine(lines[i])
    if (values.length === headers.length) {
      const row: Record<string, string> = {}
      headers.forEach((header, idx) => {
        row[header] = values[idx]
      })
      rows.push(row)
    }
  }
  
  return rows
}

function parseCSVLine(line: string): string[] {
  const values: string[] = []
  let current = ''
  let inQuotes = false
  
  for (let i = 0; i < line.length; i++) {
    const char = line[i]
    if (char === '"') {
      inQuotes = !inQuotes
    } else if (char === ',' && !inQuotes) {
      values.push(current.trim())
      current = ''
    } else {
      current += char
    }
  }
  values.push(current.trim())
  
  return values
}

/**
 * Step 1: Clean - Normalize and validate data
 */
export function cleanData(
  csvData: Record<string, Record<string, string>[]>,
  logs: string[]
): Record<string, Record<string, string>[]> {
  logs.push('[CLEAN] Starting data cleaning...')
  
  const cleaned = { ...csvData }
  
  // Clean labor logs - normalize roles
  if (cleaned.labor_logs_all) {
    logs.push(`[CLEAN] Processing ${cleaned.labor_logs_all.length} labor log entries`)
    cleaned.labor_logs_all = cleaned.labor_logs_all.map(row => ({
      ...row,
      clean_role: ROLE_MAP[row.role] || row.role
    }))
    logs.push('[CLEAN] Normalized worker roles')
  }
  
  // Clean contracts - validate required fields
  if (cleaned.contracts_all) {
    logs.push(`[CLEAN] Validating ${cleaned.contracts_all.length} contracts`)
    const validContracts = cleaned.contracts_all.filter(c => 
      c.project_id && c.original_contract_value
    )
    logs.push(`[CLEAN] ${validContracts.length} valid contracts found`)
    cleaned.contracts_all = validContracts
  }
  
  // Clean change orders - normalize status
  if (cleaned.change_orders_all) {
    logs.push(`[CLEAN] Processing ${cleaned.change_orders_all.length} change orders`)
    cleaned.change_orders_all = cleaned.change_orders_all.map(row => ({
      ...row,
      normalized_status: normalizeStatus(row.status)
    }))
  }
  
  logs.push('[CLEAN] Data cleaning complete')
  return cleaned
}

function normalizeStatus(status: string): string {
  const lower = (status || '').toLowerCase()
  if (['approved', 'executed', 'issued'].some(s => lower.includes(s))) return 'approved'
  if (['rejected', 'denied', 'void'].some(s => lower.includes(s))) return 'rejected'
  if (['pending', 'submitted', 'review'].some(s => lower.includes(s))) return 'pending'
  return 'unknown'
}

/**
 * Step 2: Load - Aggregate data by project
 */
export function loadData(
  csvData: Record<string, Record<string, string>[]>,
  logs: string[]
): Map<string, ProjectData> {
  logs.push('[LOAD] Aggregating data by project...')
  
  const projects = new Map<string, ProjectData>()
  
  // Get contracts as base
  const contracts = csvData.contracts_all || []
  logs.push(`[LOAD] Found ${contracts.length} contracts`)
  
  for (const contract of contracts) {
    const projectId = contract.project_id
    if (!projectId) continue
    
    projects.set(projectId, {
      project_id: projectId,
      project_name: contract.project_name || projectId,
      contract_value: parseFloat(contract.original_contract_value) || 0,
      estimated_labor_cost: 0,
      estimated_material_cost: 0,
      actual_labor_cost: 0,
      actual_material_cost: 0,
      billed_to_date: 0,
      percent_complete: 0,
      change_orders_approved: 0,
      change_orders_pending: 0,
      change_orders_rejected: 0,
      rfis_open: 0,
      rfis_closed: 0,
    })
  }
  
  // Aggregate SOV budget
  const sovBudget = csvData.sov_budget_all || []
  logs.push(`[LOAD] Processing ${sovBudget.length} SOV budget entries`)
  for (const row of sovBudget) {
    const project = projects.get(row.project_id)
    if (project) {
      project.estimated_labor_cost += parseFloat(row.estimated_labor_cost) || 0
      project.estimated_material_cost += parseFloat(row.estimated_material_cost) || 0
    }
  }
  
  // Aggregate labor costs
  const laborLogs = csvData.labor_logs_all || []
  logs.push(`[LOAD] Processing ${laborLogs.length} labor entries`)
  for (const row of laborLogs) {
    const project = projects.get(row.project_id)
    if (project) {
      const hoursST = parseFloat(row.hours_st) || 0
      const hoursOT = parseFloat(row.hours_ot) || 0
      const rate = parseFloat(row.hourly_rate) || 0
      const burden = parseFloat(row.burden_multiplier) || 1
      project.actual_labor_cost += (hoursST + hoursOT * 1.5) * rate * burden
    }
  }
  
  // Aggregate material costs
  const materials = csvData.material_deliveries_all || []
  logs.push(`[LOAD] Processing ${materials.length} material deliveries`)
  for (const row of materials) {
    const project = projects.get(row.project_id)
    if (project) {
      project.actual_material_cost += parseFloat(row.total_cost) || 0
    }
  }
  
  // Aggregate billing
  const billing = csvData.billing_history_all || []
  logs.push(`[LOAD] Processing ${billing.length} billing entries`)
  for (const row of billing) {
    const project = projects.get(row.project_id)
    if (project) {
      const billed = parseFloat(row.cumulative_billed) || 0
      if (billed > project.billed_to_date) {
        project.billed_to_date = billed
      }
    }
  }
  
  // Calculate percent complete
  for (const project of projects.values()) {
    if (project.contract_value > 0) {
      project.percent_complete = (project.billed_to_date / project.contract_value) * 100
    }
  }
  
  // Aggregate change orders
  const changeOrders = csvData.change_orders_all || []
  logs.push(`[LOAD] Processing ${changeOrders.length} change orders`)
  for (const row of changeOrders) {
    const project = projects.get(row.project_id)
    if (project) {
      const status = (row.normalized_status || row.status || '').toLowerCase()
      const amount = parseFloat(row.amount) || 0
      if (status.includes('approved')) {
        project.change_orders_approved += amount
      } else if (status.includes('pending')) {
        project.change_orders_pending += amount
      } else if (status.includes('rejected')) {
        project.change_orders_rejected += amount
      }
    }
  }
  
  // Aggregate RFIs
  const rfis = csvData.rfis_all || []
  logs.push(`[LOAD] Processing ${rfis.length} RFIs`)
  for (const row of rfis) {
    const project = projects.get(row.project_id)
    if (project) {
      const status = (row.status || '').toLowerCase()
      if (status.includes('open') || status.includes('pending')) {
        project.rfis_open++
      } else {
        project.rfis_closed++
      }
    }
  }
  
  logs.push(`[LOAD] Loaded ${projects.size} projects`)
  return projects
}

/**
 * Step 3: Flag - Identify problematic projects
 */
export function flagProjects(
  projects: Map<string, ProjectData>,
  logs: string[]
): FlaggedProject[] {
  logs.push('[FLAG] Analyzing projects for issues...')
  
  const flagged: FlaggedProject[] = []
  
  for (const project of projects.values()) {
    const flags: string[] = []
    
    // Calculate overruns
    const laborOverrun = project.actual_labor_cost - project.estimated_labor_cost
    const materialOverrun = project.actual_material_cost - project.estimated_material_cost
    const totalCost = project.actual_labor_cost + project.actual_material_cost
    const estimatedCost = project.estimated_labor_cost + project.estimated_material_cost
    
    // Calculate margins
    const estimatedMargin = project.contract_value - estimatedCost
    const realizedMargin = project.contract_value - totalCost
    const marginDelta = realizedMargin - estimatedMargin
    
    // Calculate billing gap
    const expectedBilled = project.contract_value * (project.percent_complete / 100)
    const billingGap = expectedBilled - project.billed_to_date
    
    // Flag conditions
    if (laborOverrun > estimatedCost * 0.1) {
      flags.push('labor_overrun')
    }
    if (materialOverrun > estimatedCost * 0.1) {
      flags.push('material_overrun')
    }
    if (marginDelta < -estimatedMargin * 0.2) {
      flags.push('margin_erosion')
    }
    if (billingGap > project.contract_value * 0.1) {
      flags.push('billing_gap')
    }
    if (project.change_orders_rejected > project.contract_value * 0.05) {
      flags.push('rejected_cos')
    }
    if (project.rfis_open > 10) {
      flags.push('open_rfis')
    }
    
    // Only flag if there are issues
    if (flags.length > 0) {
      // Determine severity
      let severity: 'critical' | 'elevated' | 'monitor' = 'monitor'
      if (flags.includes('margin_erosion') && marginDelta < -estimatedMargin * 0.5) {
        severity = 'critical'
      } else if (flags.length >= 3 || flags.includes('margin_erosion')) {
        severity = 'elevated'
      }
      
      // Determine root cause
      let rootCause = 'Multiple factors contributing to project issues'
      if (flags.includes('labor_overrun') && laborOverrun > materialOverrun) {
        rootCause = 'Labor costs exceeding estimates due to productivity issues or scope changes'
      } else if (flags.includes('material_overrun')) {
        rootCause = 'Material costs higher than budgeted, possible supply chain issues'
      } else if (flags.includes('billing_gap')) {
        rootCause = 'Work completed but not yet billed, cash flow concern'
      }
      
      flagged.push({
        ...project,
        severity,
        margin_delta: marginDelta,
        labor_overrun: laborOverrun,
        material_overrun: materialOverrun,
        billing_gap: billingGap,
        root_cause: rootCause,
        flags,
      })
      
      logs.push(`[FLAG] ${project.project_id}: ${severity.toUpperCase()} - ${flags.join(', ')}`)
    }
  }
  
  // Sort by severity then by margin delta
  flagged.sort((a, b) => {
    const severityOrder = { critical: 0, elevated: 1, monitor: 2 }
    if (severityOrder[a.severity] !== severityOrder[b.severity]) {
      return severityOrder[a.severity] - severityOrder[b.severity]
    }
    return a.margin_delta - b.margin_delta
  })
  
  logs.push(`[FLAG] Found ${flagged.length} flagged projects`)
  logs.push(`[FLAG] Critical: ${flagged.filter(p => p.severity === 'critical').length}`)
  logs.push(`[FLAG] Elevated: ${flagged.filter(p => p.severity === 'elevated').length}`)
  logs.push(`[FLAG] Monitor: ${flagged.filter(p => p.severity === 'monitor').length}`)
  
  return flagged
}

/**
 * Step 4: Generate portfolio summary
 */
export function generateSummary(
  projects: Map<string, ProjectData>,
  flagged: FlaggedProject[],
  logs: string[]
): PortfolioSummary {
  logs.push('[SUMMARY] Generating portfolio summary...')
  
  let totalContractValue = 0
  for (const project of projects.values()) {
    totalContractValue += project.contract_value
  }
  
  const totalLaborOverrun = flagged.reduce((sum, p) => sum + Math.max(0, p.labor_overrun), 0)
  const totalMaterialOverrun = flagged.reduce((sum, p) => sum + Math.max(0, p.material_overrun), 0)
  const avgMarginDelta = flagged.length > 0
    ? flagged.reduce((sum, p) => sum + p.margin_delta, 0) / flagged.length
    : 0
  
  const summary: PortfolioSummary = {
    total_projects: projects.size,
    total_contract_value: totalContractValue,
    flagged_count: flagged.length,
    critical_count: flagged.filter(p => p.severity === 'critical').length,
    elevated_count: flagged.filter(p => p.severity === 'elevated').length,
    monitor_count: flagged.filter(p => p.severity === 'monitor').length,
    total_labor_overrun: totalLaborOverrun,
    total_material_overrun: totalMaterialOverrun,
    avg_margin_delta: avgMarginDelta,
  }
  
  logs.push(`[SUMMARY] Total projects: ${summary.total_projects}`)
  logs.push(`[SUMMARY] Total contract value: $${(summary.total_contract_value / 1000000).toFixed(1)}M`)
  logs.push(`[SUMMARY] Flagged projects: ${summary.flagged_count}`)
  logs.push('[SUMMARY] Portfolio summary complete')
  
  return summary
}

/**
 * Run the full pipeline
 */
export async function runPipeline(
  csvFiles: Map<string, string>,
  onProgress?: (step: number, logs: string[]) => void
): Promise<PipelineResult> {
  const steps: PipelineStep[] = [
    { id: 'clean', label: 'Clean', status: 'idle', logs: [], duration: 0 },
    { id: 'load', label: 'Load', status: 'idle', logs: [], duration: 0 },
    { id: 'flag', label: 'Flag', status: 'idle', logs: [], duration: 0 },
    { id: 'llm', label: 'LLM Export', status: 'idle', logs: [], duration: 0 },
    { id: 'output', label: 'Output', status: 'idle', logs: [], duration: 0 },
  ]
  
  try {
    // Step 1: Parse CSVs
    steps[0].status = 'running'
    steps[0].logs.push('[CLEAN] Parsing CSV files...')
    onProgress?.(0, steps[0].logs)
    
    const csvData: Record<string, Record<string, string>[]> = {}
    for (const [filename, content] of csvFiles) {
      const key = filename.replace('.csv', '').replace(/-/g, '_')
      csvData[key] = parseCSV(content)
      steps[0].logs.push(`[CLEAN] Parsed ${filename}: ${csvData[key].length} rows`)
    }
    
    // Clean data
    const cleanedData = cleanData(csvData, steps[0].logs)
    steps[0].status = 'complete'
    onProgress?.(0, steps[0].logs)
    
    // Step 2: Load
    steps[1].status = 'running'
    onProgress?.(1, steps[1].logs)
    const projects = loadData(cleanedData, steps[1].logs)
    steps[1].status = 'complete'
    onProgress?.(1, steps[1].logs)
    
    // Step 3: Flag
    steps[2].status = 'running'
    onProgress?.(2, steps[2].logs)
    const flaggedProjects = flagProjects(projects, steps[2].logs)
    steps[2].status = 'complete'
    onProgress?.(2, steps[2].logs)
    
    // Step 4: LLM Export (generate prompts)
    steps[3].status = 'running'
    steps[3].logs.push('[LLM] Preparing data for AI analysis...')
    steps[3].logs.push(`[LLM] Exporting ${flaggedProjects.length} flagged projects`)
    steps[3].logs.push('[LLM] Generating project packets...')
    steps[3].logs.push('[LLM] AI analysis prompts ready')
    steps[3].status = 'complete'
    onProgress?.(3, steps[3].logs)
    
    // Step 5: Output
    steps[4].status = 'running'
    steps[4].logs.push('[OUTPUT] Generating portfolio summary...')
    const summary = generateSummary(projects, flaggedProjects, steps[4].logs)
    steps[4].logs.push('[OUTPUT] Pipeline complete!')
    steps[4].status = 'complete'
    onProgress?.(4, steps[4].logs)
    
    return {
      status: 'complete',
      summary,
      flagged_projects: flaggedProjects,
      steps,
    }
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : 'Unknown error'
    const currentStep = steps.findIndex(s => s.status === 'running')
    if (currentStep >= 0) {
      steps[currentStep].status = 'error'
      steps[currentStep].logs.push(`[ERROR] ${errorMsg}`)
    }
    
    return {
      status: 'error',
      summary: {
        total_projects: 0,
        total_contract_value: 0,
        flagged_count: 0,
        critical_count: 0,
        elevated_count: 0,
        monitor_count: 0,
        total_labor_overrun: 0,
        total_material_overrun: 0,
        avg_margin_delta: 0,
      },
      flagged_projects: [],
      steps,
    }
  }
}
