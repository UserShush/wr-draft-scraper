# WR Draft Scraper (2013–2022)

This project scrapes wide receiver draft data from Pro-Football-Reference for the years 2013–2022.

## 🧠 Goals

- Identify traits of successful NFL WRs drafted.
- Find hidden or underappreciated performance indicators or metrics that can be applied to predict successful current draft class players.
- Create custom metrics and apply them to the current WR draft class.

## 📦 Contents

- `scrape-wr-data.py`: Scraper script for collecting WR draft data.
- `wr_draft_data_2013_2022.csv`: Cleaned draft dataset.
- `TODO`: Analysis script to come.

## 🔍 Scraping Notes

- Target: [[https://www.pro-football-reference.com/years/](https://www.pro-football-reference.com/years/)[YEAR\]/draft.htm](https://www.pro-football-reference.com/years/\[YEAR]/draft.htm)
- Data table sometimes requires special parsing (commented-out HTML).
- Errors may occur if structure changes or fields are missing.

## 💀 Pain Points

- HTML structure isn't always consistent.
- Some draft tables are inside HTML comments.
- Not all rows have complete data.

## 📋 Success Criteria (Binary Pass/Fail)

| Metric            | Threshold                              |
|------------------|-----------------------------------------|
| Career AV        | ≥ 40                                 |
| Games Played     | ≥ 80                                 |
| Pro Bowls        | ≥ 2 selections                       |
| All-Pro          | ≥ 1 selection                        |
| OPOY             | Has won the award                      |
| Fantasy Rank     | ≥ 2 seasons ranked WR30 or better    |
| Fantasy Points   | ≥ 2 seasons with 180+ points         |

## 🎯 Weighted Success Score

| Component                         | Rule                                  | Max Points |
|----------------------------------|---------------------------------------|------------|
| **Career AV**                    | 1 point per AV, capped at 40          | 40         |
| **Games Played**                 | 0.5 point per game, capped at 80 GP   | 40         |
| **Pro Bowls**                    | 5 points each, max of 2 counted       | 10         |
| **All-Pro Selections**           | 10 points for 1 selection             | 10         |
| **Offensive Player of the Year** | 10 points if won                      | 10         |
| **Fantasy Seasons (Top 30)**     | 2 points per season, max 2 counted    | 4          |
| **Fantasy Seasons (180+ pts)**   | 2 points per season, max 2 counted    | 4          |

## 🧩 Next Steps

- Fix parsing to handle missing/hidden data more gracefully.
- Add analysis notebook to classify "successful" WRs by various metrics.
- Build a predictive model for the current WR draft class.
- Expand scraper to pull all metrics needed for binary and weighted success models.

---

Yes, this is weirdly ambitious. Yes, we know.


