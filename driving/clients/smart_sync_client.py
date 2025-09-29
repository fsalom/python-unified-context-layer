"""Smart Synchronizing Client for UCL"""
import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
import websockets
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SyncState:
    """Tracks synchronization state"""
    last_sync: datetime = field(default_factory=datetime.utcnow)
    global_context_version: int = 0
    platform_context_version: int = 0
    domain_context_versions: Dict[str, int] = field(default_factory=dict)
    pending_updates: List[Dict[str, Any]] = field(default_factory=list)
    is_online: bool = True


class SmartSyncClient:
    """
    Intelligent client that automatically keeps all AI platforms
    synchronized with the latest context
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8002/api/v1/ucl",
        websocket_url: str = "ws://localhost:8002/api/v1/ucl/ws",
        project_id: str = "",
        platform_type: str = "claude",
        api_key: Optional[str] = None
    ):
        self.base_url = base_url
        self.websocket_url = websocket_url
        self.project_id = project_id
        self.platform_type = platform_type
        self.api_key = api_key

        # Sync state
        self.sync_state = SyncState()
        self.local_cache: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, datetime] = {}

        # Event handlers
        self.on_global_context_updated: Optional[Callable] = None
        self.on_platform_context_updated: Optional[Callable] = None
        self.on_domain_context_updated: Optional[Callable] = None
        self.on_insights_received: Optional[Callable] = None
        self.on_sync_completed: Optional[Callable] = None

        # Background tasks
        self._sync_task: Optional[asyncio.Task] = None
        self._websocket_task: Optional[asyncio.Task] = None
        self._websocket: Optional[websockets.WebSocketServerProtocol] = None
        self._is_running = False

        # Configuration
        self.sync_interval = 30  # seconds
        self.cache_ttl = 300  # 5 minutes
        self.auto_contribute_insights = True
        self.offline_mode = False

    async def start(self):
        """Start the smart sync client"""
        if self._is_running:
            return

        self._is_running = True

        # Start background tasks
        self._sync_task = asyncio.create_task(self._sync_loop())
        self._websocket_task = asyncio.create_task(self._websocket_loop())

        # Initial sync
        await self._perform_full_sync()

        logger.info(f"Smart sync client started for {self.platform_type}")

    async def stop(self):
        """Stop the smart sync client"""
        self._is_running = False

        # Cancel background tasks
        for task in [self._sync_task, self._websocket_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Close websocket
        if self._websocket:
            await self._websocket.close()

        logger.info("Smart sync client stopped")

    # Context Access Methods (with automatic sync)

    async def get_context_for_query(
        self,
        query: str,
        include_global: bool = True,
        include_platform: bool = True,
        include_domains: bool = True,
        domains_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get context for a query with automatic freshness checking"""

        # Check if we need to sync first
        if await self._needs_sync():
            await self._perform_incremental_sync()

        # Build context from cache
        context = {
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "results": []
        }

        if include_global:
            global_context = await self._get_cached_global_context()
            if global_context:
                context["results"].extend(self._search_in_context(global_context, query, "global"))

        if include_platform:
            platform_context = await self._get_cached_platform_context()
            if platform_context:
                context["results"].extend(self._search_in_context(platform_context, query, "platform"))

        if include_domains:
            domain_contexts = await self._get_cached_domain_contexts(domains_filter)
            for domain_type, domain_context in domain_contexts.items():
                context["results"].extend(self._search_in_context(domain_context, query, f"domain:{domain_type}"))

        # Sort by relevance
        context["results"].sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        return context

    async def update_my_preferences(
        self,
        preferences: Dict[str, Any],
        contribute_insights: bool = None
    ) -> bool:
        """Update platform preferences with automatic insight contribution"""

        if contribute_insights is None:
            contribute_insights = self.auto_contribute_insights

        success = await self._update_platform_context({
            "learned_preferences": preferences,
            "last_updated": datetime.utcnow().isoformat()
        })

        if success and contribute_insights:
            # Extract and contribute valuable insights
            insights = await self._extract_insights_from_preferences(preferences)
            if insights:
                await self._contribute_insights(insights)

        return success

    async def log_successful_interaction(
        self,
        query: str,
        response: str,
        user_feedback: Dict[str, Any] = None
    ):
        """Log a successful interaction for learning"""

        interaction = {
            "type": "successful_interaction",
            "query": query,
            "response_length": len(response),
            "timestamp": datetime.utcnow().isoformat(),
            "platform": self.platform_type,
            "user_feedback": user_feedback or {}
        }

        # Update platform context with interaction
        await self._add_to_platform_history(interaction)

        # Extract patterns for potential sharing
        if self.auto_contribute_insights:
            patterns = await self._extract_patterns_from_interaction(query, response, user_feedback)
            if patterns:
                await self._contribute_insights({"successful_patterns": patterns})

    # Cache Management

    async def _get_cached_global_context(self) -> Optional[Dict[str, Any]]:
        """Get global context from cache or fetch if stale"""
        cache_key = f"global:{self.project_id}"

        if self._is_cache_fresh(cache_key):
            return self.local_cache.get(cache_key)

        # Fetch fresh data
        global_context = await self._fetch_global_context()
        if global_context:
            self._update_cache(cache_key, global_context)

        return global_context

    async def _get_cached_platform_context(self) -> Optional[Dict[str, Any]]:
        """Get platform context from cache or fetch if stale"""
        cache_key = f"platform:{self.project_id}:{self.platform_type}"

        if self._is_cache_fresh(cache_key):
            return self.local_cache.get(cache_key)

        # Fetch fresh data
        platform_context = await self._fetch_platform_context()
        if platform_context:
            self._update_cache(cache_key, platform_context)

        return platform_context

    async def _get_cached_domain_contexts(
        self,
        domains_filter: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Get domain contexts from cache or fetch if stale"""
        contexts = {}

        # If no filter, get all available domains
        if not domains_filter:
            domains_filter = await self._get_available_domains()

        for domain in domains_filter:
            cache_key = f"domain:{self.project_id}:{domain}"

            if self._is_cache_fresh(cache_key):
                cached = self.local_cache.get(cache_key)
                if cached:
                    contexts[domain] = cached
            else:
                # Fetch fresh data
                domain_context = await self._fetch_domain_context(domain)
                if domain_context:
                    self._update_cache(cache_key, domain_context)
                    contexts[domain] = domain_context

        return contexts

    def _is_cache_fresh(self, cache_key: str) -> bool:
        """Check if cache entry is still fresh"""
        if cache_key not in self.cache_timestamps:
            return False

        age = datetime.utcnow() - self.cache_timestamps[cache_key]
        return age.total_seconds() < self.cache_ttl

    def _update_cache(self, cache_key: str, data: Dict[str, Any]):
        """Update cache entry"""
        self.local_cache[cache_key] = data
        self.cache_timestamps[cache_key] = datetime.utcnow()

    def _invalidate_cache(self, pattern: str = None):
        """Invalidate cache entries"""
        if pattern:
            keys_to_remove = [k for k in self.local_cache.keys() if pattern in k]
            for key in keys_to_remove:
                self.local_cache.pop(key, None)
                self.cache_timestamps.pop(key, None)
        else:
            self.local_cache.clear()
            self.cache_timestamps.clear()

    # Synchronization Logic

    async def _sync_loop(self):
        """Background synchronization loop"""
        while self._is_running:
            try:
                if not self.offline_mode:
                    if await self._needs_sync():
                        await self._perform_incremental_sync()

                    # Process pending updates
                    if self.sync_state.pending_updates:
                        await self._process_pending_updates()

                await asyncio.sleep(self.sync_interval)

            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
                await asyncio.sleep(10)

    async def _websocket_loop(self):
        """WebSocket connection for real-time updates"""
        while self._is_running:
            try:
                if not self.offline_mode:
                    url = f"{self.websocket_url}/projects/{self.project_id}/stream"
                    async with websockets.connect(url) as websocket:
                        self._websocket = websocket
                        self.sync_state.is_online = True

                        async for message in websocket:
                            await self._handle_websocket_message(json.loads(message))

            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.sync_state.is_online = False
                await asyncio.sleep(5)

    async def _handle_websocket_message(self, message: Dict[str, Any]):
        """Handle real-time updates from WebSocket"""
        event_type = message.get("type")

        if event_type == "global_context_updated":
            await self._handle_global_context_update(message)
        elif event_type == "platform_context_updated":
            await self._handle_platform_context_update(message)
        elif event_type == "domain_context_updated":
            await self._handle_domain_context_update(message)
        elif event_type == "new_insights_available":
            await self._handle_new_insights(message)

    async def _handle_global_context_update(self, message: Dict[str, Any]):
        """Handle global context update"""
        # Invalidate global context cache
        self._invalidate_cache("global:")

        # Fetch fresh global context
        await self._get_cached_global_context()

        # Notify handler
        if self.on_global_context_updated:
            await self.on_global_context_updated(message["changes"])

        logger.debug("Global context updated and cache refreshed")

    async def _handle_platform_context_update(self, message: Dict[str, Any]):
        """Handle platform context update"""
        platform_type = message.get("platform_type")

        # Only invalidate if it's another platform (learning opportunity)
        if platform_type != self.platform_type:
            # Extract insights from other platform's changes
            if self.auto_contribute_insights:
                changes = message.get("changes", {})
                insights = await self._extract_cross_platform_insights(changes, platform_type)
                if insights:
                    # Store as potential improvements
                    await self._store_improvement_suggestions(insights, platform_type)

        # Notify handler
        if self.on_platform_context_updated:
            await self.on_platform_context_updated(message["changes"], platform_type)

    async def _handle_domain_context_update(self, message: Dict[str, Any]):
        """Handle domain context update"""
        domain_type = message.get("domain_type")

        # Invalidate domain cache
        self._invalidate_cache(f"domain:{self.project_id}:{domain_type}")

        # Notify handler
        if self.on_domain_context_updated:
            await self.on_domain_context_updated(message["changes"], domain_type)

        logger.debug(f"Domain context updated: {domain_type}")

    async def _handle_new_insights(self, message: Dict[str, Any]):
        """Handle new insights from other platforms"""
        insights = message.get("insights", {})
        source_platform = message.get("source_platform")

        # Apply relevant insights to our platform context
        applicable_insights = await self._filter_applicable_insights(insights, source_platform)

        if applicable_insights:
            await self._apply_insights_to_context(applicable_insights)

            # Notify handler
            if self.on_insights_received:
                await self.on_insights_received(applicable_insights, source_platform)

        logger.debug(f"Received insights from {source_platform}")

    async def _needs_sync(self) -> bool:
        """Check if synchronization is needed"""
        # Check time since last sync
        time_since_sync = datetime.utcnow() - self.sync_state.last_sync
        if time_since_sync.total_seconds() > self.sync_interval:
            return True

        # Check for pending updates
        if self.sync_state.pending_updates:
            return True

        # Check if we're offline and need to catch up
        if not self.sync_state.is_online:
            return True

        return False

    async def _perform_full_sync(self):
        """Perform complete synchronization"""
        logger.info("Performing full synchronization")

        try:
            # Clear cache
            self._invalidate_cache()

            # Fetch all contexts
            await self._get_cached_global_context()
            await self._get_cached_platform_context()
            await self._get_cached_domain_contexts()

            # Update sync state
            self.sync_state.last_sync = datetime.utcnow()

            # Notify completion
            if self.on_sync_completed:
                await self.on_sync_completed("full")

            logger.info("Full synchronization completed")

        except Exception as e:
            logger.error(f"Error during full sync: {e}")

    async def _perform_incremental_sync(self):
        """Perform incremental synchronization"""
        logger.debug("Performing incremental synchronization")

        try:
            # Check for version changes and update only what's needed
            # This would involve checking version numbers from the server

            # Update sync state
            self.sync_state.last_sync = datetime.utcnow()

            # Notify completion
            if self.on_sync_completed:
                await self.on_sync_completed("incremental")

        except Exception as e:
            logger.error(f"Error during incremental sync: {e}")

    # Helper Methods

    def _search_in_context(
        self,
        context: Dict[str, Any],
        query: str,
        source_type: str
    ) -> List[Dict[str, Any]]:
        """Search for query terms in context data"""
        results = []
        query_lower = query.lower()

        # Simple text search - can be enhanced with better algorithms
        for key, value in context.items():
            if isinstance(value, (str, dict, list)):
                value_str = str(value).lower()
                if query_lower in value_str:
                    results.append({
                        "type": key,
                        "source_type": source_type,
                        "content": value,
                        "relevance_score": self._calculate_relevance(query_lower, value_str),
                        "context_key": key
                    })

        return results

    def _calculate_relevance(self, query: str, content: str) -> float:
        """Calculate relevance score for search results"""
        # Simple relevance calculation - can be enhanced
        if query == content:
            return 1.0

        if query in content:
            return 0.8

        # Calculate word overlap
        query_words = set(query.split())
        content_words = set(content.split())
        overlap = len(query_words.intersection(content_words))

        if overlap > 0:
            return 0.5 + (overlap / len(query_words)) * 0.3

        return 0.1

    async def _extract_insights_from_preferences(
        self,
        preferences: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Extract shareable insights from preferences"""
        insights = {}

        # Look for general patterns that could help other platforms
        if "coding_style" in preferences:
            insights["preferred_coding_styles"] = preferences["coding_style"]

        if "successful_patterns" in preferences:
            insights["proven_patterns"] = preferences["successful_patterns"]

        if "error_resolution" in preferences:
            insights["error_solutions"] = preferences["error_resolution"]

        return insights if insights else None

    async def _extract_patterns_from_interaction(
        self,
        query: str,
        response: str,
        feedback: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Extract patterns from successful interactions"""
        if feedback.get("satisfaction", 0) < 4:  # Only from highly satisfied interactions
            return None

        patterns = {
            "query_type": self._classify_query_type(query),
            "response_style": self._analyze_response_style(response),
            "success_factors": feedback.get("what_worked", [])
        }

        return patterns

    def _classify_query_type(self, query: str) -> str:
        """Classify the type of query"""
        query_lower = query.lower()

        if any(word in query_lower for word in ["implement", "create", "build"]):
            return "implementation"
        elif any(word in query_lower for word in ["debug", "fix", "error"]):
            return "debugging"
        elif any(word in query_lower for word in ["explain", "how", "what"]):
            return "explanation"
        elif any(word in query_lower for word in ["optimize", "improve", "performance"]):
            return "optimization"
        else:
            return "general"

    def _analyze_response_style(self, response: str) -> Dict[str, Any]:
        """Analyze response characteristics"""
        return {
            "length": len(response),
            "has_code": "```" in response,
            "has_examples": "example" in response.lower(),
            "structure": "step_by_step" if any(word in response.lower() for word in ["step", "first", "then"]) else "direct"
        }

    # API Communication Methods

    async def _fetch_global_context(self) -> Optional[Dict[str, Any]]:
        """Fetch global context from API"""
        # Implementation would use httpx or similar
        # This is a placeholder
        return {}

    async def _fetch_platform_context(self) -> Optional[Dict[str, Any]]:
        """Fetch platform context from API"""
        # Implementation would use httpx or similar
        return {}

    async def _fetch_domain_context(self, domain_type: str) -> Optional[Dict[str, Any]]:
        """Fetch domain context from API"""
        # Implementation would use httpx or similar
        return {}

    async def _update_platform_context(self, updates: Dict[str, Any]) -> bool:
        """Update platform context via API"""
        # Implementation would use httpx or similar
        return True

    async def _contribute_insights(self, insights: Dict[str, Any]) -> bool:
        """Contribute insights to global context"""
        # Implementation would use httpx or similar
        return True

    async def _add_to_platform_history(self, interaction: Dict[str, Any]):
        """Add interaction to platform history"""
        # Implementation would use httpx or similar
        pass