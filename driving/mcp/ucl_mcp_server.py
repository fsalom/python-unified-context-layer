"""MCP Server for Unified Context Layer"""
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from fastapi_mcp import MCPServer, Tool, Resource
import httpx
import json
import os


@dataclass
class UCLConfig:
    """Configuration for UCL MCP integration"""
    ucl_api_base: str = "http://localhost:8002/api/v1/ucl"
    project_id: str = ""
    platform_type: str = "claude"  # or "chatgpt", "copilot", etc.
    api_key: Optional[str] = None


class UCLMCPServer:
    """MCP Server for Unified Context Layer"""

    def __init__(self, config: UCLConfig):
        self.config = config
        self.server = MCPServer("ucl-context-server")
        self._setup_tools()
        self._setup_resources()

    def _setup_tools(self):
        """Setup MCP tools for context operations"""

        @self.server.tool(
            name="query_project_context",
            description="Query project context with hierarchy (global + platform + domains)"
        )
        async def query_project_context(
            query: str,
            include_global: bool = True,
            include_platform: bool = True,
            include_domains: bool = True,
            domains_filter: Optional[List[str]] = None,
            max_results: int = 50
        ) -> Dict[str, Any]:
            """Query project context with all hierarchy levels"""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.ucl_api_base}/projects/{self.config.project_id}/query-hierarchy",
                    json={
                        "query_text": query,
                        "platform_type": self.config.platform_type,
                        "include_global": include_global,
                        "include_platform": include_platform,
                        "include_domains": include_domains,
                        "domains_filter": domains_filter,
                        "max_results": max_results
                    },
                    headers=self._get_headers()
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"Failed to query context: {response.text}"}

        @self.server.tool(
            name="get_global_context",
            description="Get shared global context for the project"
        )
        async def get_global_context() -> Dict[str, Any]:
            """Get global context shared across all AI platforms"""

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.ucl_api_base}/projects/{self.config.project_id}/global-context",
                    headers=self._get_headers()
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"Failed to get global context: {response.text}"}

        @self.server.tool(
            name="get_my_platform_context",
            description="Get my platform-specific context and preferences"
        )
        async def get_my_platform_context() -> Dict[str, Any]:
            """Get platform-specific context for this AI"""

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.ucl_api_base}/projects/{self.config.project_id}/platform-contexts/{self.config.platform_type}",
                    headers=self._get_headers()
                )

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    # Create platform context if it doesn't exist
                    return await self._create_platform_context()
                else:
                    return {"error": f"Failed to get platform context: {response.text}"}

        @self.server.tool(
            name="update_my_preferences",
            description="Update my learned preferences based on user interactions"
        )
        async def update_my_preferences(
            learned_preferences: Dict[str, Any],
            custom_prompts: Optional[List[str]] = None,
            platform_conventions: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            """Update platform-specific preferences and learning"""

            # First get my context to get the context_id
            platform_context = await get_my_platform_context()
            if "error" in platform_context:
                return platform_context

            context_id = platform_context["id"]

            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.config.ucl_api_base}/platform-contexts/{context_id}",
                    json={
                        "learned_preferences": learned_preferences,
                        "custom_prompts": custom_prompts,
                        "platform_conventions": platform_conventions
                    },
                    headers=self._get_headers()
                )

                if response.status_code == 200:
                    return {"success": True, "message": "Preferences updated successfully"}
                else:
                    return {"error": f"Failed to update preferences: {response.text}"}

        @self.server.tool(
            name="log_interaction",
            description="Log a successful interaction for learning purposes"
        )
        async def log_interaction(
            interaction_type: str,
            content: Dict[str, Any],
            metadata: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            """Log an interaction to platform history"""

            # Get my context first
            platform_context = await get_my_platform_context()
            if "error" in platform_context:
                return platform_context

            context_id = platform_context["id"]

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.ucl_api_base}/platform-contexts/{context_id}/interactions",
                    json={
                        "interaction_type": interaction_type,
                        "content": content,
                        "metadata": metadata or {}
                    },
                    headers=self._get_headers()
                )

                if response.status_code == 200:
                    return {"success": True, "message": "Interaction logged successfully"}
                else:
                    return {"error": f"Failed to log interaction: {response.text}"}

        @self.server.tool(
            name="contribute_to_global_context",
            description="Share useful insights with other AI platforms"
        )
        async def contribute_to_global_context(
            insights: Dict[str, Any],
            confidence_score: float = 1.0,
            metadata: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            """Contribute insights to shared global context"""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.ucl_api_base}/projects/{self.config.project_id}/global-context/merge-insights",
                    json={
                        "insights": insights,
                        "source_platform": self.config.platform_type,
                        "confidence_score": confidence_score,
                        "metadata": metadata or {}
                    },
                    headers=self._get_headers()
                )

                if response.status_code == 200:
                    return {"success": True, "message": "Insights contributed successfully"}
                else:
                    return {"error": f"Failed to contribute insights: {response.text}"}

    def _setup_resources(self):
        """Setup MCP resources for static context data"""

        @self.server.resource(
            uri="ucl://project/architecture",
            name="Project Architecture",
            description="Current project architecture and patterns"
        )
        async def get_project_architecture() -> str:
            """Get project architecture from global context"""
            global_context = await self._get_global_context_direct()

            if "error" in global_context:
                return "Error loading project architecture"

            architecture = global_context.get("shared_knowledge", {}).get("architecture", {})
            conventions = global_context.get("shared_conventions", {})
            patterns = global_context.get("common_patterns", [])

            return f"""# Project Architecture

## Architecture Pattern
{json.dumps(architecture, indent=2)}

## Conventions
{json.dumps(conventions, indent=2)}

## Common Patterns
{chr(10).join([f"- {pattern}" for pattern in patterns])}
"""

        @self.server.resource(
            uri="ucl://platform/preferences",
            name="My Platform Preferences",
            description="My learned preferences and conventions"
        )
        async def get_my_preferences() -> str:
            """Get my platform-specific preferences"""
            platform_context = await self._get_platform_context_direct()

            if "error" in platform_context:
                return "Error loading platform preferences"

            preferences = platform_context.get("learned_preferences", {})
            prompts = platform_context.get("custom_prompts", [])
            conventions = platform_context.get("platform_conventions", {})

            return f"""# My Platform Preferences ({self.config.platform_type})

## Learned Preferences
{json.dumps(preferences, indent=2)}

## Custom Prompts
{chr(10).join([f"- {prompt}" for prompt in prompts])}

## Platform Conventions
{json.dumps(conventions, indent=2)}
"""

    async def _create_platform_context(self) -> Dict[str, Any]:
        """Create initial platform context"""
        default_context = {
            "platform_type": self.config.platform_type,
            "platform_specific_data": {},
            "learned_preferences": {},
            "custom_prompts": [],
            "platform_conventions": {}
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config.ucl_api_base}/projects/{self.config.project_id}/platform-contexts",
                json=default_context,
                headers=self._get_headers()
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Failed to create platform context: {response.text}"}

    async def _get_global_context_direct(self) -> Dict[str, Any]:
        """Direct call to get global context"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.config.ucl_api_base}/projects/{self.config.project_id}/global-context",
                headers=self._get_headers()
            )
            return response.json() if response.status_code == 200 else {"error": response.text}

    async def _get_platform_context_direct(self) -> Dict[str, Any]:
        """Direct call to get platform context"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.config.ucl_api_base}/projects/{self.config.project_id}/platform-contexts/{self.config.platform_type}",
                headers=self._get_headers()
            )
            return response.json() if response.status_code == 200 else {"error": response.text}

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    async def run(self, host: str = "localhost", port: int = 8100):
        """Run the MCP server"""
        await self.server.run(host=host, port=port)


# Configuration and startup
async def main():
    config = UCLConfig(
        project_id=os.getenv("UCL_PROJECT_ID", "your-project-id"),
        platform_type=os.getenv("PLATFORM_TYPE", "claude"),
        api_key=os.getenv("UCL_API_KEY")
    )

    server = UCLMCPServer(config)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())