"""Context Repository Port for Unified Context Layer"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.entities.project_context import (
    ProjectContext,
    DomainContext,
    AISession,
    ContextQuery,
    ContextResponse
)


class ContextRepositoryPort(ABC):
    """Repository interface for project context operations"""

    @abstractmethod
    async def create_project_context(self, context: ProjectContext) -> ProjectContext:
        """Create a new project context"""
        pass

    @abstractmethod
    async def get_project_context(self, project_id: str) -> Optional[ProjectContext]:
        """Get project context by ID"""
        pass

    @abstractmethod
    async def get_project_context_by_name(self, name: str) -> Optional[ProjectContext]:
        """Get project context by project name"""
        pass

    @abstractmethod
    async def update_project_context(self, context: ProjectContext) -> ProjectContext:
        """Update existing project context"""
        pass

    @abstractmethod
    async def delete_project_context(self, project_id: str) -> bool:
        """Delete project context"""
        pass

    @abstractmethod
    async def list_project_contexts(self) -> List[ProjectContext]:
        """List all project contexts"""
        pass


class DomainContextRepositoryPort(ABC):
    """Repository interface for domain context operations"""

    @abstractmethod
    async def create_domain_context(self, domain: DomainContext, project_id: str) -> DomainContext:
        """Create domain context for a project"""
        pass

    @abstractmethod
    async def get_domain_context(self, domain_id: str) -> Optional[DomainContext]:
        """Get domain context by ID"""
        pass

    @abstractmethod
    async def get_domains_by_project(self, project_id: str) -> List[DomainContext]:
        """Get all domains for a project"""
        pass

    @abstractmethod
    async def get_domain_by_type(self, project_id: str, domain_type: str) -> Optional[DomainContext]:
        """Get domain by type for a project"""
        pass

    @abstractmethod
    async def update_domain_context(self, domain: DomainContext) -> DomainContext:
        """Update domain context"""
        pass

    @abstractmethod
    async def delete_domain_context(self, domain_id: str) -> bool:
        """Delete domain context"""
        pass

    @abstractmethod
    async def search_domains(
        self,
        project_id: str,
        query: str,
        domain_types: Optional[List[str]] = None
    ) -> List[DomainContext]:
        """Search domains by query and optionally filter by types"""
        pass


class AISessionRepositoryPort(ABC):
    """Repository interface for AI session operations"""

    @abstractmethod
    async def create_ai_session(self, session: AISession, project_id: str) -> AISession:
        """Create AI session for a project"""
        pass

    @abstractmethod
    async def get_ai_session(self, session_id: str) -> Optional[AISession]:
        """Get AI session by ID"""
        pass

    @abstractmethod
    async def get_sessions_by_project(self, project_id: str) -> List[AISession]:
        """Get all sessions for a project"""
        pass

    @abstractmethod
    async def get_active_sessions(self, project_id: str) -> List[AISession]:
        """Get active sessions for a project"""
        pass

    @abstractmethod
    async def update_ai_session(self, session: AISession) -> AISession:
        """Update AI session"""
        pass

    @abstractmethod
    async def end_ai_session(self, session_id: str) -> Optional[AISession]:
        """End AI session"""
        pass

    @abstractmethod
    async def get_sessions_by_ai_type(
        self,
        project_id: str,
        ai_type: str,
        limit: Optional[int] = None
    ) -> List[AISession]:
        """Get sessions by AI type"""
        pass


class ContextQueryRepositoryPort(ABC):
    """Repository interface for context query operations"""

    @abstractmethod
    async def save_query(self, query: ContextQuery, project_id: str) -> ContextQuery:
        """Save context query"""
        pass

    @abstractmethod
    async def save_response(self, response: ContextResponse, project_id: str) -> ContextResponse:
        """Save context response"""
        pass

    @abstractmethod
    async def get_query_history(
        self,
        project_id: str,
        ai_session_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ContextQuery]:
        """Get query history for project or session"""
        pass

    @abstractmethod
    async def get_popular_queries(
        self,
        project_id: str,
        days: int = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get most popular queries in timeframe"""
        pass

    @abstractmethod
    async def search_queries(
        self,
        project_id: str,
        search_term: str,
        limit: Optional[int] = None
    ) -> List[ContextQuery]:
        """Search queries by text"""
        pass