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

## ✅ Success Criteria for WRs

To determine whether a WR is considered "successful," we will use the following criteria, which are based on both availability and production:

- **Career AV ≥ 15** (weight: 40%) — Signals substantial contribution over time.
- **Second contract signed with the same or another NFL team** (weight: 30%) — Indicates perceived value by the league.
- **Total games played ≥ 48 (3 seasons)** (weight: 15%) — Suggests baseline durability and availability.
- **Seasons with 500+ receiving yards ≥ 2** (weight: 15%) — Indicates real, repeatable production.

Scoring will be additive. Players who exceed thresholds will score points toward an overall "success score" out of 100. We may refine thresholds or introduce additional variables (e.g., yards per route run, team context, breakout age) if supported by available data.

This system is intentionally conservative to prioritize reliability and versatility over single-season anomalies.

## 📋 Next Steps

- Fix parsing to handle missing/hidden data more gracefully.
- Add analysis notebook to classify "successful" WRs by various metrics.
- Build a predictive model for the current WR draft class.

---

Yes, this is weirdly ambitious. Yes, we know.

