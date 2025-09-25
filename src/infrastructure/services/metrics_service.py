import asyncio
import time
from typing import Dict, Optional, Any
from collections import defaultdict, deque
from datetime import datetime, timedelta
import threading

from src.core.interfaces.services import MetricsService
from src.infrastructure.logging.context import get_logger

logger = get_logger(__name__)


class InMemoryMetricsService(MetricsService):
    """In-memory implementation of metrics service."""
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.retention_period = timedelta(hours=retention_hours)
        
        # Thread-safe storage
        self._lock = threading.RLock()
        
        # Metric storage
        self._counters: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._histograms: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        self._gauges: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        
        # Timestamps for cleanup
        self._counter_timestamps: Dict[str, Dict[str, datetime]] = defaultdict(dict)
        self._histogram_timestamps: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        self._gauge_timestamps: Dict[str, Dict[str, datetime]] = defaultdict(dict)
        
        # Start cleanup task
        self._start_cleanup_task()
        
        logger.info(
            "Metrics service initialized",
            extra={"retention_hours": retention_hours}
        )
    
    async def increment_counter(
        self, 
        name: str, 
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment counter metric."""
        try:
            tag_key = self._serialize_tags(tags or {})
            
            with self._lock:
                self._counters[name][tag_key] += 1
                self._counter_timestamps[name][tag_key] = datetime.now()
            
            logger.debug(
                "Counter incremented",
                extra={
                    "metric_name": name,
                    "tags": tags,
                    "new_value": self._counters[name][tag_key]
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to increment counter",
                extra={
                    "metric_name": name,
                    "tags": tags,
                    "error": str(e)
                },
                exc_info=True
            )
    
    async def record_histogram(
        self, 
        name: str, 
        value: float, 
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record histogram metric."""
        try:
            tag_key = self._serialize_tags(tags or {})
            timestamp = datetime.now()
            
            with self._lock:
                self._histograms[name][tag_key].append(value)
                self._histogram_timestamps[name][tag_key].append(timestamp)
                
                # Keep only recent values
                cutoff_time = timestamp - self.retention_period
                while (self._histogram_timestamps[name][tag_key] and 
                       self._histogram_timestamps[name][tag_key][0] < cutoff_time):
                    self._histograms[name][tag_key].popleft()
                    self._histogram_timestamps[name][tag_key].popleft()
            
            logger.debug(
                "Histogram value recorded",
                extra={
                    "metric_name": name,
                    "value": value,
                    "tags": tags
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to record histogram",
                extra={
                    "metric_name": name,
                    "value": value,
                    "tags": tags,
                    "error": str(e)
                },
                exc_info=True
            )
    
    async def record_gauge(
        self, 
        name: str, 
        value: float, 
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record gauge metric."""
        try:
            tag_key = self._serialize_tags(tags or {})
            
            with self._lock:
                self._gauges[name][tag_key] = value
                self._gauge_timestamps[name][tag_key] = datetime.now()
            
            logger.debug(
                "Gauge value recorded",
                extra={
                    "metric_name": name,
                    "value": value,
                    "tags": tags
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to record gauge",
                extra={
                    "metric_name": name,
                    "value": value,
                    "tags": tags,
                    "error": str(e)
                },
                exc_info=True
            )
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        with self._lock:
            summary = {
                "counters": {},
                "histograms": {},
                "gauges": {},
                "timestamp": datetime.now().isoformat()
            }
            
            # Process counters
            for name, tags_data in self._counters.items():
                summary["counters"][name] = dict(tags_data)
            
            # Process histograms
            for name, tags_data in self._histograms.items():
                summary["histograms"][name] = {}
                for tag_key, values in tags_data.items():
                    if values:
                        summary["histograms"][name][tag_key] = {
                            "count": len(values),
                            "min": min(values),
                            "max": max(values),
                            "mean": sum(values) / len(values),
                            "recent_values": list(values)[-10:]  # Last 10 values
                        }
            
            # Process gauges
            for name, tags_data in self._gauges.items():
                summary["gauges"][name] = dict(tags_data)
            
            return summary
    
    def _serialize_tags(self, tags: Dict[str, str]) -> str:
        """Serialize tags to string key."""
        if not tags:
            return "default"
        
        # Sort tags for consistent keys
        sorted_items = sorted(tags.items())
        return "|".join(f"{k}={v}" for k, v in sorted_items)
    
    def _start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        def cleanup_old_metrics():
            while True:
                try:
                    self._cleanup_old_metrics()
                    # Sleep for 1 hour
                    time.sleep(3600)
                except Exception as e:
                    logger.error(
                        "Error in metrics cleanup task",
                        extra={"error": str(e)},
                        exc_info=True
                    )
                    # Sleep for 10 minutes before retrying
                    time.sleep(600)
        
        cleanup_thread = threading.Thread(target=cleanup_old_metrics, daemon=True)
        cleanup_thread.start()
        logger.info("Metrics cleanup task started")
    
    def _cleanup_old_metrics(self) -> None:
        """Clean up old metrics."""
        cutoff_time = datetime.now() - self.retention_period
        
        with self._lock:
            # Clean up counters
            for name in list(self._counter_timestamps.keys()):
                for tag_key in list(self._counter_timestamps[name].keys()):
                    if self._counter_timestamps[name][tag_key] < cutoff_time:
                        del self._counters[name][tag_key]
                        del self._counter_timestamps[name][tag_key]
                
                # Remove empty metric names
                if not self._counters[name]:
                    del self._counters[name]
                    del self._counter_timestamps[name]
            
            # Clean up gauges
            for name in list(self._gauge_timestamps.keys()):
                for tag_key in list(self._gauge_timestamps[name].keys()):
                    if self._gauge_timestamps[name][tag_key] < cutoff_time:
                        del self._gauges[name][tag_key]
                        del self._gauge_timestamps[name][tag_key]
                
                # Remove empty metric names
                if not self._gauges[name]:
                    del self._gauges[name]
                    del self._gauge_timestamps[name]
        
        logger.debug("Old metrics cleaned up")