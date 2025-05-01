import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import time

def get_player_stats(player_id):
    """Scrape AV and Games Played from PFR."""
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

        av = int(df['AV'].sum()) if 'AV' in df.columns else None
        gp = int(df['G'].sum()) if 'G' in df.columns else None

        return {'Career_AV': av, 'Games_Played': gp, 'Note': 'Success'}

    except Exception as e:
        return {'Career_AV': None, 'Games_Played': None, 'Note': str(e)}

# === Batch Mode ===

df = pd.read_csv("wr_draft_enriched.csv")

rate_limit_count = 0
cooldown_timer = [300, 900]  # 5 min, then 15 min

for i, row in df.iterrows():
    if pd.notna(row['Career_AV']) and row['Career_AV'] != 'N/A':
        print(f"✅ {i+1}: Skipping {row['Player_ID']} (already scraped)")
        continue

    player_id = row['Player_ID']
    print(f"🔍 {i+1}: Scraping {player_id}...")

    stats = get_player_stats(player_id)

    # If we get rate-limited
    if 'rate_limited' in stats and stats['rate_limited']:
        wait_time = cooldown_timer[min(rate_limit_count, len(cooldown_timer)-1)]
        print(f"🛑 Rate limit hit. Sleeping {wait_time // 60} minutes...")
        rate_limit_count += 1
        time.sleep(wait_time)
        continue  # Retry same player after cooldown

    rate_limit_count = 0  # Reset if we scrape successfully

    df.at[i, 'Career_AV'] = stats['Career_AV']
    df.at[i, 'Games_Played'] = stats['Games_Played']
    df.at[i, 'Note'] = stats['Note']

    if i % 20 == 0:
        df.to_csv("wr_draft_enriched_backup.csv", index=False)
        print("💾 Backup saved.")

    time.sleep(1.5)  # polite delay

# Final save
df.to_csv("wr_draft_enriched.csv", index=False)
print("✅ All done! Final data saved to wr_draft_enriched.csv")
