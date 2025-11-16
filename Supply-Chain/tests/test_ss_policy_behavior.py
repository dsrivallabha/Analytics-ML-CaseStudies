# tests/test_ss_policy_behavior.py
import pandas as pd
from scripts.run_simulation import build_from_config
from engine.simulator import Simulator

def test_ss_policy_orders_only_when_below_s():
    cfg = {
        "time_horizon": 25,
        "nodes": [
            {"id":"Supplier","type":"supplier","infinite_supply":True,
             "policy":{"type":"base_stock","base_stock_level":0}},
            {"id":"R","type":"retailer","initial_inventory":12,
             "policy":{"type":"sS","s":10,"S":20}}
        ],
        "edges": [
            {"from":"Supplier","to":"R","lead_time":{"type":"deterministic","value":2}}
        ],
        "demand": [
            {"node":"R","generator":{"type":"deterministic","value":1}}
        ]
    }
    net, dmap, T = build_from_config(cfg)
    sim = Simulator(net, dmap, T, order_processing_delay=1)
    df = pd.DataFrame([m.__dict__ for m in sim.run()])
    r = df[df.node_id=="R"].reset_index(drop=True)

    ip = r["on_hand"] - (r["backlog_external"] + r["backlog_children"]) + r["pipeline_in"]
    orders = r["orders_to_parent"]

    for t in range(len(r)):
        if ip.iloc[t] > 10 + 1e-9:
            assert orders.iloc[t] == 0, f"t={t}: IP={ip.iloc[t]} > s but order={orders.iloc[t]} != 0"

    # IP capped at S
    assert (ip <= 20 + 1e-9).all()
