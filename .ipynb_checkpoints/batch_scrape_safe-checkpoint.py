import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import time

def get_player_stats(player_id):
    """Scrape AV and Games Played from PFR, safely."""
    url = f"https://www.pro-football-reference.com/players/{player_id[0]}/{player_id}.htm"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 429:
            return {'rate_limited': True}

        if not response.ok:
            return {'Career_AV': None, 'Games_Played': None, 'Note': 'Request failed'}

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', id='receiving_and_rushing')
        if not table:
            return {'Career_AV': None, 'Games_Played': None, 'Note': 'Table not found'}

        df = pd.read_html(StringIO(str(table)))[0]
        df.columns = [col[1] if isinstance(col, tuple) else col for col in df.columns]
        df = df[df['Season'].astype(str).str.fullmatch(r'\d{4}')]
        df = df.drop_duplicates(subset='Season', keep='first')

        def safe_sum(series):
            cleaned = pd.to_numeric(series, errors='coerce')
            return int(cleaned.sum()) if not cleaned.isna().all() else None

        av = safe_sum(df['AV']) if 'AV' in df.columns else None
        gp = safe_sum(df['G']) if 'G' in df.columns else None

        if av is None and gp is None:
            return {'Career_AV': None, 'Games_Played': None, 'Note': 'No valid data (e.g. opt out, suspension)'}
        else:
            return {'Career_AV': av, 'Games_Played': gp, 'Note': 'Success'}

    except Exception as e:
        return {'Career_AV': None, 'Games_Played': None, 'Note': str(e)}

# === Batch Mode ===

df = pd.read_csv("wr_draft_enriched.csv")

for i, row in df.iterrows():
    if pd.notna(row['Career_AV']) and row['Career_AV'] != 'N/A':
        print(f"✅ {i+1}: Skipping {row['Player_ID']} (already scraped)")
        continue

    player_id = row['Player_ID']
    print(f"🔍 {i+1}: Scraping {player_id}...")

    stats = get_player_stats(player_id)

    if 'rate_limited' in stats and stats['rate_limited']:
        print("🛑 Rate limit detected. Saving and exiting immediately.")
        df.to_csv("wr_draft_enriched.csv", index=False)
        break

    df.at[i, 'Career_AV'] = stats['Career_AV'] if stats['Career_AV'] is not None else None
    df.at[i, 'Games_Played'] = stats['Games_Played'] if stats['Games_Played'] is not None else None
    df.at[i, 'Note'] = stats['Note']

    if i % 20 == 0:
        df.to_csv("wr_draft_enriched_backup.csv", index=False)
        print("💾 Backup saved.")

    if i % 50 == 0 and i != 0:
        print("⏸️ Taking a 4-minute break after 50 players...")
        time.sleep(240)

    time.sleep(4.5)

# Final save if we make it all the way
df.to_csv("wr_draft_enriched.csv", index=False)
print("✅ All done! Final data saved to wr_draft_enriched.csv")
