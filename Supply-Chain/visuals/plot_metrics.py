# visuals/plot_metrics.py
import argparse, os, pandas as pd, matplotlib.pyplot as plt

def plot_nodes(df, nodes, smooth=0, outdir="outputs/plots", fmt="png"):
    os.makedirs(outdir, exist_ok=True)
    df = df[df["phase"]=="EOD"].copy()
    df = df[df["node_id"].isin(nodes)]
    df = df.sort_values(["node_id","t"])

    metrics = ["on_hand", "pipeline_in", "backlog_external",
               "orders_to_parent", "demand", "fulfilled_external"]

    for metric in metrics:
        plt.figure(figsize=(10, 3.2))
        for nid, g in df.groupby("node_id"):
            s = g[metric]
            if smooth and smooth > 1:
                s = s.rolling(smooth, min_periods=1).mean()
            plt.plot(g["t"], s, label=nid)
        plt.title(metric.replace("_"," ").title())
        plt.xlabel("Day")
        plt.legend(loc="upper right", ncol=max(1, len(nodes)//3), fontsize=8)
        plt.tight_layout()
        out_path = os.path.join(outdir, f"{metric}__{'_'.join(nodes)}.{fmt}")
        plt.savefig(out_path, dpi=160, bbox_inches="tight")
        plt.close()
        print(f"[plot] wrote {out_path}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="outputs/opt_results_summary.csv")
    ap.add_argument("--nodes", nargs="+", required=True)
    ap.add_argument("--smooth", type=int, default=0)
    ap.add_argument("--outdir", default="outputs/plots")
    ap.add_argument("--format", default="png")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    plot_nodes(df, args.nodes, smooth=args.smooth, outdir=args.outdir, fmt=args.format)
