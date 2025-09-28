"""AI Adapter Port for Unified Context Layer"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from domain.entities.project_context import ContextResponse, ProjectContext


@dataclass
class AIContextRequest:
    """Request from AI for context"""
    ai_type: str
    ai_instance_id: str
    query: str
    domains: List[str]
    session_id: Optional[str] = None
    max_results: int = 100
    include_history: bool = False
    response_format: str = "structured"
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AICapabilities:
    """AI capabilities and configuration"""
    ai_type: str
    supports_streaming: bool = False
    supports_functions: bool = False
    supports_multimodal: bool = False
    max_context_length: int = 4096
    preferred_format: str = "markdown"
    rate_limits: Dict[str, int] = None

    def __post_init__(self):
        if self.rate_limits is None:
            self.rate_limits = {"requests_per_minute": 60}


@dataclass
class AIContextUpdate:
    """Update from AI about context changes"""
    ai_type: str
    ai_instance_id: str
    session_id: str
    domain_type: str
    updates: List[Dict[str, Any]]
    timestamp: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AIAdapterPort(ABC):
    """Interface for AI adapters to interact with UCL"""

    @abstractmethod
    async def register_ai(self, capabilities: AICapabilities) -> str:
        """Register AI with the UCL system"""
        pass

    @abstractmethod
    async def request_context(
        self,
        request: AIContextRequest,
        project_id: str
    ) -> ContextResponse:
        """Request context from UCL"""
        pass

    @abstractmethod
    async def update_context(
        self,
        update: AIContextUpdate,
        project_id: str
    ) -> bool:
        """Update context based on AI actions"""
        pass

    @abstractmethod
    async def subscribe_to_updates(
        self,
        ai_instance_id: str,
        project_id: str,
        domains: List[str]
    ) -> str:
        """Subscribe to real-time context updates"""
        pass

    @abstractmethod
    async def unsubscribe_from_updates(
        self,
        subscription_id: str
    ) -> bool:
        """Unsubscribe from updates"""
        pass

    @abstractmethod
    async def get_ai_sessions(
        self,
        ai_instance_id: str,
        project_id: str
    ) -> List[Dict[str, Any]]:
        """Get AI sessions for instance"""
        pass


class VectorStorePort(ABC):
    """Interface for vector storage operations"""

    @abstractmethod
    async def add_documents(
        self,
        documents: List[str],
        metadata: List[Dict[str, Any]],
        project_id: str,
        domain_type: str
    ) -> List[str]:
        """Add documents to vector store"""
        pass

    @abstractmethod
    async def search_similar(
        self,
        query: str,
        project_id: str,
        domain_types: Optional[List[str]] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        pass

    @abstractmethod
    async def delete_documents(
        self,
        document_ids: List[str],
        project_id: str
    ) -> bool:
        """Delete documents from vector store"""
        pass

    @abstractmethod
    async def update_document(
        self,
        document_id: str,
        content: str,
        metadata: Dict[str, Any],
        project_id: str
    ) -> bool:
        """Update existing document"""
        pass

    @abstractmethod
    async def get_project_stats(
        self,
        project_id: str
    ) -> Dict[str, Any]:
        """Get statistics for project in vector store"""
        pass


class IndexerPort(ABC):
    """Interface for code/file indexing operations"""

    @abstractmethod
    async def index_project(
        self,
        project_path: str,
        project_id: str,
        file_patterns: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """Index entire project"""
        pass

    @abstractmethod
    async def index_domain(
        self,
        project_path: str,
        project_id: str,
        domain_type: str,
        file_patterns: List[str]
    ) -> Dict[str, Any]:
        """Index specific domain"""
        pass

    @abstractmethod
    async def update_file_index(
        self,
        file_path: str,
        project_id: str,
        domain_type: str
    ) -> bool:
        """Update index for specific file"""
        pass

    @abstractmethod
    async def remove_file_index(
        self,
        file_path: str,
        project_id: str
    ) -> bool:
        """Remove file from index"""
        pass

    @abstractmethod
    async def get_file_dependencies(
        self,
        file_path: str,
        project_id: str
    ) -> List[str]:
        """Get file dependencies"""
        pass