import pandas as pd
from engine.network import Network
from engine.node import Node
from engine.simulator import Simulator
from policies.base_stock import BaseStockPolicy

def test_negative_demand_is_clipped():
    # network with single retailer node
    net = Network()
    r = Node("R", "retailer", policy=BaseStockPolicy(base_stock_level=10), initial_inventory=10)
    net.add_node(r)

    # demand generator with a negative value (should be clipped to 0)
    demand_series = [5, -7, 3]

    def demand_func(t):
        return demand_series[t] if t < len(demand_series) else 0

    demand_by_node = {"R": demand_func}

    sim = Simulator(network=net, demand_by_node=demand_by_node, T=3, order_processing_delay=1)
    res = sim.run(mode="summary")

    df = pd.DataFrame([m.__dict__ for m in res])
    r_df = df[df.node_id == "R"]

    # On-hand should never increase due to negative demand
    for t in range(1, len(r_df)):
        assert r_df.iloc[t]["on_hand"] <= 10, "Negative demand was not clipped properly"
