import pandas as pd
import requests
from bs4 import BeautifulSoup, Comment
from io import StringIO
import time
import re

def get_player_stats(player_id):
    """Scrape AV, Games Played, Career Yards, Career TDs, and Recognition info."""
    url = f"https://www.pro-football-reference.com/players/{player_id[0]}/{player_id}.htm"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 429:
            return {'rate_limited': True}

        if not response.ok:
            return {'Career_AV': None, 'Games_Played': None, 'Career_Yards': None, 'Career_TDs': None,
                    'Pro_Bowls': None, 'All_Pros': None, 'OPOY': None, 'Note': 'Request failed'}

        soup = BeautifulSoup(response.text, 'html.parser')

        # === Scrape Recognition ===
        recognition_text = ""
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            if "Recognition" in comment:
                recognition_text = comment
                break

        pro_bowls = 0
        all_pros = 0
        opoy = False

        if recognition_text:
            if "Pro Bowl" in recognition_text:
                match = re.search(r'(\d+)x Pro Bowl', recognition_text)
                if match:
                    pro_bowls = int(match.group(1))

            if "All-Pro" in recognition_text:
                match = re.search(r'(\d+)x All-Pro', recognition_text)
                if match:
                    all_pros = int(match.group(1))

            if "OPOY" in recognition_text or "Offensive Player of the Year" in recognition_text:
                opoy = True

        # === Scrape Receiving Table ===
        table = None
        div = soup.find('div', id='all_receiving_and_rushing')

        if div:
            comment = div.find(string=lambda text: isinstance(text, Comment))
            if comment:
                comment_html = BeautifulSoup(comment, 'html.parser')
                table = comment_html.find('table')

        if not table:
            return {'Career_AV': None, 'Games_Played': None, 'Career_Yards': None, 'Career_TDs': None,
                    'Pro_Bowls': pro_bowls, 'All_Pros': all_pros, 'OPOY': opoy, 'Note': 'Table not found'}

        df = pd.read_html(StringIO(str(table)))[0]
        df.columns = [col[1] if isinstance(col, tuple) else col for col in df.columns]
        df.columns = df.columns.str.lower()

        df = df[df['season'].astype(str).str.fullmatch(r'\d{4}')]  # Only real seasons
        df = df.drop_duplicates(subset='season', keep='first')

        def safe_sum(series):
            cleaned = pd.to_numeric(series, errors='coerce')
            return int(cleaned.sum()) if not cleaned.isna().all() else None

        av = safe_sum(df['av']) if 'av' in df.columns else None
        gp = safe_sum(df['g']) if 'g' in df.columns else None
        yds = safe_sum(df['yds']) if 'yds' in df.columns else None
        tds = safe_sum(df['td']) if 'td' in df.columns else None

        if av is None and gp is None:
            return {'Career_AV': None, 'Games_Played': None, 'Career_Yards': None, 'Career_TDs': None,
                    'Pro_Bowls': pro_bowls, 'All_Pros': all_pros, 'OPOY': opoy, 'Note': 'No valid data (opt out/suspension?)'}
        else:
            return {
                'Career_AV': av,
                'Games_Played': gp,
                'Career_Yards': yds,
                'Career_TDs': tds,
                'Pro_Bowls': pro_bowls,
                'All_Pros': all_pros,
                'OPOY': opoy,
                'Note': 'Success'
            }

    except Exception as e:
        return {'Career_AV': None, 'Games_Played': None, 'Career_Yards': None, 'Career_TDs': None,
                'Pro_Bowls': None, 'All_Pros': None, 'OPOY': None, 'Note': str(e)}

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
        df.to_csv("wr_draft_fully_enriched_partial.csv", index=False)
        break

    df.at[i, 'Career_AV'] = stats['Career_AV']
    df.at[i, 'Games_Played'] = stats['Games_Played']
    df.at[i, 'Career_Yards'] = stats['Career_Yards']
    df.at[i, 'Career_TDs'] = stats['Career_TDs']
    df.at[i, 'Pro_Bowls'] = stats['Pro_Bowls']
    df.at[i, 'All_Pros'] = stats['All_Pros']
    df.at[i, 'OPOY'] = stats['OPOY']
    df.at[i, 'Note'] = stats['Note']

    if i % 20 == 0:
        df.to_csv("wr_draft_fully_enriched_backup.csv", index=False)
        print("💾 Backup saved.")

    if i % 70 == 0 and i != 0:
        print("⏸️ Taking a 5-minute break after 70 players...")
        time.sleep(300)

    time.sleep(4.5)

# Final save
df.to_csv("wr_draft_fully_enriched.csv", index=False)
print("✅ All done! Final data saved to wr_draft_fully_enriched.csv")

















