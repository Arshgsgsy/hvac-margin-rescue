import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHANGE_FILE = ROOT / "hvac_data" / "change_orders_all.csv"

con = duckdb.connect()

df = con.execute(f"""
SELECT *
FROM read_csv_auto('{CHANGE_FILE}')
LIMIT 5
""").df()

print(df.columns.tolist())
print(df.head())
