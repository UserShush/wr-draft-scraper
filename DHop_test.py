import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO

def get_player_stats(player_id):
    url = f"https://www.pro-football-reference.com/players/{player_id[0]}/{player_id}.htm"
    print(f"🔗 Trying URL: {url}")
    
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if not response.ok:
        return {
            'Player_ID': player_id,
            'Career_AV': 'N/A',
            'Games_Played': 'N/A',
            'Receptions': 'N/A',
            'Receiving_Yards': 'N/A',
            'Receiving_TDs': 'N/A',
            'Rec/Game': 'N/A',
            'Yards/Game': 'N/A',
            'TD/Game': 'N/A',
            'Successful': 'N/A',
            'Note': 'Request failed'
        }

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', id='receiving_and_rushing')

    # Defaults
    career_av = games_played = receptions = receiving_yards = receiving_tds = None
    rec_per_game = yds_per_game = td_per_game = None
    successful = False

    if table:
        try:
            df = pd.read_html(StringIO(str(table)))[0]
            df.columns = [col[1] if isinstance(col, tuple) else col for col in df.columns]

            # Filter real NFL seasons
            df = df[df['Season'].astype(str).str.fullmatch(r'\d{4}')]
            df = df.drop_duplicates(subset='Season', keep='first')

            def safe_sum_by_index(index):
                try:
                    cleaned = pd.to_numeric(df.iloc[:, index], errors='coerce')
                    return int(cleaned.sum()) if not cleaned.isna().all() else None
                except:
                    return None

            def safe_sum_by_name(name):
                try:
                    cleaned = pd.to_numeric(df[name], errors='coerce')
                    return int(cleaned.sum()) if not cleaned.isna().all() else None
                except:
                    return None

            games_played = safe_sum_by_name('G')
            career_av = safe_sum_by_name('AV')
            receptions = safe_sum_by_name('Rec')
            receiving_yards = safe_sum_by_index(9)
            receiving_tds = safe_sum_by_index(11)

            # === Per-game calculations ===
            if games_played and games_played > 0:
                rec_per_game = round(receptions / games_played, 2) if receptions else 0
                yds_per_game = round(receiving_yards / games_played, 2) if receiving_yards else 0
                td_per_game = round(receiving_tds / games_played, 2) if receiving_tds else 0

                # === Success criteria: hit 2 out of 3 thresholds ===
                hit_count = 0
                if rec_per_game >= 5.0: hit_count += 1
                if yds_per_game >= 65: hit_count += 1
                if td_per_game >= 0.4: hit_count += 1
                successful = hit_count >= 2

        except Exception as e:
            print(f"⚠️ Error parsing table for {player_id}: {e}")

    return {
        'Player_ID': player_id,
        'Career_AV': str(career_av) if career_av is not None else 'N/A',
        'Games_Played': str(games_played) if games_played is not None else 'N/A',
        'Receptions': str(receptions) if receptions is not None else 'N/A',
        'Receiving_Yards': str(receiving_yards) if receiving_yards is not None else 'N/A',
        'Receiving_TDs': str(receiving_tds) if receiving_tds is not None else 'N/A',
        'Rec/Game': rec_per_game if rec_per_game is not None else 'N/A',
        'Yards/Game': yds_per_game if yds_per_game is not None else 'N/A',
        'TD/Game': td_per_game if td_per_game is not None else 'N/A',
        'Successful': successful,
        'Note': 'Parsed by index-aware logic + per-game success check'
    }

# === Run the test ===
print(get_player_stats("HopkDe00"))







