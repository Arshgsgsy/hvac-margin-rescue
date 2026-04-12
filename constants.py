# ═══════════════════════════════════════════════════════════════════════════════
# HVAC Margin Rescue - Centralized Constants
# ═══════════════════════════════════════════════════════════════════════════════
# All business rules and configurable thresholds in one place.
# These are industry standards or business decisions - NOT dataset-specific values.
# ═══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────────
# DATA QUALITY THRESHOLDS
# ─────────────────────────────────────────────────────────────────────────────────
COST_DISCREPANCY_THRESHOLD = 10.0  # Flag material cost discrepancies > $10
DUPLICATE_HANDLING = "keep_first"   # Strategy for duplicate records

# ─────────────────────────────────────────────────────────────────────────────────
# LABOR CALCULATIONS
# ─────────────────────────────────────────────────────────────────────────────────
OVERTIME_MULTIPLIER = 1.5  # Industry standard: OT paid at 1.5x

# ─────────────────────────────────────────────────────────────────────────────────
# RETENTION & BILLING
# ─────────────────────────────────────────────────────────────────────────────────
RETENTION_RATE = 0.10  # Standard construction retention: 10%

# ─────────────────────────────────────────────────────────────────────────────────
# PROJECT STAGE THRESHOLDS (based on billing % complete)
# ─────────────────────────────────────────────────────────────────────────────────
STAGE_COMPLETE_THRESHOLD = 0.95    # >= 95% billed = complete
STAGE_LATE_THRESHOLD = 0.75        # >= 75% billed = late stage
STAGE_ACTIVE_THRESHOLD = 0.15      # >= 15% billed = active
# Below 15% = early stage

# Billing status thresholds
BILLING_NEARLY_COMPLETE_THRESHOLD = 0.90  # 90% billed = nearly complete
BILLING_COMPLETE_THRESHOLD = 0.95         # 95% billed = effectively complete

# ─────────────────────────────────────────────────────────────────────────────────
# FLAGGING TRIGGERS - Business rules for identifying at-risk projects
# ─────────────────────────────────────────────────────────────────────────────────

# Severity thresholds (based on realized margin)
SEVERITY_CRITICAL_THRESHOLD = -0.10   # < -10% margin = Critical
SEVERITY_WARNING_THRESHOLD = 0.00     # < 0% margin = Warning
SEVERITY_WATCH_THRESHOLD = 0.10       # < 10% margin = Watch

# Overrun thresholds
MATERIAL_OVERRUN_THRESHOLD = 1.50     # > 150% of estimate triggers flag
LABOR_OVERRUN_THRESHOLD = 0.50        # > 50% of estimate triggers flag
COMPOUND_MATERIAL_OVERRUN = 1.00      # > 100% material + any labor overrun

# Budget coverage healthy range
BUDGET_COVERAGE_MIN = 0.88   # Below 88% = underbid
BUDGET_COVERAGE_MAX = 1.10   # Above 110% = padding concerns

# Change order exposure
REJECTED_CO_EXPOSURE_THRESHOLD = 0.05  # > 5% of contract value in rejected COs

# RFI thresholds
RFI_COST_IMPACT_COUNT_THRESHOLD = 25   # > 25 cost-impact RFIs
RFI_COST_IMPACT_RATE_THRESHOLD = 0.35  # > 35% of RFIs have cost impact

# RFI level classification thresholds
RFI_LEVEL_HIGH_THRESHOLD = 50    # > 50 total RFIs = HIGH
RFI_LEVEL_MEDIUM_THRESHOLD = 20  # > 20 total RFIs = MEDIUM

# ─────────────────────────────────────────────────────────────────────────────────
# DIAGNOSTIC SIGNALS - Thresholds for identifying abnormal project signals
# ─────────────────────────────────────────────────────────────────────────────────
ABNORMAL_LABOR_MULTIPLIER = 1.3       # Actual > 1.3x estimated = abnormal
ABNORMAL_MATERIAL_MULTIPLIER = 1.3    # Actual > 1.3x estimated = abnormal
ABNORMAL_MARGIN_DELTA = 0.05          # > 5 percentage point erosion
ABNORMAL_BILLING_GAP = 0.10           # > 10 percentage points underbilled
ABNORMAL_OVERTIME_SHARE = 0.25        # > 25% of hours as overtime
ABNORMAL_CREW_SIZE_MULTIPLIER = 1.5   # > 1.5x expected crew size

# Pending CO threshold
PENDING_CO_STALE_THRESHOLD = 0.10     # > 10% of contract with no movement

# ─────────────────────────────────────────────────────────────────────────────────
# RECOVERY PATH THRESHOLDS
# ─────────────────────────────────────────────────────────────────────────────────
BILLING_GAP_RECOVERY_THRESHOLD = 0.05  # > 5% billing gap = recovery opportunity

# Delivery clustering (material deliveries concentrated in one month)
DELIVERY_CLUSTERING_THRESHOLD = 0.40   # > 40% of deliveries in one month

# ─────────────────────────────────────────────────────────────────────────────────
# RISK SCORING - Percentile-based scoring weights
# ─────────────────────────────────────────────────────────────────────────────────
RISK_SCORE_HIGH_THRESHOLD = 70    # >= 70 = HIGH risk
RISK_SCORE_MEDIUM_THRESHOLD = 40  # >= 40 = MEDIUM risk
# Below 40 = LOW risk

# Component score weights (sum to 100 max)
RISK_BILLING_MAX_SCORE = 40
RISK_MARGIN_MAX_SCORE = 30
RISK_CHANGE_ORDER_MAX_SCORE = 20
RISK_RFI_MAX_SCORE = 10

# Billing gap scoring by percentile
RISK_BILLING_Q10_SCORE = 40   # Worst 10%
RISK_BILLING_Q25_SCORE = 30   # Worst 25%
RISK_BILLING_Q50_SCORE = 15   # Worst 50%

# Margin scoring by percentile
RISK_MARGIN_Q10_SCORE = 30    # Worst 10%
RISK_MARGIN_Q25_SCORE = 20    # Worst 25%
RISK_MARGIN_Q50_SCORE = 10    # Worst 50%

# Change order scoring by percentile
RISK_CO_Q90_SCORE = 20        # Worst 10%
RISK_CO_Q75_SCORE = 10        # Worst 25%

# RFI scoring by percentile
RISK_RFI_Q90_SCORE = 10       # Worst 10%
RISK_RFI_Q75_SCORE = 5        # Worst 25%

# ─────────────────────────────────────────────────────────────────────────────────
# DISPLAY LIMITS - For truncation and display purposes
# ─────────────────────────────────────────────────────────────────────────────────
FIELD_NOTE_CONTENT_LIMIT = 140   # Characters for field note snippets
FIELD_NOTE_SUBJECT_LIMIT = 80    # Characters for field note subjects
TOP_FIELD_NOTES_LIMIT = 6        # Number of top field notes to include
TOP_SOV_VARIANCES_LIMIT = 5      # Number of top SOV variances to include
TOP_COST_CODES_LIMIT = 5         # Number of top cost codes to include

# ─────────────────────────────────────────────────────────────────────────────────
# LLM CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────────
LLM_MODEL_CHAT = "gpt-5.4"       # GPT-5.4 for chat
LLM_MODEL_ANALYSIS = "gpt-5.4"   # GPT-5.4 for analysis
LLM_MAX_TOKENS_CHAT = 1024
LLM_MAX_TOKENS_ANALYSIS = 2000
LLM_MAX_TOKENS_PORTFOLIO = 6000  # Larger output for portfolio optimization

# ─────────────────────────────────────────────────────────────────────────────────
# PORTFOLIO OPTIMIZATION
# ─────────────────────────────────────────────────────────────────────────────────
# Default resource capacity (hours per week per role)
RESOURCE_CAPACITY_PM = 40        # Project Manager hours/week
RESOURCE_CAPACITY_FINANCE = 20   # Finance hours/week
RESOURCE_CAPACITY_OPS = 30       # Operations hours/week
RESOURCE_CAPACITY_EXEC = 10      # Executive hours/week

# Effort to hours mapping
EFFORT_LOW_HOURS = 2
EFFORT_MEDIUM_HOURS = 8
EFFORT_HIGH_HOURS = 24

# Portfolio optimization thresholds
GC_BUNDLE_THRESHOLD = 100000          # Min $ to recommend GC bundle negotiation
GC_BUNDLE_MIN_PROJECTS = 3            # Min projects with same GC to bundle
SYSTEMIC_ISSUE_MIN_PROJECTS = 5       # Min projects for issue to be systemic
HIGH_LOSS_MARGIN_THRESHOLD = -0.50    # Projects below -50% margin
TOP_ACTIONS_LIMIT = 50                # Max actions to send to portfolio agent

# ─────────────────────────────────────────────────────────────────────────────────
# PRIORITY SCORING WEIGHTS (for frontend ranking)
# ─────────────────────────────────────────────────────────────────────────────────
PRIORITY_BILLING_WEIGHT = 0.6
PRIORITY_OVERRUN_WEIGHT = 0.4

# ─────────────────────────────────────────────────────────────────────────────────
# BATCH PARALLELIZATION CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────────
BATCH_CONCURRENCY = 5              # Max projects processed in parallel
MAX_CONCURRENT_API_CALLS = 10      # Max simultaneous API calls

# Retry settings
RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY = 1.0             # Base delay (seconds)
RETRY_MAX_DELAY = 60.0             # Max delay between retries
RETRY_JITTER = 0.1                 # 10% random jitter

# Progress reporting
PROGRESS_REPORT_INTERVAL = 5       # Report every N projects
