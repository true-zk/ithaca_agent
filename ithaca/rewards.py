"""
Ads plan rewards.
"""
from pydantic import BaseModel


# TODO: this is demo
# TODO: we need to add structured reward for persistence and reusability.
class CTRReward(BaseModel):
    """
    CTR reward is the reward for the CTR of the ad plan.
    """
    ctr: float
    ctr_threshold: float
    weight: float
    reward: float
    description: str