#!/usr/bin/env python3
"""
Rate Limiter and Queue Manager for MCP v2 Server
Limits eSIM activations to 100 per hour with queue management
"""

import time
import logging
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, Optional, Tuple
import threading

logger = logging.getLogger(__name__)


class ActivationRateLimiter:
    """
    Rate limiter for eSIM activations
    Limits: 100 activations per hour
    Provides queue management and ETA estimation
    """
    
    def __init__(self, max_per_hour: int = 100):
        self.max_per_hour = max_per_hour
        self.activations = deque()  # Stores (timestamp, firebase_uid) tuples
        self.queue = deque()  # Stores queued requests
        self.lock = threading.Lock()
        
        # Statistics
        self.total_activations = 0
        self.total_queued = 0
        self.total_rejected = 0
        
        logger.info(f"Rate limiter initialized: {max_per_hour} activations/hour")
    
    def _clean_old_activations(self):
        """Remove activations older than 1 hour"""
        now = time.time()
        one_hour_ago = now - 3600
        
        while self.activations and self.activations[0][0] < one_hour_ago:
            self.activations.popleft()
    
    def check_rate_limit(self, firebase_uid: str) -> Tuple[bool, Optional[Dict]]:
        """
        Check if activation is allowed
        Returns: (allowed: bool, info: dict)
        """
        with self.lock:
            self._clean_old_activations()
            
            current_count = len(self.activations)
            
            # Check if under limit
            if current_count < self.max_per_hour:
                # Allow activation
                now = time.time()
                self.activations.append((now, firebase_uid))
                self.total_activations += 1
                
                return True, {
                    "allowed": True,
                    "current_usage": current_count + 1,
                    "limit": self.max_per_hour,
                    "percentage": round((current_count + 1) / self.max_per_hour * 100, 1),
                    "estimated_wait_seconds": 0
                }
            
            # Over limit - calculate wait time
            oldest_activation_time = self.activations[0][0]
            time_until_slot = oldest_activation_time + 3600 - time.time()
            
            return False, {
                "allowed": False,
                "current_usage": current_count,
                "limit": self.max_per_hour,
                "percentage": 100.0,
                "estimated_wait_seconds": max(0, int(time_until_slot)),
                "estimated_wait_minutes": max(0, int(time_until_slot / 60)),
                "queue_position": len(self.queue) + 1
            }
    
    def get_statistics(self) -> Dict:
        """Get rate limiter statistics"""
        with self.lock:
            self._clean_old_activations()
            
            now = time.time()
            one_hour_ago = now - 3600
            
            return {
                "current_hour_activations": len(self.activations),
                "max_per_hour": self.max_per_hour,
                "capacity_used_percentage": round(len(self.activations) / self.max_per_hour * 100, 1),
                "slots_available": max(0, self.max_per_hour - len(self.activations)),
                "total_lifetime_activations": self.total_activations,
                "total_queued": self.total_queued,
                "total_rejected": self.total_rejected,
                "current_queue_size": len(self.queue),
                "window_start": datetime.fromtimestamp(one_hour_ago).isoformat(),
                "window_end": datetime.fromtimestamp(now).isoformat()
            }
    
    def log_activation_attempt(self, firebase_uid: str, email: str, allowed: bool, info: Dict):
        """Log activation attempt for monitoring"""
        timestamp = datetime.now().isoformat()
        
        if allowed:
            logger.info(
                f"[ACTIVATION ALLOWED] "
                f"UID: {firebase_uid[:20]}... | "
                f"Email: {email} | "
                f"Usage: {info['current_usage']}/{info['limit']} ({info['percentage']}%)"
            )
        else:
            logger.warning(
                f"[RATE LIMITED] "
                f"UID: {firebase_uid[:20]}... | "
                f"Email: {email} | "
                f"Wait: {info['estimated_wait_minutes']}min | "
                f"Queue Pos: {info.get('queue_position', 'N/A')}"
            )
            self.total_rejected += 1


# Global rate limiter instance
rate_limiter = ActivationRateLimiter(max_per_hour=100)


def check_activation_allowed(firebase_uid: str, email: str) -> Tuple[bool, Dict]:
    """
    Check if eSIM activation is allowed
    Returns: (allowed, info_dict)
    """
    allowed, info = rate_limiter.check_rate_limit(firebase_uid)
    rate_limiter.log_activation_attempt(firebase_uid, email, allowed, info)
    return allowed, info


def get_rate_limit_stats() -> Dict:
    """Get current rate limit statistics"""
    return rate_limiter.get_statistics()
