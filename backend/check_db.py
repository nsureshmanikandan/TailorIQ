"""Check latest match result directly from DB."""
import asyncio
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", override=True)

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import get_settings
from app.models.db import MatchResult

async def check():
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    factory = async_sessionmaker(engine, class_=AsyncSession)

    async with factory() as db:
        result = await db.execute(
            select(MatchResult).order_by(desc(MatchResult.created_at)).limit(1)
        )
        mr = result.scalar_one_or_none()
        if not mr:
            print("No match results found")
            return

        print(f"run_id: {mr.run_id}")
        print(f"status: {mr.status}")
        print(f"pass1_score: {str(mr.pass1_score)[:200] if mr.pass1_score else None}")
        print(f"pass2_score: {str(mr.pass2_score)[:100] if mr.pass2_score else None}")
        print(f"parsed_resume present: {mr.parsed_resume is not None}")
        print(f"parsed_jd present: {mr.parsed_jd is not None}")
        print(f"tailored_resume present: {mr.tailored_resume is not None}")
        print(f"cover_letter present: {mr.cover_letter is not None}")
        print(f"tokens: {mr.total_tokens_used}")
        print(f"cost: {mr.total_cost_usd}")
        print(f"started: {mr.started_at}")
        print(f"completed: {mr.completed_at}")

    await engine.dispose()

asyncio.run(check())
