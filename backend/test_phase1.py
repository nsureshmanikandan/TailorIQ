"""Test Phase 1 directly - resume + JD parsing."""
import asyncio
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", override=True)

from app.config import get_settings
from app.services.llm_service import LLMService
from app.services.prompt_loader import PromptLoader
from app.agents.resume_parser import ResumeParserAgent, ResumeParserInput
from app.agents.jd_parser import JDParserAgent, JDParserInput

async def main():
    settings = get_settings()
    llm = LLMService(settings)
    loader = PromptLoader()

    resume_text = "John Doe, Python Developer, 5 years at Acme Corp doing AWS and Docker."
    jd_text = "Looking for Python Developer with AWS experience, 3+ years required."

    print("Testing Resume Parser Agent...")
    try:
        parser = ResumeParserAgent(llm, loader)
        result = await parser.execute(ResumeParserInput(raw_text=resume_text, file_format="txt"))
        print(f"  SUCCESS: candidate_name={result.candidate_name}")
        print(f"  skills count: {len(result.skills)}")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")

    print("\nTesting JD Parser Agent...")
    try:
        jd_parser = JDParserAgent(llm, loader)
        result = await jd_parser.execute(JDParserInput(raw_text=jd_text))
        print(f"  SUCCESS: role_title={result.role_title}")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")

asyncio.run(main())
