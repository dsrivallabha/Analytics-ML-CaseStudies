# engine/simulator.py
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from engine.network import Network
from engine.node import Node
from policies.base_stock import BasePolicy

@dataclass
class MetricsRow:
    t: int
    node_id: str
    on_hand: int
    backlog_external: int
    backlog_children: int
    pipeline_in: int
    orders_to_parent: int
    received: int
    phase: str = "EOD"
    demand: int = 0             
    fulfilled_external: int = 0
    holding_cost: float = 0.0
    backlog_cost: float = 0.0
    ordering_cost: float = 0.0
    transport_cost: float = 0.0
    total_cost: float = 0.0

@dataclass
class Simulator:
    network: Network
    demand_by_node: Dict[str, callable]   # node_id -> DemandGenerator.sample
    T: int
    order_processing_delay: int = 1

    metrics: List[MetricsRow] = field(default_factory=list)
    shipments_log: List[Dict] = field(default_factory=list)   # NEW: route verification

    def run(self, mode: str = "summary") -> List[MetricsRow]:
        topo = self._topological_order()
        # parent_id -> list of (process_time, child_id, qty)
        orders_waiting: Dict[str, List[Tuple[int, str, int]]] = {}
        demand_today: Dict[str, int] = {}
        fulfilled_today: Dict[str, int] = {}

        for t in range(self.T):
            received_today: Dict[str, int] = {nid: 0 for nid in self.network.nodes}
            orders_today: Dict[str, int]   = {nid: 0 for nid in self.network.nodes}
            demand_today = {nid: 0 for nid in self.network.nodes}
            fulfilled_today = {nid: 0 for nid in self.network.nodes}
            ordering_cost_today: Dict[str, float] = {nid: 0.0 for nid in self.network.nodes}
            transport_cost_today: Dict[str, float] = {nid: 0.0 for nid in self.network.nodes}

            # 1) Arrivals
            for nid in topo:
                node = self.network.nodes[nid]
                rec = node.receive_shipments(t)
                received_today[nid] = rec
                if mode == "detailed":
                    self._record(t, nid, received=rec, orders_to_parent=0, phase="after_arrivals")

            # 1a) Clear external backlog immediately after arrivals
            for nid in topo:
                node = self.network.nodes[nid]
                if node.node_type == 'retailer' and node.backlog_external > 0 and node.on_hand > 0:
                    served_backlog = min(node.on_hand, node.backlog_external)
                    node.on_hand -= served_backlog
                    node.backlog_external -= served_backlog
                    if mode == "detailed" and served_backlog > 0:
                        self._record(t, nid, received=0, orders_to_parent=0, phase="after_backlog_clear")

            # 2) External demand
            for nid in topo:
                node = self.network.nodes[nid]
                if node.node_type == 'retailer':
                    dgen = self.demand_by_node.get(nid, None)
                    demand = int(dgen(t)) if dgen else 0
                    fulfilled, unfilled = node.process_external_demand(demand)
                    demand_today[nid] = demand
                    fulfilled_today[nid] = fulfilled
                    if mode == "detailed":
                        self._record(t, nid, received=0, orders_to_parent=0, phase="after_demand")

            # 3) Parents process child orders due at t
            due: Dict[str, List[Tuple[str, int]]] = {}
            for pid, lst in list(orders_waiting.items()):
                take = [(c, q) for (tt, c, q) in lst if tt == t]
                if take:
                    due[pid] = take
                orders_waiting[pid] = [(tt, c, q) for (tt, c, q) in lst if tt != t]
                if not orders_waiting[pid]:
                    del orders_waiting[pid]

            for parent_id, items in due.items():
                parent = self.network.nodes[parent_id]
                for (child, q) in items:
                    parent.add_inbound_order(child, q)
                child_nodes = {c: self.network.nodes[c] for c in self.network.children(parent_id)}
                lt_map = self.network.lead_time_sampler_by_child(parent_id)

                def _on_ship(p, c, tt, L, qty):
                    self.shipments_log.append({"t_ship": tt, "parent": p, "child": c, "lead_time": L, "qty": qty})

                shipped = parent.process_child_orders(t, child_nodes, lt_map, on_ship=_on_ship)

                avg_cost = self.network.transport_cost_average_by_child(parent_id)
                for c, q in shipped.items():
                    transport_cost_today[parent_id] += float(avg_cost.get(c, 0.0)) * q

            if mode == "detailed":
                for nid in topo:
                    self._record(t, nid, received=0, orders_to_parent=0, phase="after_shipments")

            # 4) Place upstream orders
            for nid in topo:
                node = self.network.nodes[nid]
                hold_cost = float(node.on_hand) * float(node.holding_cost)
                # backlog penalty only on external (retailer); warehouses typically don't have external backorders
                back_cost = float(node.backlog_external) * float(node.shortage_cost) if node.node_type == 'retailer' else 0.0
                ord_cost  = ordering_cost_today[nid]
                trans_cost = transport_cost_today[nid]
                tot_cost = hold_cost + back_cost + ord_cost + trans_cost

                parent_id = self.network.parent_of(nid)
                if parent_id is None:
                    continue
                policy: BasePolicy = node.policy
                try:
                    # New: try time-aware call
                    q = policy.order_qty(
                        on_hand=node.on_hand,
                        backlog_external=node.backlog_external,
                        backlog_children=node.total_backlog_children(),
                        pipeline_in=node.total_pipeline_in(),
                        t=t,                      # <— NEW
                    )
                except TypeError:
                    # Backward-compatible fallback
                    q = policy.order_qty(
                        on_hand=node.on_hand,
                        backlog_external=node.backlog_external,
                        backlog_children=node.total_backlog_children(),
                        pipeline_in=node.total_pipeline_in(),
                    )
                if q > 0:
                    orders_waiting.setdefault(parent_id, []).append((t + self.order_processing_delay, nid, q))
                    ordering_cost_today[nid] += float(node.order_cost_fixed) + float(node.order_cost_per_unit) * float(q)
                orders_today[nid] = q

                if mode == "detailed":
                    self._record(t, nid, received=0, orders_to_parent=q, phase="after_ordering")
                    
            # 5) EOD snapshot (after demand served, before next arrivals)
            for nid in topo:
                node = self.network.nodes[nid]
                hold_cost = float(node.on_hand) * float(node.holding_cost)
                back_cost = float(node.backlog_external) * float(node.shortage_cost) if node.node_type == 'retailer' else 0.0
                ord_cost = ordering_cost_today[nid]
                trans_cost = transport_cost_today[nid]
                tot_cost = hold_cost + back_cost + ord_cost + trans_cost

                self._record(
                    t, nid,
                    received=received_today[nid],
                    orders_to_parent=orders_today[nid],
                    phase="EOD",
                    demand=demand_today[nid],
                    fulfilled_external=fulfilled_today[nid],
                    holding_cost=hold_cost,
                    backlog_cost=back_cost,
                    ordering_cost=ord_cost,
                    transport_cost=trans_cost,
                    total_cost=tot_cost
                )


            # Safety
            for nid, node in self.network.nodes.items():
                if not node.infinite_supply:
                    assert node.on_hand >= 0, f"Negative stock at {nid} t={t}"

        return self.metrics

    def _record(self, t: int, nid: str, received: int, orders_to_parent: int,
            phase: str = "EOD", demand: int = 0, fulfilled_external: int = 0,
            holding_cost: float = 0.0, backlog_cost: float = 0.0,
            ordering_cost: float = 0.0, transport_cost: float = 0.0, total_cost: float = 0.0):
        node = self.network.nodes[nid]
        self.metrics.append(MetricsRow(
            t=t, node_id=nid, on_hand=node.on_hand,
            backlog_external=node.backlog_external,
            backlog_children=node.total_backlog_children(),
            pipeline_in=node.total_pipeline_in(),
            orders_to_parent=orders_to_parent,
            received=received, phase=phase,
            demand=demand, fulfilled_external=fulfilled_external,
            holding_cost=holding_cost, backlog_cost=backlog_cost,
            ordering_cost=ordering_cost, transport_cost=transport_cost,
            total_cost=total_cost
        ))


    def _topological_order(self) -> List[str]:
        indeg = {nid: 0 for nid in self.network.nodes}
        for (p, c) in self.network.edges:
            indeg[c] += 1
        q = [nid for nid, d in indeg.items() if d == 0]
        out = []
        while q:
            u = q.pop(0)
            out.append(u)
            for v in self.network.children(u):
                indeg[v] -= 1
                if indeg[v] == 0:
                    q.append(v)
        if len(out) != len(self.network.nodes):
            raise ValueError("Graph not a DAG or disconnected.")
        return out
