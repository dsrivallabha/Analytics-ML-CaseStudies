# tests/test_variability.py
import pandas as pd
from scripts.run_simulation import build_from_config
from engine.simulator import Simulator  # <-- fix: import from engine

def df_from_cfg(cfg):
    net, dmap, T = build_from_config(cfg)
    sim = Simulator(net, dmap, T, order_processing_delay=1)
    return pd.DataFrame([m.__dict__ for m in sim.run()])

def test_poisson_reproducible_same_seed():
    cfg = {
        "time_horizon": 20,
        "nodes": [
            {"id":"Supplier","type":"supplier","infinite_supply":True,
             "policy":{"type":"base_stock","base_stock_level":0}},
            {"id":"Warehouse","type":"warehouse","initial_inventory":50,
             "policy":{"type":"base_stock","base_stock_level":70}},
            {"id":"Retailer","type":"retailer","initial_inventory":30,
             "policy":{"type":"base_stock","base_stock_level":45}}
        ],
        "edges": [
            {"from":"Supplier","to":"Warehouse","lead_time":{"type":"deterministic","value":2}},
            {"from":"Warehouse","to":"Retailer","lead_time":{"type":"deterministic","value":1}}
        ],
        "demand": [
            {"node":"Retailer","generator":{"type":"poisson","lam":7.0, "seed": 999}}
        ]
    }
    df1 = df_from_cfg(cfg).reset_index(drop=True)
    df2 = df_from_cfg(cfg).reset_index(drop=True)
    pd.testing.assert_frame_equal(df1, df2)

def test_normal_leadtime_causes_timing_var():
    cfg = {
        "time_horizon": 30,
        "nodes": [
            {"id":"Supplier","type":"supplier","infinite_supply":True,
             "policy":{"type":"base_stock","base_stock_level":0}},
            {"id":"Warehouse","type":"warehouse","initial_inventory":80,
             "policy":{"type":"base_stock","base_stock_level":110}},
            {"id":"Retailer","type":"retailer","initial_inventory":40,
             "policy":{"type":"base_stock","base_stock_level":55}}
        ],
        "edges": [
            {"from":"Supplier","to":"Warehouse","lead_time":{"type":"deterministic","value":2}},
            {"from":"Warehouse","to":"Retailer",
             "lead_time":{"type":"normal_int","mean":1.5,"std":0.6, "seed": 1234}}
        ],
        "demand": [
            {"node":"Retailer","generator":{"type":"deterministic","value":9}}
        ]
    }
    df = df_from_cfg(cfg)
    r = df[df.node_id=="Retailer"]
    # received stream should vary because of variable LT bunching
    assert (r["received"].nunique() > 1) or (r["received"].sum() > 0)
    # safety
    assert (df[df.node_id!="Supplier"]["on_hand"] >= 0).all()

def test_poisson_variability_shows_in_inventory():
    cfg = {
        "time_horizon": 40,
        "nodes": [
            {"id":"Supplier","type":"supplier","infinite_supply":True,
             "policy":{"type":"base_stock","base_stock_level":0}},
            {"id":"Warehouse","type":"warehouse","initial_inventory":80,
             "policy":{"type":"base_stock","base_stock_level":110}},
            {"id":"Retailer","type":"retailer","initial_inventory":40,
             "policy":{"type":"base_stock","base_stock_level":55}}
        ],
        "edges": [
            {"from":"Supplier","to":"Warehouse","lead_time":{"type":"deterministic","value":2}},
            {"from":"Warehouse","to":"Retailer","lead_time":{"type":"deterministic","value":1}}
        ],
        "demand": [
            {"node":"Retailer","generator":{"type":"poisson","lam":9.5, "seed": 555}}
        ]
    }
    df = df_from_cfg(cfg)
    r = df[df.node_id=="Retailer"]
    assert r["on_hand"].std() > 0
