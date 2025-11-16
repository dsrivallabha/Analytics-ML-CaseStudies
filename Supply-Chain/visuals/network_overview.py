# visuals/network_overview.py
import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt

def _ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def _derive_cols(df):
    df["backlog_total"] = df["backlog_external"].fillna(0) + df["backlog_children"].fillna(0)
    df["ip"] = df["on_hand"] - df["backlog_total"] + df["pipeline_in"]
    df["ip_effective"] = df["ip"] + df["orders_to_parent"]
    return df

def plot_single(csv_path, out_path, metric="ip", phase=None, title_note=""):
    df = pd.read_csv(csv_path)
    df = _derive_cols(df)

    if phase is not None and "phase" in df.columns:
        df = df[df.phase == phase]

    label_map = {
        "ip": "Inventory Position (IP)",
        "on_hand": "On-hand",
        "received": "Received today",
        "ip_effective": "Effective IP (incl. today’s order)",
        "pipeline_in": "Pipeline (in-transit)",
        "orders_to_parent": "Orders placed today"
    }

    plt.figure(figsize=(11,5))
    for node, sub in df.groupby("node_id"):
        plt.plot(sub["t"], sub[metric], marker="o", linewidth=1.8, label=f"{node} {metric}")

    ttl_extra  = f" [{title_note}]" if title_note else ""
    plt.title(f"Network Overview — {label_map.get(metric, metric)}{ttl_extra}")
    plt.xlabel("Period (t)")
    plt.ylabel("Quantity")
    plt.axhline(0, linewidth=0.8)
    plt.legend(loc="upper left", bbox_to_anchor=(1.02, 1))
    plt.tight_layout(rect=[0,0,0.82,1])
    _ensure_dir(out_path)
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Saved: {os.path.abspath(out_path)}")

def main():
    parser = argparse.ArgumentParser(description="Network overview plotting")
    parser.add_argument("--csv_summary", type=str, default="outputs/opt_results_summary.csv")
    parser.add_argument("--csv_detailed", type=str, default="outputs/opt_results_detailed.csv")
    parser.add_argument("--config", type=str, default="112_multiroute_simple.json")
    parser.add_argument("--out_dir", type=str, default="visuals")
    parser.add_argument("--metric", type=str, default="ip",
                        choices=["ip", "ip_effective", "on_hand", "received", "orders_to_parent", "pipeline_in"])
    parser.add_argument("--phase", type=str, default=None)
    args = parser.parse_args()

    config_name = os.path.splitext(os.path.basename(args.config))[0]

    if args.phase is None or args.phase == "EOD":
        out_path = os.path.join(args.out_dir, f"network_summary_{config_name}.png")
        plot_single(csv_path=args.csv_summary, out_path=out_path,
                    metric=args.metric, phase=None,
                    title_note=f"EOD (Summary) [{config_name}]")
    else:
        out_path = os.path.join(args.out_dir, f"network_{args.phase}_{config_name}.png")
        plot_single(csv_path=args.csv_detailed, out_path=out_path,
                    metric=args.metric, phase=args.phase,
                    title_note=f"{args.phase} [{config_name}]")

if __name__ == "__main__":
    main()
