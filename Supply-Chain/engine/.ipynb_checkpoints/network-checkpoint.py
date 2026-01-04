# engine/network.py
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Callable, Optional
import random
from engine.node import Node

@dataclass
class Edge:
    parent: str
    child: str
    lead_time_sampler: Callable[[], int]
    share: Optional[float] = None  # optional weight for route selection
    transport_cost_per_unit: Optional[float] = None  # optional cost per unit transported
def _det_lt_one():
    return 1

@dataclass
class Network:
    # ✅ allow empty construction to satisfy tests that do Network() then add_node/add_edge
    nodes: Dict[str, Node] = field(default_factory=dict)                       # id -> Node
    edges: Dict[Tuple[str, str], List[Edge]] = field(default_factory=dict)     # (parent, child) -> [Edge]
    parents_of: Dict[str, str] = field(default_factory=dict)                   # single-sourcing (one parent per child)
    children_of: Dict[str, List[str]] = field(default_factory=dict)

    def __post_init__(self):
        # rebuild adjacency maps from existing edges (if any)
        self.parents_of.clear()
        self.children_of.clear()
        for (p, c), edge_list in self.edges.items():
            if c in self.parents_of and self.parents_of[c] != p:
                raise ValueError(f"Child {c} has multiple parents (single-sourcing enforced).")
            self.parents_of[c] = p
            self.children_of.setdefault(p, [])
            if c not in self.children_of[p]:
                self.children_of[p].append(c)

    # ✅ helpers used by several tests
    def add_node(self, node: Node) -> None:
        if node.node_id in self.nodes:
            raise ValueError(f"Duplicate node id: {node.node_id}")
        self.nodes[node.node_id] = node

    def add_edge(
        self,
        parent_id: str,
        child_id: str,
        *,
        lead_time_sampler: Optional[Callable[[], int]] = None,
        share: Optional[float] = None,
    ) -> None:
        """Add a lane. Defaults to deterministic L=1 if no sampler is given."""
        sampler = lead_time_sampler or _det_lt_one
        key = (parent_id, child_id)
        self.edges.setdefault(key, []).append(Edge(parent=parent_id, child=child_id, lead_time_sampler=sampler, share=share))
        # keep adjacency maps in sync
        if child_id in self.parents_of and self.parents_of[child_id] != parent_id:
            raise ValueError(f"Child {child_id} has multiple parents (single-sourcing enforced).")
        self.parents_of[child_id] = parent_id
        self.children_of.setdefault(parent_id, [])
        if child_id not in self.children_of[parent_id]:
            self.children_of[parent_id].append(child_id)

    def parent_of(self, node_id: str):
        return self.parents_of.get(node_id)

    def children(self, node_id: str) -> List[str]:
        return self.children_of.get(node_id, [])

    def _mixed_sampler(self, edge_list: List[Edge]) -> Callable[[], int]:
        # choose a route according to normalized shares (uniform if all None)
        weights = [e.share if (e.share is not None and e.share > 0) else 1.0 for e in edge_list]
        total = sum(weights)
        probs = [w / total for w in weights]

        def sample():
            r = random.random()
            acc = 0.0
            for e, p in zip(edge_list, probs):
                acc += p
                if r <= acc:
                    return e.lead_time_sampler()
            return edge_list[-1].lead_time_sampler()

        return sample

    def lead_time_sampler_by_child(self, parent_id: str) -> Dict[str, Callable[[], int]]:
        # For each child, return a single callable that mixes across routes
        out: Dict[str, Callable[[], int]] = {}
        for c in self.children(parent_id):
            e_list = self.edges[(parent_id, c)]
            out[c] = e_list[0].lead_time_sampler if len(e_list) == 1 else self._mixed_sampler(e_list)
        return out
    
    def _avg_costs_by_child(self, parent_id: str) -> Dict[str, float]:
        """Share-weighted average transport cost per child for a given parent."""
        out: Dict[str, float] = {}
        for c in self.children(parent_id):
            e_list = self.edges[(parent_id, c)]
            weights = [e.share if (e.share is not None and e.share > 0) else 1.0 for e in e_list]
            total_w = sum(weights)
            if total_w <= 0:
                out[c] = 0.0
                continue
            # ✅ Fix: Treat None as 0.0 to avoid TypeError
            cost = sum(w * (e.transport_cost_per_unit or 0.0) for w, e in zip(weights, e_list)) / total_w
            out[c] = float(cost)
        return out

    def transport_cost_average_by_child(self, parent_id: str) -> Dict[str, float]:
        """Public helper used by Simulator to charge shipment costs without changing shipment logic."""
        return self._avg_costs_by_child(parent_id)

