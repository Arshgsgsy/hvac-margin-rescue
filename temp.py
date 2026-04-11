import duckdb

con = duckdb.connect()

df = con.execute("""
SELECT *
FROM read_csv_auto('hvac_data/material_deliveries_all.csv', header=True)
LIMIT 5
""").df()

print(df.columns.tolist())
print(df.head())