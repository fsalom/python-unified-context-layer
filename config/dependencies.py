"""Dependency injection configuration for UCL"""
from functools import lru_cache
from typing import Optional

from application.services.context_service import ContextService
from application.services.ai_orchestrator_service import AIOrchestrator
from application.ports.context_repository import (
    ContextRepositoryPort,
    DomainContextRepositoryPort,
    AISessionRepositoryPort,
    ContextQueryRepositoryPort
)
from application.ports.ai_adapter_port import (
    AIAdapterPort,
    VectorStorePort,
    IndexerPort
)
from driven.db.context.repository import (
    ContextRepository,
    DomainContextRepository,
    AISessionRepository,
    ContextQueryRepository
)


# Repository Dependencies

@lru_cache()
def get_context_repository() -> ContextRepositoryPort:
    """Get context repository instance"""
    return ContextRepository()


@lru_cache()
def get_domain_repository() -> DomainContextRepositoryPort:
    """Get domain repository instance"""
    return DomainContextRepository()


@lru_cache()
def get_session_repository() -> AISessionRepositoryPort:
    """Get AI session repository instance"""
    return AISessionRepository()


@lru_cache()
def get_query_repository() -> ContextQueryRepositoryPort:
    """Get query repository instance"""
    return ContextQueryRepository()


@lru_cache()
def get_vector_store() -> Optional[VectorStorePort]:
    """Get vector store instance (optional)"""
    # TODO: Implement ChromaDB vector store
    return None


@lru_cache()
def get_indexer() -> Optional[IndexerPort]:
    """Get indexer instance (optional)"""
    # TODO: Implement file indexer
    return None


@lru_cache()
def get_ai_adapter() -> AIAdapterPort:
    """Get AI adapter instance"""
    # TODO: Implement AI adapter
    from .ai_adapter_impl import AIAdapterImpl
    return AIAdapterImpl()


# Service Dependencies

@lru_cache()
def get_context_service() -> ContextService:
    """Get context service instance"""
    return ContextService(
        context_repo=get_context_repository(),
        domain_repo=get_domain_repository(),
        session_repo=get_session_repository(),
        query_repo=get_query_repository(),
        vector_store=get_vector_store(),
        indexer=get_indexer()
    )


@lru_cache()
def get_ai_orchestrator() -> AIOrchestrator:
    """Get AI orchestrator instance"""
    return AIOrchestrator(
        context_service=get_context_service(),
        session_repo=get_session_repository(),
        ai_adapter=get_ai_adapter()
    )


# Clear cache function for testing
def clear_dependency_cache():
    """Clear dependency cache (useful for testing)"""
    get_context_repository.cache_clear()
    get_domain_repository.cache_clear()
    get_session_repository.cache_clear()
    get_query_repository.cache_clear()
    get_vector_store.cache_clear()
    get_indexer.cache_clear()
    get_ai_adapter.cache_clear()
    get_context_service.cache_clear()
    get_ai_orchestrator.cache_clear()