from dataclasses import dataclass, field
from typing import Optional, Tuple
from policies.base_stock import BasePolicy

@dataclass
class KmCyclePolicy(BasePolicy):
    k: int                 # max number of orders allowed per cycle
    m: int                 # cycle length in periods (e.g., 7)
    S: int                 # order-up-to target
    review_offsets: Tuple[int, ...] = (0,)  # times within the cycle when ordering is permitted

    _last_cycle: int = field(default=-1, init=False)
    _used_in_cycle: int = field(default=0, init=False)

    def order_qty(self, *, on_hand: int, backlog_external: int,
                  backlog_children: int, pipeline_in: int, t: Optional[int] = None) -> int:
        if t is None:
            # If time is unknown, behave like single periodic review at every call.
            allowed = True
            cycle = 0
        else:
            cycle = t // self.m
            if cycle != self._last_cycle:
                self._last_cycle, self._used_in_cycle = cycle, 0
            allowed = ((t % self.m) in self.review_offsets) and (self._used_in_cycle < self.k)

        if not allowed:
            return 0

        ip = on_hand - (backlog_external + backlog_children) + pipeline_in
        q = max(0, self.S - ip)
        if q > 0:
            self._used_in_cycle += 1
        return q
