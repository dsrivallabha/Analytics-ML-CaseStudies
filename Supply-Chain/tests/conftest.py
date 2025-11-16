# tests/conftest.py
import pandas as pd
import pytest
from scripts.run_simulation import build_from_config
from engine.simulator import Simulator

def df_from_cfg(cfg, *, mode="summary"):
    net, dmap, T = build_from_config(cfg)
    sim = Simulator(net, dmap, T, order_processing_delay=1)
    rows = sim.run(mode=mode)
    return pd.DataFrame([r.__dict__ for r in rows])

@pytest.fixture
def basic_serial_config():
    # Supplier -> Warehouse -> Retailer, deterministic demand
    return {
        "time_horizon": 20,
        "nodes": [
            {"id":"Supplier","type":"supplier","infinite_supply":True,
             "policy":{"type":"base_stock","base_stock_level":0}},
            {"id":"Warehouse","type":"warehouse","initial_inventory":60,
             "policy":{"type":"base_stock","base_stock_level":85}},
            {"id":"Retailer","type":"retailer","initial_inventory":20,
             "policy":{"type":"base_stock","base_stock_level":35}}
        ],
        "edges": [
            {"from":"Supplier","to":"Warehouse","lead_time":{"type":"deterministic","value":2}},
            {"from":"Warehouse","to":"Retailer","lead_time":{"type":"deterministic","value":1}}
        ],
        "demand": [
            {"node":"Retailer","generator":{"type":"deterministic","value":5}}
        ]
    }
