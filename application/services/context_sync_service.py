"""Context Synchronization Service for UCL"""
import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

from domain.entities.project_context import (
    GlobalContext,
    PlatformContext,
    DomainContext
)
from application.ports.context_repository import (
    GlobalContextRepositoryPort,
    PlatformContextRepositoryPort,
    DomainContextRepositoryPort
)

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Types of context changes"""
    GLOBAL_UPDATED = "global_updated"
    PLATFORM_UPDATED = "platform_updated"
    DOMAIN_UPDATED = "domain_updated"
    INSIGHTS_MERGED = "insights_merged"
    PREFERENCES_LEARNED = "preferences_learned"


@dataclass
class ContextChange:
    """Represents a context change event"""
    id: str = field(default_factory=lambda: str(uuid4()))
    change_type: ChangeType = ChangeType.GLOBAL_UPDATED
    project_id: str = ""
    source_platform: str = ""
    target_platforms: List[str] = field(default_factory=list)
    changes: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    propagated_to: Set[str] = field(default_factory=set)
    requires_approval: bool = False
    confidence_score: float = 1.0


@dataclass
class SyncPolicy:
    """Synchronization policy configuration"""
    auto_sync_global: bool = True
    auto_sync_platform: bool = False  # Platform contexts are private by default
    auto_merge_insights: bool = True
    require_approval_threshold: float = 0.7
    propagation_delay_ms: int = 0
    max_batch_size: int = 10
    enabled_platforms: List[str] = field(default_factory=list)
    conflict_resolution: str = "merge"  # "merge", "overwrite", "manual"


class ContextSyncService:
    """Service for synchronizing context across all AI platforms"""

    def __init__(
        self,
        global_context_repo: GlobalContextRepositoryPort,
        platform_context_repo: PlatformContextRepositoryPort,
        domain_context_repo: DomainContextRepositoryPort,
        sync_policy: Optional[SyncPolicy] = None
    ):
        self._global_repo = global_context_repo
        self._platform_repo = platform_context_repo
        self._domain_repo = domain_context_repo
        self._sync_policy = sync_policy or SyncPolicy()

        # Change tracking
        self._pending_changes: List[ContextChange] = []
        self._change_subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._context_hashes: Dict[str, str] = {}

        # Background tasks
        self._sync_task: Optional[asyncio.Task] = None
        self._is_running = False

    async def start_sync_service(self):
        """Start the background synchronization service"""
        if self._is_running:
            return

        self._is_running = True
        self._sync_task = asyncio.create_task(self._sync_loop())
        logger.info("Context synchronization service started")

    async def stop_sync_service(self):
        """Stop the background synchronization service"""
        self._is_running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        logger.info("Context synchronization service stopped")

    async def _sync_loop(self):
        """Main synchronization loop"""
        while self._is_running:
            try:
                # Process pending changes
                if self._pending_changes:
                    await self._process_pending_changes()

                # Check for external changes (polling fallback)
                await self._detect_external_changes()

                # Wait before next iteration
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
                await asyncio.sleep(5)

    async def subscribe_to_changes(
        self,
        project_id: str,
        platform_type: str
    ) -> asyncio.Queue:
        """Subscribe to context changes for a platform"""
        key = f"{project_id}:{platform_type}"
        queue = asyncio.Queue()

        if key not in self._change_subscribers:
            self._change_subscribers[key] = []

        self._change_subscribers[key].append(queue)
        return queue

    async def unsubscribe_from_changes(
        self,
        project_id: str,
        platform_type: str,
        queue: asyncio.Queue
    ):
        """Unsubscribe from context changes"""
        key = f"{project_id}:{platform_type}"
        if key in self._change_subscribers:
            self._change_subscribers[key] = [
                q for q in self._change_subscribers[key] if q != queue
            ]

    # Change Detection and Propagation

    async def on_global_context_changed(
        self,
        project_id: str,
        changes: Dict[str, Any],
        source_platform: str = "system"
    ):
        """Handle global context changes"""
        change = ContextChange(
            change_type=ChangeType.GLOBAL_UPDATED,
            project_id=project_id,
            source_platform=source_platform,
            target_platforms=await self._get_active_platforms(project_id),
            changes=changes,
            confidence_score=1.0
        )

        await self._queue_change(change)

    async def on_platform_context_changed(
        self,
        project_id: str,
        platform_type: str,
        changes: Dict[str, Any],
        propagate_insights: bool = True
    ):
        """Handle platform context changes"""
        # Extract insights that could be valuable for other platforms
        if propagate_insights:
            insights = await self._extract_valuable_insights(changes, platform_type)
            if insights:
                insight_change = ContextChange(
                    change_type=ChangeType.INSIGHTS_MERGED,
                    project_id=project_id,
                    source_platform=platform_type,
                    target_platforms=await self._get_active_platforms(project_id, exclude=[platform_type]),
                    changes={"insights": insights},
                    confidence_score=await self._calculate_insight_confidence(insights, platform_type)
                )
                await self._queue_change(insight_change)

        # Record platform-specific change
        platform_change = ContextChange(
            change_type=ChangeType.PLATFORM_UPDATED,
            project_id=project_id,
            source_platform=platform_type,
            target_platforms=[],  # Platform changes are not directly propagated
            changes=changes
        )
        await self._queue_change(platform_change)

    async def on_domain_context_changed(
        self,
        project_id: str,
        domain_type: str,
        changes: Dict[str, Any]
    ):
        """Handle domain context changes"""
        change = ContextChange(
            change_type=ChangeType.DOMAIN_UPDATED,
            project_id=project_id,
            source_platform="system",
            target_platforms=await self._get_active_platforms(project_id),
            changes={"domain_type": domain_type, "changes": changes}
        )

        await self._queue_change(change)

    async def _queue_change(self, change: ContextChange):
        """Queue a change for processing"""
        # Check if approval is required
        if change.confidence_score < self._sync_policy.require_approval_threshold:
            change.requires_approval = True

        self._pending_changes.append(change)
        logger.debug(f"Queued change: {change.change_type} for project {change.project_id}")

    async def _process_pending_changes(self):
        """Process all pending changes"""
        if not self._pending_changes:
            return

        # Group changes by project for batch processing
        changes_by_project = {}
        for change in self._pending_changes:
            if change.project_id not in changes_by_project:
                changes_by_project[change.project_id] = []
            changes_by_project[change.project_id].append(change)

        # Process each project's changes
        for project_id, changes in changes_by_project.items():
            await self._process_project_changes(project_id, changes)

        # Clear processed changes
        self._pending_changes.clear()

    async def _process_project_changes(
        self,
        project_id: str,
        changes: List[ContextChange]
    ):
        """Process changes for a specific project"""
        for change in changes:
            try:
                if change.requires_approval:
                    # Store for manual approval
                    await self._store_pending_approval(change)
                    continue

                await self._propagate_change(change)

            except Exception as e:
                logger.error(f"Error processing change {change.id}: {e}")

    async def _propagate_change(self, change: ContextChange):
        """Propagate a change to target platforms"""
        if change.change_type == ChangeType.GLOBAL_UPDATED:
            await self._propagate_global_change(change)
        elif change.change_type == ChangeType.INSIGHTS_MERGED:
            await self._propagate_insights(change)
        elif change.change_type == ChangeType.DOMAIN_UPDATED:
            await self._propagate_domain_change(change)

        # Notify subscribers
        await self._notify_subscribers(change)

    async def _propagate_global_change(self, change: ContextChange):
        """Propagate global context changes"""
        for platform in change.target_platforms:
            try:
                # Send notification to platform
                await self._notify_platform_of_global_change(
                    change.project_id,
                    platform,
                    change.changes
                )

                change.propagated_to.add(platform)
                logger.debug(f"Propagated global change to {platform}")

            except Exception as e:
                logger.error(f"Failed to propagate to {platform}: {e}")

    async def _propagate_insights(self, change: ContextChange):
        """Propagate insights to other platforms"""
        insights = change.changes.get("insights", {})

        for platform in change.target_platforms:
            try:
                # Get platform context
                platform_context = await self._platform_repo.get_platform_context_by_type(
                    change.project_id, platform
                )

                if platform_context:
                    # Apply insights based on platform compatibility
                    adapted_insights = await self._adapt_insights_for_platform(
                        insights, platform, change.source_platform
                    )

                    if adapted_insights:
                        # Update platform context
                        platform_context.platform_specific_data.setdefault("shared_insights", {})
                        platform_context.platform_specific_data["shared_insights"].update(adapted_insights)
                        platform_context.last_updated = datetime.utcnow()

                        await self._platform_repo.update_platform_context(platform_context)

                        change.propagated_to.add(platform)
                        logger.debug(f"Propagated insights from {change.source_platform} to {platform}")

            except Exception as e:
                logger.error(f"Failed to propagate insights to {platform}: {e}")

    async def _propagate_domain_change(self, change: ContextChange):
        """Propagate domain context changes"""
        domain_type = change.changes.get("domain_type")
        domain_changes = change.changes.get("changes", {})

        for platform in change.target_platforms:
            try:
                # Notify platform of domain change
                await self._notify_platform_of_domain_change(
                    change.project_id,
                    platform,
                    domain_type,
                    domain_changes
                )

                change.propagated_to.add(platform)

            except Exception as e:
                logger.error(f"Failed to propagate domain change to {platform}: {e}")

    async def _notify_subscribers(self, change: ContextChange):
        """Notify all subscribers of a change"""
        for platform in change.target_platforms:
            key = f"{change.project_id}:{platform}"
            if key in self._change_subscribers:
                for queue in self._change_subscribers[key]:
                    try:
                        await queue.put(change)
                    except:
                        # Remove dead queues
                        pass

    # Insight Processing

    async def _extract_valuable_insights(
        self,
        changes: Dict[str, Any],
        source_platform: str
    ) -> Dict[str, Any]:
        """Extract insights from platform changes that could benefit others"""
        insights = {}

        # Look for learned preferences that could be generally useful
        if "learned_preferences" in changes:
            prefs = changes["learned_preferences"]

            # Extract general coding patterns
            if "coding_patterns" in prefs:
                insights["coding_patterns"] = prefs["coding_patterns"]

            # Extract tool preferences that might be universal
            if "preferred_tools" in prefs:
                insights["tool_recommendations"] = {
                    "source": source_platform,
                    "tools": prefs["preferred_tools"]
                }

        # Look for performance metrics that indicate good practices
        if "performance_metrics" in changes:
            metrics = changes["performance_metrics"]
            if metrics.get("success_rate", 0) > 0.8:  # High success rate
                insights["successful_patterns"] = {
                    "source": source_platform,
                    "patterns": metrics.get("successful_patterns", [])
                }

        # Look for error patterns to avoid
        if "interaction_history" in changes:
            # Analyze for common error patterns
            error_patterns = await self._analyze_error_patterns(changes["interaction_history"])
            if error_patterns:
                insights["error_patterns_to_avoid"] = error_patterns

        return insights

    async def _adapt_insights_for_platform(
        self,
        insights: Dict[str, Any],
        target_platform: str,
        source_platform: str
    ) -> Dict[str, Any]:
        """Adapt insights for a specific platform"""
        adapted = {}

        # Platform-specific adaptations
        platform_adaptations = {
            "claude": {
                "response_style": "detailed_with_examples",
                "format_preference": "structured_markdown"
            },
            "chatgpt": {
                "response_style": "conversational",
                "format_preference": "bullet_points"
            },
            "copilot": {
                "response_style": "code_focused",
                "format_preference": "inline_comments"
            }
        }

        # Apply platform-specific formatting
        for key, value in insights.items():
            if target_platform in platform_adaptations:
                adapted[key] = {
                    "content": value,
                    "source_platform": source_platform,
                    "adapted_for": target_platform,
                    "adaptation_metadata": platform_adaptations[target_platform]
                }
            else:
                adapted[key] = value

        return adapted

    async def _calculate_insight_confidence(
        self,
        insights: Dict[str, Any],
        source_platform: str
    ) -> float:
        """Calculate confidence score for insights"""
        base_confidence = 0.8

        # Increase confidence based on source platform reliability
        platform_reliability = {
            "claude": 0.95,
            "chatgpt": 0.90,
            "copilot": 0.85,
            "custom": 0.75
        }

        reliability = platform_reliability.get(source_platform, 0.75)

        # Increase confidence based on insight type
        insight_weights = {
            "coding_patterns": 0.9,
            "error_patterns_to_avoid": 0.95,
            "successful_patterns": 0.85,
            "tool_recommendations": 0.8
        }

        weighted_confidence = base_confidence
        for insight_type in insights.keys():
            weight = insight_weights.get(insight_type, 0.7)
            weighted_confidence = max(weighted_confidence, weight)

        return min(reliability * weighted_confidence, 1.0)

    # Platform Management

    async def _get_active_platforms(
        self,
        project_id: str,
        exclude: List[str] = None
    ) -> List[str]:
        """Get list of active platforms for a project"""
        exclude = exclude or []

        # Get all platform contexts for the project
        platform_contexts = await self._platform_repo.get_platform_contexts_by_project(project_id)

        active_platforms = []
        for context in platform_contexts:
            if context.platform_type not in exclude:
                # Check if platform is recently active (within last 24 hours)
                if context.last_updated > datetime.utcnow() - timedelta(hours=24):
                    active_platforms.append(context.platform_type)

        return active_platforms

    async def _notify_platform_of_global_change(
        self,
        project_id: str,
        platform_type: str,
        changes: Dict[str, Any]
    ):
        """Notify a platform of global context changes"""
        # This would integrate with the event system
        from driving.webhooks.context_notifications import event_manager

        await event_manager.notify_global_context_updated(
            project_id=project_id,
            changes=changes,
            source_platform="sync_service"
        )

    async def _notify_platform_of_domain_change(
        self,
        project_id: str,
        platform_type: str,
        domain_type: str,
        changes: Dict[str, Any]
    ):
        """Notify a platform of domain context changes"""
        from driving.webhooks.context_notifications import event_manager

        await event_manager.notify_domain_context_updated(
            project_id=project_id,
            domain_type=domain_type,
            changes=changes
        )

    # Cache and Conflict Resolution

    async def _detect_external_changes(self):
        """Detect changes made outside the sync service"""
        # This would check context hashes and detect external modifications
        # Implementation would depend on your specific requirements
        pass

    async def _store_pending_approval(self, change: ContextChange):
        """Store changes that require manual approval"""
        # Store in a pending approvals table/collection
        logger.info(f"Change {change.id} requires approval: confidence {change.confidence_score}")

    async def _analyze_error_patterns(
        self,
        interaction_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze interaction history for error patterns"""
        error_patterns = []

        for interaction in interaction_history:
            if interaction.get("metadata", {}).get("user_satisfaction", 5) < 3:
                # Low satisfaction - extract pattern
                pattern = {
                    "query_type": interaction.get("type"),
                    "common_issues": interaction.get("metadata", {}).get("issues", []),
                    "suggested_improvement": interaction.get("metadata", {}).get("improvement")
                }
                error_patterns.append(pattern)

        return error_patterns

    # Public API for manual operations

    async def force_sync_project(self, project_id: str):
        """Force synchronization of all contexts for a project"""
        logger.info(f"Forcing sync for project {project_id}")

        # Get global context
        global_context = await self._global_repo.get_global_context_by_project(project_id)
        if global_context:
            await self.on_global_context_changed(
                project_id,
                {
                    "shared_knowledge": global_context.shared_knowledge,
                    "shared_conventions": global_context.shared_conventions,
                    "common_patterns": global_context.common_patterns
                },
                "manual_sync"
            )

        # Get all platform contexts and cross-pollinate insights
        platform_contexts = await self._platform_repo.get_platform_contexts_by_project(project_id)

        for context in platform_contexts:
            insights = await self._extract_valuable_insights(
                context.platform_specific_data,
                context.platform_type
            )
            if insights:
                await self.on_platform_context_changed(
                    project_id,
                    context.platform_type,
                    {"shared_insights": insights},
                    propagate_insights=True
                )

    async def get_sync_status(self, project_id: str) -> Dict[str, Any]:
        """Get synchronization status for a project"""
        active_platforms = await self._get_active_platforms(project_id)

        return {
            "project_id": project_id,
            "active_platforms": active_platforms,
            "pending_changes": len([c for c in self._pending_changes if c.project_id == project_id]),
            "sync_policy": {
                "auto_sync_global": self._sync_policy.auto_sync_global,
                "auto_merge_insights": self._sync_policy.auto_merge_insights,
                "require_approval_threshold": self._sync_policy.require_approval_threshold
            },
            "last_sync": datetime.utcnow().isoformat()
        }