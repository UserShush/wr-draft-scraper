import requests
from bs4 import BeautifulSoup
import pandas as pd

BASE_URL = "https://www.pro-football-reference.com"

def get_wr_draft_data(start_year=2013, end_year=2022):
    all_data = []

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for year in range(start_year, end_year + 1):
        url = f"{BASE_URL}/years/{year}/draft.htm"
        print(f"Scraping {year} from {url}")

        response = requests.get(url, headers=headers)
        if not response.ok:
            print(f"Failed to fetch {year} page")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'id': 'drafts'})

        if not table:
            print(f"No draft table found for {year}")
            continue

        rows = table.find('tbody').find_all('tr')
        for row in rows:
            if row.get('class') == ['thead']:
                continue

            pos_cell = row.find('td', {'data-stat': 'pos'})
            if pos_cell is None or pos_cell.text.strip() != 'WR':
                continue

            try:
                player_cell = row.find('td', {'data-stat': 'player'})
                player_name = player_cell.text.strip()
                player_id = player_cell.get('data-append-csv')

                college_cell = row.find('td', {'data-stat': 'college_id'})
                pick_cell = row.find('td', {'data-stat': 'draft_pick'})
                rnd_cell = row.find('td', {'data-stat': 'draft_round'})
                team_cell = row.find('td', {'data-stat': 'team'})

                if not all([college_cell, pick_cell, rnd_cell, team_cell]):
                    continue

                college = college_cell.text.strip()
                pick = pick_cell.text.strip()
                rnd = rnd_cell.text.strip()
                team = team_cell.text.strip()

                player_data = {
                    'Year': year,
                    'Player': player_name,
                    'Player_ID': player_id,
                    'College': college,
                    'Pick': pick,
                    'Round': rnd,
                    'Team': team,
                }
                all_data.append(player_data)

            except Exception as e:
                print(f"Error extracting row: {e}")
                continue

        print(f"  WRs found in {year}: {len([x for x in all_data if x['Year'] == year])}")

    return pd.DataFrame(all_data)

if __name__ == "__main__":
    df = get_wr_draft_data()
    df.to_csv('wr_draft_data_2013_2022.csv', index=False)
    print(f"✅ Data saved to 'wr_draft_data_2013_2022.csv' with {len(df)} rows.")













