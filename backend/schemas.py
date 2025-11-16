from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime

# IMPORTANT: Each class name corresponds to a collection named as its lowercase
# Example: class User -> "user" collection

class Currency(BaseModel):
    coins: int = 0
    stars: int = 0
    energy: int = 20
    keys: int = 0

class Profile(BaseModel):
    user_id: str
    name: str
    avatar: str = "mascot"
    frame: Optional[str] = None
    mascot_skin: Optional[str] = None
    level: int = 1
    exp: int = 0
    currencies: Currency = Currency()
    unlocked_locations: List[str] = Field(default_factory=lambda: ["garden"]) 
    titles: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Reward(BaseModel):
    type: Literal["coins", "stars", "energy", "keys"]
    amount: int
    title: Optional[str] = None

class Quest(BaseModel):
    title: str
    description: str
    goal: int
    progress: int = 0
    reward: Reward
    category: Literal["daily", "weekly"] = "daily"
    completed: bool = False
    claimed: bool = False

class Achievement(BaseModel):
    key: str
    title: str
    description: str
    category: Literal["Slots", "Skill", "Progression", "Events", "Collection"]
    goal: int
    progress: int = 0
    unlocked: bool = False
    claimed: bool = False
    badge_svg: str = ""
    reward: Reward

class Event(BaseModel):
    key: str
    name: str
    theme: str
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    active: bool = True
    mini_rewards: List[Reward] = Field(default_factory=list)

class SlotResult(BaseModel):
    user_id: str
    slot_key: str
    bet: int
    win: int
    outcome: Literal["lose", "small", "medium", "big", "jackpot"]
    free_spins_awarded: int = 0
    created_at: Optional[datetime] = None

class MiniGameResult(BaseModel):
    user_id: str
    game_key: str
    score: int
    win: bool
    reward: Optional[Reward] = None
    created_at: Optional[datetime] = None

class RewardChest(BaseModel):
    chest_type: Literal["wooden", "silver", "gold", "event"]
    opened: bool = False
    rewards: List[Reward] = Field(default_factory=list)

class LeaderboardEntry(BaseModel):
    user_id: str
    name: str
    avatar: str
    score: int

# Request models
class PlaySlotRequest(BaseModel):
    user_id: str
    slot_key: str
    bet: int = 1

class PlayMiniGameRequest(BaseModel):
    user_id: str
    game_key: str
    score: int = 0

class ClaimRequest(BaseModel):
    user_id: str
    type: Literal["quest", "achievement", "login_streak", "chest"]
    key: Optional[str] = None
