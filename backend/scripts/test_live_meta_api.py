r"""
TerraQuant - Live Meta Model API Integration Test
Tests SAM 3.1 (Responses API), Muse Spark 1.3, and Muse Wonder 1.0 (Chat Completions)
against the real Meta Model API endpoint to verify connectivity and
response payloads before switching the full pipeline off MOCK_SAFE mode.

Usage:
    cd backend
    .venv\Scripts\python.exe scripts\test_live_meta_api.py
"""

import base64
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

API_KEY = os.getenv("MODEL_API_KEY", "")
BASE_URL = os.getenv("META_BASE_URL", "https://api.meta.ai/v1").rstrip("/")

if not API_KEY:
    print("ERROR: MODEL_API_KEY environment variable is not set!")
    sys.exit(1)

print(f"Meta Model API Base URL: {BASE_URL}")
print(f"API Key: {API_KEY[:12]}...{API_KEY[-4:]}")
print(f"{'=' * 60}")


# ── Test 1: Muse Wonder 1.0 (Chat Completions) ──────────────────────────────

def test_muse_wonder():
    print("\n--- Test 1: Muse Wonder 1.0 (Chat Completions) ---")
    try:
        import httpx

        url = f"{BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "muse-wonder-1.0",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a quantitative commodities risk analyst. Reply ONLY with valid JSON.",
                },
                {
                    "role": "user",
                    "content": (
                        "Evaluate a 50 MT cumin seed contract with 14.2% defect vs 5% SLA threshold. "
                        "Return JSON with: sla_breach (bool), penalty_usd (float), risk_level (str)."
                    ),
                },
            ],
            "max_tokens": 1500,
            "reasoning_effort": "low",
        }

        t0 = time.perf_counter()
        resp = httpx.post(url, headers=headers, json=payload, timeout=60.0)
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)

        if resp.status_code == 200:
            res = resp.json()
            choice = res["choices"][0]
            content = choice["message"].get("content")
            usage = res.get("usage", {})
            print(f"  STATUS:  SUCCESS ({latency_ms}ms)")
            print(f"  TOKENS:  prompt={usage.get('prompt_tokens')}, completion={usage.get('completion_tokens')}, total={usage.get('total_tokens')}")
            print(f"  FINISH:  {choice.get('finish_reason')}")
            print(f"  CONTENT: {content}")
            return bool(content)
        else:
            print(f"  STATUS:  HTTP {resp.status_code} ({latency_ms}ms)")
            print(f"  BODY:    {resp.text[:300]}")
            return False
    except Exception as e:
        print(f"  STATUS:  FAILED: {e}")
        return False


# ── Test 2: SAM 3.1 (Responses API) ─────────────────────────────────────────

def test_sam_3_1():
    print("\n--- Test 2: SAM 3.1 (Responses API) ---")
    try:
        import httpx

        # Read local sample image as base64 data URL
        sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public", "samples", "batch_critical_spoilage.png")
        if not os.path.exists(sample_path):
            print(f"  ERROR: Sample image not found at {sample_path}")
            return False

        with open(sample_path, "rb") as f:
            b64_img = base64.b64encode(f.read()).decode("utf-8")

        url = f"{BASE_URL}/responses"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "sam-3.1",
            "input": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Segment all visible defect regions, dark moisture clumping, and spoiled seeds.",
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:image/png;base64,{b64_img}",
                        },
                    ],
                }
            ],
        }

        t0 = time.perf_counter()
        resp = httpx.post(url, headers=headers, json=payload, timeout=60.0)
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)

        if resp.status_code == 200:
            res_json = resp.json()
            snippet = json.dumps(res_json, indent=2, default=str)[:400]
            print(f"  STATUS:  SUCCESS ({latency_ms}ms)")
            print(f"  HTTP:    {resp.status_code}")
            print(f"  RESPONSE SNIPPET:\n{snippet}...")
            return True
        else:
            print(f"  STATUS:  HTTP {resp.status_code} ({latency_ms}ms)")
            print(f"  BODY:    {resp.text[:300]}")
            return False
    except Exception as e:
        print(f"  STATUS:  FAILED: {e}")
        return False


# ── Test 3: Muse Spark 1.3 (Chat Completions) ───────────────────────────────

def test_muse_spark():
    print("\n--- Test 3: Muse Spark 1.3 (Chat Completions) ---")
    try:
        import httpx

        url = f"{BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "muse-spark-1.3",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a commodity grading expert. Reply ONLY with valid JSON.",
                },
                {
                    "role": "user",
                    "content": (
                        "Grade a 50 MT cumin seed batch with 14.2% defect area and 14.8% moisture. "
                        "Respond ONLY with valid JSON: {\"defect_pct\": 14.2, \"sla_status\": \"BREACH\", \"grade\": \"D\"}"
                    ),
                },
            ],
            "max_tokens": 1500,
            "reasoning_effort": "low",
        }

        t0 = time.perf_counter()
        resp = httpx.post(url, headers=headers, json=payload, timeout=60.0)
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)

        if resp.status_code == 200:
            res = resp.json()
            choice = res["choices"][0]
            content = choice["message"].get("content")
            usage = res.get("usage", {})
            print(f"  STATUS:  SUCCESS ({latency_ms}ms)")
            print(f"  TOKENS:  prompt={usage.get('prompt_tokens')}, completion={usage.get('completion_tokens')}, total={usage.get('total_tokens')}")
            print(f"  FINISH:  {choice.get('finish_reason')}")
            print(f"  CONTENT: {content}")
            return bool(content)
        else:
            print(f"  STATUS:  HTTP {resp.status_code} ({latency_ms}ms)")
            print(f"  BODY:    {resp.text[:300]}")
            return False
    except Exception as e:
        print(f"  STATUS:  FAILED: {e}")
        return False


# ── Main Runner ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Testing live Meta Model API connectivity for all 3 models...\n")

    r1 = test_muse_wonder()
    r2 = test_sam_3_1()
    r3 = test_muse_spark()

    print(f"\n{'=' * 60}")
    print("LIVE META MODEL API TEST SUMMARY:")
    print(f"  Muse Wonder 1.0: {'PASS' if r1 else 'FAIL'}")
    print(f"  SAM 3.1:         {'PASS' if r2 else 'FAIL'}")
    print(f"  Muse Spark 1.3:  {'PASS' if r3 else 'FAIL'}")
    print(f"{'=' * 60}")

    if all([r1, r2, r3]):
        print("\nAll live Meta Model API calls succeeded with real content!")
    else:
        print("\nSome tests failed. Inspect the logs above.")
