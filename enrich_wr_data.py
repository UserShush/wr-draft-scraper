import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re

BASE_URL = "https://www.pro-football-reference.com/players"

def get_player_url(player_name):
    last, first = player_name.split(",") if "," in player_name else ("", "")
    if not first or not last:
        return None
    player_id = (last[:4] + first[:2]).title().replace(" ", "") + "00"
    first_letter = last[0].upper()
    return f"{BASE_URL}/{first_letter}/{player_id}.htm"

def scrape_player_stats(url):
    stats = {
        'Games_Played': None,
        'Career_AV': None,
        'Receiving_Yards': None,
        'Receiving_TDs': None,
        'Seasons_Played': None,
    }

    try:
        res = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0"
        })
        soup = BeautifulSoup(res.text, 'html.parser')

        # Find AV and Games from the summary box
        summary = soup.find('div', {'id': 'meta'})
        if summary:
            info_text = summary.text
            g_match = re.search(r'G\b.*?(\d+)', info_text)
            av_match = re.search(r'AV\b.*?(\d+)', info_text)
            if g_match:
                stats['Games_Played'] = int(g_match.group(1))
            if av_match:
                stats['Career_AV'] = int(av_match.group(1))

        # Find receiving career totals
        rec_table = soup.find('table', {'id': 'receiving_and_rushing'})
        if rec_table:
            tfoot = rec_table.find('tfoot')
            if tfoot:
                row = tfoot.find('tr')
                stats['Receiving_Yards'] = int(row.find('td', {'data-stat': 'rec_yds'}).text.replace(",", ""))
                stats['Receiving_TDs'] = int(row.find('td', {'data-stat': 'rec_td'}).text)

        # Estimate seasons played from the years in player stats table
        years = soup.find_all('th', {'data-stat': 'year_id'})
        year_values = sorted({int(y.text) for y in years if y.text.isdigit()})
        if year_values:
            stats['Seasons_Played'] = len(set(year_values))

    except Exception as e:
        print(f"Error scraping {url}: {e}")

    return stats

# Load your WR draft data
df = pd.read_csv('wr_draft_data_2013_2022.csv')

# Add new stat columns
df['Games_Played'] = None
df['Career_AV'] = None
df['Receiving_Yards'] = None
df['Receiving_TDs'] = None
df['Seasons_Played'] = None

for i, row in df.iterrows():
    player_name = row['Player']
    url = get_player_url(player_name)
    if not url:
        print(f"Skipping {player_name} - could not generate URL")
        continue

    print(f"Scraping: {player_name} → {url}")
    stats = scrape_player_stats(url)

    for key in stats:
        df.at[i, key] = stats[key]

    time.sleep(1.5)  # Be kind to PFR. They remember.

df.to_csv('wr_draft_enriched.csv', index=False)
print("✅ WR data enriched and saved to 'wr_draft_enriched.csv'")
