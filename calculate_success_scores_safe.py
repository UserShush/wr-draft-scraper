import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import StringIO
import time

def parse_awards(awards_str):
    if pd.isna(awards_str):
        return 0, 0, False  # Pro Bowls, All-Pros, OPOY

    pro_bowls = awards_str.count("PB")
    all_pros = awards_str.count("AP-1") + awards_str.count("AP-2")
    opoy = "OPoY" in awards_str
    return pro_bowls, all_pros, opoy

def get_1000yd_seasons(player_id):
    url = f"https://www.pro-football-reference.com/players/{player_id[0]}/{player_id}.htm"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 429:
            print(f"🛑 Rate limited on {player_id}. Stopping scrape.")
            return "RATE_LIMITED"

        from bs4 import Comment

        soup = BeautifulSoup(response.text, 'html.parser')

        # Look for commented tables
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        table = None

        for comment in comments:
            if 'receiving_and_rushing' in comment:
                table_soup = BeautifulSoup(comment, 'html.parser')
                table = table_soup.find('table', id='receiving_and_rushing')
                break

        if not table:
            print(f"⚠️ No receiving_and_rushing table found for {player_id}.")
            return 0
        
        try:
            df = pd.read_html(StringIO(str(table)))[0]
            df.columns = [col[1] if isinstance(col, tuple) else col for col in df.columns]
        except Exception as e:
            print(f"⚠️ Error reading/parsing table for {player_id}: {e}")
            return 0

        df = df[df['Season'].astype(str).str.fullmatch(r'\d{4}')]

        if 'Yds' not in df.columns:
            return 0

        yds_cleaned = pd.to_numeric(df['Yds'], errors='coerce')
        return (yds_cleaned >= 1000).sum()

    except Exception as e:
        print(f"⚠️ Error fetching page for {player_id}: {e}")
        return 0

# === MAIN SCRIPT ===

df = pd.read_csv("wr_draft_enriched.csv")

seasons = []
success_score = []
successful_flag = []

for i, row in df.iterrows():
    player_id = row['Player_ID']
    career_av = row['Career_AV']
    games = row['Games_Played']
    awards = row.get("Awards", None)

    # Parse numbers safely
    try: career_av = int(career_av)
    except: career_av = 0
    try: games = int(games)
    except: games = 0

    # === Parse Awards ===
    pro_bowls, all_pros, opoy = parse_awards(awards)

    # === Get 1000-yard seasons (with rate limit check)
    yd_seasons = get_1000yd_seasons(player_id)
    if yd_seasons == "RATE_LIMITED":
        print("💾 Saving progress before exit due to rate limit...")
        if len(seasons) > 0:
            df_partial = df.iloc[:len(seasons)].copy()
            df_partial['Estimated_Seasons'] = seasons
            df_partial['Success_Score'] = success_score
            df_partial['Successful'] = successful_flag
            df_partial.to_csv("wr_draft_partial_score.csv", index=False)
            print(f"💾 Partial file saved with {len(seasons)} players.")
        else:
            print(f"⚠️ No data to save (zero players processed).")
        break

    # === Estimate seasons played ===
    est_seasons = max(1, round(games / 16)) if games else 0

    # === Success Score Calculation ===
    score = (
        (career_av * 1.5) +
        (games * 0.4) +
        (5 * est_seasons) +
        (15 * all_pros) +
        (8 * pro_bowls) +
        (15 if opoy else 0) +
        (10 if yd_seasons >= 2 else 0)
    )

    # === Simple Binary Label
    criteria = sum([
        career_av >= 40,
        games >= 65,
        est_seasons >= 5,
        pro_bowls >= 2,
        all_pros >= 1,
        yd_seasons >= 2
    ])
    is_successful = 1 if criteria >= 2 else 0

    # Append
    seasons.append(est_seasons)
    success_score.append(score)
    successful_flag.append(is_successful)

    # 💾 Save backup every 20 players
    if (i + 1) % 20 == 0:
        if len(seasons) > 0:
            df_partial = df.iloc[:len(seasons)].copy()
            df_partial['Estimated_Seasons'] = seasons
            df_partial['Success_Score'] = success_score
            df_partial['Successful'] = successful_flag
            df_partial.to_csv("wr_draft_score_backup.csv", index=False)
            print(f"💾 Backup saved at player {i+1}")
        else:
            print(f"⚠️ No data to backup at player {i+1}")

    # ⏳ Pause after every 70 players
    if (i + 1) % 70 == 0:
        print("⏸️ Taking a 5-minute break after 70 players...")
        time.sleep(300)

    time.sleep(4.5)

# === Final Save
if len(seasons) > 0:
    df_final = df.iloc[:len(seasons)].copy()
    df_final['Estimated_Seasons'] = seasons
    df_final['Success_Score'] = success_score
    df_final['Successful'] = successful_flag
    df_final.to_csv("wr_draft_scored.csv", index=False)
    print("✅ Success scoring complete! File saved to wr_draft_scored.csv")
else:
    print("⚠️ No data to save at end of script.")



