import duckdb

con = duckdb.connect()

sample = con.execute("""
SELECT *
FROM read_csv_auto('hvac_data/sov_budget_all.csv', header=True)
LIMIT 5
""").df()

print("COLUMNS:")
print(sample.columns.tolist())

print("\nSAMPLE DATA:")
print(sample.head())