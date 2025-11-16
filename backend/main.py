from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import random

from schemas import (
    Profile, Quest, Achievement, Reward, Event,
    PlaySlotRequest, PlayMiniGameRequest, SlotResult, MiniGameResult, RewardChest
)
from database import create_document, get_documents, update_document

app = FastAPI(title="Cozy Social Casino API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SLOT_KEYS = [
    "sunny_garden_spin",
    "candy_carnival_wheel",
    "pirate_treasure_reels",
    "fairytale_forest_fortune",
    "royal_pet_palace",
]

MINI_GAME_KEYS = [
    "lucky_flip_tiles",
    "bubble_pop_chance",
    "treasure_drop_path",
    "magic_timing_ring",
    "puzzle_pick_chest",
]

class CreateProfileRequest(BaseModel):
    user_id: str
    name: str

@app.get("/test")
async def test():
    # Quick DB verify by listing any profiles (may be empty)
    profiles = await get_documents("profile", {}, 1)
    return {"ok": True, "profiles_sample": profiles}

@app.post("/profiles", response_model=Dict[str, Any])
async def create_profile(req: CreateProfileRequest):
    profile = Profile(user_id=req.user_id, name=req.name)
    doc = await create_document("profile", profile.dict())
    return {"profile": doc}

@app.get("/profiles/{user_id}", response_model=Dict[str, Any])
async def get_profile(user_id: str):
    docs = await get_documents("profile", {"user_id": user_id}, 1)
    if not docs:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"profile": docs[0]}

@app.get("/quests/{user_id}")
async def get_quests(user_id: str):
    # Placeholder: return a few daily quests definitions
    quests = [
        Quest(title="Spin the Garden", description="Play Sunny Garden Spin 3 times", goal=3, reward=Reward(type="coins", amount=100)),
        Quest(title="Pop Bubbles", description="Score 50 in Bubble Pop Chance", goal=50, reward=Reward(type="stars", amount=2), category="weekly"),
    ]
    return {"quests": [q.dict() for q in quests]}

@app.post("/play/slot", response_model=Dict[str, Any])
async def play_slot(req: PlaySlotRequest):
    if req.slot_key not in SLOT_KEYS:
        raise HTTPException(status_code=400, detail="Invalid slot")
    # very simple RNG outcome tiers
    roll = random.random()
    if roll > 0.995:
        outcome = "jackpot"; win = req.bet * 200
    elif roll > 0.95:
        outcome = "big"; win = req.bet * 20
    elif roll > 0.75:
        outcome = "medium"; win = req.bet * 5
    elif roll > 0.5:
        outcome = "small"; win = req.bet * 2
    else:
        outcome = "lose"; win = 0

    free_spins = 5 if outcome in ("big", "jackpot") and random.random() > 0.6 else 0

    result = SlotResult(
        user_id=req.user_id,
        slot_key=req.slot_key,
        bet=req.bet,
        win=win,
        outcome=outcome,
        free_spins_awarded=free_spins,
    )
    doc = await create_document("slotresult", result.dict())
    return {"result": doc}

@app.post("/play/mini", response_model=Dict[str, Any])
async def play_mini(req: PlayMiniGameRequest):
    win = req.score >= 50
    reward = Reward(type="coins", amount=50 if win else 10)
    result = MiniGameResult(
        user_id=req.user_id, game_key=req.game_key, score=req.score, win=win, reward=reward
    )
    doc = await create_document("minigameresult", result.dict())
    return {"result": doc}

@app.get("/events")
async def list_events():
    events = [
        Event(key="spring_garden", name="Spring Garden Gala", theme="garden").dict(),
        Event(key="sweet_carnival", name="Sweet Carnival", theme="candy").dict(),
    ]
    return {"events": events}

@app.get("/leaderboard")
async def leaderboard():
    # Demo static leaderboard
    return {
        "entries": [
            {"user_id": "1", "name": "Luna", "avatar": "cat", "score": 1234},
            {"user_id": "2", "name": "Pip", "avatar": "parrot", "score": 984},
            {"user_id": "3", "name": "Milo", "avatar": "fox", "score": 746},
        ]
    }
