from dataclasses import dataclass


@dataclass(frozen=True)
class TriggerRule:
    key: str
    label: str
    alert_class: str
    score: int
    description: str


SEVERITY_CRITICAL_THRESHOLD = -0.10
SEVERITY_WARNING_THRESHOLD = 0.00
WEAK_MARGIN_THRESHOLD = 0.08

UNDERWATER_BUFFER_DOLLARS = 0.0
COMPOUND_OVERRUN_THRESHOLD = 25.0
MAJOR_LABOR_BLOWOUT_THRESHOLD = 50.0
MAJOR_MATERIAL_BLOWOUT_THRESHOLD = 150.0
LATE_STAGE_PCT_COMPLETE_THRESHOLD = 0.75
LATE_STAGE_UNDERBILLING_THRESHOLD = 0.10
REJECTED_CO_EXPOSURE_THRESHOLD = 0.05

BUDGET_COVERAGE_MIN = 0.88
BUDGET_COVERAGE_MAX = 1.12
HIGH_RFI_PER_MILLION_THRESHOLD = 18.0
HIGH_RFI_COST_IMPACT_RATE_THRESHOLD = 0.30
STALE_OPEN_RFI_AGE_DAYS = 30
HIGH_APPROVED_CO_PCT_THRESHOLD = 0.10
ESTIMATING_ANOMALY_BUDGET_COVERAGE = 0.95
ESTIMATING_ANOMALY_APPROVED_CO_PCT = 0.07
MILD_OT_SPIKE_THRESHOLD = 0.05
MILD_BURN_ACCELERATION_THRESHOLD = 0.15
MILD_CREW_SPIKE_THRESHOLD = 0.20
MILD_FTC_TREND_THRESHOLD = 0.05

ALERT_SCORE_ESCALATION_DELTA = 15
ALERT_MARGIN_DROP_DELTA = 0.03

ALERT_CLASS_RANK = {
    "watch_signal": 1,
    "hard_alert": 2,
}

SEVERITY_RANK = {
    "watch": 1,
    "warning": 2,
    "critical": 3,
}


HARD_ALERT_RULES = {
    "underwater": TriggerRule(
        key="underwater",
        label="Underwater",
        alert_class="hard_alert",
        score=100,
        description="Tracked costs have overtaken the adjusted contract value.",
    ),
    "negative_margin": TriggerRule(
        key="negative_margin",
        label="Negative Margin",
        alert_class="hard_alert",
        score=90,
        description="Realized margin is now below zero.",
    ),
    "compound_overrun": TriggerRule(
        key="compound_overrun",
        label="Compound Overrun",
        alert_class="hard_alert",
        score=80,
        description="Labor and material both show meaningful overruns at the same time.",
    ),
    "major_labor_blowout": TriggerRule(
        key="major_labor_blowout",
        label="Major Labor Blowout",
        alert_class="hard_alert",
        score=75,
        description="Labor burn is materially above estimate and needs executive attention.",
    ),
    "major_material_blowout": TriggerRule(
        key="major_material_blowout",
        label="Major Material Blowout",
        alert_class="hard_alert",
        score=70,
        description="Material spend is materially above estimate.",
    ),
    "late_stage_underbilling": TriggerRule(
        key="late_stage_underbilling",
        label="Late-Stage Underbilling",
        alert_class="hard_alert",
        score=68,
        description="The project is late stage but billing has not kept up with earned progress.",
    ),
    "large_rejected_co_exposure": TriggerRule(
        key="large_rejected_co_exposure",
        label="Rejected CO Exposure",
        alert_class="hard_alert",
        score=62,
        description="Rejected change orders represent a large commercial exposure.",
    ),
}


WATCH_SIGNAL_RULES = {
    "budget_coverage_anomaly": TriggerRule(
        key="budget_coverage_anomaly",
        label="Budget Coverage Anomaly",
        alert_class="watch_signal",
        score=22,
        description="Budget coverage is outside the healthy planning range.",
    ),
    "high_rfi_rate": TriggerRule(
        key="high_rfi_rate",
        label="High RFI Rate",
        alert_class="watch_signal",
        score=20,
        description="RFI volume or RFI aging suggests coordination friction.",
    ),
    "high_approved_co_pct": TriggerRule(
        key="high_approved_co_pct",
        label="High Approved CO %",
        alert_class="watch_signal",
        score=18,
        description="Approved change orders represent an unusually large share of the contract.",
    ),
    "estimating_anomaly": TriggerRule(
        key="estimating_anomaly",
        label="Estimating Anomaly",
        alert_class="watch_signal",
        score=18,
        description="Budget coverage and commercial behavior suggest an estimate/scope miss.",
    ),
    "mild_burn_irregularity": TriggerRule(
        key="mild_burn_irregularity",
        label="Mild Burn Irregularity",
        alert_class="watch_signal",
        score=16,
        description="Recent labor burn, overtime, crew size, or forecast trend is drifting the wrong way.",
    ),
}


ALL_TRIGGER_RULES = {
    **HARD_ALERT_RULES,
    **WATCH_SIGNAL_RULES,
}
