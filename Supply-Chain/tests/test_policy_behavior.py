import pandas as pd
import numpy as np
from scripts.run_simulation import build_from_config
from engine.simulator import Simulator

# ------------------------------------------------------------------------------------------
# 1️⃣ Base-stock policy test
# ------------------------------------------------------------------------------------------
def test_base_stock_policy_behavior():
    """
    Base-stock policy should reorder every time inventory + pipeline < base_stock_level.
    The resulting inventory levels should hover near the base-stock level with minimal backlog.
    """
    cfg = {
        "time_horizon": 25,
        "nodes": [
            {"id": "Supplier", "type": "supplier", "infinite_supply": True,
             "policy": {"type": "base_stock", "base_stock_level": 0}},
            {"id": "R", "type": "retailer", "initial_inventory": 10,
             "policy": {"type": "base_stock", "base_stock_level": 30},
             "holding_cost": 0.5, "shortage_cost": 3.0}
        ],
        "edges": [
            {"from": "Supplier", "to": "R",
             "lead_time": {"type": "deterministic", "value": 2}}
        ],
        "demand": [
            {"node": "R", "generator": {"type": "poisson", "lam": 4}}
        ]
    }

    net, demand_by_node, T = build_from_config(cfg)
    sim = Simulator(net, demand_by_node, T=T, order_processing_delay=1)
    df = pd.DataFrame([m.__dict__ for m in sim.run(mode="summary")])
    eod = df[df.phase == "EOD"]

    # Average inventory should be below base stock, and low backlog
    inv_mean = eod[eod.node_id == "R"]["on_hand"].mean()
    backlog_mean = eod[eod.node_id == "R"]["backlog_external"].mean()
    assert inv_mean < 30, "Inventory exceeding base-stock level unrealistically"
    assert backlog_mean < 5, "Base-stock policy accumulating high backlog"

# ------------------------------------------------------------------------------------------
# 2️⃣ (s, S) policy test
# ------------------------------------------------------------------------------------------
def test_sS_policy_triggers_and_levels():
    """
    (s, S) policy should order only when inventory position <= s.
    Orders should replenish to near S.
    """
    cfg = {
        "time_horizon": 30,
        "nodes": [
            {"id": "Supplier", "type": "supplier", "infinite_supply": True,
             "policy": {"type": "base_stock", "base_stock_level": 0}},
            {"id": "R", "type": "retailer", "initial_inventory": 20,
             "policy": {"type": "sS", "s": 10, "S": 30},
             "holding_cost": 0.5, "shortage_cost": 4.0}
        ],
        "edges": [
            {"from": "Supplier", "to": "R",
             "lead_time": {"type": "deterministic", "value": 1}}
        ],
        "demand": [
            {"node": "R", "generator": {"type": "poisson", "lam": 5}}
        ]
    }

    net, demand_by_node, T = build_from_config(cfg)
    sim = Simulator(net, demand_by_node, T=T, order_processing_delay=1)
    df = pd.DataFrame([m.__dict__ for m in sim.run(mode="summary")])
    eod = df[(df.phase == "EOD") & (df.node_id == "R")].reset_index(drop=True)

    # Find ordering days and corresponding inventory levels
    order_days = eod[eod["orders_to_parent"] > 0]
    inv_positions = eod["on_hand"] + eod["pipeline_in"]

    if len(order_days) > 0:
        # Orders should mostly occur when inventory position <= s
        trigger_ok = (inv_positions.loc[order_days.index] <= 10 + 1e-6).all()
        assert trigger_ok, "(s,S) orders not triggered correctly"
    else:
        # If no orders placed, demand too low — fine
        assert eod["demand"].sum() < 1, "Unexpected absence of orders"

    # On-hand should stay below or near S
    assert eod["on_hand"].max() <= 30 + 5, "Inventory exceeded upper level S significantly"

# ------------------------------------------------------------------------------------------
# 3️⃣ (Optional) order-up-to (R,S) policy placeholder
# ------------------------------------------------------------------------------------------
def test_order_up_to_policy_placeholder():
    """
    This will activate once you add OrderUpToPolicy in policies/order_up_to.py.
    For now, it simply ensures the import and build pipeline doesn’t break.
    """
    cfg = {
        "time_horizon": 10,
        "nodes": [
            {"id": "Supplier", "type": "supplier", "infinite_supply": True,
             "policy": {"type": "base_stock", "base_stock_level": 0}},
            {"id": "R", "type": "retailer", "initial_inventory": 15,
             "policy": {"type": "base_stock", "base_stock_level": 25}}
        ],
        "edges": [
            {"from": "Supplier", "to": "R",
             "lead_time": {"type": "deterministic", "value": 1}}
        ],
        "demand": [
            {"node": "R", "generator": {"type": "deterministic", "value": 3}}
        ]
    }

    net, demand_by_node, T = build_from_config(cfg)
    sim = Simulator(net, demand_by_node, T=T)
    df = pd.DataFrame([m.__dict__ for m in sim.run(mode="summary")])
    assert not df.empty, "Simulation failed for placeholder policy test"
