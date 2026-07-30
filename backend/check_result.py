"""Check the latest analysis result from the API."""
import asyncio
import httpx

async def check():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Login
        r = await client.post("/api/v1/auth/login", json={"email": "test@gmail.com", "password": "Test@123"})
        if r.status_code != 200:
            print(f"Login failed: {r.status_code} {r.text}")
            return
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get history
        r = await client.get("/api/v1/analysis/history", headers=headers)
        if r.status_code != 200:
            print(f"History failed: {r.status_code}")
            return

        runs = r.json()
        print(f"Total runs: {len(runs)}")
        if not runs:
            print("No runs found")
            return

        latest = runs[-1]
        run_id = latest.get("run_id")
        print(f"Latest run_id: {run_id}")
        print(f"Status: {latest.get('status')}")

        # Get full result
        r2 = await client.get(f"/api/v1/analysis/{run_id}", headers=headers)
        data = r2.json()
        print(f"Full status: {data.get('status')}")
        print(f"pass1_score: {data.get('pass1_score')}")
        print(f"pass2_score: {data.get('pass2_score')}")
        print(f"parsed_resume present: {data.get('parsed_resume') is not None}")
        print(f"parsed_jd present: {data.get('parsed_jd') is not None}")
        print(f"gap_report present: {data.get('gap_report') is not None}")
        print(f"tailored_resume present: {data.get('tailored_resume') is not None}")
        print(f"cover_letter present: {data.get('cover_letter') is not None}")
        print(f"tokens used: {data.get('total_tokens_used')}")

asyncio.run(check())
