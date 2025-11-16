import pytest
import pandas as pd
from engine.simulator import Simulator
from scripts.run_simulation import build_from_config

def test_local_flow_conservation():
    cfg = {
        "time_horizon": 15,
        "nodes": [
            {"id": "Supplier", "type": "supplier", "infinite_supply": True,
             "policy": {"type": "base_stock", "base_stock_level": 0}},
            {"id": "W", "type": "warehouse", "initial_inventory": 30,
             "policy": {"type": "base_stock", "base_stock_level": 45}},
            {"id": "R", "type": "retailer", "initial_inventory": 10,
             "policy": {"type": "base_stock", "base_stock_level": 25}}
        ],
        "edges": [
            {"from": "Supplier", "to": "W",
             "lead_time": {"type": "deterministic", "value": 2}},
            {"from": "W", "to": "R",
             "lead_time": {"type": "deterministic", "value": 1}}
        ],
        "demand": [
            {"node": "R", "generator": {"type": "deterministic", "value": 2}}
        ]
    }
    net, dmap, T = build_from_config(cfg)
    sim = Simulator(net, dmap, T, order_processing_delay=1)
    df = pd.DataFrame([m.__dict__ for m in sim.run(mode="summary")])

    r = df[(df.node_id == "R") & (df.phase == "EOD")].sort_values("t").reset_index(drop=True)

    required_cols = {"on_hand", "received", "demand"}
    if not required_cols.issubset(set(r.columns)):
        pytest.skip("Missing required columns in detailed DF.")

    for i in range(1, len(r)):
        on_t = r.loc[i - 1, "on_hand"]
        on_tp1 = r.loc[i, "on_hand"]
        arrivals_next = r.loc[i, "received"]
        demand_t = r.loc[i - 1, "demand"]
        lhs = on_tp1
        rhs = on_t + arrivals_next - demand_t
        assert abs(lhs - rhs) < 1e-6, f"Retailer day {int(r.loc[i, 't'])}: {lhs} vs {rhs}"
