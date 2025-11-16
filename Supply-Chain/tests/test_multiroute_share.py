# tests/test_multiroute_share.py
from collections import Counter
from scripts.run_simulation import build_from_config
from engine.simulator import Simulator  # just to bring in engine modules (ensures imports)

def test_multiroute_share_proportions_sampler():
    cfg = {
        "time_horizon": 1,  # not actually running sim; just building network
        "nodes": [
            {"id": "Supplier", "type": "supplier", "infinite_supply": True,
             "policy": {"type": "base_stock", "base_stock_level": 0}},
            {"id": "R", "type": "retailer", "initial_inventory": 0,
             "policy": {"type": "base_stock", "base_stock_level": 20}},
        ],
        "edges": [
            # Two separate edges with shares
            {"from": "Supplier", "to": "R",
             "lead_time": {"type": "deterministic", "value": 1}, "share": 0.7},
            {"from": "Supplier", "to": "R",
             "lead_time": {"type": "deterministic", "value": 3}, "share": 0.3},
        ],
        "demand": []
    }
    net, _, _ = build_from_config(cfg)
    sampler = net.lead_time_sampler_by_child("Supplier")["R"]

    # Sample many times
    N = 20000
    ctr = Counter(sampler() for _ in range(N))
    p1 = ctr[1] / N
    p3 = ctr[3] / N

    # ±5% absolute tolerance
    assert abs(p1 - 0.7) < 0.05, p1
    assert abs(p3 - 0.3) < 0.05, p3
