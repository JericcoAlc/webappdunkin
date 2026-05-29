from google_places import search_places

df = search_places(
    keyword="Starbucks",
    lat=25.6866,
    lon=-100.3161,
    radius=10000
)

print("========== DATAFRAME ==========")
print(df)

print("========== ROWS ==========")
print(len(df))