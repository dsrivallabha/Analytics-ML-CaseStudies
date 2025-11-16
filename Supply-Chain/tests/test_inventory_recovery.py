import pandas as pd
from scripts.run_simulation import build_from_config
from engine.simulator import Simulator

def test_inventory_recovery_from_backlog():
    cfg = {
        "time_horizon": 30,
        "nodes": [
            {"id": "Supplier", "type": "supplier", "infinite_supply": True,
             "policy": {"type": "base_stock", "base_stock_level": 0}},
            {"id": "R", "type": "retailer", "initial_inventory": 10,
             "policy": {"type": "base_stock", "base_stock_level": 50},
             "holding_cost": 0.5, "shortage_cost": 3.0}
        ],
        "edges": [
            {"from": "Supplier", "to": "R",
             "lead_time": {"type": "deterministic", "value": 3}}
        ],
        "demand": [
            {"node": "R", "generator": {"type": "deterministic", "value": 8}}
        ]
    }

    net, demand_by_node, T = build_from_config(cfg)
    sim = Simulator(net, demand_by_node, T=T, order_processing_delay=1)
    df = pd.DataFrame([m.__dict__ for m in sim.run(mode="summary")])
    r = df[(df.node_id == "R") & (df.phase == "EOD")]

    backlog_present = (r["backlog_external"] > 0).any()
    backlog_recovered = r.iloc[-1]["backlog_external"] == 0
    assert backlog_present, "No backlog ever built (demand too low)"
    assert backlog_recovered, "Backlog never recovered even after replenishment"
