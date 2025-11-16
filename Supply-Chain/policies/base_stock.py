from dataclasses import dataclass

class BasePolicy:
    def order_qty(self, on_hand: int, backlog_external: int,
                  backlog_children: int, pipeline_in: int) -> int:
        raise NotImplementedError

@dataclass
class BaseStockPolicy(BasePolicy):
    base_stock_level: int

    def order_qty(self, on_hand, backlog_external, backlog_children, pipeline_in):
        # IP = OnHand - (backlogs owed) + inbound pipeline
        ip = on_hand - (backlog_external + backlog_children) + pipeline_in
        return max(0, self.base_stock_level - ip)
