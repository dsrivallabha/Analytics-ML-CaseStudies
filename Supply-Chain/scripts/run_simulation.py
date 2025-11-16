# scripts/run_simulation.py
import json
import os
import argparse
import pandas as pd
import sys
from pathlib import Path
import numpy as np

# --- make project imports work even when launched via VS Code Run button ---
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.node import Node
from engine.network import Network, Edge
from engine.simulator import Simulator
from policies.base_stock import BaseStockPolicy
from policies.ss_policy import SsPolicy

# demand/lead-time generators (inline)
from dataclasses import dataclass
import math, random
from typing import List

# ---------- Demand ----------
class DemandGenerator:
    def sample(self, t: int) -> int: raise NotImplementedError

@dataclass
class DeterministicDemand(DemandGenerator):
    value: int
    def sample(self, t): return int(self.value)

@dataclass
class PoissonDemand(DemandGenerator):
    lam: float
    rng: random.Random
    def sample(self, t):
        L = math.exp(-self.lam)
        k = 0
        p = 1.0
        while p > L:
            k += 1
            p *= self.rng.random()
        return k - 1

# NEW: CSV-driven demand (wrap/clip strategies)
@dataclass
class CSVDrivenDemand(DemandGenerator):
    series: List[int]
    strategy: str = "wrap"      # "wrap" or "clip"
    start_index: int = 0        # allows starting near the end
    def sample(self, t: int) -> int:
        if not self.series:
            return 0
        i = self.start_index + t
        if i < len(self.series):
            return int(self.series[i])
        # after we exhaust the tail segment, apply strategy
        if self.strategy == "wrap":
            return int(self.series[(i) % len(self.series)])
        return 0

# ---------- Lead time ----------
class LeadTimeGenerator:
    def sample(self) -> int: raise NotImplementedError

@dataclass
class DeterministicLeadTime(LeadTimeGenerator):
    value: int
    def sample(self): return int(self.value)

@dataclass
class NormalIntLeadTime(LeadTimeGenerator):
    mean: float
    std: float
    rng: random.Random
    def sample(self):
        return max(0, int(round(self.rng.gauss(self.mean, self.std))))

def _read_csv_series(path: Path, date_col: str, qty_col: str) -> List[int]:
    df = pd.read_csv(path)
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)
    # tolerate extra cols; just take qty
    s = df[qty_col].fillna(0).astype(int).tolist()
    return s

def build_from_config(cfg_or_path):
    if isinstance(cfg_or_path, (str, os.PathLike)):
        with open(cfg_or_path, "r") as f:
            cfg = json.load(f)
    elif isinstance(cfg_or_path, dict):
        cfg = cfg_or_path
    else:
        raise TypeError("build_from_config expects a path or a dict")

    top_seed = cfg.get("seed", None)

    # nodes
    nodes = {}
    for nd in cfg["nodes"]:
        pol = nd.get("policy", {})
        ptype = pol.get("type", "base_stock")
        if ptype == "base_stock":
            policy = BaseStockPolicy(base_stock_level=pol["base_stock_level"])
        elif ptype == "sS":
            policy = SsPolicy(s=pol["s"], S=pol["S"])
        elif ptype == "order_up_to":
            from policies.order_up_to import OrderUpToPolicy
            policy = OrderUpToPolicy(R=pol["R"], S=pol["S"], phase_offset=pol.get("phase_offset", 0))
        elif ptype == "km_cycle":
            from policies.km_cycle import KmCyclePolicy
            policy = KmCyclePolicy(
                k=pol["k"], m=pol["m"], S=pol["S"],
                review_offsets=tuple(pol.get("review_offsets", (0,)))
            )
        else:
            raise ValueError(f"Unknown policy type {ptype}")

        nodes[nd["id"]] = Node(
            node_id=nd["id"],
            node_type=nd["type"],
            policy=policy,
            initial_inventory=nd.get("initial_inventory", 0),
            holding_cost=nd.get("holding_cost", 0.0),
            shortage_cost=nd.get("shortage_cost", 0.0),
            infinite_supply=nd.get("infinite_supply", False),
            order_cost_fixed=nd.get("order_cost_fixed", 0.0),
            order_cost_per_unit=nd.get("order_cost_per_unit", 0.0),
        )

    # edges (support multiple routes with per-route shares)
    edges = {}
    for e in cfg["edges"]:
        lt = e["lead_time"]
        lt_seed = lt.get("seed", top_seed)
        lt_rng = random.Random(lt_seed) if lt_seed is not None else random.Random()

        if lt["type"] == "deterministic":
            sampler = DeterministicLeadTime(lt["value"]).sample
        elif lt["type"] == "normal_int":
            sampler = NormalIntLeadTime(lt["mean"], lt["std"], lt_rng).sample
        else:
            raise ValueError("Unknown lead time type")

        key = (e["from"], e["to"])
        edges.setdefault(key, []).append(
            Edge(parent=e["from"], child=e["to"], lead_time_sampler=sampler, share=e.get("share"), transport_cost_per_unit=e.get("transport_cost_per_unit", 0.0))
        )

    net = Network(nodes=nodes, edges=edges)

    # demand (now supports csv/manifest in addition to deterministic/poisson)
    demand_by_node = {}
    for d in cfg.get("demand", []):
        node = d["node"]; g = d["generator"]
        d_seed = g.get("seed", top_seed)
        d_rng = random.Random(d_seed) if d_seed is not None else random.Random()

        gtype = g["type"]
        if gtype == "deterministic":
            demand_by_node[node] = DeterministicDemand(g["value"]).sample
        elif gtype == "poisson":
            demand_by_node[node] = PoissonDemand(g["lam"], d_rng).sample
        elif gtype == "csv":
            strategy = g.get("strategy", "wrap")
            date_col = g.get("date_col", "date")
            qty_col = g.get("qty_col", "quantity")

            if "path" in g:
                # direct file
                path = (ROOT / g["path"]).resolve() if not os.path.isabs(g["path"]) else Path(g["path"])
                series = _read_csv_series(path, date_col, qty_col)
            elif "manifest" in g and "store_id" in g:
                # via manifest
                man_path = (ROOT / g["manifest"]).resolve() if not os.path.isabs(g["manifest"]) else Path(g["manifest"])
                with open(man_path, "r") as mf:
                    manifest = json.load(mf)
                sid = str(g["store_id"])
                csv_rel = manifest["files"][sid]
                csv_path = Path(csv_rel)

                # If the manifest stores a relative path (like "demand_store_1.csv"),
                # join with manifest parent. If it’s already absolute or starts with "dataset/",
                # trust it directly.
                if not csv_path.is_absolute() and not str(csv_path).startswith("dataset/"):
                    path = (man_path.parent / csv_rel).resolve()
                else:
                    path = (ROOT / csv_rel).resolve() if not csv_path.is_absolute() else csv_path

                series = _read_csv_series(path, date_col, qty_col)

            else:
                raise ValueError("csv generator requires either 'path' or ('manifest' + 'store_id').")

            # ... after you have built `series` ...
            tail_days = int(g.get("tail_days", 0))
            if tail_days > 0:
                start_index = max(0, len(series) - tail_days)
            else:
                start_index = int(g.get("start_index", 0))

            demand_by_node[node] = CSVDrivenDemand(series=series, strategy=g.get("strategy", "wrap"), start_index=start_index).sample

        else:
            raise ValueError(f"Unknown demand generator type {gtype}")

    T = int(cfg["time_horizon"])
    return net, demand_by_node, T


def main():
    parser = argparse.ArgumentParser(description="Run supply chain sim and write CSV.")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to config JSON. Defaults to <repo>/config/123.json")
    parser.add_argument("--mode", type=str, default="both",
                        choices=["summary", "detailed", "both"],
                        help="What to emit into CSVs.")
    parser.add_argument("--outdir", type=str, default=str(ROOT / "outputs"))
    args = parser.parse_args()

    cfg_path = args.config or str(ROOT / "config" / "112_multiroute_simple.json")
    net, demand_by_node, T = build_from_config(cfg_path)
    os.makedirs(args.outdir, exist_ok=True)

    # Run the summary model first (we’ll also use it to dump the shipments log)
    sim_sum = Simulator(network=net, demand_by_node=demand_by_node, T=T, order_processing_delay=1)
    metrics_sum = sim_sum.run(mode="summary")
    import pandas as _pd
    df_sum = _pd.DataFrame([m.__dict__ for m in metrics_sum])
    out_sum = os.path.join(args.outdir, "opt_results_summary.csv")
    df_sum.to_csv(out_sum, index=False)
    print(f"[summary] wrote {out_sum}")

        # -------- Costs summary (EOD rows only) --------
    is_eod = df_sum["phase"] == "EOD"
    c = df_sum[is_eod].copy()
    grp = c.groupby("node_id").agg(
        holding_cost=("holding_cost", "sum"),
        backlog_cost=("backlog_cost", "sum"),
        ordering_cost=("ordering_cost", "sum"),
        transport_cost=("transport_cost", "sum"),
        total_cost=("total_cost", "sum"),
    ).reset_index()

    overall = pd.DataFrame([{
        "node_id": "_OVERALL_",
        "holding_cost": grp["holding_cost"].sum(),
        "backlog_cost": grp["backlog_cost"].sum(),
        "ordering_cost": grp["ordering_cost"].sum(),
        "transport_cost": grp["transport_cost"].sum(),
        "total_cost": grp["total_cost"].sum(),
    }])

    costs_df = pd.concat([grp, overall], ignore_index=True)
    out_costs = os.path.join(args.outdir, "costs_summary.csv")
    costs_df.to_csv(out_costs, index=False)
    print(f"[costs] wrote {out_costs}")


    # Dump shipments log for route verification
    if sim_sum.shipments_log:
        df_ship = _pd.DataFrame(sim_sum.shipments_log)
        out_ship = os.path.join(args.outdir, "shipments_log.csv")
        df_ship.to_csv(out_ship, index=False)
        print(f"[debug] wrote {out_ship}")

    if args.mode in ("detailed", "both"):
        # Rebuild to keep runs independent
        net, demand_by_node, T = build_from_config(cfg_path)
        sim_det = Simulator(network=net, demand_by_node=demand_by_node, T=T, order_processing_delay=1)
        metrics_det = sim_det.run(mode="detailed")
        df_det = _pd.DataFrame([m.__dict__ for m in metrics_det])
        out_det = os.path.join(args.outdir, "opt_results_detailed.csv")
        df_det.to_csv(out_det, index=False)
        print(f"[detailed] wrote {out_det}")

    def _compute_kpis(df):
        
        out = []

        # Retailer-level demand/service
        is_eod = df["phase"] == "EOD"
        dfe = df[is_eod].copy()

        # Per-node aggregates
        grp = dfe.groupby("node_id")
        agg = grp.agg(
            demand_sum=("demand", "sum"),
            fulfilled_sum=("fulfilled_external", "sum"),
            onhand_avg=("on_hand", "mean"),
            backlog_ext_avg=("backlog_external", "mean"),
            backlog_child_avg=("backlog_children", "mean"),
            pipeline_avg=("pipeline_in", "mean"),
            orders_var=("orders_to_parent", "var"),
            orders_mean=("orders_to_parent", "mean"),
            demand_var=("demand", "var"),
        ).reset_index()


        # Fill rate (retailer service level)
        agg["fill_rate"] = np.where(agg["demand_sum"] > 0,
                                    agg["fulfilled_sum"] / agg["demand_sum"], np.nan)

        # Bullwhip (node-level): Var(orders)/Var(demand) — defined for nodes with demand stream
        agg["bullwhip_ratio"] = np.where(agg["demand_var"] > 0,
                                        agg["orders_var"] / agg["demand_var"], np.nan)

        # Overall KPIs
        overall = {
            "node_id": "_OVERALL_",
            "demand_sum": agg["demand_sum"].sum(),
            "fulfilled_sum": agg["fulfilled_sum"].sum(),
            "onhand_avg": agg["onhand_avg"].mean(),
            "backlog_ext_avg": agg["backlog_ext_avg"].mean(),
            "backlog_child_avg": agg["backlog_child_avg"].mean(),
            "pipeline_avg": agg["pipeline_avg"].mean(),
            "orders_var": agg["orders_var"].mean(),
            "orders_mean": agg["orders_mean"].mean(),
            "demand_var": agg["demand_var"].mean(),
        }
        overall["fill_rate"] = (overall["fulfilled_sum"] / overall["demand_sum"]
                                if overall["demand_sum"] > 0 else np.nan)
        overall["bullwhip_ratio"] = (overall["orders_var"] / overall["demand_var"]
                                    if overall["demand_var"] and overall["demand_var"] > 0 else np.nan)

        out_df = pd.concat([agg, pd.DataFrame([overall])], ignore_index=True)
        return out_df

    kpi_df = _compute_kpis(df_sum)
    out_kpi = os.path.join(args.outdir, "kpis_summary.csv")
    kpi_df.to_csv(out_kpi, index=False)
    print(f"[kpis] wrote {out_kpi}")

if __name__ == "__main__":
    main()
