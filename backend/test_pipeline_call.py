"""Test the exact LLM call the pipeline makes."""
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=True)

from app.config import get_settings
from openai import AsyncAzureOpenAI


async def main():
    settings = get_settings()
    print(f"Endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
    print(f"Deployment: {settings.AZURE_OPENAI_DEPLOYMENT_NAME}")
    print(f"Key (last6): ...{settings.AZURE_OPENAI_API_KEY.get_secret_value()[-6:]}")
    print()

    client = AsyncAzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY.get_secret_value(),
        api_version=settings.AZURE_OPENAI_API_VERSION,
    )

    # Test 1: Basic call (like your working test)
    print("Test 1: Basic call (no response_format)...")
    try:
        r = await client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "Reply in JSON."},
                {"role": "user", "content": "Return {\"status\": \"ok\"}"},
            ],
        )
        print(f"  OK: {r.choices[0].message.content[:100]}")
    except Exception as e:
        print(f"  FAILED: {e}")

    # Test 2: With response_format json_object
    print("\nTest 2: With response_format=json_object...")
    try:
        r = await client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "Reply in JSON format."},
                {"role": "user", "content": "Return {\"status\": \"ok\"}"},
            ],
            response_format={"type": "json_object"},
        )
        print(f"  OK: {r.choices[0].message.content[:100]}")
    except Exception as e:
        print(f"  FAILED: {e}")

    # Test 3: With max_completion_tokens
    print("\nTest 3: With max_completion_tokens=100...")
    try:
        r = await client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[{"role": "user", "content": "Say hi"}],
            max_completion_tokens=100,
        )
        print(f"  OK: {r.choices[0].message.content[:100]}")
    except Exception as e:
        print(f"  FAILED: {e}")


asyncio.run(main())
