import duckdb

con = duckdb.connect()

df = con.execute("""
SELECT *
FROM read_csv_auto('hvac_data/change_orders_all.csv')
LIMIT 5
""").df()

print(df.columns.tolist())
print(df.head())