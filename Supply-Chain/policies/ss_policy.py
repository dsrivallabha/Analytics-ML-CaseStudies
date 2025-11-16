from dataclasses import dataclass
from policies.base_stock import BasePolicy

@dataclass
class SsPolicy(BasePolicy):
    s: int
    S: int

    def order_qty(self, on_hand, backlog_external, backlog_children, pipeline_in):
        ip = on_hand - (backlog_external + backlog_children) + pipeline_in
        return max(0, self.S - ip) if ip <= self.s else 0
