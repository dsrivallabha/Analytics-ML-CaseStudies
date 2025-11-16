import pandas as pd
from scripts.run_simulation import build_from_config, Simulator

def test_112_first_receipts():
    cfg = {
        "time_horizon": 8,
        "nodes": [
            {"id":"Supplier","type":"supplier","infinite_supply":True,
             "policy":{"type":"base_stock","base_stock_level":0}},
            {"id":"WH","type":"warehouse","initial_inventory":40,
             "policy":{"type":"base_stock","base_stock_level":60}},
            {"id":"R1","type":"retailer","initial_inventory":10,
             "policy":{"type":"base_stock","base_stock_level":20}},
            {"id":"R2","type":"retailer","initial_inventory":10,
             "policy":{"type":"base_stock","base_stock_level":20}}
        ],
        "edges": [
            {"from":"Supplier","to":"WH","lead_time":{"type":"deterministic","value":2}},
            {"from":"WH","to":"R1","lead_time":{"type":"deterministic","value":1}},
            {"from":"WH","to":"R2","lead_time":{"type":"deterministic","value":1}}
        ],
        "demand": [
            {"node":"R1","generator":{"type":"deterministic","value":3}},
            {"node":"R2","generator":{"type":"deterministic","value":2}}
        ]
    }
    net, dmap, T = build_from_config(cfg)
    sim = Simulator(net, dmap, T, order_processing_delay=1)
    df = pd.DataFrame([m.__dict__ for m in sim.run()])
    for r in ["R1", "R2"]:
        first = df[(df.node_id==r) & (df.received>0)]["t"].min()
        assert first >= 2  # order@0 -> process@1 -> LT=1
    assert (df[df.node_id!="Supplier"]["on_hand"] >= 0).all()
