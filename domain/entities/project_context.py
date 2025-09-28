"""Project Context Domain Entity for Unified Context Layer"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4


@dataclass
class ProjectMetadata:
    """Project metadata information"""
    name: str
    description: Optional[str] = None
    version: Optional[str] = None
    repository_url: Optional[str] = None
    technologies: List[str] = field(default_factory=list)
    team_members: List[str] = field(default_factory=list)
    documentation_urls: List[str] = field(default_factory=list)


@dataclass
class DomainContext:
    """Context for a specific domain (frontend, backend, design, etc.)"""
    id: str = field(default_factory=lambda: str(uuid4()))
    domain_type: str = ""  # "frontend", "backend", "design", "infrastructure", "testing"
    technologies: List[str] = field(default_factory=list)
    file_patterns: List[str] = field(default_factory=list)
    key_files: List[str] = field(default_factory=list)
    apis: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    conventions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AISession:
    """AI session tracking"""
    id: str = field(default_factory=lambda: str(uuid4()))
    ai_type: str = ""  # "claude", "chatgpt", "copilot", "custom"
    session_start: datetime = field(default_factory=datetime.utcnow)
    session_end: Optional[datetime] = None
    domains_accessed: List[str] = field(default_factory=list)
    queries_count: int = 0
    last_query: Optional[str] = None
    context_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextQuery:
    """Query for context information"""
    id: str = field(default_factory=lambda: str(uuid4()))
    query_text: str = ""
    domains_filter: List[str] = field(default_factory=list)
    ai_session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    response_format: str = "structured"  # "structured", "markdown", "json"
    include_history: bool = False
    max_results: int = 100


@dataclass
class ContextResponse:
    """Response to a context query"""
    query_id: str
    results: List[Dict[str, Any]] = field(default_factory=list)
    domains_found: List[str] = field(default_factory=list)
    total_results: int = 0
    processing_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ProjectContext:
    """Main project context entity"""
    id: str = field(default_factory=lambda: str(uuid4()))
    project_metadata: ProjectMetadata = field(default_factory=ProjectMetadata)
    domains: List[DomainContext] = field(default_factory=list)
    ai_sessions: List[AISession] = field(default_factory=list)
    global_context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def get_domain(self, domain_type: str) -> Optional[DomainContext]:
        """Get domain context by type"""
        return next((d for d in self.domains if d.domain_type == domain_type), None)

    def add_domain(self, domain: DomainContext) -> None:
        """Add or update domain context"""
        existing = self.get_domain(domain.domain_type)
        if existing:
            self.domains.remove(existing)
        self.domains.append(domain)
        self.last_updated = datetime.utcnow()

    def get_active_ai_sessions(self) -> List[AISession]:
        """Get currently active AI sessions"""
        return [session for session in self.ai_sessions if session.session_end is None]

    def start_ai_session(self, ai_type: str, metadata: Optional[Dict[str, Any]] = None) -> AISession:
        """Start new AI session"""
        session = AISession(
            ai_type=ai_type,
            metadata=metadata or {}
        )
        self.ai_sessions.append(session)
        return session

    def end_ai_session(self, session_id: str) -> Optional[AISession]:
        """End AI session"""
        session = next((s for s in self.ai_sessions if s.id == session_id), None)
        if session and session.session_end is None:
            session.session_end = datetime.utcnow()
        return session