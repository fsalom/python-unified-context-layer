"""Mapper between domain entities and Django models"""
from typing import Optional
from datetime import datetime

from domain.entities.project_context import (
    ProjectContext,
    DomainContext,
    AISession,
    ContextQuery,
    ContextResponse,
    ProjectMetadata
)
from .models import (
    ProjectContextDBO,
    DomainContextDBO,
    AISessionDBO,
    ContextQueryDBO,
    ContextResponseDBO
)


class ContextMapper:
    """Maps between domain entities and Django models"""

    # Project Context mappings

    async def entity_to_dbo(self, entity: ProjectContext) -> ProjectContextDBO:
        """Convert ProjectContext entity to Django model"""
        return ProjectContextDBO(
            id=entity.id,
            name=entity.project_metadata.name,
            description=entity.project_metadata.description,
            version=entity.project_metadata.version,
            repository_url=entity.project_metadata.repository_url,
            technologies=entity.project_metadata.technologies,
            team_members=entity.project_metadata.team_members,
            documentation_urls=entity.project_metadata.documentation_urls,
            global_context=entity.global_context,
            created_at=entity.created_at,
            last_updated=entity.last_updated
        )

    async def dbo_to_entity(self, dbo: ProjectContextDBO) -> ProjectContext:
        """Convert Django model to ProjectContext entity"""
        metadata = ProjectMetadata(
            name=dbo.name,
            description=dbo.description,
            version=dbo.version,
            repository_url=dbo.repository_url,
            technologies=dbo.technologies,
            team_members=dbo.team_members,
            documentation_urls=dbo.documentation_urls
        )

        return ProjectContext(
            id=str(dbo.id),
            project_metadata=metadata,
            global_context=dbo.global_context,
            created_at=dbo.created_at,
            last_updated=dbo.last_updated
        )

    async def update_dbo_from_entity(
        self,
        dbo: ProjectContextDBO,
        entity: ProjectContext
    ) -> ProjectContextDBO:
        """Update Django model from entity"""
        dbo.name = entity.project_metadata.name
        dbo.description = entity.project_metadata.description
        dbo.version = entity.project_metadata.version
        dbo.repository_url = entity.project_metadata.repository_url
        dbo.technologies = entity.project_metadata.technologies
        dbo.team_members = entity.project_metadata.team_members
        dbo.documentation_urls = entity.project_metadata.documentation_urls
        dbo.global_context = entity.global_context
        dbo.last_updated = entity.last_updated
        return dbo

    # Domain Context mappings

    async def domain_entity_to_dbo(
        self,
        entity: DomainContext,
        project_dbo: ProjectContextDBO
    ) -> DomainContextDBO:
        """Convert DomainContext entity to Django model"""
        return DomainContextDBO(
            id=entity.id,
            project=project_dbo,
            domain_type=entity.domain_type,
            technologies=entity.technologies,
            file_patterns=entity.file_patterns,
            key_files=entity.key_files,
            apis=entity.apis,
            dependencies=entity.dependencies,
            conventions=entity.conventions,
            metadata=entity.metadata,
            last_updated=entity.last_updated
        )

    async def domain_dbo_to_entity(self, dbo: DomainContextDBO) -> DomainContext:
        """Convert Django model to DomainContext entity"""
        return DomainContext(
            id=str(dbo.id),
            domain_type=dbo.domain_type,
            technologies=dbo.technologies,
            file_patterns=dbo.file_patterns,
            key_files=dbo.key_files,
            apis=dbo.apis,
            dependencies=dbo.dependencies,
            conventions=dbo.conventions,
            metadata=dbo.metadata,
            last_updated=dbo.last_updated
        )

    async def update_domain_dbo_from_entity(
        self,
        dbo: DomainContextDBO,
        entity: DomainContext
    ) -> DomainContextDBO:
        """Update Django model from entity"""
        dbo.domain_type = entity.domain_type
        dbo.technologies = entity.technologies
        dbo.file_patterns = entity.file_patterns
        dbo.key_files = entity.key_files
        dbo.apis = entity.apis
        dbo.dependencies = entity.dependencies
        dbo.conventions = entity.conventions
        dbo.metadata = entity.metadata
        dbo.last_updated = entity.last_updated
        return dbo

    # AI Session mappings

    async def session_entity_to_dbo(
        self,
        entity: AISession,
        project_dbo: ProjectContextDBO
    ) -> AISessionDBO:
        """Convert AISession entity to Django model"""
        return AISessionDBO(
            id=entity.id,
            project=project_dbo,
            ai_type=entity.ai_type,
            session_start=entity.session_start,
            session_end=entity.session_end,
            domains_accessed=entity.domains_accessed,
            queries_count=entity.queries_count,
            last_query=entity.last_query,
            context_hash=entity.context_hash,
            metadata=entity.metadata
        )

    async def session_dbo_to_entity(self, dbo: AISessionDBO) -> AISession:
        """Convert Django model to AISession entity"""
        return AISession(
            id=str(dbo.id),
            ai_type=dbo.ai_type,
            session_start=dbo.session_start,
            session_end=dbo.session_end,
            domains_accessed=dbo.domains_accessed,
            queries_count=dbo.queries_count,
            last_query=dbo.last_query,
            context_hash=dbo.context_hash,
            metadata=dbo.metadata
        )

    async def update_session_dbo_from_entity(
        self,
        dbo: AISessionDBO,
        entity: AISession
    ) -> AISessionDBO:
        """Update Django model from entity"""
        dbo.ai_type = entity.ai_type
        dbo.session_start = entity.session_start
        dbo.session_end = entity.session_end
        dbo.domains_accessed = entity.domains_accessed
        dbo.queries_count = entity.queries_count
        dbo.last_query = entity.last_query
        dbo.context_hash = entity.context_hash
        dbo.metadata = entity.metadata
        return dbo

    # Context Query mappings

    async def query_entity_to_dbo(
        self,
        entity: ContextQuery,
        project_dbo: ProjectContextDBO,
        session_dbo: Optional[AISessionDBO] = None
    ) -> ContextQueryDBO:
        """Convert ContextQuery entity to Django model"""
        return ContextQueryDBO(
            id=entity.id,
            project=project_dbo,
            ai_session=session_dbo,
            query_text=entity.query_text,
            domains_filter=entity.domains_filter,
            response_format=entity.response_format,
            include_history=entity.include_history,
            max_results=entity.max_results,
            timestamp=entity.timestamp
        )

    async def query_dbo_to_entity(self, dbo: ContextQueryDBO) -> ContextQuery:
        """Convert Django model to ContextQuery entity"""
        return ContextQuery(
            id=str(dbo.id),
            query_text=dbo.query_text,
            domains_filter=dbo.domains_filter,
            ai_session_id=str(dbo.ai_session.id) if dbo.ai_session else None,
            timestamp=dbo.timestamp,
            response_format=dbo.response_format,
            include_history=dbo.include_history,
            max_results=dbo.max_results
        )

    # Context Response mappings

    async def response_entity_to_dbo(
        self,
        entity: ContextResponse,
        project_dbo: ProjectContextDBO,
        query_dbo: ContextQueryDBO
    ) -> ContextResponseDBO:
        """Convert ContextResponse entity to Django model"""
        return ContextResponseDBO(
            id=entity.query_id,  # Use query_id as response ID
            query=query_dbo,
            project=project_dbo,
            results=entity.results,
            domains_found=entity.domains_found,
            total_results=entity.total_results,
            processing_time_ms=entity.processing_time_ms,
            metadata=entity.metadata,
            timestamp=entity.timestamp
        )

    async def response_dbo_to_entity(self, dbo: ContextResponseDBO) -> ContextResponse:
        """Convert Django model to ContextResponse entity"""
        return ContextResponse(
            query_id=str(dbo.query.id),
            results=dbo.results,
            domains_found=dbo.domains_found,
            total_results=dbo.total_results,
            processing_time_ms=dbo.processing_time_ms,
            metadata=dbo.metadata,
            timestamp=dbo.timestamp
        )