"""Context Service for Unified Context Layer"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import hashlib

from domain.entities.project_context import (
    ProjectContext,
    DomainContext,
    AISession,
    ContextQuery,
    ContextResponse,
    ProjectMetadata,
    GlobalContext,
    PlatformContext
)
from application.ports.context_repository import (
    ContextRepositoryPort,
    DomainContextRepositoryPort,
    AISessionRepositoryPort,
    ContextQueryRepositoryPort,
    GlobalContextRepositoryPort,
    PlatformContextRepositoryPort
)
from application.ports.ai_adapter_port import VectorStorePort, IndexerPort


class ContextService:
    """Main service for managing project context"""

    def __init__(
        self,
        context_repo: ContextRepositoryPort,
        domain_repo: DomainContextRepositoryPort,
        session_repo: AISessionRepositoryPort,
        query_repo: ContextQueryRepositoryPort,
        global_context_repo: GlobalContextRepositoryPort,
        platform_context_repo: PlatformContextRepositoryPort,
        vector_store: Optional[VectorStorePort] = None,
        indexer: Optional[IndexerPort] = None
    ):
        self._context_repo = context_repo
        self._domain_repo = domain_repo
        self._session_repo = session_repo
        self._query_repo = query_repo
        self._global_context_repo = global_context_repo
        self._platform_context_repo = platform_context_repo
        self._vector_store = vector_store
        self._indexer = indexer

    async def create_project_context(
        self,
        name: str,
        description: Optional[str] = None,
        technologies: Optional[List[str]] = None,
        repository_url: Optional[str] = None
    ) -> ProjectContext:
        """Create new project context"""
        metadata = ProjectMetadata(
            name=name,
            description=description,
            technologies=technologies or [],
            repository_url=repository_url
        )

        context = ProjectContext(project_metadata=metadata)

        # Create global context for this project
        global_context = GlobalContext(
            project_id=context.id,
            shared_knowledge={
                "project_info": {
                    "name": name,
                    "description": description,
                    "technologies": technologies or [],
                    "repository_url": repository_url
                }
            }
        )
        created_global_context = await self._global_context_repo.create_global_context(global_context)
        context.global_context_id = created_global_context.id

        return await self._context_repo.create_project_context(context)

    async def get_project_context(self, project_id: str) -> Optional[ProjectContext]:
        """Get project context with all domains and sessions"""
        context = await self._context_repo.get_project_context(project_id)
        if not context:
            return None

        # Load domains
        domains = await self._domain_repo.get_domains_by_project(project_id)
        context.domains = domains

        # Load recent AI sessions
        sessions = await self._session_repo.get_sessions_by_project(project_id)
        context.ai_sessions = sessions[-50:]  # Keep last 50 sessions

        return context

    async def add_domain_context(
        self,
        project_id: str,
        domain_type: str,
        technologies: List[str],
        file_patterns: List[str],
        conventions: Optional[Dict[str, Any]] = None
    ) -> DomainContext:
        """Add or update domain context"""
        domain = DomainContext(
            domain_type=domain_type,
            technologies=technologies,
            file_patterns=file_patterns,
            conventions=conventions or {}
        )

        # Check if domain exists
        existing = await self._domain_repo.get_domain_by_type(project_id, domain_type)
        if existing:
            domain.id = existing.id
            return await self._domain_repo.update_domain_context(domain)
        else:
            return await self._domain_repo.create_domain_context(domain, project_id)

    async def query_context(
        self,
        project_id: str,
        query_text: str,
        domains_filter: Optional[List[str]] = None,
        ai_session_id: Optional[str] = None,
        response_format: str = "structured",
        include_history: bool = False,
        max_results: int = 100
    ) -> ContextResponse:
        """Query project context with hybrid search"""
        start_time = datetime.utcnow()

        # Create query object
        query = ContextQuery(
            query_text=query_text,
            domains_filter=domains_filter or [],
            ai_session_id=ai_session_id,
            response_format=response_format,
            include_history=include_history,
            max_results=max_results
        )

        # Save query for analytics
        await self._query_repo.save_query(query, project_id)

        results = []
        domains_found = []

        # 1. Search in structured domain data
        structured_results = await self._search_structured_context(
            project_id, query_text, domains_filter, max_results // 2
        )
        results.extend(structured_results)

        # 2. Search in vector store if available
        if self._vector_store:
            vector_results = await self._search_vector_context(
                project_id, query_text, domains_filter, max_results // 2
            )
            results.extend(vector_results)

        # 3. Include query history if requested
        if include_history and ai_session_id:
            history_results = await self._get_query_history_context(
                project_id, ai_session_id, limit=10
            )
            results.extend(history_results)

        # Process and deduplicate results
        processed_results = await self._process_query_results(results, response_format)
        domains_found = list(set([r.get("domain_type") for r in processed_results if r.get("domain_type")]))

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        response = ContextResponse(
            query_id=query.id,
            results=processed_results[:max_results],
            domains_found=domains_found,
            total_results=len(processed_results),
            processing_time_ms=processing_time
        )

        # Save response for analytics
        await self._query_repo.save_response(response, project_id)

        return response

    async def start_ai_session(
        self,
        project_id: str,
        ai_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AISession:
        """Start new AI session"""
        session = AISession(
            ai_type=ai_type,
            metadata=metadata or {}
        )

        return await self._session_repo.create_ai_session(session, project_id)

    async def end_ai_session(self, session_id: str) -> Optional[AISession]:
        """End AI session"""
        return await self._session_repo.end_ai_session(session_id)

    async def update_session_activity(
        self,
        session_id: str,
        query_text: str,
        domains_accessed: List[str]
    ) -> Optional[AISession]:
        """Update session with activity"""
        session = await self._session_repo.get_ai_session(session_id)
        if not session:
            return None

        session.queries_count += 1
        session.last_query = query_text
        session.domains_accessed = list(set(session.domains_accessed + domains_accessed))

        return await self._session_repo.update_ai_session(session)

    async def get_project_analytics(
        self,
        project_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get project analytics"""
        # Get query statistics
        popular_queries = await self._query_repo.get_popular_queries(project_id, days)

        # Get session statistics
        sessions = await self._session_repo.get_sessions_by_project(project_id)
        recent_sessions = [
            s for s in sessions
            if s.session_start > datetime.utcnow() - timedelta(days=days)
        ]

        # Get domain statistics
        domains = await self._domain_repo.get_domains_by_project(project_id)

        # Vector store stats if available
        vector_stats = {}
        if self._vector_store:
            vector_stats = await self._vector_store.get_project_stats(project_id)

        return {
            "queries": {
                "popular": popular_queries,
                "total_recent": len([s for s in recent_sessions if s.queries_count > 0])
            },
            "sessions": {
                "total_recent": len(recent_sessions),
                "by_ai_type": self._group_sessions_by_ai_type(recent_sessions),
                "active": len([s for s in recent_sessions if s.session_end is None])
            },
            "domains": {
                "total": len(domains),
                "types": [d.domain_type for d in domains],
                "last_updated": [d.last_updated.isoformat() for d in domains]
            },
            "vector_store": vector_stats
        }

    # Private helper methods

    async def _search_structured_context(
        self,
        project_id: str,
        query: str,
        domains_filter: Optional[List[str]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search in structured domain data"""
        domains = await self._domain_repo.search_domains(project_id, query, domains_filter)

        results = []
        for domain in domains[:limit]:
            results.append({
                "type": "domain_context",
                "domain_type": domain.domain_type,
                "technologies": domain.technologies,
                "conventions": domain.conventions,
                "key_files": domain.key_files,
                "apis": domain.apis,
                "relevance_score": 0.8,  # TODO: Implement scoring
                "source": "structured"
            })

        return results

    async def _search_vector_context(
        self,
        project_id: str,
        query: str,
        domains_filter: Optional[List[str]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search in vector store"""
        if not self._vector_store:
            return []

        similar_docs = await self._vector_store.search_similar(
            query, project_id, domains_filter, limit
        )

        results = []
        for doc in similar_docs:
            results.append({
                "type": "vector_search",
                "content": doc.get("content", ""),
                "metadata": doc.get("metadata", {}),
                "similarity_score": doc.get("similarity", 0.0),
                "source": "vector"
            })

        return results

    async def _get_query_history_context(
        self,
        project_id: str,
        session_id: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get query history context"""
        history = await self._query_repo.get_query_history(project_id, session_id, limit)

        results = []
        for query in history:
            results.append({
                "type": "query_history",
                "query_text": query.query_text,
                "domains_filter": query.domains_filter,
                "timestamp": query.timestamp.isoformat(),
                "source": "history"
            })

        return results

    async def _process_query_results(
        self,
        results: List[Dict[str, Any]],
        response_format: str
    ) -> List[Dict[str, Any]]:
        """Process and format query results"""
        # TODO: Implement deduplication, ranking, formatting
        processed = []
        seen = set()

        for result in results:
            # Simple deduplication by content hash
            content_key = self._get_result_hash(result)
            if content_key not in seen:
                seen.add(content_key)
                processed.append(result)

        # Sort by relevance/similarity score
        processed.sort(
            key=lambda x: x.get("relevance_score", x.get("similarity_score", 0)),
            reverse=True
        )

        return processed

    def _get_result_hash(self, result: Dict[str, Any]) -> str:
        """Get hash for result deduplication"""
        content = json.dumps(result, sort_keys=True, default=str)
        return hashlib.md5(content.encode()).hexdigest()

    def _group_sessions_by_ai_type(self, sessions: List[AISession]) -> Dict[str, int]:
        """Group sessions by AI type"""
        groups = {}
        for session in sessions:
            groups[session.ai_type] = groups.get(session.ai_type, 0) + 1
        return groups

    # Global Context Methods

    async def get_global_context(self, project_id: str) -> Optional[GlobalContext]:
        """Get global context for project"""
        return await self._global_context_repo.get_global_context_by_project(project_id)

    async def update_global_context(
        self,
        project_id: str,
        shared_knowledge: Optional[Dict[str, Any]] = None,
        shared_conventions: Optional[Dict[str, Any]] = None,
        common_patterns: Optional[List[str]] = None
    ) -> Optional[GlobalContext]:
        """Update global context"""
        global_context = await self._global_context_repo.get_global_context_by_project(project_id)
        if not global_context:
            return None

        if shared_knowledge:
            global_context.shared_knowledge.update(shared_knowledge)
        if shared_conventions:
            global_context.shared_conventions.update(shared_conventions)
        if common_patterns:
            global_context.common_patterns.extend(common_patterns)

        global_context.version += 1
        global_context.last_updated = datetime.utcnow()

        return await self._global_context_repo.update_global_context(global_context)

    async def merge_platform_insights_to_global(
        self,
        project_id: str,
        insights: Dict[str, Any],
        source_platform: str
    ) -> bool:
        """Merge insights from platform context to global context"""
        global_context = await self._global_context_repo.get_global_context_by_project(project_id)
        if not global_context:
            return False

        return await self._global_context_repo.merge_insights_to_global(
            global_context.id, insights, source_platform
        )

    # Platform Context Methods

    async def create_platform_context(
        self,
        project_id: str,
        platform_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PlatformContext:
        """Create platform-specific context"""
        # Get global context
        global_context = await self._global_context_repo.get_global_context_by_project(project_id)
        if not global_context:
            raise ValueError(f"No global context found for project {project_id}")

        platform_context = PlatformContext(
            platform_type=platform_type,
            project_id=project_id,
            global_context_id=global_context.id,
            platform_specific_data=metadata or {}
        )

        created_context = await self._platform_context_repo.create_platform_context(platform_context)

        # Add to project
        project_context = await self._context_repo.get_project_context(project_id)
        if project_context:
            project_context.add_platform_context(created_context.id)
            await self._context_repo.update_project_context(project_context)

        return created_context

    async def get_platform_context(
        self,
        project_id: str,
        platform_type: str
    ) -> Optional[PlatformContext]:
        """Get platform context by type"""
        return await self._platform_context_repo.get_platform_context_by_type(
            project_id, platform_type
        )

    async def update_platform_context(
        self,
        context_id: str,
        learned_preferences: Optional[Dict[str, Any]] = None,
        custom_prompts: Optional[List[str]] = None,
        platform_conventions: Optional[Dict[str, Any]] = None
    ) -> Optional[PlatformContext]:
        """Update platform context"""
        context = await self._platform_context_repo.get_platform_context(context_id)
        if not context:
            return None

        if learned_preferences:
            context.learned_preferences.update(learned_preferences)
        if custom_prompts:
            context.custom_prompts.extend(custom_prompts)
        if platform_conventions:
            context.platform_conventions.update(platform_conventions)

        context.version += 1
        context.last_updated = datetime.utcnow()

        return await self._platform_context_repo.update_platform_context(context)

    async def add_interaction_to_platform_history(
        self,
        context_id: str,
        interaction: Dict[str, Any]
    ) -> bool:
        """Add interaction to platform history"""
        interaction["timestamp"] = datetime.utcnow().isoformat()
        return await self._platform_context_repo.add_interaction_to_history(
            context_id, interaction
        )

    async def get_platform_contexts_for_project(
        self,
        project_id: str
    ) -> List[PlatformContext]:
        """Get all platform contexts for project"""
        return await self._platform_context_repo.get_platform_contexts_by_project(project_id)

    async def query_context_with_hierarchy(
        self,
        project_id: str,
        platform_type: str,
        query_text: str,
        include_global: bool = True,
        include_platform: bool = True,
        domains_filter: Optional[List[str]] = None,
        max_results: int = 100
    ) -> ContextResponse:
        """Query context with global and platform hierarchy"""
        start_time = datetime.utcnow()
        results = []

        # 1. Get platform context if requested
        if include_platform:
            platform_context = await self.get_platform_context(project_id, platform_type)
            if platform_context:
                platform_results = self._search_platform_context(
                    platform_context, query_text, max_results // 3
                )
                results.extend(platform_results)

        # 2. Get global context if requested
        if include_global:
            global_context = await self.get_global_context(project_id)
            if global_context:
                global_results = self._search_global_context(
                    global_context, query_text, max_results // 3
                )
                results.extend(global_results)

        # 3. Get domain contexts (existing functionality)
        if domains_filter or not (include_platform or include_global):
            domain_results = await self._search_structured_context(
                project_id, query_text, domains_filter, max_results // 3
            )
            results.extend(domain_results)

        # Process and deduplicate results
        processed_results = await self._process_query_results(results, "structured")
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Create and save query
        query = ContextQuery(
            query_text=query_text,
            domains_filter=domains_filter or [],
            response_format="structured",
            max_results=max_results
        )
        await self._query_repo.save_query(query, project_id)

        response = ContextResponse(
            query_id=query.id,
            results=processed_results[:max_results],
            domains_found=list(set([r.get("source_type") for r in processed_results])),
            total_results=len(processed_results),
            processing_time_ms=processing_time
        )

        await self._query_repo.save_response(response, project_id)
        return response

    def _search_platform_context(
        self,
        platform_context: PlatformContext,
        query: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search in platform-specific context"""
        results = []

        # Search in platform-specific data
        if query.lower() in str(platform_context.platform_specific_data).lower():
            results.append({
                "type": "platform_context",
                "source_type": "platform",
                "platform_type": platform_context.platform_type,
                "content": platform_context.platform_specific_data,
                "relevance_score": 0.9,
                "context_id": platform_context.id
            })

        # Search in learned preferences
        if query.lower() in str(platform_context.learned_preferences).lower():
            results.append({
                "type": "learned_preferences",
                "source_type": "platform",
                "platform_type": platform_context.platform_type,
                "content": platform_context.learned_preferences,
                "relevance_score": 0.8,
                "context_id": platform_context.id
            })

        # Search in interaction history
        for interaction in platform_context.interaction_history[-10:]:  # Last 10 interactions
            if query.lower() in str(interaction).lower():
                results.append({
                    "type": "interaction_history",
                    "source_type": "platform",
                    "platform_type": platform_context.platform_type,
                    "content": interaction,
                    "relevance_score": 0.7,
                    "context_id": platform_context.id
                })

        return results[:limit]

    def _search_global_context(
        self,
        global_context: GlobalContext,
        query: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search in global context"""
        results = []

        # Search in shared knowledge
        if query.lower() in str(global_context.shared_knowledge).lower():
            results.append({
                "type": "shared_knowledge",
                "source_type": "global",
                "content": global_context.shared_knowledge,
                "relevance_score": 0.95,
                "context_id": global_context.id
            })

        # Search in shared conventions
        if query.lower() in str(global_context.shared_conventions).lower():
            results.append({
                "type": "shared_conventions",
                "source_type": "global",
                "content": global_context.shared_conventions,
                "relevance_score": 0.9,
                "context_id": global_context.id
            })

        # Search in common patterns
        for pattern in global_context.common_patterns:
            if query.lower() in pattern.lower():
                results.append({
                    "type": "common_pattern",
                    "source_type": "global",
                    "content": pattern,
                    "relevance_score": 0.85,
                    "context_id": global_context.id
                })

        return results[:limit]