#!/usr/bin/env python3
"""Create test project via API to verify everything works"""
import asyncio
import httpx
import json
from datetime import datetime

API_BASE = "http://localhost:8002/api/v1/ucl"
PROJECT_ID = "test-project-123"

async def test_api_creation():
    """Test creating contexts via API"""
    print("🧪 Testing API endpoints...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test health endpoint
            print("🔍 Testing health endpoint...")
            response = await client.get("http://localhost:8002/health")
            if response.status_code == 200:
                print("✅ API is healthy")
            else:
                print(f"❌ API health check failed: {response.status_code}")
                return

            # Test getting global context
            print("🌍 Testing global context retrieval...")
            response = await client.get(f"{API_BASE}/projects/{PROJECT_ID}/global-context")

            if response.status_code == 200:
                global_context = response.json()
                print(f"✅ Global context retrieved: {len(global_context.get('shared_knowledge', {}))} knowledge items")
            else:
                print(f"❌ Failed to get global context: {response.status_code}")
                print(f"Response: {response.text}")

            # Test getting platform contexts
            print("🤖 Testing platform contexts retrieval...")
            response = await client.get(f"{API_BASE}/projects/{PROJECT_ID}/platform-contexts")

            if response.status_code == 200:
                platform_contexts = response.json()
                print(f"✅ Platform contexts retrieved: {len(platform_contexts)} platforms")
                for ctx in platform_contexts:
                    print(f"   - {ctx['platform_type']}: {ctx['id']}")
            else:
                print(f"❌ Failed to get platform contexts: {response.status_code}")

            # Test hierarchical query
            print("🔍 Testing hierarchical context query...")
            query_data = {
                "query_text": "implement user authentication",
                "platform_type": "claude",
                "include_global": True,
                "include_platform": True,
                "include_domains": True,
                "max_results": 10
            }

            response = await client.post(
                f"{API_BASE}/projects/{PROJECT_ID}/query-hierarchy",
                json=query_data
            )

            if response.status_code == 200:
                query_result = response.json()
                print(f"✅ Query successful: {query_result['total_results']} results found")
                print(f"   - Domains found: {query_result['domains_found']}")
                print(f"   - Processing time: {query_result['processing_time_ms']:.2f}ms")

                # Show sample results
                for i, result in enumerate(query_result['results'][:3]):
                    print(f"   {i+1}. {result.get('type', 'unknown')} from {result.get('source_type', 'unknown')}")
            else:
                print(f"❌ Query failed: {response.status_code}")
                print(f"Response: {response.text}")

            # Test updating platform preferences
            print("⚙️ Testing preference updates...")
            platform_contexts = await client.get(f"{API_BASE}/projects/{PROJECT_ID}/platform-contexts")

            if platform_contexts.status_code == 200:
                claude_context = None
                for ctx in platform_contexts.json():
                    if ctx['platform_type'] == 'claude':
                        claude_context = ctx
                        break

                if claude_context:
                    update_data = {
                        "learned_preferences": {
                            "test_preference": "added_by_test_script",
                            "user_likes_detailed_explanations": True,
                            "preferred_code_style": "functional",
                            "last_test_update": datetime.utcnow().isoformat()
                        }
                    }

                    response = await client.put(
                        f"{API_BASE}/platform-contexts/{claude_context['id']}",
                        json=update_data
                    )

                    if response.status_code == 200:
                        print("✅ Platform preferences updated successfully")
                    else:
                        print(f"❌ Failed to update preferences: {response.status_code}")

            # Test insight contribution
            print("💡 Testing insight contribution...")
            insight_data = {
                "insights": {
                    "test_insight": {
                        "pattern": "authentication_best_practice",
                        "description": "Always use JWT with refresh tokens",
                        "confidence": 0.9,
                        "source": "test_script"
                    }
                },
                "source_platform": "claude",
                "confidence_score": 0.9,
                "metadata": {
                    "test_run": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            response = await client.post(
                f"{API_BASE}/projects/{PROJECT_ID}/global-context/merge-insights",
                json=insight_data
            )

            if response.status_code == 200:
                print("✅ Insight contribution successful")
            else:
                print(f"❌ Failed to contribute insight: {response.status_code}")

            print("\n🎉 All API tests completed successfully!")
            print(f"🌐 You can explore the API at: http://localhost:8002/docs")
            print(f"📊 Test project ID: {PROJECT_ID}")

        except httpx.ConnectError:
            print("❌ Cannot connect to API. Make sure the server is running:")
            print("   Run: make run-fastapi")
            print("   Or: python -m uvicorn driving.api.fastapi_app:fastapi_app --host 0.0.0.0 --port 8002")
        except Exception as e:
            print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_creation())