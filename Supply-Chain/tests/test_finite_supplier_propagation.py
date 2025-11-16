import pandas as pd
import numpy as np
from scripts.run_simulation import build_from_config
from engine.simulator import Simulator

def test_finite_supplier_shortage_propagation():
    """
    Finite supplier stress test:
    - Supplier inventory should deplete to 0 at some point.
    - Downstream backlog (W children backlog, R external backlog) should rise.
    - AFTER the first depletion time, the supplier must NOT ship any NEW orders.
      (Downstream may still 'receive' later due to pipeline-in shipments created before depletion.)
    - Retailer backlog cost should become positive.
    """

    cfg = {
        "time_horizon": 25,
        "nodes": [
            {"id": "Supplier", "type": "supplier",
             "initial_inventory": 100,
             "policy": {"type": "base_stock", "base_stock_level": 50},
             "holding_cost": 0.2},
            {"id": "W", "type": "warehouse", "initial_inventory": 40,
             "policy": {"type": "base_stock", "base_stock_level": 60},
             "holding_cost": 0.5, "shortage_cost": 3.0},
            {"id": "R", "type": "retailer", "initial_inventory": 20,
             "policy": {"type": "base_stock", "base_stock_level": 40},
             "holding_cost": 0.8, "shortage_cost": 5.0}
        ],
        "edges": [
            {"from": "Supplier", "to": "W",
             "lead_time": {"type": "deterministic", "value": 2},
             "transport_cost_per_unit": 0.3},
            {"from": "W", "to": "R",
             "lead_time": {"type": "deterministic", "value": 1},
             "transport_cost_per_unit": 0.4}
        ],
        "demand": [
            {"node": "R", "generator": {"type": "deterministic", "value": 10}}
        ]
    }

    # Run
    net, demand_by_node, T = build_from_config(cfg)
    sim = Simulator(net, demand_by_node, T=T, order_processing_delay=1)
    df = pd.DataFrame([m.__dict__ for m in sim.run(mode="summary")])
    eod = df[df.phase == "EOD"].reset_index(drop=True)

    # 1) Supplier inventory eventually hits zero
    supplier_eod = eod[eod.node_id == "Supplier"].reset_index(drop=True)
    assert supplier_eod["on_hand"].min() == 0, "Supplier inventory never depleted"

    # First depletion time (EOD)
    t_empty = int(supplier_eod.loc[supplier_eod["on_hand"] == 0, "t"].iloc[0])

    # 2) Downstream backlog rises
    r_backlog = eod[eod.node_id == "R"]["backlog_external"]
    w_backlog = eod[eod.node_id == "W"]["backlog_children"]
    assert r_backlog.max() > 0, "Retailer backlog never built"
    assert w_backlog.max() > 0, "Warehouse backlog never built"

    # 3) Supplier must NOT ship AFTER depletion (pipeline may still deliver later)
    ship_df = pd.DataFrame(sim.shipments_log) if sim.shipments_log else pd.DataFrame(
        columns=["t_ship","parent","child","lead_time","qty"])
    sup_ship = ship_df[ship_df.get("parent", "") == "Supplier"]
    if not sup_ship.empty:
        assert (sup_ship["t_ship"] <= t_empty).all(), \
            f"Supplier shipped after depletion: {sup_ship[sup_ship['t_ship'] > t_empty]}"

    # 4) Backlog cost at retailer becomes positive
    r_cost = eod[eod.node_id == "R"]["backlog_cost"]
    assert r_cost.max() > 0, "No backlog cost incurred under supplier shortage"

    # 5) Sanity: no negative backlog values
    assert r_backlog.iloc[-1] >= 0 and w_backlog.iloc[-1] >= 0, "Negative backlog detected"
