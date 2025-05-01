import pandas as pd

# Load your dataset
df = pd.read_csv("wr_draft_full_enriched.csv")

# === Safe conversions ===
df['Rec/Game'] = pd.to_numeric(df['Rec/Game'], errors='coerce')
df['Yards/Game'] = pd.to_numeric(df['Yards/Game'], errors='coerce')
df['TD/Game'] = pd.to_numeric(df['TD/Game'], errors='coerce')
df['Career_AV'] = pd.to_numeric(df['Career_AV'], errors='coerce')
df['Pro_Bowls'] = pd.to_numeric(df['Pro_Bowls'], errors='coerce')
df['All_Pros'] = pd.to_numeric(df['All_Pros'], errors='coerce')

# === Scaling constants (max realistic values) ===
max_rec_pg = 10
max_yds_pg = 100
max_td_pg = 1
max_av = 120
max_pb = 5
max_ap = 3

# === Calculate scaled values (0–1) ===
df['scaled_rec_pg'] = df['Rec/Game'] / max_rec_pg
df['scaled_yds_pg'] = df['Yards/Game'] / max_yds_pg
df['scaled_td_pg']  = df['TD/Game'] / max_td_pg
df['scaled_av']     = df['Career_AV'] / max_av
df['scaled_pb']     = df['Pro_Bowls'] / max_pb
df['scaled_ap']     = df['All_Pros'] / max_ap

# Fill NA values with 0 (safe default for scoring)
df.fillna({
    'scaled_rec_pg': 0,
    'scaled_yds_pg': 0,
    'scaled_td_pg': 0,
    'scaled_av': 0,
    'scaled_pb': 0,
    'scaled_ap': 0
}, inplace=True)

# === Score formula ===
df['Performance_Score'] = (
    df['scaled_rec_pg'] * 0.2 +
    df['scaled_yds_pg'] * 0.3 +
    df['scaled_td_pg']  * 0.2 +
    df['scaled_av']     * 0.15 +
    df['scaled_pb']     * 0.1 +
    df['scaled_ap']     * 0.05
) * 100

# === Save result ===
df.to_csv("wr_draft_scored.csv", index=False)
print("✅ Scoring complete. File saved as wr_draft_scored.csv")
