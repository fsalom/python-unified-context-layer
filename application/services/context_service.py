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
    ProjectMetadata
)
from application.ports.context_repository import (
    ContextRepositoryPort,
    DomainContextRepositoryPort,
    AISessionRepositoryPort,
    ContextQueryRepositoryPort
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
        vector_store: Optional[VectorStorePort] = None,
        indexer: Optional[IndexerPort] = None
    ):
        self._context_repo = context_repo
        self._domain_repo = domain_repo
        self._session_repo = session_repo
        self._query_repo = query_repo
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