import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import time

def get_player_stats(player_id):
    url = f"https://www.pro-football-reference.com/players/{player_id[0]}/{player_id}.htm"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
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
        return {'Career_AV': 'N/A', 'Games_Played': 'N/A', 'Note': str(e)}

# === Main Batch Job ===

input_file = "wr_draft_data_2013_2022.csv"
df = pd.read_csv(input_file)

df['Career_AV'] = None
df['Games_Played'] = None
df['Note'] = None

for i, row in df.iterrows():
    player_id = row['Player_ID']
    print(f"🔍 {i+1}/{len(df)}: Scraping {player_id}...")
    stats = get_player_stats(player_id)
    df.at[i, 'Career_AV'] = stats['Career_AV']
    df.at[i, 'Games_Played'] = stats['Games_Played']
    df.at[i, 'Note'] = stats['Note']
    time.sleep(1.5)  # Respectful scraping

output_file = "wr_draft_enriched.csv"
df.to_csv(output_file, index=False)
print(f"\n✅ Done! Enriched data saved to {output_file}")
