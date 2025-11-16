import pandas as pd
from engine.network import Network, Edge
from engine.node import Node
from policies.base_stock import BaseStockPolicy
from engine.simulator import Simulator

def test_multiroute_transport_cost_average():
    net = Network()
    s = Node("S", "supplier", policy=BaseStockPolicy(base_stock_level=0),
             infinite_supply=True)
    w = Node("W", "warehouse", policy=BaseStockPolicy(base_stock_level=50),
             initial_inventory=100)
    net.add_node(s)
    net.add_node(w)

    # Two routes with different shares and transport costs
    net.add_edge("S", "W", lead_time_sampler=lambda: 1, share=0.7)
    net.edges[("S", "W")][0].transport_cost_per_unit = 0.2
    net.add_edge("S", "W", lead_time_sampler=lambda: 2, share=0.3)
    net.edges[("S", "W")][1].transport_cost_per_unit = 0.8

    avg_costs = net.transport_cost_average_by_child("S")
    assert "W" in avg_costs
    expected = 0.7 * 0.2 + 0.3 * 0.8
    assert abs(avg_costs["W"] - expected) < 1e-6, "Weighted average transport cost incorrect"
