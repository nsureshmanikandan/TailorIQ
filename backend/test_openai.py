"""Quick test to verify Azure OpenAI credentials."""
import asyncio
from openai import AsyncAzureOpenAI
from app.config import get_settings

async def test():
    settings = get_settings()
    print(f"Endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
    print(f"Deployment: {settings.AZURE_OPENAI_DEPLOYMENT_NAME}")
    print(f"API Version: {settings.AZURE_OPENAI_API_VERSION}")
    print(f"Key (first 10): {settings.AZURE_OPENAI_API_KEY.get_secret_value()[:10]}...")
    print()

    client = AsyncAzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY.get_secret_value(),
        api_version=settings.AZURE_OPENAI_API_VERSION,
    )

    try:
        response = await client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10,
        )
        print("SUCCESS!")
        print(f"Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"FAILED: {e}")

asyncio.run(test())
