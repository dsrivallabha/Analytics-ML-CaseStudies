import json, os, pandas as pd
from scripts.run_simulation import build_from_config, Simulator

def test_no_demand(tmp_path):
    cfg = {
        "time_horizon": 6,
        "nodes": [
            {"id":"Supplier","type":"supplier","infinite_supply":True,
             "policy":{"type":"base_stock","base_stock_level":0}},
            {"id":"Warehouse","type":"warehouse","initial_inventory":10,
             "policy":{"type":"base_stock","base_stock_level":10}},
            {"id":"Retailer","type":"retailer","initial_inventory":5,
             "policy":{"type":"base_stock","base_stock_level":5}}
        ],
        "edges": [
            {"from":"Supplier","to":"Warehouse","lead_time":{"type":"deterministic","value":1}},
            {"from":"Warehouse","to":"Retailer","lead_time":{"type":"deterministic","value":1}}
        ],
        "demand": []
    }
    p = tmp_path/"cfg.json"; p.write_text(json.dumps(cfg))
    net, dmap, T = build_from_config(str(p))
    sim = Simulator(net, dmap, T)
    df = pd.DataFrame([m.__dict__ for m in sim.run()])
    assert df["backlog_external"].max() == 0
    assert df["received"].sum() == 0  # no shipments to retailer
