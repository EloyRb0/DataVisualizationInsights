# Salesforce Event Report — Analysis

Reproducible script to compute summary statistics and generate simple visualizations for event participation data.

## Pipeline
- Parse event dates and normalize flags (Registered, Attended, Newsletter).
- Aggregate by month, campaign, and country.
- Export CSV tables and PNG charts.
- Emit `summary.json` and `insights.md`.

## How to run
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/run_analysis.py --input clean_salesforce_report.csv --outdir outputs
```

## Tools
- Python 3.10+
- pandas, numpy, matplotlib

## Outputs
- `outputs/summary.json`
- `outputs/registrations_by_month.csv`
- `outputs/registrations_by_campaign.csv`
- `outputs/registrations_by_country.csv`
- `outputs/chart_registrations_by_month.png`
- `outputs/chart_top10_campaigns_registrations.png`
- `outputs/chart_attendance_rate_by_country.png`
- `outputs/insights.md`

## Actionable insights (sample)
# Actionable Insights

- '[Workshop] Crea tu primer GPT (2024)' attracts many registrations (431) but converts poorly (26%). Add reminder emails/SMS and calendar invites.
- Guatemala shows strong conversion (75%) with solid volume (12). Prioritize localized follow-ups.
- Standardize country labels and split multi-country entries to improve targeting and reporting.