import requests
from bs4 import BeautifulSoup, Comment
import pandas as pd
from io import StringIO
import time
import re

def get_player_stats(player_id):
    """Scrape AV, Games Played, Pro Bowl, All-Pro, and OPOY info."""
    url = f"https://www.pro-football-reference.com/players/{player_id[0]}/{player_id}.htm"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 429:
            return {'rate_limited': True}

        if not response.ok:
            return {'Career_AV': None, 'Games_Played': None,
                    'Pro_Bowls': None, 'All_Pros': None, 'OPOY': None, 'Note': 'Request failed'}

        soup = BeautifulSoup(response.text, 'html.parser')
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))

        # === RECOGNITION ===
        pro_bowls = 0
        all_pros = 0
        opoy = False
        recognition_text = ""

        for comment in comments:
            if "Recognition" in comment:
                recognition_text = comment.lower()
                break

        if recognition_text:
            pb_match = re.search(r'(\d+)x pro bowl', recognition_text)
            ap_match = re.search(r'(\d+)x all-pro', recognition_text)
            if pb_match:
                pro_bowls = int(pb_match.group(1))
            if ap_match:
                all_pros = int(ap_match.group(1))
            if "opoy" in recognition_text or "offensive player of the year" in recognition_text:
                opoy = True

                # === STATS TABLE (Receiving) ===
        career_av = None
        games_played = None

        # Step 1: Try to find the table normally
        table = soup.find('table', id='receiving_and_rushing')
        if table:
            try:
                df = pd.read_html(StringIO(str(table)))[0]
            except Exception:
                df = None
        else:
            # Step 2: Look in HTML comments if table is hidden
            df = None
            for comment in comments:
                if 'receiving_and_rushing' in comment:
                    comment_html = BeautifulSoup(comment, 'html.parser')
                    table = comment_html.find('table', id='receiving_and_rushing')
                    if table:
                        try:
                            df = pd.read_html(StringIO(str(table)))[0]
                            break
                        except Exception:
                            continue

        # Parse the table if found
        if df is not None:
            try:
                df.columns = [col[1] if isinstance(col, tuple) else col for col in df.columns]
                df.columns = df.columns.str.lower()
                if 'season' in df.columns:
                    df = df[df['season'].astype(str).str.fullmatch(r'\d{4}')]
                    df = df.drop_duplicates(subset='season', keep='first')

                    def safe_sum(series):
                        cleaned = pd.to_numeric(series, errors='coerce')
                        return int(cleaned.sum()) if not cleaned.isna().all() else None

                    career_av = safe_sum(df['av']) if 'av' in df.columns else None
                    games_played = safe_sum(df['g']) if 'g' in df.columns else None
            except Exception as e:
                print(f"⚠️ Error processing table for {player_id}: {e}")
        else:
            print(f"⚠️ Still could not find receiving stats for {player_id}")


        return {
            'Career_AV': career_av,
            'Games_Played': games_played,
            'Pro_Bowls': pro_bowls,
            'All_Pros': all_pros,
            'OPOY': opoy,
            'Note': 'Success' if career_av is not None or games_played is not None else 'No valid data'
        }

    except Exception as e:
        return {
            'Career_AV': None,
            'Games_Played': None,
            'Pro_Bowls': None,
            'All_Pros': None,
            'OPOY': None,
            'Note': str(e)
        }

# === BATCH MODE ===

df = pd.read_csv("wr_draft_enriched.csv")
df = df.head(10).copy()  # Only test on first 10 players

# Ensure necessary columns exist
for col in ['Career_AV', 'Games_Played', 'Pro_Bowls', 'All_Pros', 'OPOY', 'Note']:
    if col not in df.columns:
        df[col] = None

for i, row in df.iterrows():
    if pd.notna(row['Career_AV']):
        print(f"✅ {i+1}: Skipping {row['Player_ID']} (already scraped)")
        continue

    player_id = row['Player_ID']
    print(f"\n🔍 {i+1}: Scraping {player_id}...")

    stats = get_player_stats(player_id)

    if stats.get('rate_limited'):
        print("🛑 Rate limit detected. Saving and exiting early.")
        df.to_csv("wr_draft_enriched.csv", index=False)
        break

    for key in ['Career_AV', 'Games_Played', 'Pro_Bowls', 'All_Pros', 'OPOY', 'Note']:
        df.at[i, key] = stats.get(key)

    time.sleep(4.5)

df.to_csv("2wr_draft_enriched.csv", index=False)
print("\n✅ Test batch completed. Data saved to 2wr_draft_enriched.csv")


