"""Distributed Context Cache Service for UCL"""
import asyncio
import json
import redis.asyncio as redis
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import hashlib
import pickle
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached context entry"""
    key: str
    data: Dict[str, Any]
    version: int
    last_updated: datetime
    expires_at: Optional[datetime] = None
    dependencies: List[str] = None  # Keys that this entry depends on


class ContextCacheService:
    """Distributed cache service for context data with intelligent invalidation"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_ttl: int = 3600,  # 1 hour
        namespace: str = "ucl_context"
    ):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.namespace = namespace
        self._redis: Optional[redis.Redis] = None

        # Cache configuration
        self.cache_config = {
            "global_context": {"ttl": 7200, "version_tracking": True},
            "platform_context": {"ttl": 3600, "version_tracking": True},
            "domain_context": {"ttl": 1800, "version_tracking": True},
            "query_results": {"ttl": 900, "version_tracking": False},
            "insights": {"ttl": 86400, "version_tracking": True}  # 24 hours
        }

    async def initialize(self):
        """Initialize Redis connection"""
        self._redis = await redis.from_url(self.redis_url)
        logger.info("Context cache service initialized")

    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()

    def _make_key(self, key_type: str, *args) -> str:
        """Generate cache key"""
        key_parts = [self.namespace, key_type] + list(args)
        return ":".join(str(part) for part in key_parts)

    def _make_version_key(self, base_key: str) -> str:
        """Generate version key for a cache entry"""
        return f"{base_key}:version"

    def _make_dependency_key(self, base_key: str) -> str:
        """Generate dependency key for a cache entry"""
        return f"{base_key}:deps"

    async def get_global_context(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get cached global context"""
        key = self._make_key("global", project_id)
        return await self._get_with_version_check(key)

    async def set_global_context(
        self,
        project_id: str,
        context: Dict[str, Any],
        version: int = None
    ) -> bool:
        """Cache global context"""
        key = self._make_key("global", project_id)
        config = self.cache_config["global_context"]

        success = await self._set_with_version(key, context, config["ttl"], version)

        if success:
            # Invalidate dependent caches
            await self._invalidate_dependents(key)

        return success

    async def get_platform_context(
        self,
        project_id: str,
        platform_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached platform context"""
        key = self._make_key("platform", project_id, platform_type)
        return await self._get_with_version_check(key)

    async def set_platform_context(
        self,
        project_id: str,
        platform_type: str,
        context: Dict[str, Any],
        version: int = None
    ) -> bool:
        """Cache platform context"""
        key = self._make_key("platform", project_id, platform_type)
        config = self.cache_config["platform_context"]

        # Set up dependencies on global context
        global_key = self._make_key("global", project_id)
        dependencies = [global_key]

        return await self._set_with_version(
            key, context, config["ttl"], version, dependencies
        )

    async def get_domain_context(
        self,
        project_id: str,
        domain_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached domain context"""
        key = self._make_key("domain", project_id, domain_type)
        return await self._get_with_version_check(key)

    async def set_domain_context(
        self,
        project_id: str,
        domain_type: str,
        context: Dict[str, Any],
        version: int = None
    ) -> bool:
        """Cache domain context"""
        key = self._make_key("domain", project_id, domain_type)
        config = self.cache_config["domain_context"]

        # Set up dependencies on global context
        global_key = self._make_key("global", project_id)
        dependencies = [global_key]

        success = await self._set_with_version(
            key, context, config["ttl"], version, dependencies
        )

        if success:
            # Invalidate query results that might include this domain
            await self._invalidate_pattern(f"{self.namespace}:query:*")

        return success

    async def get_query_result(
        self,
        project_id: str,
        query_hash: str,
        platform_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached query result"""
        key = self._make_key("query", project_id, platform_type, query_hash)
        return await self._get_simple(key)

    async def set_query_result(
        self,
        project_id: str,
        query_hash: str,
        platform_type: str,
        result: Dict[str, Any]
    ) -> bool:
        """Cache query result"""
        key = self._make_key("query", project_id, platform_type, query_hash)
        config = self.cache_config["query_results"]

        # Query results depend on all contexts
        dependencies = [
            self._make_key("global", project_id),
            self._make_key("platform", project_id, platform_type)
        ]

        # Add domain dependencies based on query content
        if "domains_filter" in result.get("metadata", {}):
            for domain in result["metadata"]["domains_filter"]:
                dependencies.append(self._make_key("domain", project_id, domain))

        return await self._set_with_dependencies(key, result, config["ttl"], dependencies)

    async def get_merged_context(
        self,
        project_id: str,
        platform_type: str,
        include_domains: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get merged context from cache or build it"""
        # Create cache key based on what's included
        include_domains = include_domains or []
        domains_hash = hashlib.md5(":".join(sorted(include_domains)).encode()).hexdigest()[:8]
        cache_key = self._make_key("merged", project_id, platform_type, domains_hash)

        # Try to get from cache
        cached = await self._get_simple(cache_key)
        if cached:
            return cached

        # Build merged context
        merged = {}

        # Get global context
        global_context = await self.get_global_context(project_id)
        if global_context:
            merged["global"] = global_context

        # Get platform context
        platform_context = await self.get_platform_context(project_id, platform_type)
        if platform_context:
            merged["platform"] = platform_context

        # Get domain contexts
        merged["domains"] = {}
        for domain in include_domains:
            domain_context = await self.get_domain_context(project_id, domain)
            if domain_context:
                merged["domains"][domain] = domain_context

        # Cache the merged result with shorter TTL
        if merged:
            await self._set_simple(cache_key, merged, 600)  # 10 minutes

        return merged

    async def invalidate_project(self, project_id: str):
        """Invalidate all cache entries for a project"""
        pattern = f"{self.namespace}:*:{project_id}*"
        await self._invalidate_pattern(pattern)

    async def invalidate_platform(self, project_id: str, platform_type: str):
        """Invalidate platform-specific cache entries"""
        pattern = f"{self.namespace}:*:{project_id}:{platform_type}*"
        await self._invalidate_pattern(pattern)

    async def invalidate_global_context(self, project_id: str):
        """Invalidate global context and all dependents"""
        key = self._make_key("global", project_id)
        await self._invalidate_with_dependents(key)

    # Internal cache operations

    async def _get_with_version_check(self, key: str) -> Optional[Dict[str, Any]]:
        """Get entry with version validation"""
        if not self._redis:
            return None

        try:
            # Get data and version
            pipe = self._redis.pipeline()
            pipe.get(key)
            pipe.get(self._make_version_key(key))
            results = await pipe.execute()

            data_bytes, version_bytes = results

            if not data_bytes:
                return None

            data = pickle.loads(data_bytes)

            # Check if version is still valid
            if version_bytes:
                cached_version = int(version_bytes)
                current_version = data.get("_version", 0)

                if cached_version != current_version:
                    # Version mismatch, invalidate
                    await self._redis.delete(key)
                    return None

            return data

        except Exception as e:
            logger.error(f"Error getting cached entry {key}: {e}")
            return None

    async def _set_with_version(
        self,
        key: str,
        data: Dict[str, Any],
        ttl: int,
        version: int = None,
        dependencies: List[str] = None
    ) -> bool:
        """Set entry with version tracking"""
        if not self._redis:
            return False

        try:
            # Add version to data
            if version is not None:
                data["_version"] = version
            else:
                version = data.get("_version", 1)

            # Serialize data
            data_bytes = pickle.dumps(data)

            # Set data and version atomically
            pipe = self._redis.pipeline()
            pipe.setex(key, ttl, data_bytes)
            pipe.setex(self._make_version_key(key), ttl, version)

            # Set dependencies
            if dependencies:
                deps_key = self._make_dependency_key(key)
                pipe.setex(deps_key, ttl, json.dumps(dependencies))

                # Add this key as dependent of each dependency
                for dep_key in dependencies:
                    dependents_key = f"{dep_key}:dependents"
                    pipe.sadd(dependents_key, key)
                    pipe.expire(dependents_key, ttl)

            await pipe.execute()
            return True

        except Exception as e:
            logger.error(f"Error setting cached entry {key}: {e}")
            return False

    async def _set_with_dependencies(
        self,
        key: str,
        data: Dict[str, Any],
        ttl: int,
        dependencies: List[str]
    ) -> bool:
        """Set entry with dependency tracking"""
        return await self._set_with_version(key, data, ttl, None, dependencies)

    async def _get_simple(self, key: str) -> Optional[Dict[str, Any]]:
        """Simple get without version checking"""
        if not self._redis:
            return None

        try:
            data_bytes = await self._redis.get(key)
            if data_bytes:
                return pickle.loads(data_bytes)
            return None

        except Exception as e:
            logger.error(f"Error getting simple cached entry {key}: {e}")
            return None

    async def _set_simple(self, key: str, data: Dict[str, Any], ttl: int) -> bool:
        """Simple set without version tracking"""
        if not self._redis:
            return False

        try:
            data_bytes = pickle.dumps(data)
            await self._redis.setex(key, ttl, data_bytes)
            return True

        except Exception as e:
            logger.error(f"Error setting simple cached entry {key}: {e}")
            return False

    async def _invalidate_dependents(self, key: str):
        """Invalidate all entries that depend on this key"""
        if not self._redis:
            return

        try:
            dependents_key = f"{key}:dependents"
            dependents = await self._redis.smembers(dependents_key)

            if dependents:
                # Delete all dependents
                keys_to_delete = []
                for dependent in dependents:
                    dependent_str = dependent.decode('utf-8')
                    keys_to_delete.extend([
                        dependent_str,
                        self._make_version_key(dependent_str),
                        self._make_dependency_key(dependent_str)
                    ])

                await self._redis.delete(*keys_to_delete)

            # Clear dependents set
            await self._redis.delete(dependents_key)

        except Exception as e:
            logger.error(f"Error invalidating dependents of {key}: {e}")

    async def _invalidate_with_dependents(self, key: str):
        """Invalidate key and all its dependents"""
        await self._invalidate_dependents(key)

        # Delete the key itself
        await self._redis.delete(
            key,
            self._make_version_key(key),
            self._make_dependency_key(key)
        )

    async def _invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching a pattern"""
        if not self._redis:
            return

        try:
            cursor = 0
            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern, count=100)

                if keys:
                    await self._redis.delete(*keys)

                if cursor == 0:
                    break

        except Exception as e:
            logger.error(f"Error invalidating pattern {pattern}: {e}")

    # Cache statistics and monitoring

    async def get_cache_stats(self, project_id: str) -> Dict[str, Any]:
        """Get cache statistics for a project"""
        if not self._redis:
            return {}

        try:
            stats = {
                "project_id": project_id,
                "cached_entries": {},
                "hit_rates": {},
                "memory_usage": {}
            }

            # Count entries by type
            for entry_type in ["global", "platform", "domain", "query", "merged"]:
                pattern = f"{self.namespace}:{entry_type}:*{project_id}*"
                cursor = 0
                count = 0

                while True:
                    cursor, keys = await self._redis.scan(cursor, match=pattern, count=100)
                    count += len(keys)

                    if cursor == 0:
                        break

                stats["cached_entries"][entry_type] = count

            return stats

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}

    async def warm_cache(self, project_id: str, platform_types: List[str]):
        """Pre-warm cache with commonly accessed data"""
        # This would be called during startup or after major updates
        logger.info(f"Warming cache for project {project_id}")

        # Warm global context
        # global_context = await some_service.get_global_context(project_id)
        # await self.set_global_context(project_id, global_context)

        # Warm platform contexts
        # for platform_type in platform_types:
        #     platform_context = await some_service.get_platform_context(project_id, platform_type)
        #     await self.set_platform_context(project_id, platform_type, platform_context)

        pass  # Implementation depends on your services