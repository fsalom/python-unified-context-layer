"""AI Orchestrator Service for Unified Context Layer"""
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
import asyncio
import json
from dataclasses import asdict

from domain.entities.project_context import AISession, ContextResponse
from application.ports.ai_adapter_port import (
    AIAdapterPort,
    AIContextRequest,
    AIContextUpdate,
    AICapabilities
)
from application.ports.context_repository import AISessionRepositoryPort
from application.services.context_service import ContextService


class AIOrchestrator:
    """Service for orchestrating multiple AI interactions with UCL"""

    def __init__(
        self,
        context_service: ContextService,
        session_repo: AISessionRepositoryPort,
        ai_adapter: AIAdapterPort
    ):
        self._context_service = context_service
        self._session_repo = session_repo
        self._ai_adapter = ai_adapter
        self._registered_ais: Dict[str, AICapabilities] = {}
        self._active_subscriptions: Dict[str, Dict[str, Any]] = {}
        self._rate_limiters: Dict[str, Dict[str, Any]] = {}

    async def register_ai(self, capabilities: AICapabilities) -> str:
        """Register AI with orchestrator"""
        ai_id = await self._ai_adapter.register_ai(capabilities)
        self._registered_ais[ai_id] = capabilities

        # Initialize rate limiter for this AI
        self._rate_limiters[ai_id] = {
            "requests": [],
            "limits": capabilities.rate_limits
        }

        return ai_id

    async def handle_ai_context_request(
        self,
        request: AIContextRequest,
        project_id: str
    ) -> ContextResponse:
        """Handle context request from AI"""
        # Check rate limits
        if not await self._check_rate_limit(request.ai_instance_id):
            raise ValueError(f"Rate limit exceeded for AI {request.ai_instance_id}")

        # Get or create AI session
        session = await self._get_or_create_session(request, project_id)

        # Process context request
        response = await self._context_service.query_context(
            project_id=project_id,
            query_text=request.query,
            domains_filter=request.domains,
            ai_session_id=session.id,
            response_format=request.response_format,
            include_history=request.include_history,
            max_results=request.max_results
        )

        # Update session activity
        await self._context_service.update_session_activity(
            session.id,
            request.query,
            request.domains
        )

        # Format response for specific AI
        formatted_response = await self._format_response_for_ai(
            response, request.ai_type, request.response_format
        )

        # Notify other subscribed AIs if relevant
        await self._notify_subscribed_ais(project_id, request.domains, response)

        return formatted_response

    async def handle_ai_context_update(
        self,
        update: AIContextUpdate,
        project_id: str
    ) -> bool:
        """Handle context update from AI"""
        # Validate session
        session = await self._session_repo.get_ai_session(update.session_id)
        if not session or session.ai_type != update.ai_type:
            raise ValueError("Invalid session or AI type mismatch")

        # Process updates
        success = True
        for update_item in update.updates:
            try:
                await self._process_context_update(
                    project_id, update.domain_type, update_item, session.id
                )
            except Exception as e:
                print(f"Error processing update: {e}")
                success = False

        # Notify subscribed AIs about changes
        if success:
            await self._broadcast_context_changes(
                project_id, [update.domain_type], update.updates
            )

        return success

    async def subscribe_ai_to_updates(
        self,
        ai_instance_id: str,
        project_id: str,
        domains: List[str]
    ) -> str:
        """Subscribe AI to real-time context updates"""
        subscription_id = await self._ai_adapter.subscribe_to_updates(
            ai_instance_id, project_id, domains
        )

        self._active_subscriptions[subscription_id] = {
            "ai_instance_id": ai_instance_id,
            "project_id": project_id,
            "domains": set(domains),
            "created_at": datetime.utcnow()
        }

        return subscription_id

    async def unsubscribe_ai_from_updates(self, subscription_id: str) -> bool:
        """Unsubscribe AI from updates"""
        success = await self._ai_adapter.unsubscribe_from_updates(subscription_id)
        if success and subscription_id in self._active_subscriptions:
            del self._active_subscriptions[subscription_id]
        return success

    async def get_ai_analytics(
        self,
        project_id: str,
        ai_type: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get analytics for AI usage"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get sessions
        if ai_type:
            sessions = await self._session_repo.get_sessions_by_ai_type(
                project_id, ai_type
            )
        else:
            sessions = await self._session_repo.get_sessions_by_project(project_id)

        recent_sessions = [
            s for s in sessions if s.session_start > cutoff_date
        ]

        # Calculate metrics
        total_queries = sum(s.queries_count for s in recent_sessions)
        active_sessions = len([s for s in recent_sessions if s.session_end is None])
        avg_session_duration = self._calculate_avg_session_duration(recent_sessions)

        # Domain usage analysis
        domain_usage = self._analyze_domain_usage(recent_sessions)

        # AI type distribution
        ai_type_usage = {}
        for session in recent_sessions:
            ai_type_usage[session.ai_type] = ai_type_usage.get(session.ai_type, 0) + 1

        return {
            "period_days": days,
            "total_sessions": len(recent_sessions),
            "active_sessions": active_sessions,
            "total_queries": total_queries,
            "avg_queries_per_session": total_queries / len(recent_sessions) if recent_sessions else 0,
            "avg_session_duration_minutes": avg_session_duration,
            "domain_usage": domain_usage,
            "ai_type_usage": ai_type_usage,
            "active_subscriptions": len(self._active_subscriptions)
        }

    async def get_collaboration_insights(
        self,
        project_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get insights about AI collaboration patterns"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        sessions = await self._session_repo.get_sessions_by_project(project_id)
        recent_sessions = [s for s in sessions if s.session_start > cutoff_date]

        # Analyze concurrent AI usage
        concurrent_usage = self._analyze_concurrent_usage(recent_sessions)

        # Analyze domain overlap
        domain_overlap = self._analyze_domain_overlap(recent_sessions)

        # Analyze handoff patterns
        handoff_patterns = self._analyze_handoff_patterns(recent_sessions)

        return {
            "concurrent_usage": concurrent_usage,
            "domain_overlap": domain_overlap,
            "handoff_patterns": handoff_patterns,
            "collaboration_score": self._calculate_collaboration_score(recent_sessions)
        }

    # Private helper methods

    async def _check_rate_limit(self, ai_instance_id: str) -> bool:
        """Check if AI is within rate limits"""
        if ai_instance_id not in self._rate_limiters:
            return True

        rate_limiter = self._rate_limiters[ai_instance_id]
        now = datetime.utcnow()

        # Clean old requests
        rate_limiter["requests"] = [
            req_time for req_time in rate_limiter["requests"]
            if now - req_time < timedelta(minutes=1)
        ]

        # Check limit
        requests_per_minute = rate_limiter["limits"].get("requests_per_minute", 60)
        if len(rate_limiter["requests"]) >= requests_per_minute:
            return False

        # Add current request
        rate_limiter["requests"].append(now)
        return True

    async def _get_or_create_session(
        self,
        request: AIContextRequest,
        project_id: str
    ) -> AISession:
        """Get existing session or create new one"""
        if request.session_id:
            session = await self._session_repo.get_ai_session(request.session_id)
            if session:
                return session

        # Create new session
        return await self._context_service.start_ai_session(
            project_id, request.ai_type, request.metadata
        )

    async def _format_response_for_ai(
        self,
        response: ContextResponse,
        ai_type: str,
        response_format: str
    ) -> ContextResponse:
        """Format response based on AI capabilities"""
        ai_capabilities = self._registered_ais.get(ai_type)
        if not ai_capabilities:
            return response

        # Adjust response based on AI capabilities
        if ai_capabilities.max_context_length:
            # Truncate results if needed
            total_length = sum(len(str(result)) for result in response.results)
            if total_length > ai_capabilities.max_context_length:
                # TODO: Implement smart truncation
                response.results = response.results[:ai_capabilities.max_context_length // 1000]

        # Format according to AI preference
        if response_format == "auto":
            response_format = ai_capabilities.preferred_format

        # TODO: Implement format-specific transformations

        return response

    async def _process_context_update(
        self,
        project_id: str,
        domain_type: str,
        update_item: Dict[str, Any],
        session_id: str
    ) -> None:
        """Process individual context update"""
        update_type = update_item.get("type")

        if update_type == "file_change":
            # Handle file changes
            pass
        elif update_type == "api_change":
            # Handle API changes
            pass
        elif update_type == "dependency_change":
            # Handle dependency changes
            pass
        # TODO: Implement specific update handlers

    async def _notify_subscribed_ais(
        self,
        project_id: str,
        domains: List[str],
        response: ContextResponse
    ) -> None:
        """Notify subscribed AIs about relevant context"""
        relevant_subscriptions = []

        for sub_id, sub_info in self._active_subscriptions.items():
            if (sub_info["project_id"] == project_id and
                any(domain in sub_info["domains"] for domain in domains)):
                relevant_subscriptions.append(sub_id)

        # TODO: Implement notification mechanism
        for sub_id in relevant_subscriptions:
            # Send notification to subscribed AI
            pass

    async def _broadcast_context_changes(
        self,
        project_id: str,
        domains: List[str],
        changes: List[Dict[str, Any]]
    ) -> None:
        """Broadcast context changes to relevant AIs"""
        # TODO: Implement broadcasting mechanism
        pass

    def _calculate_avg_session_duration(self, sessions: List[AISession]) -> float:
        """Calculate average session duration in minutes"""
        durations = []
        for session in sessions:
            if session.session_end:
                duration = (session.session_end - session.session_start).total_seconds() / 60
                durations.append(duration)

        return sum(durations) / len(durations) if durations else 0

    def _analyze_domain_usage(self, sessions: List[AISession]) -> Dict[str, int]:
        """Analyze domain usage across sessions"""
        domain_counts = {}
        for session in sessions:
            for domain in session.domains_accessed:
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
        return domain_counts

    def _analyze_concurrent_usage(self, sessions: List[AISession]) -> Dict[str, Any]:
        """Analyze concurrent AI usage patterns"""
        # TODO: Implement concurrent usage analysis
        return {"max_concurrent": 0, "avg_concurrent": 0}

    def _analyze_domain_overlap(self, sessions: List[AISession]) -> Dict[str, Any]:
        """Analyze domain overlap between AIs"""
        # TODO: Implement domain overlap analysis
        return {"overlap_score": 0}

    def _analyze_handoff_patterns(self, sessions: List[AISession]) -> Dict[str, Any]:
        """Analyze AI handoff patterns"""
        # TODO: Implement handoff pattern analysis
        return {"handoffs": []}

    def _calculate_collaboration_score(self, sessions: List[AISession]) -> float:
        """Calculate collaboration effectiveness score"""
        # TODO: Implement collaboration scoring
        return 0.0