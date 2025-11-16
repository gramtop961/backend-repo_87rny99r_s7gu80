import os
import random
from datetime import datetime, timezone
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from schemas import (
    Profile,
    Quest,
    Event,
    LeaderboardEntry,
    SlotPlayRequest,
    SlotResult,
    MiniGamePlayRequest,
    MiniGameResult,
    Reward,
    Currency,
)
from database import db, create_document, get_documents

app = FastAPI(title="Cozy Social Casino API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Cozy Casino Backend Running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                cols = db.list_collection_names()
                response["collections"] = cols
                response["connection_status"] = "Connected"
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:120]}"

    return response


# -------- Profiles --------
@app.post("/profiles", response_model=Profile)
def create_profile(profile: Profile):
    # Upsert style: if exists return existing, else create
    existing = db["profile"].find_one({"user_id": profile.user_id}) if db else None
    if existing:
        # Return merged
        pdata = {
            "user_id": existing.get("user_id"),
            "display_name": existing.get("display_name", profile.display_name),
            "avatar": existing.get("avatar"),
            "currencies": existing.get("currencies", profile.currencies),
            "level": existing.get("level", 1),
            "exp": existing.get("exp", 0),
            "streak": existing.get("streak", 0),
            "created_at": existing.get("created_at"),
            "updated_at": datetime.now(timezone.utc),
        }
        return Profile(**pdata)

    doc = profile.model_dump()
    doc["created_at"] = datetime.now(timezone.utc)
    doc["updated_at"] = datetime.now(timezone.utc)
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    db["profile"].insert_one(doc)
    return Profile(**doc)


@app.get("/profiles/{user_id}", response_model=Profile)
def get_profile(user_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    found = db["profile"].find_one({"user_id": user_id})
    if not found:
        raise HTTPException(status_code=404, detail="Profile not found")
    return Profile(**found)


# -------- Quests & Events & Leaderboard (demo data) --------
@app.get("/quests/{user_id}", response_model=List[Quest])
def list_quests(user_id: str):
    # Demo quests
    return [
        Quest(
            quest_id="q1",
            title="Spin 10 times",
            description="Warm up your reels",
            target=10,
            progress=3,
            reward=Reward(type="coins", amount=200),
            user_id=user_id,
        ),
        Quest(
            quest_id="q2",
            title="Win a medium prize",
            description="Feel the bloom",
            target=1,
            progress=0,
            reward=Reward(type="stars", amount=1),
            user_id=user_id,
        ),
    ]


@app.get("/events", response_model=List[Event])
def list_events():
    return [
        Event(event_id="e1", name="Garden Gala", description="Seasonal blossoms"),
        Event(event_id="e2", name="Candy Carnival", description="Sweet treats week"),
    ]


@app.get("/leaderboard", response_model=List[LeaderboardEntry])
def leaderboard():
    return [
        LeaderboardEntry(user_id="alice", display_name="Alice", score=1200),
        LeaderboardEntry(user_id="bob", display_name="Bob", score=980),
        LeaderboardEntry(user_id="you", display_name="You", score=500),
    ]


# -------- Play Slot --------

SYMBOLS = ["🌼", "🍀", "🍓", "🐝", "🧚", "💎"]


def spin_reels() -> List[List[str]]:
    return [[random.choice(SYMBOLS) for _ in range(3)] for _ in range(3)]


def determine_outcome(reels: List[List[str]]):
    # Simple check: count three-in-a-row on each row
    lines = reels
    payouts = {"miss": 0, "small": 2, "medium": 5, "big": 20, "jackpot": 100}
    outcome = "miss"
    wins = 0
    for row in lines:
        if row[0] == row[1] == row[2]:
            wins += 1
    if wins >= 1:
        outcome = "small"
    if wins >= 2:
        outcome = "medium"
    if wins == 3:
        # Jackpot if all rows match same symbol
        if len({tuple(row) for row in lines}) == 1:
            outcome = "jackpot"
        else:
            outcome = "big"
    return outcome, payouts[outcome]


@app.post("/play/slot", response_model=SlotResult)
def play_slot(req: SlotPlayRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    profile = db["profile"].find_one({"user_id": req.user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Energy cost: 1 per spin
    if profile.get("currencies", {}).get("energy", 0) < 1:
        raise HTTPException(status_code=400, detail="Not enough energy")

    reels = spin_reels()
    outcome, multiplier = determine_outcome(reels)
    win_amount = req.bet * multiplier

    # Update currencies: spend energy, add coins
    currencies = profile.get("currencies", {})
    currencies["energy"] = max(0, currencies.get("energy", 0) - 1)
    currencies["coins"] = currencies.get("coins", 0) + win_amount

    db["profile"].update_one({"user_id": req.user_id}, {"$set": {"currencies": currencies, "updated_at": datetime.now(timezone.utc)}})

    reward = Reward(type="coins", amount=win_amount) if win_amount > 0 else None

    doc = SlotResult(
        user_id=req.user_id,
        theme=req.theme,
        bet=req.bet,
        win_amount=win_amount,
        outcome=outcome,
        reels=reels,
        reward=reward,
        created_at=datetime.now(timezone.utc),
    ).model_dump()

    db["slotresult"].insert_one(doc)

    return SlotResult(**doc)


# -------- Play Mini-game --------

@app.post("/play/mini", response_model=MiniGameResult)
def play_mini(req: MiniGamePlayRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    profile = db["profile"].find_one({"user_id": req.user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Energy cost: 2 per mini-game
    currencies = profile.get("currencies", {})
    if currencies.get("energy", 0) < 2:
        raise HTTPException(status_code=400, detail="Not enough energy")

    currencies["energy"] = max(0, currencies.get("energy", 0) - 2)

    # Simple success RNG
    success = random.random() < 0.6
    score = random.randint(10, 100) if success else random.randint(0, 20)

    reward_amt = 50 + score // 2 if success else 10
    currencies["coins"] = currencies.get("coins", 0) + reward_amt

    db["profile"].update_one({"user_id": req.user_id}, {"$set": {"currencies": currencies, "updated_at": datetime.now(timezone.utc)}})

    reward = Reward(type="coins", amount=reward_amt)

    doc = MiniGameResult(
        user_id=req.user_id,
        game=req.game,
        success=success,
        score=score,
        reward=reward,
        created_at=datetime.now(timezone.utc),
    ).model_dump()

    db["minigameresult"].insert_one(doc)

    return MiniGameResult(**doc)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
