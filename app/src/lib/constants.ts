// ═══════════════════════════════════════════════════════════════════════════════
// HVAC Margin Rescue - Frontend Constants
// ═══════════════════════════════════════════════════════════════════════════════
// Shared constants for the frontend. Keep in sync with backend constants.py
// ═══════════════════════════════════════════════════════════════════════════════

// Priority scoring weights for project ranking
export const PRIORITY_BILLING_WEIGHT = 0.6
export const PRIORITY_OVERRUN_WEIGHT = 0.4

// Severity thresholds (realized margin)
export const SEVERITY_CRITICAL_THRESHOLD = -0.10
export const SEVERITY_WARNING_THRESHOLD = 0.00
export const SEVERITY_WATCH_THRESHOLD = 0.10

// Risk score thresholds
export const RISK_SCORE_HIGH_THRESHOLD = 70
export const RISK_SCORE_MEDIUM_THRESHOLD = 40

// Retention rate
export const RETENTION_RATE = 0.10

// LLM Configuration
export const LLM_MODEL_CHAT = 'claude-haiku-4-5-20251001'
export const LLM_MODEL_ANALYSIS = 'claude-sonnet-4-20250514'
export const LLM_MAX_TOKENS_CHAT = 1024
export const LLM_MAX_TOKENS_ANALYSIS = 2000
