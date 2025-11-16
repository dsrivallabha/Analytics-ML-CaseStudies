# tests/test_system_properties.py
"""
Flow conservation for an OPEN system:
- We track only non-supplier nodes as the "system".
- External outflow = fulfilled end-customer demand (at Retailer).
- External inflow = shipments from Supplier (both arrived and still in transit).

Identity at EOD t:
    (Physical inventory of non-supplier nodes)
  + (All pipeline headed to non-supplier nodes)
  + (Cumulative fulfilled demand up to t)
  =
    (Initial physical inventory of non-supplier nodes)
  + (Cumulative ARRIVALS from Supplier up to t)
  + (Current pipeline that originated at Supplier and is still in transit)

Notes:
- Single-sourcing is enforced in the Network (each child has exactly one parent),
  so pipeline_in for any direct child of Supplier comes only from Supplier.
"""

from scripts.run_simulation import build_from_config
from tests.conftest import df_from_cfg

def test_conservation_of_flow(basic_serial_config):
    cfg = basic_serial_config
    df = df_from_cfg(cfg)

    # Initial physical inventory in system (exclude Supplier)
    init_non_supplier_inv = sum(
        nd["initial_inventory"] for nd in cfg["nodes"] if nd["type"] != "supplier"
    )

    # Find direct children of Supplier (single-sourcing)
    net, _, _ = build_from_config(cfg)
    children_of_supplier = [c for (p, c) in net.edges.keys() if p == "Supplier"]

    # Deterministic external demand per period (Retailer)
    demand_per_period = cfg["demand"][0]["generator"]["value"]

    cum_arrivals_from_supplier = 0  # cumulative ARRIVED quantities from Supplier

    for t in sorted(df["t"].unique()):
        cur = df[df.t == t]

        # State of the system (exclude Supplier rows)
        physical = cur[cur.node_id != "Supplier"]["on_hand"].sum()
        in_transit_total = cur[cur.node_id != "Supplier"]["pipeline_in"].sum()

        # Pipeline that ORIGINATED at Supplier and hasn't arrived yet:
        # Since each child has a single parent, pipeline_in of Supplier's children
        # is exactly "pipeline from Supplier".
        P_supplier = cur[cur.node_id.isin(children_of_supplier)]["pipeline_in"].sum()

        # Cumulative fulfilled demand = cumulative demand - current backlog at Retailer
        if not cur[cur.node_id == "Retailer"].empty:
            backlog_E = int(cur[cur.node_id == "Retailer"]["backlog_external"].iloc[0])
        else:
            backlog_E = 0
        cum_demand = demand_per_period * (t + 1)
        cum_fulfilled = cum_demand - backlog_E

        # Cumulative ARRIVALS from Supplier (to its children) up to t
        cum_arrivals_from_supplier += cur[cur.node_id.isin(children_of_supplier)]["received"].sum()

        # Open-system conservation:
        lhs = physical + in_transit_total + cum_fulfilled
        rhs = init_non_supplier_inv + cum_arrivals_from_supplier + P_supplier

        assert abs(lhs - rhs) < 1e-9, (
            f"Flow conservation fails at t={t}:\n"
            f"LHS={lhs} (phys + in_transit + cum_fulfilled)\n"
            f"RHS={rhs} (init_non_supplier + cum_arrivals_from_supplier + P_supplier)\n"
        )
