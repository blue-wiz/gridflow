"""Step 3: read the dbt marts and write charts + summary for the README."""
import json, os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "reports" / "figures"; FIG.mkdir(parents=True, exist_ok=True)
URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/gridflow")
eng = create_engine(URL.replace("postgresql://", "postgresql+psycopg2://"))
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titleweight": "bold"})
COL = {"coal": "#3d3d3d", "gas": "#8a8f98", "oil": "#5c4033", "nuclear": "#7b5ea7",
       "hydro": "#1f6fb2", "wind": "#2a9d8f", "solar": "#e9c46a", "bioenergy": "#6a994e",
       "other_renewable": "#a7c957"}

mix = pd.read_sql("SELECT * FROM marts.mart_electricity_mix WHERE iso_code='GBR' ORDER BY year", eng)
piv = mix.pivot(index="year", columns="source", values="twh").fillna(0)
order = [s for s in COL if s in piv.columns]
fig, ax = plt.subplots(figsize=(9, 4.4))
ax.stackplot(piv.index, [piv[s] for s in order], labels=[s.replace("_", " ").title() for s in order],
             colors=[COL[s] for s in order], alpha=0.95)
ax.set_xlim(piv.index.min(), piv.index.max()); ax.set_ylabel("TWh")
ax.set_title("UK electricity generation by source")
ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(FIG / "uk_mix.png", dpi=160); fig.savefig(FIG / "uk_mix.svg"); plt.close(fig)

dec = pd.read_sql("SELECT * FROM marts.mart_decarbonisation ORDER BY rank_low_carbon_gain", eng)
top = dec.head(15).iloc[::-1]
fig, ax = plt.subplots(figsize=(8, 5.2))
ax.barh(top.country, top.low_carbon_share_2010, color="#c9ced6", label="2010")
ax.barh(top.country, top.low_carbon_change_pp, left=top.low_carbon_share_2010, color="#2a9d8f",
        label=f"Gain to {int(dec.latest_year.iloc[0])}")
for i, (a, b) in enumerate(zip(top.low_carbon_share_latest, top.low_carbon_change_pp)):
    ax.text(a + 1, i, f"{a:.0f}% (+{b:.0f} pp)", va="center", fontsize=8)
ax.set_xlim(0, 110); ax.set_xlabel("Low-carbon share of electricity (%)")
ax.set_title("Fastest electricity decarbonisers since 2010 (≥10 TWh)")
ax.legend(frameon=False, loc="lower right")
fig.tight_layout(); fig.savefig(FIG / "decarbonisers.png", dpi=160); fig.savefig(FIG / "decarbonisers.svg"); plt.close(fig)

ci = pd.read_sql("""SELECT d.country, f.year, f.carbon_intensity_g_per_kwh ci FROM marts.fct_country_year f
                    JOIN marts.dim_country d USING (iso_code)
                    WHERE iso_code IN ('GBR','DEU','USA','CHN','IND','FRA') AND year >= 2000 ORDER BY d.country, f.year""", eng)
fig, ax = plt.subplots(figsize=(8.5, 4))
for (c, g), col in zip(ci.groupby("country"), ["#1f3a5f", "#c8553d", "#2a9d8f", "#7b5ea7", "#e9c46a", "#8a8f98"]):
    g = g.dropna().sort_values("year")
    ax.plot(g.year, g.ci, color=col, lw=2)
    ax.text(g.year.iloc[-1] + 0.3, g.ci.iloc[-1], c, color=col, fontsize=8, va="center")
ax.set_ylabel("gCO₂ per kWh"); ax.set_ylim(0); ax.set_xlim(2000, ci.year.max() + 4)
ax.set_title("Carbon intensity of electricity")
fig.tight_layout(); fig.savefig(FIG / "carbon_intensity.png", dpi=160); fig.savefig(FIG / "carbon_intensity.svg"); plt.close(fig)

uk = pd.read_sql("""SELECT year, coal_twh, electricity_twh, low_carbon_share_elec_pct, carbon_intensity_g_per_kwh
                    FROM marts.fct_country_year WHERE iso_code='GBR' ORDER BY year""", eng).set_index("year")
loads = pd.read_sql("SELECT source, n_rows, n_columns, sha256, loaded_at FROM raw.load_log ORDER BY load_id DESC", eng)
counts = pd.read_sql("""SELECT (SELECT COUNT(*) FROM marts.fct_country_year) fct,
                               (SELECT COUNT(*) FROM marts.dim_country) countries,
                               (SELECT COUNT(*) FROM marts.mart_electricity_mix) mix,
                               (SELECT COUNT(*) FROM marts.mart_decarbonisation) ranked""", eng).iloc[0]
latest_uk = uk.dropna(subset=["carbon_intensity_g_per_kwh"]).iloc[-1]
summary = {
    "loads": loads.drop_duplicates("source").astype(str).to_dict(orient="records"),
    "rows": {k: int(v) for k, v in counts.items()},
    "uk": {"coal_share_1990_pct": round(100 * uk.loc[1990, "coal_twh"] / uk.loc[1990, "electricity_twh"], 1),
           "carbon_intensity_2010": float(uk.loc[2010, "carbon_intensity_g_per_kwh"]),
           "latest_year": int(latest_uk.name),
           "carbon_intensity_latest": float(latest_uk.carbon_intensity_g_per_kwh),
           "low_carbon_share_latest": float(latest_uk.low_carbon_share_elec_pct),
           "low_carbon_share_2010": float(uk.loc[2010, "low_carbon_share_elec_pct"])},
    "top5_decarbonisers": dec.head(5)[["country", "low_carbon_share_2010", "low_carbon_share_latest", "low_carbon_change_pp"]].to_dict(orient="records"),
    "uk_rank": int(dec.loc[dec.iso_code == "GBR", "rank_low_carbon_gain"].iloc[0]), "n_ranked": int(len(dec)),
    "latest_year": int(dec.latest_year.iloc[0]),
}
(ROOT / "reports" / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
print(json.dumps(summary, indent=1, default=str))
