import { Project, PortfolioSummary } from './types'

export const MOCK_PROJECTS = [
  {
    id: 'PRJ-2021-260',
    name: 'Riverside Medical Center HVAC Retrofit',
    sector: 'Healthcare',
    contractValue: 4820000,
    bidMargin: 0.148,
    realizedMargin: 0.062,
    marginDelta: -0.086,
    severity: 'critical',
    laborOverrun: 312400,
    materialOverrun: 87200,
    billingGap: 0.14,
    laborCost: { budget: 1820000, actual: 2132400 },
    materialCost: { budget: 920000, actual: 1007200 },
    billingStatus: { percentComplete: 0.82, percentBilled: 0.68 },
    fieldNoteSummary: 'Repeated duct re-routing due to uncoordinated drawings. Crew on-site 3 extra weeks. Foreman reports 40+ change order events undocumented.',
    rootCause: 'Labor overrun driven by 3 undocumented scope changes: duct rerouting around structural beam (+$148K), owner-directed equipment substitution (+$92K), commissioning delays from BMS coordination failure (+$72K). Billing gap of 14% = ~$675K earned but unbilled.',
    recoveryActions: [
      { description: 'Submit retroactive change orders CO-19 through CO-24', amount: 187000, priority: 'high', category: 'change_order' },
      { description: 'Invoice for completed SOV lines 12-18 (currently unbilled)', amount: 675000, priority: 'high', category: 'billing' },
      { description: 'Negotiate owner acceptance of equipment substitution premium', amount: 92000, priority: 'medium', category: 'renegotiation' },
    ],
    changeOrders: [
      { id: 'CO-19', description: 'Duct rerouting Level 3 east wing', costIncurred: 148000, billedToClient: false, status: 'pending', marginImpact: -3.1 },
      { id: 'CO-20', description: 'Structural interference beam 14B', costIncurred: 38000, billedToClient: false, status: 'draft', marginImpact: -0.8 },
      { id: 'CO-21', description: 'Equipment substitution premium', costIncurred: 92000, billedToClient: false, status: 'draft', marginImpact: -1.9 },
      { id: 'CO-22', description: 'BMS coordination delay T&M', costIncurred: 46000, billedToClient: true, status: 'approved', marginImpact: 0 },
    ],
    rfis: [
      { id: 'RFI-041', status: 'open', daysOpen: 34, description: 'Beam 14B clearance conflict' },
      { id: 'RFI-047', status: 'open', daysOpen: 21, description: 'BMS sequence of operations' },
      { id: 'RFI-052', status: 'closed', daysOpen: 8, description: 'Diffuser model substitution approval' },
    ],
    sovLines: [
      { name: 'Mobilization', budgeted: 120000, actual: 145000 },
      { name: 'Ductwork', budgeted: 680000, actual: 1020000 },
      { name: 'Mechanical Equipment', budgeted: 920000, actual: 1007200 },
      { name: 'Piping', budgeted: 380000, actual: 412000 },
      { name: 'Controls / BMS', budgeted: 290000, actual: 388000 },
      { name: 'Insulation', budgeted: 180000, actual: 196000 },
      { name: 'Commissioning', budgeted: 150000, actual: 224000 },
    ],
    laborByWeek: [
      { week: 'W1', regular: 42000, overtime: 2100 },
      { week: 'W2', regular: 44000, overtime: 3200 },
      { week: 'W3', regular: 41000, overtime: 8400 },
      { week: 'W4', regular: 43000, overtime: 12600 },
      { week: 'W5', regular: 45000, overtime: 18900 },
      { week: 'W6', regular: 44000, overtime: 21000 },
      { week: 'W7', regular: 42000, overtime: 16800 },
      { week: 'W8', regular: 43000, overtime: 9100 },
    ],
    materialDeliveries: [
      { description: 'AHU Units (3)', budgetedCost: 280000, actualCost: 312000, condition: 'Good', date: '2021-03-12' },
      { description: 'Ductwork Sheet Metal', budgetedCost: 180000, actualCost: 180000, condition: 'Good', date: '2021-03-18' },
      { description: 'Diffusers & Grilles', budgetedCost: 42000, actualCost: 68000, condition: 'Reordered', date: '2021-04-02' },
      { description: 'Insulation Batts', budgetedCost: 38000, actualCost: 41000, condition: 'Partial', date: '2021-04-10' },
    ],
    billingHistory: [
      { month: 'Jan', billed: 180000, actualCost: 210000 },
      { month: 'Feb', billed: 320000, actualCost: 380000 },
      { month: 'Mar', billed: 480000, actualCost: 560000 },
      { month: 'Apr', billed: 520000, actualCost: 640000 },
      { month: 'May', billed: 490000, actualCost: 610000 },
      { month: 'Jun', billed: 310000, actualCost: 420000 },
    ],
    rfiByWeek: [
      { week: 'W1', rfiCount: 1, weeklyCost: 44100 },
      { week: 'W2', rfiCount: 2, weeklyCost: 47200 },
      { week: 'W3', rfiCount: 4, weeklyCost: 49400 },
      { week: 'W4', rfiCount: 6, weeklyCost: 55600 },
      { week: 'W5', rfiCount: 5, weeklyCost: 63900 },
      { week: 'W6', rfiCount: 3, weeklyCost: 65000 },
      { week: 'W7', rfiCount: 2, weeklyCost: 58800 },
      { week: 'W8', rfiCount: 1, weeklyCost: 52100 },
    ],
  },
  {
    id: 'PRJ-2022-118',
    name: 'Greenfield Office Tower Central Plant Upgrade',
    sector: 'Commercial',
    contractValue: 7340000,
    bidMargin: 0.162,
    realizedMargin: 0.071,
    marginDelta: -0.091,
    severity: 'critical',
    laborOverrun: 498000,
    materialOverrun: 164000,
    billingGap: 0.09,
    laborCost: { budget: 2640000, actual: 3138000 },
    materialCost: { budget: 1820000, actual: 1984000 },
    billingStatus: { percentComplete: 0.74, percentBilled: 0.65 },
    fieldNoteSummary: 'Chiller delivery delayed 6 weeks from manufacturer. Crew kept on standby. Owner rejected initial submittal package, forcing complete resubmission.',
    rootCause: 'Primary driver is standby labor cost during 6-week chiller delivery delay ($284K). Secondary: two rounds of owner-rejected submittals added 3 weeks of engineering rework ($142K).',
    recoveryActions: [
      { description: 'File delay claim against chiller manufacturer for standby costs', amount: 284000, priority: 'high', category: 'labor' },
      { description: 'Submit CO for owner-directed submittal resubmission engineering time', amount: 142000, priority: 'high', category: 'change_order' },
      { description: 'Bill outstanding SOV lines 8-12', amount: 660000, priority: 'high', category: 'billing' },
    ],
    changeOrders: [
      { id: 'CO-07', description: 'Chiller standby labor - delay claim', costIncurred: 284000, billedToClient: false, status: 'pending', marginImpact: -3.9 },
      { id: 'CO-08', description: 'Submittal resubmission engineering', costIncurred: 142000, billedToClient: false, status: 'draft', marginImpact: -1.9 },
      { id: 'CO-09', description: 'Cooling tower foundation upsizing', costIncurred: 78000, billedToClient: true, status: 'approved', marginImpact: 0 },
    ],
    rfis: [
      { id: 'RFI-012', status: 'open', daysOpen: 45, description: 'Chiller clearance vs. structural steel' },
      { id: 'RFI-019', status: 'open', daysOpen: 28, description: 'Cooling tower vibration isolation spec' },
    ],
    sovLines: [
      { name: 'Mobilization', budgeted: 180000, actual: 195000 },
      { name: 'Chiller Plant Equipment', budgeted: 1820000, actual: 1984000 },
      { name: 'Piping & Headers', budgeted: 820000, actual: 912000 },
      { name: 'Electrical / Controls', budgeted: 480000, actual: 540000 },
      { name: 'Cooling Towers', budgeted: 620000, actual: 698000 },
      { name: 'Insulation & Testing', budgeted: 240000, actual: 276000 },
      { name: 'Commissioning', budgeted: 280000, actual: 384000 },
    ],
    laborByWeek: [
      { week: 'W1', regular: 68000, overtime: 4200 },
      { week: 'W2', regular: 72000, overtime: 5600 },
      { week: 'W3', regular: 71000, overtime: 4900 },
      { week: 'W4', regular: 68000, overtime: 68000 },
      { week: 'W5', regular: 69000, overtime: 69000 },
      { week: 'W6', regular: 70000, overtime: 70000 },
      { week: 'W7', regular: 72000, overtime: 24000 },
      { week: 'W8', regular: 74000, overtime: 8200 },
    ],
    materialDeliveries: [
      { description: 'Centrifugal Chiller (1200T)', budgetedCost: 920000, actualCost: 1020000, condition: 'Good', date: '2022-05-14' },
      { description: 'Cooling Tower Assembly', budgetedCost: 380000, actualCost: 398000, condition: 'Good', date: '2022-04-22' },
      { description: 'Variable Speed Drives (12 units)', budgetedCost: 180000, actualCost: 216000, condition: 'Damaged', date: '2022-06-01' },
    ],
    billingHistory: [
      { month: 'Jan', billed: 320000, actualCost: 380000 },
      { month: 'Feb', billed: 480000, actualCost: 560000 },
      { month: 'Mar', billed: 520000, actualCost: 680000 },
      { month: 'Apr', billed: 410000, actualCost: 820000 },
      { month: 'May', billed: 390000, actualCost: 780000 },
      { month: 'Jun', billed: 560000, actualCost: 640000 },
    ],
    rfiByWeek: [
      { week: 'W1', rfiCount: 1, weeklyCost: 72200 },
      { week: 'W2', rfiCount: 2, weeklyCost: 77600 },
      { week: 'W3', rfiCount: 3, weeklyCost: 75900 },
      { week: 'W4', rfiCount: 5, weeklyCost: 136000 },
      { week: 'W5', rfiCount: 6, weeklyCost: 138000 },
      { week: 'W6', rfiCount: 4, weeklyCost: 140000 },
      { week: 'W7', rfiCount: 2, weeklyCost: 96000 },
      { week: 'W8', rfiCount: 1, weeklyCost: 82200 },
    ],
  },
  {
    id: 'PRJ-2022-334',
    name: 'Westside K-12 School District HVAC Modernization',
    sector: 'Education',
    contractValue: 3180000,
    bidMargin: 0.131,
    realizedMargin: 0.058,
    marginDelta: -0.073,
    severity: 'critical',
    laborOverrun: 184000,
    materialOverrun: 48000,
    billingGap: 0.11,
    laborCost: { budget: 1080000, actual: 1264000 },
    materialCost: { budget: 640000, actual: 688000 },
    billingStatus: { percentComplete: 0.71, percentBilled: 0.60 },
    fieldNoteSummary: 'Work windows limited to summer break. Additional abatement scope discovered mid-project. Owner slow to approve change orders.',
    rootCause: 'Abatement scope discovered post-demo added $184K in unplanned labor. Limited work windows during school year compressed schedule, requiring overtime surcharges.',
    recoveryActions: [
      { description: 'Submit diffuse scope CO for abatement labor', amount: 184000, priority: 'high', category: 'change_order' },
      { description: 'Bill Phase 2 completion (11% gap)', amount: 350000, priority: 'high', category: 'billing' },
    ],
    changeOrders: [
      { id: 'CO-04', description: 'Asbestos abatement - discovery', costIncurred: 184000, billedToClient: false, status: 'pending', marginImpact: -5.8 },
      { id: 'CO-05', description: 'Extended work window surcharge', costIncurred: 42000, billedToClient: false, status: 'draft', marginImpact: -1.3 },
    ],
    rfis: [
      { id: 'RFI-022', status: 'open', daysOpen: 18, description: 'Abatement containment protocol' },
      { id: 'RFI-031', status: 'closed', daysOpen: 12, description: 'Duct route above ceiling tiles' },
    ],
    sovLines: [
      { name: 'Demolition / Abatement', budgeted: 180000, actual: 364000 },
      { name: 'New HVAC Units (8)', budgeted: 480000, actual: 498000 },
      { name: 'Ductwork', budgeted: 320000, actual: 348000 },
      { name: 'Controls & Thermostats', budgeted: 160000, actual: 184000 },
      { name: 'Commissioning', budgeted: 80000, actual: 98000 },
    ],
    laborByWeek: [
      { week: 'W1', regular: 28000, overtime: 1400 },
      { week: 'W2', regular: 30000, overtime: 4500 },
      { week: 'W3', regular: 32000, overtime: 12800 },
      { week: 'W4', regular: 34000, overtime: 17000 },
      { week: 'W5', regular: 31000, overtime: 9300 },
      { week: 'W6', regular: 29000, overtime: 4350 },
    ],
    materialDeliveries: [
      { description: 'Packaged RTUs (8 units)', budgetedCost: 320000, actualCost: 338000, condition: 'Good', date: '2022-06-20' },
      { description: 'Abatement Supplies', budgetedCost: 28000, actualCost: 62000, condition: 'Reordered', date: '2022-06-25' },
    ],
    billingHistory: [
      { month: 'Jun', billed: 280000, actualCost: 340000 },
      { month: 'Jul', billed: 480000, actualCost: 580000 },
      { month: 'Aug', billed: 520000, actualCost: 640000 },
      { month: 'Sep', billed: 180000, actualCost: 290000 },
    ],
    rfiByWeek: [
      { week: 'W1', rfiCount: 0, weeklyCost: 29400 },
      { week: 'W2', rfiCount: 2, weeklyCost: 34500 },
      { week: 'W3', rfiCount: 5, weeklyCost: 44800 },
      { week: 'W4', rfiCount: 4, weeklyCost: 51000 },
      { week: 'W5', rfiCount: 2, weeklyCost: 40300 },
      { week: 'W6', rfiCount: 1, weeklyCost: 33350 },
    ],
  },
  {
    id: 'PRJ-2023-077',
    name: 'Harbor Logistics Warehouse Climate Control',
    sector: 'Industrial',
    contractValue: 2240000,
    bidMargin: 0.119,
    realizedMargin: 0.054,
    marginDelta: -0.065,
    severity: 'critical',
    laborOverrun: 102000,
    materialOverrun: 43000,
    billingGap: 0.08,
    laborCost: { budget: 780000, actual: 882000 },
    materialCost: { budget: 620000, actual: 663000 },
    billingStatus: { percentComplete: 0.88, percentBilled: 0.80 },
    fieldNoteSummary: 'Industrial high-bay installation required specialized lift equipment rental not in original bid. Material lead times extended 4 weeks.',
    rootCause: 'Unbudgeted specialized lift equipment ($68K) and overtime for accelerated schedule to meet tenant move-in date ($102K labor overrun).',
    recoveryActions: [
      { description: 'Submit CO for high-bay lift equipment rental', amount: 68000, priority: 'high', category: 'change_order' },
      { description: 'Invoice remaining 8% billing gap', amount: 179000, priority: 'medium', category: 'billing' },
    ],
    changeOrders: [
      { id: 'CO-11', description: 'Specialized lift equipment rental', costIncurred: 68000, billedToClient: false, status: 'pending', marginImpact: -3.0 },
      { id: 'CO-12', description: 'Accelerated schedule overtime premium', costIncurred: 42000, billedToClient: false, status: 'draft', marginImpact: -1.9 },
    ],
    rfis: [
      { id: 'RFI-008', status: 'closed', daysOpen: 14, description: 'High-bay equipment clearance requirements' },
      { id: 'RFI-015', status: 'open', daysOpen: 9, description: 'Evaporative cooler drain connection detail' },
    ],
    sovLines: [
      { name: 'Equipment Procurement', budgeted: 620000, actual: 663000 },
      { name: 'High-Bay Ductwork', budgeted: 280000, actual: 324000 },
      { name: 'Installation Labor', budgeted: 380000, actual: 448000 },
      { name: 'Controls', budgeted: 120000, actual: 134000 },
      { name: 'Testing & Commissioning', budgeted: 80000, actual: 96000 },
    ],
    laborByWeek: [
      { week: 'W1', regular: 24000, overtime: 1200 },
      { week: 'W2', regular: 26000, overtime: 5200 },
      { week: 'W3', regular: 28000, overtime: 14000 },
      { week: 'W4', regular: 29000, overtime: 17400 },
      { week: 'W5', regular: 27000, overtime: 10800 },
      { week: 'W6', regular: 25000, overtime: 3750 },
    ],
    materialDeliveries: [
      { description: 'Evaporative Coolers (6)', budgetedCost: 240000, actualCost: 258000, condition: 'Good', date: '2023-02-14' },
      { description: 'Industrial Duct (galvanized)', budgetedCost: 180000, actualCost: 192000, condition: 'Partial', date: '2023-02-28' },
      { description: 'Controls Package', budgetedCost: 120000, actualCost: 134000, condition: 'Good', date: '2023-03-10' },
    ],
    billingHistory: [
      { month: 'Jan', billed: 180000, actualCost: 220000 },
      { month: 'Feb', billed: 320000, actualCost: 380000 },
      { month: 'Mar', billed: 480000, actualCost: 520000 },
      { month: 'Apr', billed: 410000, actualCost: 440000 },
    ],
    rfiByWeek: [
      { week: 'W1', rfiCount: 0, weeklyCost: 25200 },
      { week: 'W2', rfiCount: 1, weeklyCost: 31200 },
      { week: 'W3', rfiCount: 2, weeklyCost: 42000 },
      { week: 'W4', rfiCount: 3, weeklyCost: 46400 },
      { week: 'W5', rfiCount: 2, weeklyCost: 37800 },
      { week: 'W6', rfiCount: 1, weeklyCost: 28750 },
    ],
  },
  {
    id: 'PRJ-2022-491',
    name: 'St. Agnes Hospital Chiller Replacement',
    sector: 'Healthcare',
    contractValue: 5610000,
    bidMargin: 0.142,
    realizedMargin: 0.089,
    marginDelta: -0.053,
    severity: 'warning',
    laborOverrun: 198000,
    materialOverrun: 112000,
    billingGap: 0.07,
    laborCost: { budget: 1980000, actual: 2178000 },
    materialCost: { budget: 1640000, actual: 1752000 },
    billingStatus: { percentComplete: 0.79, percentBilled: 0.72 },
    fieldNoteSummary: 'Infection control protocols required additional crew time. Refrigerant transition costs exceeded estimate.',
    rootCause: 'Infection control zone requirements added 18% to installation labor. R-22 to R-410A refrigerant transition cost $112K above estimate.',
    recoveryActions: [
      { description: 'Submit infection control premium CO', amount: 148000, priority: 'high', category: 'change_order' },
      { description: 'Bill SOV lines 14-17 outstanding', amount: 393000, priority: 'medium', category: 'billing' },
    ],
    changeOrders: [
      { id: 'CO-31', description: 'Infection control premium labor', costIncurred: 148000, billedToClient: false, status: 'pending', marginImpact: -2.6 },
      { id: 'CO-32', description: 'Refrigerant transition cost delta', costIncurred: 112000, billedToClient: true, status: 'approved', marginImpact: 0 },
    ],
    rfis: [
      { id: 'RFI-018', status: 'open', daysOpen: 22, description: 'Infection control containment method' },
    ],
    sovLines: [
      { name: 'Chiller Equipment', budgeted: 1640000, actual: 1752000 },
      { name: 'Piping & Connections', budgeted: 480000, actual: 520000 },
      { name: 'Electrical', budgeted: 280000, actual: 312000 },
      { name: 'Controls Upgrade', budgeted: 220000, actual: 248000 },
      { name: 'Commissioning', budgeted: 160000, actual: 196000 },
    ],
    laborByWeek: [
      { week: 'W1', regular: 52000, overtime: 2600 },
      { week: 'W2', regular: 54000, overtime: 5400 },
      { week: 'W3', regular: 56000, overtime: 11200 },
      { week: 'W4', regular: 58000, overtime: 14500 },
      { week: 'W5', regular: 55000, overtime: 8250 },
      { week: 'W6', regular: 53000, overtime: 3975 },
    ],
    materialDeliveries: [
      { description: 'Centrifugal Chiller 800T', budgetedCost: 980000, actualCost: 1040000, condition: 'Good', date: '2022-09-18' },
      { description: 'R-410A Refrigerant (bulk)', budgetedCost: 180000, actualCost: 292000, condition: 'Good', date: '2022-10-02' },
    ],
    billingHistory: [
      { month: 'Jul', billed: 280000, actualCost: 340000 },
      { month: 'Aug', billed: 520000, actualCost: 580000 },
      { month: 'Sep', billed: 640000, actualCost: 720000 },
      { month: 'Oct', billed: 580000, actualCost: 640000 },
      { month: 'Nov', billed: 420000, actualCost: 490000 },
    ],
    rfiByWeek: [
      { week: 'W1', rfiCount: 1, weeklyCost: 54600 },
      { week: 'W2', rfiCount: 2, weeklyCost: 59400 },
      { week: 'W3', rfiCount: 3, weeklyCost: 67200 },
      { week: 'W4', rfiCount: 2, weeklyCost: 72500 },
      { week: 'W5', rfiCount: 1, weeklyCost: 63250 },
      { week: 'W6', rfiCount: 1, weeklyCost: 56975 },
    ],
  },
  {
    id: 'PRJ-2023-155',
    name: 'Luxe Hotel Chain HVAC Systems Install',
    sector: 'Hospitality',
    contractValue: 6820000,
    bidMargin: 0.156,
    realizedMargin: 0.108,
    marginDelta: -0.048,
    severity: 'warning',
    laborOverrun: 224000,
    materialOverrun: 104000,
    billingGap: 0.06,
    laborCost: { budget: 2380000, actual: 2604000 },
    materialCost: { budget: 1920000, actual: 2024000 },
    billingStatus: { percentComplete: 0.85, percentBilled: 0.79 },
    fieldNoteSummary: 'Hotel occupancy during construction required work hours limited to 10pm-6am. Premium labor rates apply. Guest complaints triggered two work stoppages.',
    rootCause: 'Overnight work premium rates increased effective labor cost by 22%. Two owner-directed work stoppages cost $84K in mobilization/demobilization.',
    recoveryActions: [
      { description: 'Submit overnight premium rate CO', amount: 180000, priority: 'high', category: 'labor' },
      { description: 'Bill work stoppage remobilization costs', amount: 84000, priority: 'medium', category: 'change_order' },
      { description: 'Close out 6% billing gap on Phases 3-4', amount: 409000, priority: 'medium', category: 'billing' },
    ],
    changeOrders: [
      { id: 'CO-18', description: 'Overnight work premium - all trades', costIncurred: 224000, billedToClient: false, status: 'pending', marginImpact: -3.3 },
      { id: 'CO-19', description: 'Work stoppage remobilization (x2)', costIncurred: 84000, billedToClient: false, status: 'draft', marginImpact: -1.2 },
    ],
    rfis: [
      { id: 'RFI-033', status: 'open', daysOpen: 16, description: 'Sound attenuation requirements - guest floors' },
      { id: 'RFI-039', status: 'closed', daysOpen: 7, description: 'Aesthetic grille specification match' },
    ],
    sovLines: [
      { name: 'Guest Room Fan Coils (320)', budgeted: 960000, actual: 1020000 },
      { name: 'Central AHU Systems', budgeted: 480000, actual: 524000 },
      { name: 'Kitchen Hood Systems', budgeted: 320000, actual: 348000 },
      { name: 'Spa / Pool HVAC', budgeted: 280000, actual: 312000 },
      { name: 'Controls & BAS', budgeted: 380000, actual: 420000 },
      { name: 'Testing & Balancing', budgeted: 180000, actual: 214000 },
    ],
    laborByWeek: [
      { week: 'W1', regular: 58000, overtime: 11600 },
      { week: 'W2', regular: 60000, overtime: 18000 },
      { week: 'W3', regular: 62000, overtime: 24800 },
      { week: 'W4', regular: 64000, overtime: 25600 },
      { week: 'W5', regular: 61000, overtime: 18300 },
      { week: 'W6', regular: 59000, overtime: 11800 },
    ],
    materialDeliveries: [
      { description: 'Fan Coil Units (320)', budgetedCost: 640000, actualCost: 680000, condition: 'Good', date: '2023-04-15' },
      { description: 'Kitchen Hood Assemblies', budgetedCost: 180000, actualCost: 194000, condition: 'Good', date: '2023-04-28' },
      { description: 'Sound Attenuators (custom)', budgetedCost: 120000, actualCost: 168000, condition: 'Damaged', date: '2023-05-10' },
    ],
    billingHistory: [
      { month: 'Feb', billed: 420000, actualCost: 480000 },
      { month: 'Mar', billed: 680000, actualCost: 760000 },
      { month: 'Apr', billed: 820000, actualCost: 920000 },
      { month: 'May', billed: 740000, actualCost: 840000 },
      { month: 'Jun', billed: 620000, actualCost: 700000 },
    ],
    rfiByWeek: [
      { week: 'W1', rfiCount: 1, weeklyCost: 69600 },
      { week: 'W2', rfiCount: 2, weeklyCost: 78000 },
      { week: 'W3', rfiCount: 3, weeklyCost: 86800 },
      { week: 'W4', rfiCount: 2, weeklyCost: 89600 },
      { week: 'W5', rfiCount: 1, weeklyCost: 79300 },
      { week: 'W6', rfiCount: 1, weeklyCost: 70800 },
    ],
  },
  {
    id: 'PRJ-2023-288',
    name: 'Downtown Mixed-Use Tower MEP Coordination',
    sector: 'Commercial',
    contractValue: 8940000,
    bidMargin: 0.141,
    realizedMargin: 0.103,
    marginDelta: -0.038,
    severity: 'warning',
    laborOverrun: 198000,
    materialOverrun: 142000,
    billingGap: 0.05,
    laborCost: { budget: 3120000, actual: 3318000 },
    materialCost: { budget: 2640000, actual: 2782000 },
    billingStatus: { percentComplete: 0.69, percentBilled: 0.64 },
    fieldNoteSummary: 'Dense MEP coordination with 4 other trades. Multiple redesigns due to BIM clash detection. Facade delays pushed HVAC schedule 3 weeks.',
    rootCause: 'BIM coordination clashes required 3 redesign cycles, adding $142K in engineering and rework labor. Facade delay compressed HVAC installation window.',
    recoveryActions: [
      { description: 'Submit CO for BIM redesign cycles (3 iterations)', amount: 142000, priority: 'high', category: 'change_order' },
      { description: 'Pursue liquidated damages claim for facade delay impact', amount: 120000, priority: 'medium', category: 'labor' },
    ],
    changeOrders: [
      { id: 'CO-24', description: 'BIM clash resolution redesign cycles', costIncurred: 142000, billedToClient: false, status: 'pending', marginImpact: -1.6 },
      { id: 'CO-25', description: 'Facade delay impact - compressed schedule', costIncurred: 120000, billedToClient: false, status: 'draft', marginImpact: -1.3 },
      { id: 'CO-26', description: 'Additional MEP coordination meetings', costIncurred: 38000, billedToClient: true, status: 'approved', marginImpact: 0 },
    ],
    rfis: [
      { id: 'RFI-055', status: 'open', daysOpen: 19, description: 'Ceiling plenum clearance coordination' },
      { id: 'RFI-062', status: 'open', daysOpen: 11, description: 'Chilled beam vs. VAV decision - floors 12-18' },
    ],
    sovLines: [
      { name: 'Residential Floors (HVAC)', budgeted: 1240000, actual: 1312000 },
      { name: 'Commercial Lobby / Base', budgeted: 680000, actual: 724000 },
      { name: 'Retail Podium', budgeted: 480000, actual: 516000 },
      { name: 'Central Plant', budgeted: 920000, actual: 980000 },
      { name: 'Parking Ventilation', budgeted: 320000, actual: 350000 },
      { name: 'Controls & BAS', budgeted: 540000, actual: 592000 },
    ],
    laborByWeek: [
      { week: 'W1', regular: 78000, overtime: 3900 },
      { week: 'W2', regular: 82000, overtime: 8200 },
      { week: 'W3', regular: 84000, overtime: 16800 },
      { week: 'W4', regular: 86000, overtime: 17200 },
      { week: 'W5', regular: 83000, overtime: 12450 },
      { week: 'W6', regular: 80000, overtime: 6000 },
    ],
    materialDeliveries: [
      { description: 'VAV Boxes (180 units)', budgetedCost: 540000, actualCost: 572000, condition: 'Good', date: '2023-08-12' },
      { description: 'Chilled Beams (24 units)', budgetedCost: 280000, actualCost: 308000, condition: 'Partial', date: '2023-08-28' },
      { description: 'Flexible Ductwork', budgetedCost: 120000, actualCost: 134000, condition: 'Good', date: '2023-09-05' },
    ],
    billingHistory: [
      { month: 'Jun', billed: 480000, actualCost: 560000 },
      { month: 'Jul', billed: 720000, actualCost: 820000 },
      { month: 'Aug', billed: 840000, actualCost: 940000 },
      { month: 'Sep', billed: 780000, actualCost: 860000 },
    ],
    rfiByWeek: [
      { week: 'W1', rfiCount: 2, weeklyCost: 81900 },
      { week: 'W2', rfiCount: 3, weeklyCost: 90200 },
      { week: 'W3', rfiCount: 5, weeklyCost: 100800 },
      { week: 'W4', rfiCount: 4, weeklyCost: 103200 },
      { week: 'W5', rfiCount: 3, weeklyCost: 95450 },
      { week: 'W6', rfiCount: 2, weeklyCost: 86000 },
    ],
  },
  {
    id: 'PRJ-2023-401',
    name: 'Federal Courthouse HVAC Compliance Upgrade',
    sector: 'Government',
    contractValue: 4120000,
    bidMargin: 0.128,
    realizedMargin: 0.094,
    marginDelta: -0.034,
    severity: 'watch',
    laborOverrun: 86000,
    materialOverrun: 54000,
    billingGap: 0.04,
    laborCost: { budget: 1420000, actual: 1506000 },
    materialCost: { budget: 980000, actual: 1034000 },
    billingStatus: { percentComplete: 0.64, percentBilled: 0.60 },
    fieldNoteSummary: 'Security clearance requirements for workers delayed start by 3 weeks. Federal procurement specs required custom-spec equipment with long lead times.',
    rootCause: 'Federal security vetting delayed crew start by 3 weeks ($86K standby + accelerated labor). Custom GSA-spec equipment lead time added 4 weeks to schedule.',
    recoveryActions: [
      { description: 'Submit delay claim for security clearance standby period', amount: 86000, priority: 'medium', category: 'labor' },
      { description: 'Invoice Phase 2 milestone (4% gap)', amount: 165000, priority: 'medium', category: 'billing' },
    ],
    changeOrders: [
      { id: 'CO-41', description: 'Security clearance delay standby labor', costIncurred: 86000, billedToClient: false, status: 'pending', marginImpact: -2.1 },
      { id: 'CO-42', description: 'Custom GSA spec equipment premium', costIncurred: 54000, billedToClient: true, status: 'approved', marginImpact: 0 },
    ],
    rfis: [
      { id: 'RFI-011', status: 'closed', daysOpen: 10, description: 'Security zone HVAC separation requirements' },
      { id: 'RFI-017', status: 'open', daysOpen: 14, description: 'SCIF room pressurization spec' },
    ],
    sovLines: [
      { name: 'Security Zone HVAC', budgeted: 480000, actual: 522000 },
      { name: 'General Office Areas', budgeted: 380000, actual: 398000 },
      { name: 'Courtroom Systems', budgeted: 320000, actual: 344000 },
      { name: 'SCIF Room Units', budgeted: 280000, actual: 312000 },
      { name: 'Controls & Monitoring', budgeted: 240000, actual: 264000 },
    ],
    laborByWeek: [
      { week: 'W1', regular: 36000, overtime: 1800 },
      { week: 'W2', regular: 38000, overtime: 3800 },
      { week: 'W3', regular: 40000, overtime: 8000 },
      { week: 'W4', regular: 42000, overtime: 10500 },
      { week: 'W5', regular: 39000, overtime: 5850 },
      { week: 'W6', regular: 37000, overtime: 2775 },
    ],
    materialDeliveries: [
      { description: 'GSA-Spec AHU Units (4)', budgetedCost: 380000, actualCost: 434000, condition: 'Good', date: '2023-11-14' },
      { description: 'SCIF Pressurization Units', budgetedCost: 180000, actualCost: 196000, condition: 'Good', date: '2023-11-28' },
    ],
    billingHistory: [
      { month: 'Sep', billed: 240000, actualCost: 280000 },
      { month: 'Oct', billed: 480000, actualCost: 520000 },
      { month: 'Nov', billed: 560000, actualCost: 600000 },
      { month: 'Dec', billed: 380000, actualCost: 416000 },
    ],
    rfiByWeek: [
      { week: 'W1', rfiCount: 0, weeklyCost: 37800 },
      { week: 'W2', rfiCount: 1, weeklyCost: 41800 },
      { week: 'W3', rfiCount: 2, weeklyCost: 48000 },
      { week: 'W4', rfiCount: 3, weeklyCost: 52500 },
      { week: 'W5', rfiCount: 1, weeklyCost: 44850 },
      { week: 'W6', rfiCount: 0, weeklyCost: 39775 },
    ],
  },
] as any as Project[]

// Real data from pipeline/output/portfolio_summary.json
export const PORTFOLIO_SUMMARY = {
  totalProjects: 405,
  totalValue: 6398815000, // $6.4B total contract value
  avgBidMargin: -0.008, // -0.8% avg bid margin
  avgRealizedMargin: 0.143, // 14.3% avg realized margin
  flaggedCount: 101, // 101 flagged projects
  criticalCount: 12, // 12 underwater (critical) projects
  totalExposure: 221808800, // Total rejected COs as exposure proxy
} as any as PortfolioSummary

export function getProject(id: string): Project | undefined {
  return MOCK_PROJECTS.find((p) => p.id === id)
}

export function formatCurrency(value: number | undefined | null): string {
  if (value == null || !Number.isFinite(value)) return '$0'
  if (value >= 1000000) return `$${(value / 1000000).toFixed(2)}M`
  if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`
  return `$${value.toFixed(0)}`
}

export function formatPercent(value: number | undefined | null): string {
  if (value == null || !Number.isFinite(value)) return '0.0%'
  return `${(value * 100).toFixed(1)}%`
}

export function getPriorityScore(p: Project): number {
  const project = p as Project & Record<string, number | undefined>
  const marginDelta = Math.abs(project.margin_delta ?? project.marginDelta ?? 0)
  const billingGap = project.billing_gap ?? project.billingGap ?? 0
  const laborOverrun = project.labor_overrun ?? project.laborOverrun ?? 0
  const materialOverrun = project.material_overrun ?? project.materialOverrun ?? 0
  const contractValue = project.contract_value ?? project.contractValue ?? 0
  const primaryAction = p.primary_action ?? p.recovery_actions?.[0]
  const actionValue = primaryAction?.expected_value ?? primaryAction?.estimated_recovery_dollars ?? primaryAction?.amount ?? 0
  const timeToCash = primaryAction?.time_to_cash_days ?? 45
  const erosion = marginDelta * 100
  const billing = billingGap * 100 * 0.6
  const overrun = contractValue > 0 ? ((laborOverrun + materialOverrun) / contractValue) * 100 * 0.4 : 0
  const actionScore = contractValue > 0 ? (actionValue / contractValue) * 100 * 1.1 : 0
  const cashSpeed = actionValue > 0 ? Math.max(0, 20 - Math.min(timeToCash, 20)) : 0
  return erosion + billing + overrun + actionScore + cashSpeed
}

export function getSortedByPriority<T extends Project>(projects: T[]) {
  return [...projects].sort((a, b) => getPriorityScore(b) - getPriorityScore(a))
}
