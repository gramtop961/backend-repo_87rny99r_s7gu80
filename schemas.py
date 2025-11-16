"""
Game Database Schemas (Pydantic)

Each Pydantic model maps to a MongoDB collection where the collection name is the
lowercased class name. These models are used for request/response validation and
for shaping data written to the database.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

# Core primitives

class Currency(BaseModel):
    coins: int = 0
    stars: int = 0
    energy: int = 30
    keys: int = 0

class Reward(BaseModel):
    type: Literal["coins", "stars", "energy", "keys"]
    amount: int = Field(..., ge=0)

# Profile

class Profile(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    display_name: str = Field(..., description="Player chosen name")
    avatar: Optional[str] = None
    currencies: Currency = Field(default_factory=Currency)
    level: int = 1
    exp: int = 0
    streak: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# Quests & Achievements & Events

class Quest(BaseModel):
    quest_id: str
    title: str
    description: Optional[str] = None
    target: int = 1
    progress: int = 0
    reward: Reward
    user_id: str
    completed: bool = False

class Achievement(BaseModel):
    achievement_id: str
    title: str
    description: Optional[str] = None
    condition: str
    reward: Reward
    user_id: str
    unlocked: bool = False

class Event(BaseModel):
    event_id: str
    name: str
    description: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    badge: Optional[str] = None

# Leaderboard

class LeaderboardEntry(BaseModel):
    user_id: str
    display_name: str
    score: int

# Slot play

class SlotPlayRequest(BaseModel):
    user_id: str
    theme: Literal[
        "sunny_garden",
        "candy_carnival",
        "pirate_treasure",
        "fairytale_forest",
        "royal_pet_palace",
    ] = "sunny_garden"
    bet: int = Field(10, ge=1)

class SlotResult(BaseModel):
    user_id: str
    theme: str
    bet: int
    win_amount: int
    outcome: Literal["miss", "small", "medium", "big", "jackpot"]
    reels: List[List[str]] = Field(default_factory=list)
    reward: Optional[Reward] = None
    created_at: Optional[datetime] = None

# Mini-game play

class MiniGamePlayRequest(BaseModel):
    user_id: str
    game: Literal[
        "lucky_flip",
        "bubble_pop",
        "treasure_drop",
        "magic_ring",
        "puzzle_pick",
    ] = "bubble_pop"

class MiniGameResult(BaseModel):
    user_id: str
    game: str
    success: bool
    score: int = 0
    reward: Optional[Reward] = None
    created_at: Optional[datetime] = None
