import pandas as pd
from engine.network import Network
from engine.node import Node
from engine.simulator import Simulator
from policies.base_stock import BaseStockPolicy

def test_no_negative_on_hand_over_horizon():
    net = Network()
    s = Node("S", "supplier", policy=BaseStockPolicy(base_stock_level=0),
             initial_inventory=0, infinite_supply=True)
    w = Node("W", "warehouse", policy=BaseStockPolicy(base_stock_level=70),
             initial_inventory=50)
    r = Node("R", "retailer", policy=BaseStockPolicy(base_stock_level=25),
             initial_inventory=20)

    net.add_node(s)
    net.add_node(w)
    net.add_node(r)
    net.add_edge("S", "W")
    net.add_edge("W", "R")

    demand_by_node = {"R": lambda t: 5}
    sim = Simulator(net, demand_by_node, T=50, order_processing_delay=1)
    df = pd.DataFrame([m.__dict__ for m in sim.run(mode="summary")])

    for _, row in df.iterrows():
        assert row.on_hand >= 0, f"Negative on-hand inventory at {row.node_id}, t={row.t}"
        assert row.backlog_external >= 0
        assert row.backlog_children >= 0
        assert row.pipeline_in >= 0
