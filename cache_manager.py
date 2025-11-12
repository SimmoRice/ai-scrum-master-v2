"""
Agent Output Cache Manager

Caches agent execution results to avoid redundant API calls.
Uses hash-based cache keys from agent role, task, and git context.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional


class WorkflowCache:
    """Cache agent outputs for identical prompts and git contexts"""

    def __init__(self, cache_dir: Path = Path("logs/cache")):
        """
        Initialize workflow cache

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "agent_cache.json"
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cache from disk"""
        if self.cache_file.exists():
            try:
                self.cache = json.loads(self.cache_file.read_text())
            except (json.JSONDecodeError, Exception):
                # If cache is corrupted, start fresh
                self.cache = {}
        else:
            self.cache = {}

    def _save_cache(self) -> None:
        """Save cache to disk"""
        try:
            self.cache_file.write_text(json.dumps(self.cache, indent=2))
        except Exception as e:
            # Don't fail workflow if cache save fails
            print(f"⚠️  Warning: Failed to save cache: {e}")

    def _compute_key(
        self,
        agent_role: str,
        task: str,
        git_context: Dict[str, Any]
    ) -> str:
        """
        Compute cache key from agent role, task, and git context

        Args:
            agent_role: Name of the agent (e.g., "Architect")
            task: User story or task description
            git_context: Dictionary with git state info (branch, diff hash, etc.)

        Returns:
            SHA256 hash as cache key
        """
        # Create deterministic cache key
        cache_data = {
            "role": agent_role,
            "task": task,
            "git_diff_hash": git_context.get("git_diff_hash", ""),
            "branch": git_context.get("branch", ""),
            "file_count": git_context.get("file_count", 0)
        }

        # Sort keys for deterministic hashing
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()

    def get(
        self,
        agent_role: str,
        task: str,
        git_context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached result if exists and valid

        Args:
            agent_role: Name of the agent
            task: User story or task description
            git_context: Dictionary with git state info

        Returns:
            Cached result dict if found and valid, None otherwise
        """
        key = self._compute_key(agent_role, task, git_context)

        if key not in self.cache:
            return None

        entry = self.cache[key]

        # Check if cache entry is too old (7 day TTL)
        max_age_seconds = 7 * 24 * 60 * 60  # 7 days
        age = time.time() - entry.get("timestamp", 0)

        if age > max_age_seconds:
            # Cache expired, remove it
            del self.cache[key]
            self._save_cache()
            return None

        # Return the cached result
        return entry.get("result")

    def set(
        self,
        agent_role: str,
        task: str,
        git_context: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """
        Cache agent result

        Args:
            agent_role: Name of the agent
            task: User story or task description
            git_context: Dictionary with git state info
            result: Agent execution result to cache
        """
        key = self._compute_key(agent_role, task, git_context)

        # Only cache successful results
        if not result.get("success", False):
            return

        self.cache[key] = {
            "result": result,
            "timestamp": time.time(),
            "agent_role": agent_role,
            "task_preview": task[:100]  # Store preview for debugging
        }

        self._save_cache()

    def clear_old_entries(self, max_age_days: int = 7) -> int:
        """
        Clear cache entries older than max_age_days

        Args:
            max_age_days: Maximum age in days

        Returns:
            Number of entries removed
        """
        cutoff = time.time() - (max_age_days * 86400)
        initial_count = len(self.cache)

        self.cache = {
            k: v for k, v in self.cache.items()
            if v.get("timestamp", 0) > cutoff
        }

        removed = initial_count - len(self.cache)

        if removed > 0:
            self._save_cache()

        return removed

    def clear_all(self) -> None:
        """Clear all cached entries"""
        self.cache = {}
        self._save_cache()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        total_entries = len(self.cache)
        total_size_bytes = len(json.dumps(self.cache))

        # Count entries per agent
        agent_counts = {}
        for entry in self.cache.values():
            agent = entry.get("agent_role", "unknown")
            agent_counts[agent] = agent_counts.get(agent, 0) + 1

        return {
            "total_entries": total_entries,
            "total_size_kb": round(total_size_bytes / 1024, 2),
            "agents": agent_counts,
            "cache_file": str(self.cache_file)
        }
