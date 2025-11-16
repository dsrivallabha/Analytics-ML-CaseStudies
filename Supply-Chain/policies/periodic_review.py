from typing import Dict, Any
from .base_stock import BasePolicy

class PeriodicReviewPolicy(BasePolicy):
    """
    (k,m) Periodic Review Policy:
    - Check inventory every k periods
    - Order up to level m when checking
    """
    def __init__(self, review_period: int, order_up_to: int):
        """
        Parameters:
        -----------
        review_period : int
            Number of periods between reviews (k)
        order_up_to : int
            Target inventory position (m)
        """
        self.review_period = review_period
        self.order_up_to = order_up_to
        self.last_review = -1  # Initialize to -1 to ensure first period triggers review

    def order_qty(self, 
                 on_hand: int,
                 backlog_external: int,
                 backlog_children: int,
                 pipeline_in: int,
                 t: int) -> int:
        """
        Determine order quantity based on current state
        
        Parameters:
        -----------
        on_hand : int
            Current on-hand inventory
        backlog_external : int
            Current external backlog
        backlog_children : int
            Current backlog to child nodes
        pipeline_in : int
            Current pipeline inventory
        t : int
            Current time period
            
        Returns:
        --------
        int : Order quantity
        """
        # Only review every k periods
        if t % self.review_period != 0:
            return 0
            
        # Calculate current inventory position
        inv_position = on_hand - backlog_external - backlog_children + pipeline_in
        
        # Order up to m
        return max(0, self.order_up_to - inv_position)

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "periodic_review",
            "review_period": self.review_period,
            "order_up_to": self.order_up_to
        }
