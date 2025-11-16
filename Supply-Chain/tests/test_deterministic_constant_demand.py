# tests/test_deterministic_constant_demand.py
import json, pandas as pd
from scripts.run_simulation import build_from_config
from engine.simulator import Simulator

def test_constant_demand_sawtooth(tmp_path):
    cfg = {
        "time_horizon": 15,
        "nodes": [
            {"id":"Supplier","type":"supplier","infinite_supply":True,
             "policy":{"type":"base_stock","base_stock_level":0}},
            {"id":"Warehouse","type":"warehouse","initial_inventory":20,
             "policy":{"type":"base_stock","base_stock_level":30}},
            {"id":"Retailer","type":"retailer","initial_inventory":15,
             "policy":{"type":"base_stock","base_stock_level":25}}
        ],
        "edges": [
            {"from":"Supplier","to":"Warehouse","lead_time":{"type":"deterministic","value":2}},
            {"from":"Warehouse","to":"Retailer","lead_time":{"type":"deterministic","value":1}}
        ],
        "demand": [
            {"node":"Retailer","generator":{"type":"deterministic","value":3}}
        ]
    }
    p = tmp_path/"cfg.json"; p.write_text(json.dumps(cfg))
    net, dmap, T = build_from_config(str(p))
    sim = Simulator(net, dmap, T, order_processing_delay=1)
    df = pd.DataFrame([m.__dict__ for m in sim.run()])

    r = df[df.node_id=="Retailer"].reset_index(drop=True)
    # no negatives
    assert (r["on_hand"] >= 0).all()
    # backlog bounded under base-stock sizing
    assert r["backlog_external"].max() <= 3
    # shipments cadence should be periodic (first receipt after 1+delay)
    first_recv = r[r["received"]>0]["t"].min()
    assert first_recv >= 2
