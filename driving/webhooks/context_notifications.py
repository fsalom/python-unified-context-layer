"""Real-time notifications for context updates"""
from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Set
import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# Global event manager
class ContextEventManager:
    """Manages real-time context events and subscriptions"""

    def __init__(self):
        self.subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self.project_subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self.platform_subscribers: Dict[str, Set[asyncio.Queue]] = {}

    async def subscribe_to_project(self, project_id: str) -> asyncio.Queue:
        """Subscribe to project context changes"""
        queue = asyncio.Queue()

        if project_id not in self.project_subscribers:
            self.project_subscribers[project_id] = set()

        self.project_subscribers[project_id].add(queue)
        return queue

    async def subscribe_to_platform(self, platform_type: str) -> asyncio.Queue:
        """Subscribe to platform-specific changes"""
        queue = asyncio.Queue()

        if platform_type not in self.platform_subscribers:
            self.platform_subscribers[platform_type] = set()

        self.platform_subscribers[platform_type].add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from all events"""
        for subscribers in self.project_subscribers.values():
            subscribers.discard(queue)

        for subscribers in self.platform_subscribers.values():
            subscribers.discard(queue)

    async def notify_global_context_updated(
        self,
        project_id: str,
        changes: Dict[str, Any],
        source_platform: str = None
    ):
        """Notify about global context updates"""
        event = {
            "type": "global_context_updated",
            "project_id": project_id,
            "changes": changes,
            "source_platform": source_platform,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self._broadcast_to_project(project_id, event)

    async def notify_platform_context_updated(
        self,
        project_id: str,
        platform_type: str,
        context_id: str,
        changes: Dict[str, Any]
    ):
        """Notify about platform context updates"""
        event = {
            "type": "platform_context_updated",
            "project_id": project_id,
            "platform_type": platform_type,
            "context_id": context_id,
            "changes": changes,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self._broadcast_to_project(project_id, event)
        await self._broadcast_to_platform(platform_type, event)

    async def notify_new_insights_available(
        self,
        project_id: str,
        insights: Dict[str, Any],
        source_platform: str
    ):
        """Notify about new insights shared to global context"""
        event = {
            "type": "new_insights_available",
            "project_id": project_id,
            "insights": insights,
            "source_platform": source_platform,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self._broadcast_to_project(project_id, event)

    async def notify_domain_context_updated(
        self,
        project_id: str,
        domain_type: str,
        changes: Dict[str, Any]
    ):
        """Notify about domain context updates"""
        event = {
            "type": "domain_context_updated",
            "project_id": project_id,
            "domain_type": domain_type,
            "changes": changes,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self._broadcast_to_project(project_id, event)

    async def _broadcast_to_project(self, project_id: str, event: Dict[str, Any]):
        """Broadcast event to all project subscribers"""
        if project_id in self.project_subscribers:
            for queue in self.project_subscribers[project_id].copy():
                try:
                    await queue.put(event)
                except:
                    # Remove dead queues
                    self.project_subscribers[project_id].discard(queue)

    async def _broadcast_to_platform(self, platform_type: str, event: Dict[str, Any]):
        """Broadcast event to all platform subscribers"""
        if platform_type in self.platform_subscribers:
            for queue in self.platform_subscribers[platform_type].copy():
                try:
                    await queue.put(event)
                except:
                    # Remove dead queues
                    self.platform_subscribers[platform_type].discard(queue)


# Global event manager instance
event_manager = ContextEventManager()

# Router for webhook and SSE endpoints
router = APIRouter(prefix="/events", tags=["Context Events"])


@router.get("/projects/{project_id}/stream")
async def stream_project_events(project_id: str):
    """Stream real-time events for a project via SSE"""

    async def event_generator():
        queue = await event_manager.subscribe_to_project(project_id)

        try:
            # Send initial connection event
            yield {
                "event": "connected",
                "data": json.dumps({
                    "type": "connection_established",
                    "project_id": project_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            }

            # Keep sending events
            while True:
                try:
                    # Wait for event with timeout to send keep-alive
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": event["type"],
                        "data": json.dumps(event)
                    }
                except asyncio.TimeoutError:
                    # Send keep-alive
                    yield {
                        "event": "keep_alive",
                        "data": json.dumps({
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    }

        except asyncio.CancelledError:
            logger.info(f"SSE connection cancelled for project {project_id}")
        finally:
            await event_manager.unsubscribe(queue)

    return EventSourceResponse(event_generator())


@router.get("/platforms/{platform_type}/stream")
async def stream_platform_events(platform_type: str):
    """Stream real-time events for a platform via SSE"""

    async def event_generator():
        queue = await event_manager.subscribe_to_platform(platform_type)

        try:
            yield {
                "event": "connected",
                "data": json.dumps({
                    "type": "connection_established",
                    "platform_type": platform_type,
                    "timestamp": datetime.utcnow().isoformat()
                })
            }

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": event["type"],
                        "data": json.dumps(event)
                    }
                except asyncio.TimeoutError:
                    yield {
                        "event": "keep_alive",
                        "data": json.dumps({
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    }

        except asyncio.CancelledError:
            logger.info(f"SSE connection cancelled for platform {platform_type}")
        finally:
            await event_manager.unsubscribe(queue)

    return EventSourceResponse(event_generator())


@router.post("/webhooks/register")
async def register_webhook(
    webhook_url: str,
    project_id: str = None,
    platform_type: str = None,
    event_types: List[str] = None
):
    """Register a webhook for context events"""
    # TODO: Implement webhook registration and delivery
    return {
        "webhook_id": "webhook_123",
        "url": webhook_url,
        "project_id": project_id,
        "platform_type": platform_type,
        "event_types": event_types or ["all"],
        "status": "registered"
    }


# Integration with context services
class ContextEventIntegration:
    """Integration layer to emit events from context operations"""

    @staticmethod
    async def on_global_context_updated(
        project_id: str,
        changes: Dict[str, Any],
        source_platform: str = None
    ):
        """Called when global context is updated"""
        await event_manager.notify_global_context_updated(
            project_id, changes, source_platform
        )

    @staticmethod
    async def on_platform_context_updated(
        project_id: str,
        platform_type: str,
        context_id: str,
        changes: Dict[str, Any]
    ):
        """Called when platform context is updated"""
        await event_manager.notify_platform_context_updated(
            project_id, platform_type, context_id, changes
        )

    @staticmethod
    async def on_insights_merged(
        project_id: str,
        insights: Dict[str, Any],
        source_platform: str
    ):
        """Called when insights are merged to global context"""
        await event_manager.notify_new_insights_available(
            project_id, insights, source_platform
        )

    @staticmethod
    async def on_domain_context_updated(
        project_id: str,
        domain_type: str,
        changes: Dict[str, Any]
    ):
        """Called when domain context is updated"""
        await event_manager.notify_domain_context_updated(
            project_id, domain_type, changes
        )


# JavaScript client for SSE connection
SSE_CLIENT_JAVASCRIPT = """
class UCLEventStream {
    constructor(projectId, baseUrl = 'http://localhost:8002/api/v1/ucl/events') {
        this.projectId = projectId;
        this.baseUrl = baseUrl;
        this.eventSource = null;
        this.listeners = {};
    }

    connect() {
        if (this.eventSource) {
            this.disconnect();
        }

        const url = `${this.baseUrl}/projects/${this.projectId}/stream`;
        this.eventSource = new EventSource(url);

        this.eventSource.onopen = () => {
            console.log('UCL Event Stream connected');
            this.emit('connected');
        };

        this.eventSource.onerror = (error) => {
            console.error('UCL Event Stream error:', error);
            this.emit('error', error);
        };

        // Listen for specific event types
        const eventTypes = [
            'global_context_updated',
            'platform_context_updated',
            'new_insights_available',
            'domain_context_updated'
        ];

        eventTypes.forEach(eventType => {
            this.eventSource.addEventListener(eventType, (event) => {
                const data = JSON.parse(event.data);
                this.emit(eventType, data);
                this.emit('any', data);
            });
        });

        return this;
    }

    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }

    on(eventType, callback) {
        if (!this.listeners[eventType]) {
            this.listeners[eventType] = [];
        }
        this.listeners[eventType].push(callback);
        return this;
    }

    off(eventType, callback) {
        if (this.listeners[eventType]) {
            this.listeners[eventType] = this.listeners[eventType].filter(cb => cb !== callback);
        }
        return this;
    }

    emit(eventType, data = null) {
        if (this.listeners[eventType]) {
            this.listeners[eventType].forEach(callback => callback(data));
        }
    }
}

// Usage example:
// const stream = new UCLEventStream('my-project-id');
// stream.on('global_context_updated', (data) => {
//     console.log('Global context updated:', data);
//     // Refresh your AI's context
// });
// stream.connect();
"""