#!/usr/bin/env python3
"""
Comprehensive API endpoint test for GIMS backend.
Run this after starting the backend server.

Usage:
    cd gims/backend
    PYTHONPATH="F:\Anterndata\Hackathon\gims\backend" venv/Scripts/python.exe ..\..\tests\backend\test_api_endpoints.py
"""

import asyncio
import json
import uuid
import httpx

BASE_URL = "http://localhost:8080"
DEMO_USER_ID = "15fbd066-510b-4794-817b-ea111215bbff"


async def test_endpoint(client, method, path, expected_status, body=None, params=None, description=""):
    """Test a single endpoint and print result."""
    try:
        if method == "GET":
            r = await client.get(f"{BASE_URL}{path}", params=params)
        elif method == "POST":
            r = await client.post(f"{BASE_URL}{path}", json=body, params=params)
        elif method == "PUT":
            r = await client.put(f"{BASE_URL}{path}", json=body)
        elif method == "DELETE":
            r = await client.delete(f"{BASE_URL}{path}")
        else:
            r = await client.request(method, f"{BASE_URL}{path}", json=body)

        ok = r.status_code == expected_status
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {method} {path} -> {r.status_code} (expected {expected_status})")
        if not ok:
            print(f"       Response: {r.text[:200]}")
        return ok, r
    except Exception as e:
        print(f"  [FAIL] {method} {path} -> Exception: {e}")
        return False, None


async def main():
    print("=" * 60)
    print("GIMS API Endpoint Smoke Test")
    print("=" * 60)
    print()

    async with httpx.AsyncClient(timeout=30.0) as client:
        all_passed = 0
        all_failed = 0

        # ─── Health & Root ───
        print("Health & Root")
        ok, _ = await test_endpoint(client, "GET", "/health", 200, description="Health check")
        all_passed += ok
        all_failed += not ok
        ok, _ = await test_endpoint(client, "GET", "/", 200, description="Root")
        all_passed += ok
        all_failed += not ok
        print()

        # ─── Chat Endpoints ───
        print("Chat Endpoints")
        ok, r = await test_endpoint(client, "POST", "/api/v1/chat/conversations", 200,
                                    body={"user_id": DEMO_USER_ID, "memory_consent": True},
                                    description="Create conversation")
        all_passed += ok
        all_failed += not ok
        conv_id = None
        if ok and r:
            conv_id = r.json().get("conversation_id")

        ok, _ = await test_endpoint(client, "GET", "/api/v1/chat/conversations", 200,
                                    params={"user_id": DEMO_USER_ID},
                                    description="List conversations")
        all_passed += ok
        all_failed += not ok

        if conv_id:
            ok, _ = await test_endpoint(client, "GET", f"/api/v1/chat/conversations/{conv_id}/messages", 200,
                                        description="Get conversation messages")
            all_passed += ok
            all_failed += not ok

            ok, r_msg = await test_endpoint(client, "POST", "/api/v1/chat", 200,
                                            body={"message": "I love hiking", "user_id": DEMO_USER_ID,
                                                  "conversation_id": conv_id, "memory_consent": True},
                                            description="Send chat message")
            all_passed += ok
            all_failed += not ok

            ok, _ = await test_endpoint(client, "DELETE", f"/api/v1/chat/conversations/{conv_id}", 200,
                                        description="Delete conversation")
            all_passed += ok
            all_failed += not ok
        else:
            print("  [SKIP] Skipping conversation-dependent tests (create failed)")
        print()

        # ─── Memory Endpoints ───
        print("Memory Endpoints")
        ok, _ = await test_endpoint(client, "GET", "/api/v1/memories", 200,
                                    params={"user_id": DEMO_USER_ID, "limit": 5},
                                    description="List memories")
        all_passed += ok
        all_failed += not ok

        ok, r_mem = await test_endpoint(client, "POST", "/api/v1/memories", 201,
                                        body={"user_id": DEMO_USER_ID, "content": "API test memory",
                                              "memory_type": "semantic"},
                                        description="Create memory")
        all_passed += ok
        all_failed += not ok
        mem_id = None
        if ok and r_mem:
            mem_id = r_mem.json().get("id")

        ok, _ = await test_endpoint(client, "GET", "/api/v1/memories/stats", 200,
                                    params={"user_id": DEMO_USER_ID},
                                    description="Memory stats")
        all_passed += ok
        all_failed += not ok

        if mem_id:
            ok, _ = await test_endpoint(client, "GET", f"/api/v1/memories/{mem_id}", 200,
                                        description="Get single memory")
            all_passed += ok
            all_failed += not ok

            ok, _ = await test_endpoint(client, "PUT", f"/api/v1/memories/{mem_id}", 200,
                                        body={"content": "Updated via API"},
                                        description="Update memory")
            all_passed += ok
            all_failed += not ok

            ok, _ = await test_endpoint(client, "DELETE", f"/api/v1/memories/{mem_id}", 204,
                                        description="Delete memory")
            all_passed += ok
            all_failed += not ok
        else:
            print("  [SKIP] Skipping memory-dependent tests (create failed)")
        print()

        # ─── HITL Endpoints ───
        print("HITL Endpoints")
        ok, _ = await test_endpoint(client, "GET", "/api/v1/hitl/queue", 200,
                                    description="HITL queue")
        all_passed += ok
        all_failed += not ok
        print()

        # ─── Audit Endpoints ───
        print("Audit Endpoints")
        ok, _ = await test_endpoint(client, "GET", "/api/v1/audit", 200,
                                    params={"limit": 10},
                                    description="Audit logs")
        all_passed += ok
        all_failed += not ok
        print()

        # ─── Metrics Endpoints ───
        print("Metrics Endpoints")
        ok, _ = await test_endpoint(client, "GET", "/api/v1/metrics", 200,
                                    description="System metrics")
        all_passed += ok
        all_failed += not ok
        print()

    # ─── Summary ───
    print("=" * 60)
    print(f"Results: {all_passed} passed, {all_failed} failed")
    if all_failed == 0:
        print("All endpoints are working correctly!")
    else:
        print(f"{all_failed} endpoint(s) failed — check output above.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
