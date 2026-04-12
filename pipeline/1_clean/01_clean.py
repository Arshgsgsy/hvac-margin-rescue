"""
Data Cleaning Pipeline - Stage 1
Cleans raw CSV files and outputs cleaned versions to data_cleaned/

Handles:
- Role normalization (33 variants -> 13 canonical roles)
- Material category normalization (25 variants -> 5 categories)
- Duplicate removal (labor logs by log_id)
- Cost recalculation (materials: total_cost = quantity * unit_cost)
- Data type standardization
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from constants import COST_DISCREPANCY_THRESHOLD

# Input paths (raw data)
DATA_DIR = ROOT / "data"
LABOR_INPUT = DATA_DIR / "labor_logs_all.csv"
MATERIAL_INPUT = DATA_DIR / "material_deliveries_all.csv"
CHANGE_ORDER_INPUT = DATA_DIR / "change_orders_all.csv"
RFI_INPUT = DATA_DIR / "rfis_all.csv"

# Output paths (cleaned data)
CLEANED_DIR = ROOT / "data_cleaned"
CLEANED_DIR.mkdir(exist_ok=True)

LABOR_OUTPUT = CLEANED_DIR / "labor_logs_clean.csv"
MATERIAL_OUTPUT = CLEANED_DIR / "material_deliveries_clean.csv"
CHANGE_ORDER_OUTPUT = CLEANED_DIR / "change_orders_clean.csv"
RFI_OUTPUT = CLEANED_DIR / "rfis_clean.csv"

# Quality report output
OUTPUT_SUMMARIES = ROOT / "output_summaries"
OUTPUT_SUMMARIES.mkdir(exist_ok=True)
QUALITY_REPORT_PATH = OUTPUT_SUMMARIES / "data_quality_report.json"

# ═══════════════════════════════════════════════════════════════════════════════
# ROLE NORMALIZATION MAP (33 variants -> 13 canonical roles)
# ═══════════════════════════════════════════════════════════════════════════════
ROLE_MAP = {
    # Journeyman Pipefitter variants
    'JM Pipefitter': 'Journeyman Pipefitter',
    'J. Pipefitter': 'Journeyman Pipefitter',
    'Pipefitter JM': 'Journeyman Pipefitter',
    'Journeyman P.F.': 'Journeyman Pipefitter',
    # Journeyman Sheet Metal variants
    'Sheet Metal JM': 'Journeyman Sheet Metal',
    'J. Sheet Metal': 'Journeyman Sheet Metal',
    'JM Sheet Metal': 'Journeyman Sheet Metal',
    'Journeyman S.M.': 'Journeyman Sheet Metal',
    # Apprentice 2nd Year variants
    'Apprentice 2nd Yr': 'Apprentice 2nd Year',
    'App 2nd Year': 'Apprentice 2nd Year',
    'Apprentice - 2nd': 'Apprentice 2nd Year',
    # Apprentice 4th Year variants
    'Apprentice 4th Yr': 'Apprentice 4th Year',
    'App 4th Year': 'Apprentice 4th Year',
    'Apprentice - 4th': 'Apprentice 4th Year',
    '4th Yr Apprentice': 'Apprentice 4th Year',
    # Controls Technician variants
    'Controls Tech': 'Controls Technician',
    'DDC Tech': 'Controls Technician',
    'Ctrl Technician': 'Controls Technician',
    'Controls Specialist': 'Controls Technician',
    # Foreman variants
    'Fmn': 'Foreman',
    'Lead Foreman': 'Foreman',
    'General Foreman': 'Foreman',
    # Helper/Laborer
    'Helper': 'Helper/Laborer',
}

# ═══════════════════════════════════════════════════════════════════════════════
# MATERIAL CATEGORY NORMALIZATION MAP (25 variants -> 5 categories)
# ═══════════════════════════════════════════════════════════════════════════════
CATEGORY_MAP = {
    # Controls variants
    'CONTROLS': 'Controls',
    'Control': 'Controls',
    'Controls/BAS': 'Controls',
    'controls': 'Controls',
    # Ductwork variants
    'DUCTWORK': 'Ductwork',
    'Duct Work': 'Ductwork',
    'duct work': 'Ductwork',
    'ductwork': 'Ductwork',
    # Equipment variants
    'EQUIPMENT': 'Equipment',
    'Equip.': 'Equipment',
    'equip': 'Equipment',
    'equipment': 'Equipment',
    # Insulation variants
    'INSULATION': 'Insulation',
    'Insul.': 'Insulation',
    'insul': 'Insulation',
    'insulation': 'Insulation',
    # Piping variants
    'PIPING': 'Piping',
    'Pipe': 'Piping',
    'pipe': 'Piping',
    'piping': 'Piping',
}


def build_role_case_sql():
    """Build SQL CASE expression for role normalization."""
    cases = []
    for variant, canonical in ROLE_MAP.items():
        cases.append(f"WHEN role = '{variant}' THEN '{canonical}'")
    return "CASE " + " ".join(cases) + " ELSE role END"


def build_category_case_sql():
    """Build SQL CASE expression for category normalization."""
    cases = []
    for variant, canonical in CATEGORY_MAP.items():
        cases.append(f"WHEN material_category = '{variant}' THEN '{canonical}'")
    return "CASE " + " ".join(cases) + " ELSE material_category END"


def clean_labor_data(con):
    """
    Clean labor logs:
    - Normalize role names
    - Remove duplicates (by log_id, keep first)
    - Standardize data types
    """
    print("Cleaning labor data...")

    # Get input row count
    input_count = con.execute(f"""
        SELECT COUNT(*) FROM read_csv_auto('{LABOR_INPUT}', header=True)
    """).fetchone()[0]

    # Count duplicates
    duplicate_count = con.execute(f"""
        SELECT COUNT(*) - COUNT(DISTINCT log_id)
        FROM read_csv_auto('{LABOR_INPUT}', header=True)
    """).fetchone()[0]

    # Count roles that will be normalized
    role_case = build_role_case_sql()
    roles_normalized = con.execute(f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{LABOR_INPUT}', header=True)
        WHERE role != ({role_case})
    """).fetchone()[0]

    # Create cleaned table with deduplication and normalization
    con.execute(f"""
        CREATE OR REPLACE TABLE labor_clean AS
        WITH ranked AS (
            SELECT *,
                ROW_NUMBER() OVER (PARTITION BY log_id ORDER BY date) as rn
            FROM read_csv_auto('{LABOR_INPUT}', header=True)
        )
        SELECT
            project_id,
            log_id,
            TRY_CAST(date AS DATE) AS date,
            employee_id,
            {role_case} AS role,
            sov_line_id,
            TRY_CAST(hours_st AS DOUBLE) AS hours_st,
            TRY_CAST(hours_ot AS DOUBLE) AS hours_ot,
            TRY_CAST(hourly_rate AS DOUBLE) AS hourly_rate,
            TRY_CAST(burden_multiplier AS DOUBLE) AS burden_multiplier,
            work_area,
            cost_code
        FROM ranked
        WHERE rn = 1
          AND project_id IS NOT NULL
          AND log_id IS NOT NULL
    """)

    # Export to CSV
    con.execute(f"""
        COPY labor_clean TO '{LABOR_OUTPUT}' (HEADER, DELIMITER ',')
    """)

    output_count = con.execute("SELECT COUNT(*) FROM labor_clean").fetchone()[0]

    return {
        "input_rows": input_count,
        "duplicates_removed": duplicate_count,
        "roles_normalized": roles_normalized,
        "output_rows": output_count,
    }


def clean_material_data(con):
    """
    Clean material deliveries:
    - Normalize category names
    - Recalculate total_cost = quantity * unit_cost
    - Flag significant discrepancies
    - Standardize data types
    """
    print("Cleaning material data...")

    # Get input row count
    input_count = con.execute(f"""
        SELECT COUNT(*) FROM read_csv_auto('{MATERIAL_INPUT}', header=True)
    """).fetchone()[0]

    # Count categories that will be normalized
    category_case = build_category_case_sql()
    categories_normalized = con.execute(f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{MATERIAL_INPUT}', header=True)
        WHERE material_category != ({category_case})
    """).fetchone()[0]

    # Count cost discrepancies (where recalculated != stored)
    costs_recalculated = con.execute(f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{MATERIAL_INPUT}', header=True)
        WHERE ABS(
            TRY_CAST(quantity AS DOUBLE) * TRY_CAST(unit_cost AS DOUBLE)
            - TRY_CAST(total_cost AS DOUBLE)
        ) > {COST_DISCREPANCY_THRESHOLD}
    """).fetchone()[0]

    # Create cleaned table with normalization and cost recalculation
    con.execute(f"""
        CREATE OR REPLACE TABLE material_clean AS
        SELECT
            project_id,
            delivery_id,
            TRY_CAST(date AS DATE) AS date,
            sov_line_id,
            {category_case} AS material_category,
            item_description,
            TRY_CAST(quantity AS DOUBLE) AS quantity,
            unit,
            TRY_CAST(unit_cost AS DOUBLE) AS unit_cost,
            -- Recalculate total_cost for consistency
            TRY_CAST(quantity AS DOUBLE) * TRY_CAST(unit_cost AS DOUBLE) AS total_cost,
            -- Keep original for audit
            TRY_CAST(total_cost AS DOUBLE) AS total_cost_original,
            po_number,
            vendor,
            received_by,
            condition_notes
        FROM read_csv_auto('{MATERIAL_INPUT}', header=True)
        WHERE project_id IS NOT NULL
          AND delivery_id IS NOT NULL
    """)

    # Export to CSV (exclude audit column for downstream compatibility)
    con.execute(f"""
        COPY (
            SELECT
                project_id, delivery_id, date, sov_line_id, material_category,
                item_description, quantity, unit, unit_cost, total_cost,
                po_number, vendor, received_by, condition_notes
            FROM material_clean
        ) TO '{MATERIAL_OUTPUT}' (HEADER, DELIMITER ',')
    """)

    output_count = con.execute("SELECT COUNT(*) FROM material_clean").fetchone()[0]

    return {
        "input_rows": input_count,
        "categories_normalized": categories_normalized,
        "costs_recalculated": costs_recalculated,
        "output_rows": output_count,
    }


def clean_change_orders(con):
    """
    Clean change orders:
    - Standardize data types
    - Handle NULL/empty strings uniformly
    """
    print("Cleaning change order data...")

    input_count = con.execute(f"""
        SELECT COUNT(*) FROM read_csv_auto('{CHANGE_ORDER_INPUT}', header=True)
    """).fetchone()[0]

    con.execute(f"""
        CREATE OR REPLACE TABLE change_orders_clean AS
        SELECT
            project_id,
            co_number,
            TRY_CAST(date_submitted AS DATE) AS date_submitted,
            reason_category,
            description,
            TRY_CAST(amount AS DOUBLE) AS amount,
            status,
            related_rfi,
            affected_sov_lines,
            TRY_CAST(labor_hours_impact AS DOUBLE) AS labor_hours_impact,
            TRY_CAST(schedule_impact_days AS DOUBLE) AS schedule_impact_days,
            submitted_by,
            approved_by
        FROM read_csv_auto('{CHANGE_ORDER_INPUT}', header=True)
        WHERE project_id IS NOT NULL
          AND co_number IS NOT NULL
    """)

    con.execute(f"""
        COPY change_orders_clean TO '{CHANGE_ORDER_OUTPUT}' (HEADER, DELIMITER ',')
    """)

    output_count = con.execute("SELECT COUNT(*) FROM change_orders_clean").fetchone()[0]

    return {
        "input_rows": input_count,
        "output_rows": output_count,
    }


def clean_rfis(con):
    """
    Clean RFIs:
    - Standardize data types
    - Handle NULL/empty strings uniformly
    """
    print("Cleaning RFI data...")

    input_count = con.execute(f"""
        SELECT COUNT(*) FROM read_csv_auto('{RFI_INPUT}', header=True)
    """).fetchone()[0]

    con.execute(f"""
        CREATE OR REPLACE TABLE rfis_clean AS
        SELECT
            project_id,
            rfi_number,
            TRY_CAST(date_submitted AS DATE) AS date_submitted,
            subject,
            submitted_by,
            assigned_to,
            priority,
            status,
            TRY_CAST(date_required AS DATE) AS date_required,
            TRY_CAST(date_responded AS DATE) AS date_responded,
            response_summary,
            cost_impact,
            schedule_impact
        FROM read_csv_auto('{RFI_INPUT}', header=True)
        WHERE project_id IS NOT NULL
          AND rfi_number IS NOT NULL
    """)

    con.execute(f"""
        COPY rfis_clean TO '{RFI_OUTPUT}' (HEADER, DELIMITER ',')
    """)

    output_count = con.execute("SELECT COUNT(*) FROM rfis_clean").fetchone()[0]

    return {
        "input_rows": input_count,
        "output_rows": output_count,
    }


def main():
    print("=" * 60)
    print("Data Cleaning Pipeline - Stage 1")
    print("=" * 60)

    con = duckdb.connect()

    report = {
        "timestamp": datetime.now().isoformat(),
        "labor": {},
        "materials": {},
        "change_orders": {},
        "rfis": {},
    }

    # Clean each dataset
    report["labor"] = clean_labor_data(con)
    report["materials"] = clean_material_data(con)
    report["change_orders"] = clean_change_orders(con)
    report["rfis"] = clean_rfis(con)

    # Write quality report
    with open(QUALITY_REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("Data Cleaning Complete")
    print("=" * 60)
    print(f"\nLabor:")
    print(f"  Input rows: {report['labor']['input_rows']:,}")
    print(f"  Duplicates removed: {report['labor']['duplicates_removed']:,}")
    print(f"  Roles normalized: {report['labor']['roles_normalized']:,}")
    print(f"  Output rows: {report['labor']['output_rows']:,}")

    print(f"\nMaterials:")
    print(f"  Input rows: {report['materials']['input_rows']:,}")
    print(f"  Categories normalized: {report['materials']['categories_normalized']:,}")
    print(f"  Costs recalculated: {report['materials']['costs_recalculated']:,}")
    print(f"  Output rows: {report['materials']['output_rows']:,}")

    print(f"\nChange Orders:")
    print(f"  Input rows: {report['change_orders']['input_rows']:,}")
    print(f"  Output rows: {report['change_orders']['output_rows']:,}")

    print(f"\nRFIs:")
    print(f"  Input rows: {report['rfis']['input_rows']:,}")
    print(f"  Output rows: {report['rfis']['output_rows']:,}")

    print(f"\nCleaned files written to: {CLEANED_DIR}")
    print(f"Quality report written to: {QUALITY_REPORT_PATH}")


if __name__ == "__main__":
    main()
