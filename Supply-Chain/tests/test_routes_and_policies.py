# tests/test_routes_and_policies.py
import json
from pathlib import Path
from scripts.run_simulation import build_from_config
from engine.simulator import Simulator

def _tmp_config(tmp_path, *, R=1, phase_offset=0, S=50, use_km=False, k=2, m=5, T=30):
    """
    Minimal 1-echelon: Supplier -> Retailer, no demand, LT=2
    """
    retailer_policy = (
        {"type": "km_cycle", "S": S, "k": k, "m": m, "review_offsets": [0]}
        if use_km else
        {"type": "order_up_to", "S": S, "R": R, "phase_offset": phase_offset}
    )
    cfg = {
        "time_horizon": T,
        "nodes": [
            {"id": "Supplier", "type": "supplier", "infinite_supply": True,
             "policy": {"type": "base_stock", "base_stock_level": 0}},
            {"id": "Retailer", "type": "retailer", "initial_inventory": 0,
             "policy": retailer_policy}
        ],
        "edges": [
            {"from": "Supplier", "to": "Retailer",
             "lead_time": {"type": "deterministic", "value": 2}}
        ],
        "demand": []  # isolate ordering behavior
    }
    p = tmp_path / "unit_cfg.json"
    p.write_text(json.dumps(cfg, indent=2))
    return str(p)

def _pipeline_in_increments(timeline_df, node="Retailer"):
    inc_days = []
    prev = None
    for t, sub in timeline_df[timeline_df.node_id == node].sort_values("t").iterrows():
        cur = sub["pipeline_in"]
        if prev is not None and cur > prev:
            inc_days.append(int(sub["t"]))
        prev = cur
    return inc_days

def test_orderupto_periodic_respects_R(tmp_path):
    R, phase = 3, 1
    cfg_path = _tmp_config(tmp_path, R=R, phase_offset=phase, S=40, T=22)

    net, dmap, T = build_from_config(cfg_path)
    sim = Simulator(net, dmap, T, order_processing_delay=1)
    import pandas as pd
    df = pd.DataFrame([m.__dict__ for m in sim.run()])

    inc_days = _pipeline_in_increments(df, "Retailer")

    # Orders happen at review ticks, but pipeline increments are logged after lead time
    lead_time = 1
    expected_first_tick = [phase + 1]
    assert inc_days == expected_first_tick, f"Got {inc_days}, expected pipeline increment after LT at {expected_first_tick}"

    r = df[df.node_id == "Retailer"]
    ip = r["on_hand"] - (r["backlog_external"] + r["backlog_children"]) + r["pipeline_in"]
    assert (ip <= 40 + 1e-9).all()




def test_km_cap_per_cycle(tmp_path):
    # km_cycle: allow at most k=2 orders per cycle of length m=5
    cfg_path = _tmp_config(tmp_path, use_km=True, k=2, m=5, S=30, T=35)

    net, dmap, T = build_from_config(cfg_path)
    sim = Simulator(net, dmap, T, order_processing_delay=1)
    df = __import__("pandas").DataFrame([m.__dict__ for m in sim.run()])

    inc_days = _pipeline_in_increments(df, "Retailer")
    by_cycle = {}
    for t in inc_days:
        cyc = t // 5
        by_cycle[cyc] = by_cycle.get(cyc, 0) + 1

    for cyc, cnt in by_cycle.items():
        assert cnt <= 2, f"cycle {cyc} has {cnt} orders (expected <= 2)"
