"""FastAPI adapter for Unified Context Layer"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging

from application.services.context_service import ContextService
from application.services.ai_orchestrator_service import AIOrchestrator
from .schemas import (
    ProjectContextCreate,
    ProjectContextResponse,
    DomainContextCreate,
    DomainContextUpdate,
    DomainContextResponse,
    AISessionCreate,
    AISessionResponse,
    ContextQueryRequest,
    ContextQueryResponse,
    AIContextRequest,
    AICapabilitiesRequest,
    AICapabilitiesResponse,
    AIContextUpdate,
    AISubscriptionRequest,
    AISubscriptionResponse,
    ProjectAnalyticsResponse,
    AIAnalyticsResponse,
    CollaborationInsightsResponse,
    ErrorResponse,
    SuccessResponse
)

logger = logging.getLogger(__name__)

# Router for UCL endpoints
router = APIRouter(prefix="/ucl", tags=["Unified Context Layer"])


class ContextAdapter:
    """FastAPI adapter for context operations"""

    def __init__(self, context_service: ContextService, ai_orchestrator: AIOrchestrator):
        self._context_service = context_service
        self._ai_orchestrator = ai_orchestrator

    # Project Context Endpoints

    @router.post("/projects", response_model=ProjectContextResponse)
    async def create_project_context(
        self,
        request: ProjectContextCreate,
        context_service: ContextService = Depends()
    ):
        """Create new project context"""
        try:
            context = await context_service.create_project_context(
                name=request.project_metadata.name,
                description=request.project_metadata.description,
                technologies=request.project_metadata.technologies,
                repository_url=str(request.project_metadata.repository_url) if request.project_metadata.repository_url else None
            )
            return self._project_context_to_response(context)
        except Exception as e:
            logger.error(f"Error creating project context: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/projects/{project_id}", response_model=ProjectContextResponse)
    async def get_project_context(
        self,
        project_id: str,
        context_service: ContextService = Depends()
    ):
        """Get project context by ID"""
        context = await context_service.get_project_context(project_id)
        if not context:
            raise HTTPException(status_code=404, detail="Project context not found")
        return self._project_context_to_response(context)

    @router.get("/projects", response_model=List[ProjectContextResponse])
    async def list_project_contexts(
        self,
        context_service: ContextService = Depends()
    ):
        """List all project contexts"""
        contexts = await context_service._context_repo.list_project_contexts()
        return [self._project_context_to_response(ctx) for ctx in contexts]

    # Domain Context Endpoints

    @router.post("/projects/{project_id}/domains", response_model=DomainContextResponse)
    async def create_domain_context(
        self,
        project_id: str,
        request: DomainContextCreate,
        context_service: ContextService = Depends()
    ):
        """Create domain context for project"""
        try:
            domain = await context_service.add_domain_context(
                project_id=project_id,
                domain_type=request.domain_type.value,
                technologies=request.technologies,
                file_patterns=request.file_patterns,
                conventions=request.conventions
            )
            return self._domain_context_to_response(domain)
        except Exception as e:
            logger.error(f"Error creating domain context: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/projects/{project_id}/domains", response_model=List[DomainContextResponse])
    async def get_project_domains(
        self,
        project_id: str,
        context_service: ContextService = Depends()
    ):
        """Get all domains for project"""
        domains = await context_service._domain_repo.get_domains_by_project(project_id)
        return [self._domain_context_to_response(domain) for domain in domains]

    @router.get("/projects/{project_id}/domains/{domain_type}", response_model=DomainContextResponse)
    async def get_domain_by_type(
        self,
        project_id: str,
        domain_type: str,
        context_service: ContextService = Depends()
    ):
        """Get domain by type for project"""
        domain = await context_service._domain_repo.get_domain_by_type(project_id, domain_type)
        if not domain:
            raise HTTPException(status_code=404, detail="Domain context not found")
        return self._domain_context_to_response(domain)

    @router.put("/domains/{domain_id}", response_model=DomainContextResponse)
    async def update_domain_context(
        self,
        domain_id: str,
        request: DomainContextUpdate,
        context_service: ContextService = Depends()
    ):
        """Update domain context"""
        try:
            # Get existing domain
            domain = await context_service._domain_repo.get_domain_context(domain_id)
            if not domain:
                raise HTTPException(status_code=404, detail="Domain context not found")

            # Update fields
            if request.technologies is not None:
                domain.technologies = request.technologies
            if request.file_patterns is not None:
                domain.file_patterns = request.file_patterns
            if request.key_files is not None:
                domain.key_files = request.key_files
            if request.conventions is not None:
                domain.conventions = request.conventions

            updated_domain = await context_service._domain_repo.update_domain_context(domain)
            return self._domain_context_to_response(updated_domain)
        except Exception as e:
            logger.error(f"Error updating domain context: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    # Context Query Endpoints

    @router.post("/projects/{project_id}/query", response_model=ContextQueryResponse)
    async def query_context(
        self,
        project_id: str,
        request: ContextQueryRequest,
        context_service: ContextService = Depends()
    ):
        """Query project context"""
        try:
            domains_filter = [domain.value for domain in request.domains_filter] if request.domains_filter else None

            response = await context_service.query_context(
                project_id=project_id,
                query_text=request.query_text,
                domains_filter=domains_filter,
                ai_session_id=request.ai_session_id,
                response_format=request.response_format.value,
                include_history=request.include_history,
                max_results=request.max_results
            )
            return self._context_response_to_response(response)
        except Exception as e:
            logger.error(f"Error querying context: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    # AI Session Endpoints

    @router.post("/projects/{project_id}/ai-sessions", response_model=AISessionResponse)
    async def create_ai_session(
        self,
        project_id: str,
        request: AISessionCreate,
        context_service: ContextService = Depends()
    ):
        """Create AI session"""
        try:
            session = await context_service.start_ai_session(
                project_id=project_id,
                ai_type=request.ai_type.value,
                metadata=request.metadata
            )
            return self._ai_session_to_response(session)
        except Exception as e:
            logger.error(f"Error creating AI session: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @router.patch("/ai-sessions/{session_id}/end", response_model=AISessionResponse)
    async def end_ai_session(
        self,
        session_id: str,
        context_service: ContextService = Depends()
    ):
        """End AI session"""
        session = await context_service.end_ai_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="AI session not found")
        return self._ai_session_to_response(session)

    @router.get("/projects/{project_id}/ai-sessions", response_model=List[AISessionResponse])
    async def get_project_ai_sessions(
        self,
        project_id: str,
        ai_type: Optional[str] = Query(None),
        active_only: bool = Query(False),
        context_service: ContextService = Depends()
    ):
        """Get AI sessions for project"""
        if active_only:
            sessions = await context_service._session_repo.get_active_sessions(project_id)
        elif ai_type:
            sessions = await context_service._session_repo.get_sessions_by_ai_type(project_id, ai_type)
        else:
            sessions = await context_service._session_repo.get_sessions_by_project(project_id)

        return [self._ai_session_to_response(session) for session in sessions]

    # AI Integration Endpoints

    @router.post("/ai/register", response_model=AICapabilitiesResponse)
    async def register_ai(
        self,
        request: AICapabilitiesRequest,
        ai_orchestrator: AIOrchestrator = Depends()
    ):
        """Register AI with UCL"""
        try:
            from application.ports.ai_adapter_port import AICapabilities

            capabilities = AICapabilities(
                ai_type=request.ai_type.value,
                supports_streaming=request.supports_streaming,
                supports_functions=request.supports_functions,
                supports_multimodal=request.supports_multimodal,
                max_context_length=request.max_context_length,
                preferred_format=request.preferred_format.value,
                rate_limits=request.rate_limits
            )

            ai_id = await ai_orchestrator.register_ai(capabilities)
            return AICapabilitiesResponse(ai_id=ai_id, **request.dict())
        except Exception as e:
            logger.error(f"Error registering AI: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/ai/context-request", response_model=ContextQueryResponse)
    async def handle_ai_context_request(
        self,
        project_id: str,
        request: AIContextRequest,
        ai_orchestrator: AIOrchestrator = Depends()
    ):
        """Handle context request from AI"""
        try:
            from application.ports.ai_adapter_port import AIContextRequest as AIContextRequestPort

            ai_request = AIContextRequestPort(
                ai_type=request.ai_type.value,
                ai_instance_id=request.ai_instance_id,
                query=request.query,
                domains=[domain.value for domain in request.domains],
                session_id=request.session_id,
                max_results=request.max_results,
                include_history=request.include_history,
                response_format=request.response_format.value,
                metadata=request.metadata
            )

            response = await ai_orchestrator.handle_ai_context_request(ai_request, project_id)
            return self._context_response_to_response(response)
        except Exception as e:
            logger.error(f"Error handling AI context request: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/ai/context-update", response_model=SuccessResponse)
    async def handle_ai_context_update(
        self,
        project_id: str,
        request: AIContextUpdate,
        ai_orchestrator: AIOrchestrator = Depends()
    ):
        """Handle context update from AI"""
        try:
            from application.ports.ai_adapter_port import AIContextUpdate as AIContextUpdatePort
            from datetime import datetime

            ai_update = AIContextUpdatePort(
                ai_type=request.ai_type.value,
                ai_instance_id=request.ai_instance_id,
                session_id=request.session_id,
                domain_type=request.domain_type.value,
                updates=request.updates,
                timestamp=datetime.utcnow().isoformat(),
                metadata=request.metadata
            )

            success = await ai_orchestrator.handle_ai_context_update(ai_update, project_id)
            return SuccessResponse(success=success, message="Context updated successfully" if success else "Failed to update context")
        except Exception as e:
            logger.error(f"Error handling AI context update: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/ai/subscribe", response_model=AISubscriptionResponse)
    async def subscribe_ai_to_updates(
        self,
        project_id: str,
        request: AISubscriptionRequest,
        ai_orchestrator: AIOrchestrator = Depends()
    ):
        """Subscribe AI to context updates"""
        try:
            domains = [domain.value for domain in request.domains]
            subscription_id = await ai_orchestrator.subscribe_ai_to_updates(
                request.ai_instance_id,
                project_id,
                domains
            )

            from datetime import datetime
            return AISubscriptionResponse(
                subscription_id=subscription_id,
                ai_instance_id=request.ai_instance_id,
                project_id=project_id,
                domains=domains,
                created_at=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Error subscribing AI to updates: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    # Analytics Endpoints

    @router.get("/projects/{project_id}/analytics", response_model=ProjectAnalyticsResponse)
    async def get_project_analytics(
        self,
        project_id: str,
        days: int = Query(30, ge=1, le=365),
        context_service: ContextService = Depends()
    ):
        """Get project analytics"""
        try:
            analytics = await context_service.get_project_analytics(project_id, days)
            return ProjectAnalyticsResponse(**analytics)
        except Exception as e:
            logger.error(f"Error getting project analytics: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/projects/{project_id}/ai-analytics", response_model=AIAnalyticsResponse)
    async def get_ai_analytics(
        self,
        project_id: str,
        ai_type: Optional[str] = Query(None),
        days: int = Query(7, ge=1, le=365),
        ai_orchestrator: AIOrchestrator = Depends()
    ):
        """Get AI analytics"""
        try:
            analytics = await ai_orchestrator.get_ai_analytics(project_id, ai_type, days)
            return AIAnalyticsResponse(**analytics)
        except Exception as e:
            logger.error(f"Error getting AI analytics: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/projects/{project_id}/collaboration-insights", response_model=CollaborationInsightsResponse)
    async def get_collaboration_insights(
        self,
        project_id: str,
        days: int = Query(7, ge=1, le=365),
        ai_orchestrator: AIOrchestrator = Depends()
    ):
        """Get collaboration insights"""
        try:
            insights = await ai_orchestrator.get_collaboration_insights(project_id, days)
            return CollaborationInsightsResponse(**insights)
        except Exception as e:
            logger.error(f"Error getting collaboration insights: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    # Helper methods for response conversion

    def _project_context_to_response(self, context) -> ProjectContextResponse:
        """Convert project context entity to response"""
        return ProjectContextResponse(
            id=context.id,
            project_metadata=context.project_metadata.__dict__,
            global_context=context.global_context,
            created_at=context.created_at,
            last_updated=context.last_updated
        )

    def _domain_context_to_response(self, domain) -> DomainContextResponse:
        """Convert domain context entity to response"""
        return DomainContextResponse(
            id=domain.id,
            domain_type=domain.domain_type,
            technologies=domain.technologies,
            file_patterns=domain.file_patterns,
            key_files=domain.key_files,
            apis=domain.apis,
            dependencies=domain.dependencies,
            conventions=domain.conventions,
            metadata=domain.metadata,
            last_updated=domain.last_updated
        )

    def _ai_session_to_response(self, session) -> AISessionResponse:
        """Convert AI session entity to response"""
        return AISessionResponse(
            id=session.id,
            ai_type=session.ai_type,
            ai_instance_id=getattr(session, 'ai_instance_id', None),
            session_start=session.session_start,
            session_end=session.session_end,
            domains_accessed=session.domains_accessed,
            queries_count=session.queries_count,
            last_query=session.last_query,
            context_hash=session.context_hash,
            metadata=session.metadata,
            is_active=session.session_end is None
        )

    def _context_response_to_response(self, response) -> ContextQueryResponse:
        """Convert context response entity to response"""
        return ContextQueryResponse(
            query_id=response.query_id,
            results=response.results,
            domains_found=response.domains_found,
            total_results=response.total_results,
            processing_time_ms=response.processing_time_ms,
            metadata=response.metadata,
            timestamp=response.timestamp
        )


# Exception handlers
@router.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(detail=str(exc), error_type="ValidationError").dict()
    )


@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(detail="Internal server error", error_type="ServerError").dict()
    )