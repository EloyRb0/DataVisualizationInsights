import os, json, pandas as pd, numpy as np
import argparse
import matplotlib.pyplot as plt

def normalize_flags(df):
    for c in ["Registered","Attended","Recibe newsletter"]:
        if c in df.columns:
            if df[c].dtype == bool:
                df[c] = df[c].astype(int)
            else:
                df[c] = df[c].astype(str).str.strip().str.lower().map({
                    "1":1,"0":0,"true":1,"false":0,"yes":1,"no":0,"si":1,"sí":1,"nan":np.nan
                }).fillna(pd.to_numeric(df[c], errors="coerce"))
                df[c] = df[c].fillna(0).astype(int)
        else:
            df[c] = 0
    return df

def main(input_path, outdir):
    os.makedirs(outdir, exist_ok=True)
    df = pd.read_csv(input_path)

    if "Start Date_ISO" in df.columns:
        df["event_date"] = pd.to_datetime(df["Start Date_ISO"], errors="coerce")
    elif "Start Date" in df.columns:
        df["event_date"] = pd.to_datetime(df["Start Date"], errors="coerce")
    else:
        df["event_date"] = pd.NaT
    df["year_month"] = df["event_date"].dt.to_period("M").astype(str)

    if "Campaign Name" not in df.columns: df["Campaign Name"] = "Unknown"
    if "Country_Best" not in df.columns:
        cand = [c for c in df.columns if "Country" in c]
        df["Country_Best"] = df[cand[0]] if cand else "Unknown"

    df = normalize_flags(df)

    summary = {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "registered_rate": float(df["Registered"].mean()),
        "attended_rate": float(df["Attended"].mean()),
        "newsletter_optin_rate": float(df["Recibe newsletter"].mean()),
    }
    with open(os.path.join(outdir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    by_month = df.groupby("year_month", dropna=True).agg(
        registrations=("Registered","sum"),
        attendance=("Attended","sum"),
        events=("Campaign Name","count")
    ).reset_index().sort_values("year_month")
    by_month.to_csv(os.path.join(outdir, "registrations_by_month.csv"), index=False)

    by_campaign = df.groupby("Campaign Name").agg(
        registrations=("Registered","sum"),
        attendance=("Attended","sum"),
        events=("Campaign Name","count")
    ).reset_index()
    by_campaign["attendance_rate"] = np.where(by_campaign["registrations"]>0,
                                              by_campaign["attendance"]/by_campaign["registrations"], np.nan)
    by_campaign.to_csv(os.path.join(outdir, "registrations_by_campaign.csv"), index=False)

    by_country = df.groupby("Country_Best").agg(
        registrations=("Registered","sum"),
        attendance=("Attended","sum")
    ).reset_index()
    by_country["attendance_rate"] = np.where(by_country["registrations"]>0,
                                             by_country["attendance"]/by_country["registrations"], np.nan)
    by_country.to_csv(os.path.join(outdir, "registrations_by_country.csv"), index=False)

    # Charts
    plt.figure()
    plt.plot(by_month["year_month"], by_month["registrations"], marker="o")
    plt.xticks(rotation=45, ha="right")
    plt.title("Registrations by Month")
    plt.xlabel("Year-Month")
    plt.ylabel("Registrations")
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "chart_registrations_by_month.png"), dpi=200)
    plt.close()

    top_campaigns = by_campaign.sort_values("registrations", ascending=False).head(10)
    plt.figure()
    plt.bar(top_campaigns["Campaign Name"], top_campaigns["registrations"])
    plt.xticks(rotation=60, ha="right")
    plt.title("Top 10 Campaigns by Registrations")
    plt.xlabel("Campaign")
    plt.ylabel("Registrations")
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "chart_top10_campaigns_registrations.png"), dpi=200)
    plt.close()

    top_countries = by_country.sort_values("registrations", ascending=False).head(10)
    top_countries_sorted = top_countries.sort_values("attendance_rate", ascending=False)
    plt.figure()
    plt.bar(top_countries_sorted["Country_Best"], top_countries_sorted["attendance_rate"])
    plt.xticks(rotation=45, ha="right")
    plt.title("Attendance Rate — Top Countries by Registrations")
    plt.xlabel("Country")
    plt.ylabel("Attendance Rate")
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "chart_attendance_rate_by_country.png"), dpi=200)
    plt.close()

    # Insights
    insights = []
    low_attendance_threshold = 0.5
    problem_campaigns = by_campaign[(by_campaign["registrations"] >= by_campaign["registrations"].quantile(0.75)) &
                                    (by_campaign["attendance_rate"] < low_attendance_threshold)]
    if not problem_campaigns.empty:
        c = problem_campaigns.iloc[0]
        insights.append(f"Campaign '{c['Campaign Name']}' draws many registrations ({int(c['registrations'])}) but low attendance ({c['attendance_rate']:.0%}).")
    by_month_nonempty = by_month[by_month["registrations"] > 0].copy()
    if len(by_month_nonempty) >= 3:
        last = by_month_nonempty.iloc[-1]["registrations"]
        prev_med = by_month_nonempty.iloc[-4:-1]["registrations"].median() if len(by_month_nonempty) >= 4 else by_month_nonempty.iloc[:-1]["registrations"].median()
        if pd.notna(prev_med) and last < prev_med * 0.85:
            insights.append(f"Registrations declined: last month {int(last)} vs median {int(prev_med)} earlier; adjust cadence/channels.")
    good_countries = by_country[by_country["attendance_rate"] >= 0.75].sort_values("registrations", ascending=False)
    if not good_countries.empty:
        g = good_countries.iloc[0]
        insights.append(f"{g['Country_Best']} shows strong conversion ({g['attendance_rate']:.0%}) with solid volume ({int(g['registrations'])}); scale localized programming.")
    while len(insights) < 3:
        if summary.get("newsletter_optin_rate") is not None:
            insights.append(f"Newsletter opt-in is {summary['newsletter_optin_rate']:.0%}; use post-event nurture.")
        else:
            insights.append("Standardize dates and country codes to improve comparability.")
    with open(os.path.join(outdir, "insights.md"), "w") as f:
        f.write("# Actionable Insights\n\n" + "\n".join([f"- {s}" for s in insights]))

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="clean_salesforce_report.csv")
    ap.add_argument("--outdir", default="outputs")
    args = ap.parse_args()
    main(args.input, args.outdir)