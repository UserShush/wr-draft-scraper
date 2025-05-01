import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import time

def get_player_stats(player_id):
    """Scrapes Career AV and Games Played from PFR."""
    url = f"https://www.pro-football-reference.com/players/{player_id[0]}/{player_id}.htm"
    headers = {"User-Agent": "Mozilla/5.0"}

    for attempt in range(3):  # Retry up to 3 times
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 429:
                print("🛑 Rate limit hit. Sleeping 30 seconds...")
                time.sleep(30)
                continue
            if not response.ok:
                return {'Career_AV': 'N/A', 'Games_Played': 'N/A', 'Note': 'Request failed'}

            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', id='receiving_and_rushing')
            if not table:
                return {'Career_AV': 'N/A', 'Games_Played': 'N/A', 'Note': 'Table not found'}

            df = pd.read_html(StringIO(str(table)))[0]
            df.columns = [col[1] if isinstance(col, tuple) else col for col in df.columns]
            df = df[df['Season'].astype(str).str.fullmatch(r'\d{4}')]
            df = df.drop_duplicates(subset='Season', keep='first')

            av = int(df['AV'].sum()) if 'AV' in df.columns else 'N/A'
            gp = int(df['G'].sum()) if 'G' in df.columns else 'N/A'

            return {'Career_AV': av, 'Games_Played': gp, 'Note': 'Success'}

        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} failed: {e}")
            time.sleep(5)  # Wait before retry

    return {'Career_AV': 'N/A', 'Games_Played': 'N/A', 'Note': 'Max retries failed'}

# === Batch Mode ===

df = pd.read_csv("wr_draft_enriched.csv")

for i, row in df.iterrows():
    if pd.notna(row['Career_AV']) and row['Career_AV'] != 'N/A':
        print(f"✅ {i+1}: Skipping {row['Player_ID']} (already scraped)")
        continue

    player_id = row['Player_ID']
    print(f"🔍 {i+1}: Scraping {player_id}...")
    stats = get_player_stats(player_id)

    df.at[i, 'Career_AV'] = stats['Career_AV'] if stats['Career_AV'] != 'N/A' else None
    df.at[i, 'Games_Played'] = stats['Games_Played'] if stats['Games_Played'] != 'N/A' else None
    df.at[i, 'Note'] = stats['Note']

    # Save every 20 scrapes as backup
    if i % 20 == 0:
        df.to_csv("wr_draft_enriched_backup.csv", index=False)
        print("💾 Backup saved.")

    time.sleep(1)  # Respectful delay to avoid rate limits

# Final save
df.to_csv("wr_draft_enriched.csv", index=False)
print("✅ All done! Final data saved to wr_draft_enriched.csv")
