# tests/test_periodic_review.py
import pandas as pd
from scripts.run_simulation import build_from_config
from engine.simulator import Simulator

def test_periodic_review_only_on_ticks():
    cfg = {
        "time_horizon": 16,
        "nodes": [
            {"id":"Supplier","type":"supplier","infinite_supply":True,
             "policy":{"type":"base_stock","base_stock_level":0}},
            {"id":"Retailer","type":"retailer","initial_inventory":20,
             "policy":{"type":"order_up_to","S":40,"R":3,"phase_offset":1}}
        ],
        "edges": [
            {"from":"Supplier","to":"Retailer","lead_time":{"type":"deterministic","value":1}}
        ],
        "demand": [
            {"node":"Retailer","generator":{"type":"deterministic","value":0}}
        ]
    }
    net, dmap, T = build_from_config(cfg)
    sim = Simulator(net, dmap, T, order_processing_delay=1)
    df = pd.DataFrame([r.__dict__ for r in sim.run()])
    orders = df[df.node_id=="Retailer"]["orders_to_parent"].reset_index(drop=True)

    expected_ticks = {t for t in range(T) if ((t - 1) % 3) == 0}
    for t, qty in enumerate(orders):
        if t not in expected_ticks:
            assert qty == 0

def test_periodic_review_ip_capped_at_S():
    cfg = {
        "time_horizon": 20,
        "nodes": [
            {"id":"Supplier","type":"supplier","infinite_supply":True,
             "policy":{"type":"base_stock","base_stock_level":0}},
            {"id":"Retailer","type":"retailer","initial_inventory":10,
             "policy":{"type":"order_up_to","S":35,"R":2,"phase_offset":0}}
        ],
        "edges": [
            {"from":"Supplier","to":"Retailer","lead_time":{"type":"deterministic","value":2}}
        ],
        "demand": [
            {"node":"Retailer","generator":{"type":"deterministic","value":4}}
        ]
    }
    net, dmap, T = build_from_config(cfg)
    sim = Simulator(net, dmap, T, order_processing_delay=1)
    df = pd.DataFrame([r.__dict__ for r in sim.run()])
    r = df[df.node_id=="Retailer"]

    ip = r["on_hand"] - (r["backlog_external"] + r["backlog_children"]) + r["pipeline_in"]
    assert (ip <= 35 + 1e-9).all()
