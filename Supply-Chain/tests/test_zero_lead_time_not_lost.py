import pandas as pd
from engine.network import Network
from engine.node import Node
from engine.simulator import Simulator
from policies.base_stock import BaseStockPolicy

def test_zero_lead_time_not_lost():
    # 1 -> 1 network
    net = Network()
    w = Node("W", "warehouse", policy=BaseStockPolicy(base_stock_level=0),
             initial_inventory=100)
    r = Node("R", "retailer", policy=BaseStockPolicy(base_stock_level=20),
             initial_inventory=0)

    net.add_node(w)
    net.add_node(r)
    # lead time = 0
    net.add_edge("W", "R", lead_time_sampler=lambda: 0)

    demand_by_node = {"R": lambda t: 0}
    sim = Simulator(net, demand_by_node, T=4, order_processing_delay=1)
    df = pd.DataFrame([m.__dict__ for m in sim.run(mode="summary")])

    # Retailer should receive some goods by t=2
    r_eod = df[(df.node_id == "R") & (df.phase == "EOD")]
    assert (r_eod["on_hand"] > 0).any(), "Zero lead-time shipment was lost or delayed"
