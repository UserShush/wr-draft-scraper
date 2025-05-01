import requests
from bs4 import BeautifulSoup, Comment
import pandas as pd
from io import StringIO
import time
import re

def get_player_stats(player_id):
    url = f"https://www.pro-football-reference.com/players/{player_id[0]}/{player_id}.htm"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 429:
            return {'rate_limited': True}

        if not response.ok:
            return {'Note': 'Request failed'}

        soup = BeautifulSoup(response.text, 'html.parser')

        stats = {
            'Career_AV': None,
            'Games_Played': None,
            'Receptions': None,
            'Receiving_Yards': None,
            'Receiving_TDs': None,
            'Rec/Game': None,
            'Yards/Game': None,
            'TD/Game': None,
            'Pro_Bowls': 0,
            'All_Pros': 0,
            'OPOY': False,
            'Successful': None,
            'Note': 'Parsed'
        }

        # === Honors: Pro Bowl, All-Pro, OPOY ===
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        recognition_text = ""
        for comment in comments:
            if "Recognition" in comment:
                recognition_text = comment.lower()
                break

        if not recognition_text:
            meta = soup.find('div', id='meta')
            if meta:
                recognition_text = meta.get_text(" ").lower()

        if recognition_text:
            pb_match = re.search(r'(\d+)[x\- ]+pro bowl', recognition_text)
            ap_match = re.search(r'(\d+)[x\- ]+all-pro', recognition_text)
            if pb_match:
                stats['Pro_Bowls'] = int(pb_match.group(1))
            if ap_match:
                stats['All_Pros'] = int(ap_match.group(1))
            if "opoy" in recognition_text or "offensive player of the year" in recognition_text:
                stats['OPOY'] = True

        # === Receiving Table ===
        table = soup.find('table', id='receiving_and_rushing')
        if table:
            df = pd.read_html(StringIO(str(table)))[0]
            df.columns = [col[1] if isinstance(col, tuple) else col for col in df.columns]
            df = df[df['Season'].astype(str).str.fullmatch(r'\d{4}')]
            df = df.drop_duplicates(subset='Season', keep='first')

            def safe_sum(col_name):
                try:
                    return int(pd.to_numeric(df[col_name], errors='coerce').sum())
                except:
                    return None

            def safe_sum_idx(idx):
                try:
                    return int(pd.to_numeric(df.iloc[:, idx], errors='coerce').sum())
                except:
                    return None

            stats['Career_AV'] = safe_sum('AV')
            stats['Games_Played'] = safe_sum('G')
            stats['Receptions'] = safe_sum('Rec')
            stats['Receiving_Yards'] = safe_sum_idx(9)     # Receiving Yards
            stats['Receiving_TDs'] = safe_sum_idx(11)      # Receiving TDs

            # === Per-game stats
            gp = stats['Games_Played']
            if gp and gp > 0:
                stats['Rec/Game'] = round(stats['Receptions'] / gp, 2) if stats['Receptions'] else 0
                stats['Yards/Game'] = round(stats['Receiving_Yards'] / gp, 2) if stats['Receiving_Yards'] else 0
                stats['TD/Game'] = round(stats['Receiving_TDs'] / gp, 2) if stats['Receiving_TDs'] else 0

                # === Success Criteria ===
                per_game_hits = sum([
                    stats['Rec/Game'] >= 4.5,
                    stats['Yards/Game'] >= 55,
                    stats['TD/Game'] >= 0.3
                ])
                stats['Successful'] = (
                    per_game_hits >= 2 or
                    (stats['Career_AV'] is not None and stats['Career_AV'] >= 40) or
                    stats['Pro_Bowls'] >= 2
                )

        return stats

    except Exception as e:
        return {'Note': f'Request error: {e}'}

# === Load and prepare dataframe ===
df = pd.read_csv("wr_draft_enriched.csv")
# df = df.head(30).copy()  # ← comment out or remove

columns = [
    'Career_AV', 'Games_Played', 'Receptions', 'Receiving_Yards', 'Receiving_TDs',
    'Rec/Game', 'Yards/Game', 'TD/Game', 'Pro_Bowls', 'All_Pros', 'OPOY', 'Successful', 'Note'
]
for col in columns:
    if col not in df.columns:
        df[col] = None

# Reset for fresh test
df[columns] = None

# === Scraping loop ===
for i, row in df.iterrows():
    player_id = row['Player_ID']
    print(f"🔍 {i+1}: Scraping {player_id}...")

    stats = get_player_stats(player_id)

    if stats.get('rate_limited'):
        print("🛑 Rate limit hit. Exiting.")
        df.to_csv("wr_draft_30_test.csv", index=False)
        break

    for key, value in stats.items():
        df.at[i, key] = value

    if i % 10 == 0 and i != 0:
        print("💾 Backup saved.")
        df.to_csv("wr_draft_30_test_backup.csv", index=False)

    if i % 70 == 0 and i != 0:
        print("⏸️ Taking a 5-minute rest...")
        time.sleep(300)
    else:
        time.sleep(4.5)

df.to_csv("wr_draft_30_test.csv", index=False)
print("\n✅ Done! Data saved to wr_draft_30_test.csv")

