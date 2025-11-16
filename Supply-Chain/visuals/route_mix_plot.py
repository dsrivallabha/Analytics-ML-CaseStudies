# visuals/route_mix_plot.py
import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt

def plot_lane(df, parent, child, out_path):
    lane = df[(df.parent == parent) & (df.child == child)]
    if lane.empty:
        print(f"[skip] No shipments for {parent}->{child}")
        return False
    counts = lane.groupby("lead_time")["qty"].sum().reset_index()
    plt.figure(figsize=(8,5))
    plt.bar(counts["lead_time"].astype(str), counts["qty"])
    plt.xlabel("Lead Time selected")
    plt.ylabel("Total quantity shipped via this lead time")
    plt.title(f"Route mix — {parent} → {child}")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"[ok] {parent}->{child}: {os.path.abspath(out_path)}")
    return True

def main():
    ap = argparse.ArgumentParser("Plot histogram of lead times used for a parent->child lane")
    ap.add_argument("--ship_csv", type=str, default="outputs/shipments_log.csv")
    ap.add_argument("--parent", type=str, help="Parent node id (or leave empty to auto-plot all lanes)")
    ap.add_argument("--child", type=str, help="Child node id (or leave empty to auto-plot all lanes)")
    ap.add_argument("--out", type=str, default="visuals/route_mix.png",
                   help="Output file (used only when both --parent and --child are provided)")
    args = ap.parse_args()

    df = pd.read_csv(args.ship_csv)

    if args.parent and args.child:
        plot_lane(df, args.parent, args.child, args.out)
        return

    # Auto-plot all lanes
    lanes = (df[["parent","child"]].drop_duplicates()
                               .sort_values(["parent","child"])
                               .values.tolist())
    print(f"[info] Auto mode. Found {len(lanes)} lanes:")
    for p, c in lanes:
        out = f"visuals/route_mix_{p}_{c}.png"
        plot_lane(df, p, c, out)

if __name__ == "__main__":
    main()
