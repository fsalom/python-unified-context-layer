"""Repository implementation for Unified Context Layer"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import Q, Count
from django.utils import timezone

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
from .models import (
    ProjectContextDBO,
    DomainContextDBO,
    AISessionDBO,
    ContextQueryDBO,
    ContextResponseDBO
)
from .mapper import ContextMapper


class ContextRepository(ContextRepositoryPort):
    """Django implementation of context repository"""

    def __init__(self):
        self.mapper = ContextMapper()

    async def create_project_context(self, context: ProjectContext) -> ProjectContext:
        """Create a new project context"""
        dbo = await self.mapper.entity_to_dbo(context)
        await dbo.asave()
        return await self.mapper.dbo_to_entity(dbo)

    async def get_project_context(self, project_id: str) -> Optional[ProjectContext]:
        """Get project context by ID"""
        try:
            dbo = await ProjectContextDBO.objects.aget(id=project_id)
            return await self.mapper.dbo_to_entity(dbo)
        except ProjectContextDBO.DoesNotExist:
            return None

    async def get_project_context_by_name(self, name: str) -> Optional[ProjectContext]:
        """Get project context by project name"""
        try:
            dbo = await ProjectContextDBO.objects.aget(name=name)
            return await self.mapper.dbo_to_entity(dbo)
        except ProjectContextDBO.DoesNotExist:
            return None

    async def update_project_context(self, context: ProjectContext) -> ProjectContext:
        """Update existing project context"""
        try:
            dbo = await ProjectContextDBO.objects.aget(id=context.id)
            updated_dbo = await self.mapper.update_dbo_from_entity(dbo, context)
            await updated_dbo.asave()
            return await self.mapper.dbo_to_entity(updated_dbo)
        except ProjectContextDBO.DoesNotExist:
            raise ValueError(f"Project context {context.id} not found")

    async def delete_project_context(self, project_id: str) -> bool:
        """Delete project context"""
        try:
            dbo = await ProjectContextDBO.objects.aget(id=project_id)
            await dbo.adelete()
            return True
        except ProjectContextDBO.DoesNotExist:
            return False

    async def list_project_contexts(self) -> List[ProjectContext]:
        """List all project contexts"""
        contexts = []
        async for dbo in ProjectContextDBO.objects.all():
            entity = await self.mapper.dbo_to_entity(dbo)
            contexts.append(entity)
        return contexts


class DomainContextRepository(DomainContextRepositoryPort):
    """Django implementation of domain context repository"""

    def __init__(self):
        self.mapper = ContextMapper()

    async def create_domain_context(self, domain: DomainContext, project_id: str) -> DomainContext:
        """Create domain context for a project"""
        try:
            project_dbo = await ProjectContextDBO.objects.aget(id=project_id)
            dbo = await self.mapper.domain_entity_to_dbo(domain, project_dbo)
            await dbo.asave()
            return await self.mapper.domain_dbo_to_entity(dbo)
        except ProjectContextDBO.DoesNotExist:
            raise ValueError(f"Project {project_id} not found")

    async def get_domain_context(self, domain_id: str) -> Optional[DomainContext]:
        """Get domain context by ID"""
        try:
            dbo = await DomainContextDBO.objects.aget(id=domain_id)
            return await self.mapper.domain_dbo_to_entity(dbo)
        except DomainContextDBO.DoesNotExist:
            return None

    async def get_domains_by_project(self, project_id: str) -> List[DomainContext]:
        """Get all domains for a project"""
        domains = []
        async for dbo in DomainContextDBO.objects.filter(project_id=project_id):
            entity = await self.mapper.domain_dbo_to_entity(dbo)
            domains.append(entity)
        return domains

    async def get_domain_by_type(self, project_id: str, domain_type: str) -> Optional[DomainContext]:
        """Get domain by type for a project"""
        try:
            dbo = await DomainContextDBO.objects.aget(
                project_id=project_id,
                domain_type=domain_type
            )
            return await self.mapper.domain_dbo_to_entity(dbo)
        except DomainContextDBO.DoesNotExist:
            return None

    async def update_domain_context(self, domain: DomainContext) -> DomainContext:
        """Update domain context"""
        try:
            dbo = await DomainContextDBO.objects.aget(id=domain.id)
            updated_dbo = await self.mapper.update_domain_dbo_from_entity(dbo, domain)
            await updated_dbo.asave()
            return await self.mapper.domain_dbo_to_entity(updated_dbo)
        except DomainContextDBO.DoesNotExist:
            raise ValueError(f"Domain context {domain.id} not found")

    async def delete_domain_context(self, domain_id: str) -> bool:
        """Delete domain context"""
        try:
            dbo = await DomainContextDBO.objects.aget(id=domain_id)
            await dbo.adelete()
            return True
        except DomainContextDBO.DoesNotExist:
            return False

    async def search_domains(
        self,
        project_id: str,
        query: str,
        domain_types: Optional[List[str]] = None
    ) -> List[DomainContext]:
        """Search domains by query and optionally filter by types"""
        q_filter = Q(project_id=project_id)

        if domain_types:
            q_filter &= Q(domain_type__in=domain_types)

        # Simple text search across multiple fields
        q_filter &= (
            Q(domain_type__icontains=query) |
            Q(technologies__icontains=query) |
            Q(key_files__icontains=query)
        )

        domains = []
        async for dbo in DomainContextDBO.objects.filter(q_filter):
            entity = await self.mapper.domain_dbo_to_entity(dbo)
            domains.append(entity)
        return domains


class AISessionRepository(AISessionRepositoryPort):
    """Django implementation of AI session repository"""

    def __init__(self):
        self.mapper = ContextMapper()

    async def create_ai_session(self, session: AISession, project_id: str) -> AISession:
        """Create AI session for a project"""
        try:
            project_dbo = await ProjectContextDBO.objects.aget(id=project_id)
            dbo = await self.mapper.session_entity_to_dbo(session, project_dbo)
            await dbo.asave()
            return await self.mapper.session_dbo_to_entity(dbo)
        except ProjectContextDBO.DoesNotExist:
            raise ValueError(f"Project {project_id} not found")

    async def get_ai_session(self, session_id: str) -> Optional[AISession]:
        """Get AI session by ID"""
        try:
            dbo = await AISessionDBO.objects.aget(id=session_id)
            return await self.mapper.session_dbo_to_entity(dbo)
        except AISessionDBO.DoesNotExist:
            return None

    async def get_sessions_by_project(self, project_id: str) -> List[AISession]:
        """Get all sessions for a project"""
        sessions = []
        async for dbo in AISessionDBO.objects.filter(project_id=project_id).order_by('-session_start'):
            entity = await self.mapper.session_dbo_to_entity(dbo)
            sessions.append(entity)
        return sessions

    async def get_active_sessions(self, project_id: str) -> List[AISession]:
        """Get active sessions for a project"""
        sessions = []
        async for dbo in AISessionDBO.objects.filter(
            project_id=project_id,
            session_end__isnull=True
        ):
            entity = await self.mapper.session_dbo_to_entity(dbo)
            sessions.append(entity)
        return sessions

    async def update_ai_session(self, session: AISession) -> AISession:
        """Update AI session"""
        try:
            dbo = await AISessionDBO.objects.aget(id=session.id)
            updated_dbo = await self.mapper.update_session_dbo_from_entity(dbo, session)
            await updated_dbo.asave()
            return await self.mapper.session_dbo_to_entity(updated_dbo)
        except AISessionDBO.DoesNotExist:
            raise ValueError(f"AI session {session.id} not found")

    async def end_ai_session(self, session_id: str) -> Optional[AISession]:
        """End AI session"""
        try:
            dbo = await AISessionDBO.objects.aget(id=session_id)
            dbo.session_end = timezone.now()
            await dbo.asave()
            return await self.mapper.session_dbo_to_entity(dbo)
        except AISessionDBO.DoesNotExist:
            return None

    async def get_sessions_by_ai_type(
        self,
        project_id: str,
        ai_type: str,
        limit: Optional[int] = None
    ) -> List[AISession]:
        """Get sessions by AI type"""
        queryset = AISessionDBO.objects.filter(
            project_id=project_id,
            ai_type=ai_type
        ).order_by('-session_start')

        if limit:
            queryset = queryset[:limit]

        sessions = []
        async for dbo in queryset:
            entity = await self.mapper.session_dbo_to_entity(dbo)
            sessions.append(entity)
        return sessions


class ContextQueryRepository(ContextQueryRepositoryPort):
    """Django implementation of context query repository"""

    def __init__(self):
        self.mapper = ContextMapper()

    async def save_query(self, query: ContextQuery, project_id: str) -> ContextQuery:
        """Save context query"""
        try:
            project_dbo = await ProjectContextDBO.objects.aget(id=project_id)
            session_dbo = None
            if query.ai_session_id:
                session_dbo = await AISessionDBO.objects.aget(id=query.ai_session_id)

            dbo = await self.mapper.query_entity_to_dbo(query, project_dbo, session_dbo)
            await dbo.asave()
            return await self.mapper.query_dbo_to_entity(dbo)
        except (ProjectContextDBO.DoesNotExist, AISessionDBO.DoesNotExist) as e:
            raise ValueError(f"Related object not found: {e}")

    async def save_response(self, response: ContextResponse, project_id: str) -> ContextResponse:
        """Save context response"""
        try:
            project_dbo = await ProjectContextDBO.objects.aget(id=project_id)
            query_dbo = await ContextQueryDBO.objects.aget(id=response.query_id)

            dbo = await self.mapper.response_entity_to_dbo(response, project_dbo, query_dbo)
            await dbo.asave()
            return await self.mapper.response_dbo_to_entity(dbo)
        except (ProjectContextDBO.DoesNotExist, ContextQueryDBO.DoesNotExist) as e:
            raise ValueError(f"Related object not found: {e}")

    async def get_query_history(
        self,
        project_id: str,
        ai_session_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ContextQuery]:
        """Get query history for project or session"""
        q_filter = Q(project_id=project_id)
        if ai_session_id:
            q_filter &= Q(ai_session_id=ai_session_id)

        queryset = ContextQueryDBO.objects.filter(q_filter).order_by('-timestamp')
        if limit:
            queryset = queryset[:limit]

        queries = []
        async for dbo in queryset:
            entity = await self.mapper.query_dbo_to_entity(dbo)
            queries.append(entity)
        return queries

    async def get_popular_queries(
        self,
        project_id: str,
        days: int = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get most popular queries in timeframe"""
        cutoff_date = timezone.now() - timedelta(days=days)

        # This would be more complex in real implementation
        # For now, returning simple aggregation
        popular = []
        async for query in ContextQueryDBO.objects.filter(
            project_id=project_id,
            timestamp__gte=cutoff_date
        ).order_by('-timestamp')[:limit]:
            popular.append({
                "query_text": query.query_text,
                "count": 1,  # TODO: Implement proper counting
                "last_used": query.timestamp.isoformat()
            })

        return popular

    async def search_queries(
        self,
        project_id: str,
        search_term: str,
        limit: Optional[int] = None
    ) -> List[ContextQuery]:
        """Search queries by text"""
        queryset = ContextQueryDBO.objects.filter(
            project_id=project_id,
            query_text__icontains=search_term
        ).order_by('-timestamp')

        if limit:
            queryset = queryset[:limit]

        queries = []
        async for dbo in queryset:
            entity = await self.mapper.query_dbo_to_entity(dbo)
            queries.append(entity)
        return queries