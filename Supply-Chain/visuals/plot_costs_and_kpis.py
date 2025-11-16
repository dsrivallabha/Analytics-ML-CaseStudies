# visuals/plot_costs_and_kpis.py
"""
Unified visualization for cost and KPI metrics in the MEIO simulator.
Reads outputs/costs_summary.csv and outputs/kpis_summary.csv (if present)
and generates:
    1. Cost composition per node (stacked bar)
    2. Cost vs Fill Rate (scatter)
    3. Topline KPI summary per node (bar plots)
"""

import os, argparse
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams.update({
    "figure.figsize": (8, 4),
    "axes.grid": True,
    "grid.linestyle": "--",
    "grid.alpha": 0.4
})

def ensure_dir(d):
    os.makedirs(d, exist_ok=True)

# ---------- PLOT 1: COST COMPOSITION ----------
def plot_cost_composition(costs_csv, outdir):
    df = pd.read_csv(costs_csv)
    df = df[df["node_id"] != "_OVERALL_"].copy()

    cost_cols = ["holding_cost", "backlog_cost", "ordering_cost", "transport_cost"]
    df["total_cost"] = df[cost_cols].sum(axis=1)

    df_long = df.melt(id_vars=["node_id"], value_vars=cost_cols,
                      var_name="cost_type", value_name="cost_value")

    plt.figure(figsize=(9, 5))
    bottom = None
    for c in cost_cols:
        vals = df[df["node_id"].isin(df["node_id"])]
        plt.bar(df["node_id"], df[c], label=c.replace("_", " ").title(), bottom=bottom)
        if bottom is None:
            bottom = df[c].copy()
        else:
            bottom += df[c]
    plt.ylabel("Total Cost")
    plt.title("Cost Composition per Node")
    plt.legend()
    ensure_dir(outdir)
    out_path = os.path.join(outdir, "cost_composition_per_node.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"[ok] cost composition → {out_path}")

# ---------- PLOT 2: COST vs FILL RATE ----------
def plot_cost_vs_fillrate(costs_csv, kpis_csv, outdir):
    cost_df = pd.read_csv(costs_csv)
    kpi_df = pd.read_csv(kpis_csv)
    if "node_id" not in cost_df or "node_id" not in kpi_df:
        print("[skip] Missing node_id column in CSVs.")
        return
    df = pd.merge(cost_df, kpi_df, on="node_id", suffixes=("_cost", "_kpi"))
    if "fill_rate" not in df.columns:
        print("[skip] No fill_rate in KPI CSV.")
        return
    df = df[df["node_id"] != "_OVERALL_"]

    plt.figure(figsize=(7,5))
    plt.scatter(df["fill_rate"], df["total_cost"], s=60, color="steelblue")
    for _, row in df.iterrows():
        plt.text(row["fill_rate"], row["total_cost"], row["node_id"],
                 fontsize=8, ha="center", va="bottom")
    plt.xlabel("Fill Rate (OTIF)")
    plt.ylabel("Total Cost")
    plt.title("Cost vs Fill Rate per Node")
    ensure_dir(outdir)
    out_path = os.path.join(outdir, "cost_vs_fillrate.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"[ok] cost vs fill rate → {out_path}")

# ---------- PLOT 3: KPI SUMMARY ----------
def plot_kpi_summary(kpis_csv, outdir):
    df = pd.read_csv(kpis_csv)
    if "_OVERALL_" in df["node_id"].values:
        df = df[df["node_id"] != "_OVERALL_"]

    metrics = ["fill_rate", "bullwhip_ratio", "demand_var", "orders_var"]
    for m in metrics:
        if m not in df.columns:
            continue
        plt.figure(figsize=(8,4))
        plt.bar(df["node_id"], df[m])
        plt.title(f"{m.replace('_',' ').title()} per Node")
        plt.ylabel(m.replace("_"," ").title())
        ensure_dir(outdir)
        out_path = os.path.join(outdir, f"{m}_per_node.png")
        plt.tight_layout()
        plt.savefig(out_path, dpi=150)
        plt.close()
        print(f"[ok] {m} plot → {out_path}")

def main():
    ap = argparse.ArgumentParser(description="Plot cost and KPI metrics together")
    ap.add_argument("--costs", default="outputs/costs_summary.csv")
    ap.add_argument("--kpis", default="outputs/kpis_summary.csv")
    ap.add_argument("--outdir", default="outputs/plots_combined")
    args = ap.parse_args()

    ensure_dir(args.outdir)
    plot_cost_composition(args.costs, args.outdir)
    if os.path.exists(args.kpis):
        plot_cost_vs_fillrate(args.costs, args.kpis, args.outdir)
        plot_kpi_summary(args.kpis, args.outdir)
    else:
        print("[warn] KPI file not found — skipping KPI plots.")

if __name__ == "__main__":
    main()
