"""Pydantic schemas for UCL API"""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DomainType(str, Enum):
    """Domain types for context"""
    FRONTEND = "frontend"
    BACKEND = "backend"
    DESIGN = "design"
    INFRASTRUCTURE = "infrastructure"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DATA = "data"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    API = "api"
    DATABASE = "database"
    SECURITY = "security"
    DEVOPS = "devops"
    ANALYTICS = "analytics"
    OTHER = "other"


class AIType(str, Enum):
    """AI types"""
    CLAUDE = "claude"
    CHATGPT = "chatgpt"
    COPILOT = "copilot"
    BARD = "bard"
    CUSTOM = "custom"
    OTHER = "other"


class ResponseFormat(str, Enum):
    """Response formats"""
    STRUCTURED = "structured"
    MARKDOWN = "markdown"
    JSON = "json"
    TEXT = "text"


class ContextScope(str, Enum):
    """Context scope types"""
    GLOBAL = "global"
    PLATFORM = "platform"
    DOMAIN = "domain"
    ALL = "all"


# Project Context Schemas

class ProjectMetadataCreate(BaseModel):
    """Schema for creating project metadata"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    version: Optional[str] = None
    repository_url: Optional[HttpUrl] = None
    technologies: List[str] = Field(default_factory=list)
    team_members: List[str] = Field(default_factory=list)
    documentation_urls: List[HttpUrl] = Field(default_factory=list)


class ProjectMetadataResponse(ProjectMetadataCreate):
    """Schema for project metadata response"""
    pass


class ProjectContextCreate(BaseModel):
    """Schema for creating project context"""
    project_metadata: ProjectMetadataCreate
    global_context: Dict[str, Any] = Field(default_factory=dict)


class ProjectContextResponse(BaseModel):
    """Schema for project context response"""
    id: str
    project_metadata: ProjectMetadataResponse
    global_context: Dict[str, Any]
    created_at: datetime
    last_updated: datetime

    class Config:
        from_attributes = True


# Domain Context Schemas

class DomainContextCreate(BaseModel):
    """Schema for creating domain context"""
    domain_type: DomainType
    technologies: List[str] = Field(default_factory=list)
    file_patterns: List[str] = Field(default_factory=list)
    key_files: List[str] = Field(default_factory=list)
    apis: List[Dict[str, Any]] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    conventions: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DomainContextUpdate(BaseModel):
    """Schema for updating domain context"""
    technologies: Optional[List[str]] = None
    file_patterns: Optional[List[str]] = None
    key_files: Optional[List[str]] = None
    apis: Optional[List[Dict[str, Any]]] = None
    dependencies: Optional[List[str]] = None
    conventions: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class DomainContextResponse(BaseModel):
    """Schema for domain context response"""
    id: str
    domain_type: str
    technologies: List[str]
    file_patterns: List[str]
    key_files: List[str]
    apis: List[Dict[str, Any]]
    dependencies: List[str]
    conventions: Dict[str, Any]
    metadata: Dict[str, Any]
    last_updated: datetime

    class Config:
        from_attributes = True


# AI Session Schemas

class AISessionCreate(BaseModel):
    """Schema for creating AI session"""
    ai_type: AIType
    ai_instance_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AISessionResponse(BaseModel):
    """Schema for AI session response"""
    id: str
    ai_type: str
    ai_instance_id: Optional[str]
    session_start: datetime
    session_end: Optional[datetime]
    domains_accessed: List[str]
    queries_count: int
    last_query: Optional[str]
    context_hash: Optional[str]
    metadata: Dict[str, Any]
    is_active: bool

    class Config:
        from_attributes = True


# Context Query Schemas

class ContextQueryRequest(BaseModel):
    """Schema for context query request"""
    query_text: str = Field(..., min_length=1)
    domains_filter: List[DomainType] = Field(default_factory=list)
    ai_session_id: Optional[str] = None
    response_format: ResponseFormat = ResponseFormat.STRUCTURED
    include_history: bool = False
    max_results: int = Field(default=100, ge=1, le=1000)


class ContextQueryResponse(BaseModel):
    """Schema for context query response"""
    query_id: str
    results: List[Dict[str, Any]]
    domains_found: List[str]
    total_results: int
    processing_time_ms: float
    metadata: Dict[str, Any]
    timestamp: datetime

    class Config:
        from_attributes = True


# AI Context Schemas

class AIContextRequest(BaseModel):
    """Schema for AI context request"""
    ai_type: AIType
    ai_instance_id: str
    query: str = Field(..., min_length=1)
    domains: List[DomainType] = Field(default_factory=list)
    session_id: Optional[str] = None
    max_results: int = Field(default=100, ge=1, le=1000)
    include_history: bool = False
    response_format: ResponseFormat = ResponseFormat.STRUCTURED
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AICapabilitiesRequest(BaseModel):
    """Schema for AI capabilities registration"""
    ai_type: AIType
    supports_streaming: bool = False
    supports_functions: bool = False
    supports_multimodal: bool = False
    max_context_length: int = Field(default=4096, ge=1)
    preferred_format: ResponseFormat = ResponseFormat.MARKDOWN
    rate_limits: Dict[str, int] = Field(default_factory=lambda: {"requests_per_minute": 60})


class AICapabilitiesResponse(AICapabilitiesRequest):
    """Schema for AI capabilities response"""
    ai_id: str


class AIContextUpdate(BaseModel):
    """Schema for AI context update"""
    ai_type: AIType
    ai_instance_id: str
    session_id: str
    domain_type: DomainType
    updates: List[Dict[str, Any]]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AISubscriptionRequest(BaseModel):
    """Schema for AI subscription request"""
    ai_instance_id: str
    domains: List[DomainType]


class AISubscriptionResponse(BaseModel):
    """Schema for AI subscription response"""
    subscription_id: str
    ai_instance_id: str
    project_id: str
    domains: List[str]
    created_at: datetime


# Global Context Schemas

class GlobalContextCreate(BaseModel):
    """Schema for creating global context"""
    project_id: str
    shared_knowledge: Dict[str, Any] = Field(default_factory=dict)
    shared_conventions: Dict[str, Any] = Field(default_factory=dict)
    shared_resources: List[Dict[str, Any]] = Field(default_factory=list)
    common_patterns: List[str] = Field(default_factory=list)


class GlobalContextUpdate(BaseModel):
    """Schema for updating global context"""
    shared_knowledge: Optional[Dict[str, Any]] = None
    shared_conventions: Optional[Dict[str, Any]] = None
    shared_resources: Optional[List[Dict[str, Any]]] = None
    common_patterns: Optional[List[str]] = None
    cross_platform_insights: Optional[Dict[str, Any]] = None


class GlobalContextResponse(BaseModel):
    """Schema for global context response"""
    id: str
    project_id: str
    shared_knowledge: Dict[str, Any]
    shared_conventions: Dict[str, Any]
    shared_resources: List[Dict[str, Any]]
    common_patterns: List[str]
    cross_platform_insights: Dict[str, Any]
    last_updated: datetime
    version: int


# Platform Context Schemas

class PlatformContextCreate(BaseModel):
    """Schema for creating platform context"""
    platform_type: AIType
    platform_specific_data: Dict[str, Any] = Field(default_factory=dict)
    learned_preferences: Dict[str, Any] = Field(default_factory=dict)
    custom_prompts: List[str] = Field(default_factory=list)
    platform_conventions: Dict[str, Any] = Field(default_factory=dict)


class PlatformContextUpdate(BaseModel):
    """Schema for updating platform context"""
    platform_specific_data: Optional[Dict[str, Any]] = None
    learned_preferences: Optional[Dict[str, Any]] = None
    custom_prompts: Optional[List[str]] = None
    platform_conventions: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None


class PlatformContextResponse(BaseModel):
    """Schema for platform context response"""
    id: str
    platform_type: str
    project_id: str
    global_context_id: str
    platform_specific_data: Dict[str, Any]
    learned_preferences: Dict[str, Any]
    interaction_history: List[Dict[str, Any]]
    custom_prompts: List[str]
    platform_conventions: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    last_updated: datetime
    version: int


class InteractionCreate(BaseModel):
    """Schema for creating interaction"""
    interaction_type: str = Field(..., description="Type of interaction (query, response, action)")
    content: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContextQueryWithHierarchy(BaseModel):
    """Schema for hierarchical context query"""
    query_text: str = Field(..., min_length=1)
    platform_type: AIType
    include_global: bool = True
    include_platform: bool = True
    include_domains: bool = True
    domains_filter: Optional[List[DomainType]] = None
    response_format: ResponseFormat = ResponseFormat.STRUCTURED
    max_results: int = Field(default=100, ge=1, le=1000)


class MergeInsightsRequest(BaseModel):
    """Schema for merging insights to global context"""
    insights: Dict[str, Any]
    source_platform: AIType
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Analytics Schemas

class ProjectAnalyticsResponse(BaseModel):
    """Schema for project analytics response"""
    queries: Dict[str, Any]
    sessions: Dict[str, Any]
    domains: Dict[str, Any]
    vector_store: Dict[str, Any]


class AIAnalyticsResponse(BaseModel):
    """Schema for AI analytics response"""
    period_days: int
    total_sessions: int
    active_sessions: int
    total_queries: int
    avg_queries_per_session: float
    avg_session_duration_minutes: float
    domain_usage: Dict[str, int]
    ai_type_usage: Dict[str, int]
    active_subscriptions: int


class CollaborationInsightsResponse(BaseModel):
    """Schema for collaboration insights response"""
    concurrent_usage: Dict[str, Any]
    domain_overlap: Dict[str, Any]
    handoff_patterns: Dict[str, Any]
    collaboration_score: float


# Error Schemas

class ErrorResponse(BaseModel):
    """Schema for error responses"""
    detail: str
    error_type: Optional[str] = None
    error_code: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Schema for validation error responses"""
    detail: str
    errors: List[Dict[str, Any]]


# Common Response Schemas

class SuccessResponse(BaseModel):
    """Schema for success responses"""
    success: bool = True
    message: Optional[str] = None


class PaginatedResponse(BaseModel):
    """Schema for paginated responses"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int