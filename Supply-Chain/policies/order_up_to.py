from dataclasses import dataclass, field
from typing import Optional
from policies.base_stock import BasePolicy

@dataclass
class OrderUpToPolicy(BasePolicy):
    R: int                 # review period (e.g., weekly = 7)
    S: int                 # order-up-to target
    phase_offset: int = 0  # review happens when (t - phase_offset) % R == 0

    # (k,m) cycle parameters
    k: Optional[int] = None   # max number of orders in a cycle
    m: Optional[int] = None   # cycle length
    _cycle_start: int = field(default=0, init=False)
    _orders_in_cycle: int = field(default=0, init=False)

    def order_qty(self, *, on_hand: int, backlog_external: int,
                  backlog_children: int, pipeline_in: int, t: Optional[int] = None) -> int:
        if t is None:
            review_due = True
        else:
            review_due = ((t - self.phase_offset) % self.R) == 0

        # Handle cycle reset if (k,m) is enabled
        if self.m is not None and t is not None:
            if (t - self._cycle_start) >= self.m:
                self._cycle_start = t
                self._orders_in_cycle = 0

        # If it’s not a review period, no order
        if not review_due:
            return 0

        # If (k,m) prevents more orders this cycle, no order
        if self.k is not None and self._orders_in_cycle >= self.k:
            return 0

        # Compute inventory position (IP)
        ip = on_hand - (backlog_external + backlog_children) + pipeline_in
        qty = max(0, self.S - ip)

        # Count this order if positive
        if qty > 0 and self.k is not None:
            self._orders_in_cycle += 1

        return qty
