"""
Data Collection Scheduler
Background task scheduler for automated intelligence gathering.

Schedules:
- Real-time market data (every 5 minutes)
- News aggregation (every 30 minutes)
- Policy monitoring (every 4 hours)
- Financial sector analysis (daily)
- Deep market analysis (weekly)
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable, List
from enum import Enum
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class TaskFrequency(str, Enum):
    """Task execution frequency."""
    REALTIME = "realtime"  # Every 5 minutes
    FREQUENT = "frequent"  # Every 30 minutes
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class TaskPriority(str, Enum):
    """Task priority level."""
    CRITICAL = "critical"  # Must run on schedule
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"  # Can be delayed if system busy


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ScheduledTask:
    """Definition of a scheduled data collection task."""
    id: str
    name: str
    frequency: TaskFrequency
    priority: TaskPriority
    handler: Callable
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    last_status: TaskStatus = TaskStatus.PENDING
    last_error: Optional[str] = None
    run_count: int = 0
    error_count: int = 0
    avg_duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    """Result of a task execution."""
    task_id: str
    status: TaskStatus
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    records_processed: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataCollectionScheduler:
    """
    Scheduler for automated data collection tasks.
    
    Features:
    - Multiple frequency levels
    - Priority-based execution
    - Automatic retry on failure
    - Health monitoring
    - Graceful shutdown
    """
    
    # Frequency intervals in seconds
    FREQUENCY_INTERVALS = {
        TaskFrequency.REALTIME: 300,     # 5 minutes
        TaskFrequency.FREQUENT: 1800,    # 30 minutes
        TaskFrequency.HOURLY: 3600,      # 1 hour
        TaskFrequency.DAILY: 86400,      # 24 hours
        TaskFrequency.WEEKLY: 604800,    # 7 days
    }
    
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.results: List[TaskResult] = []
        self.max_results_history = 1000
        self._running = False
        self._loop_task: Optional[asyncio.Task] = None
        
        # Register default tasks
        self._register_default_tasks()
    
    def _register_default_tasks(self):
        """Register default data collection tasks."""
        # Real-time market data
        self.register_task(
            id="aemo_prices",
            name="AEMO Dispatch Prices",
            frequency=TaskFrequency.REALTIME,
            priority=TaskPriority.CRITICAL,
            handler=self._collect_aemo_prices,
        )
        
        # Frequent updates
        self.register_task(
            id="news_aggregation",
            name="News Aggregation",
            frequency=TaskFrequency.FREQUENT,
            priority=TaskPriority.HIGH,
            handler=self._collect_news,
        )
        
        self.register_task(
            id="cer_certificates",
            name="CER Certificate Data",
            frequency=TaskFrequency.FREQUENT,
            priority=TaskPriority.NORMAL,
            handler=self._collect_cer_data,
        )
        
        # Hourly updates
        self.register_task(
            id="carbon_prices",
            name="Carbon Market Prices",
            frequency=TaskFrequency.HOURLY,
            priority=TaskPriority.HIGH,
            handler=self._collect_carbon_prices,
        )
        
        # Daily updates
        self.register_task(
            id="government_policy",
            name="Government Policy Monitor",
            frequency=TaskFrequency.DAILY,
            priority=TaskPriority.NORMAL,
            handler=self._collect_government_data,
        )
        
        self.register_task(
            id="financial_sentiment",
            name="Financial Sector Sentiment",
            frequency=TaskFrequency.DAILY,
            priority=TaskPriority.NORMAL,
            handler=self._collect_financial_sentiment,
        )
        
        self.register_task(
            id="bank_lending",
            name="Bank Lending Analysis",
            frequency=TaskFrequency.DAILY,
            priority=TaskPriority.HIGH,
            handler=self._collect_bank_data,
        )
        
        # Weekly updates
        self.register_task(
            id="deep_analysis",
            name="Deep Market Analysis",
            frequency=TaskFrequency.WEEKLY,
            priority=TaskPriority.LOW,
            handler=self._run_deep_analysis,
        )
    
    def register_task(
        self,
        id: str,
        name: str,
        frequency: TaskFrequency,
        priority: TaskPriority,
        handler: Callable,
        enabled: bool = True,
    ):
        """Register a new scheduled task."""
        task = ScheduledTask(
            id=id,
            name=name,
            frequency=frequency,
            priority=priority,
            handler=handler,
            enabled=enabled,
            next_run=datetime.utcnow(),
        )
        self.tasks[id] = task
        logger.info(f"Registered task: {name} ({frequency.value})")
    
    def enable_task(self, task_id: str):
        """Enable a task."""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
    
    def disable_task(self, task_id: str):
        """Disable a task."""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
    
    async def start(self):
        """Start the scheduler loop."""
        if self._running:
            return
        
        self._running = True
        self._loop_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Data collection scheduler started")
    
    async def stop(self):
        """Stop the scheduler gracefully."""
        self._running = False
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
        logger.info("Data collection scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                await self._check_and_run_tasks()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)
    
    async def _check_and_run_tasks(self):
        """Check for due tasks and run them."""
        now = datetime.utcnow()
        
        # Get tasks sorted by priority
        due_tasks = [
            task for task in self.tasks.values()
            if task.enabled
            and task.next_run
            and task.next_run <= now
            and task.last_status != TaskStatus.RUNNING
        ]
        
        due_tasks.sort(key=lambda t: (
            list(TaskPriority).index(t.priority),
            t.next_run
        ))
        
        for task in due_tasks:
            await self._run_task(task)
    
    async def _run_task(self, task: ScheduledTask):
        """Execute a single task."""
        started_at = datetime.utcnow()
        task.last_status = TaskStatus.RUNNING
        
        try:
            logger.info(f"Running task: {task.name}")
            records = await task.handler()
            
            completed_at = datetime.utcnow()
            duration = (completed_at - started_at).total_seconds()
            
            # Update task stats
            task.last_run = completed_at
            task.last_status = TaskStatus.COMPLETED
            task.run_count += 1
            task.avg_duration_seconds = (
                (task.avg_duration_seconds * (task.run_count - 1) + duration)
                / task.run_count
            )
            task.next_run = completed_at + timedelta(
                seconds=self.FREQUENCY_INTERVALS[task.frequency]
            )
            
            # Store result
            result = TaskResult(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                records_processed=records if isinstance(records, int) else 0,
            )
            self._store_result(result)
            
            logger.info(f"Task completed: {task.name} ({duration:.2f}s)")
            
        except Exception as e:
            completed_at = datetime.utcnow()
            duration = (completed_at - started_at).total_seconds()
            
            task.last_status = TaskStatus.FAILED
            task.error_count += 1
            task.last_error = str(e)
            # Retry after 5 minutes on failure
            task.next_run = completed_at + timedelta(minutes=5)
            
            result = TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                error_message=str(e),
            )
            self._store_result(result)
            
            logger.error(f"Task failed: {task.name} - {e}")
    
    def _store_result(self, result: TaskResult):
        """Store task result, maintaining history limit."""
        self.results.append(result)
        if len(self.results) > self.max_results_history:
            self.results = self.results[-self.max_results_history:]
    
    async def run_task_now(self, task_id: str) -> Optional[TaskResult]:
        """Manually trigger a task to run immediately."""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        await self._run_task(task)
        return self.results[-1] if self.results else None
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        return {
            "running": self._running,
            "task_count": len(self.tasks),
            "enabled_tasks": sum(1 for t in self.tasks.values() if t.enabled),
            "recent_results": len(self.results),
            "tasks": {
                task_id: {
                    "name": task.name,
                    "frequency": task.frequency.value,
                    "priority": task.priority.value,
                    "enabled": task.enabled,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "next_run": task.next_run.isoformat() if task.next_run else None,
                    "last_status": task.last_status.value,
                    "run_count": task.run_count,
                    "error_count": task.error_count,
                }
                for task_id, task in self.tasks.items()
            }
        }
    
    def get_health(self) -> Dict[str, Any]:
        """Get scheduler health metrics."""
        recent_failures = sum(
            1 for r in self.results[-100:]
            if r.status == TaskStatus.FAILED
        )
        
        return {
            "status": "healthy" if recent_failures < 10 else "degraded",
            "recent_failure_rate": recent_failures / min(len(self.results), 100) if self.results else 0,
            "tasks_running": sum(
                1 for t in self.tasks.values()
                if t.last_status == TaskStatus.RUNNING
            ),
            "tasks_failing": sum(
                1 for t in self.tasks.values()
                if t.last_status == TaskStatus.FAILED
            ),
        }
    
    # Task handlers
    async def _collect_aemo_prices(self) -> int:
        """Collect AEMO market prices."""
        # Would use AEMOScraper
        logger.debug("Collecting AEMO prices...")
        await asyncio.sleep(0.1)  # Simulate work
        return 5  # records
    
    async def _collect_news(self) -> int:
        """Aggregate news from all sources."""
        # Would use RenewEconomyScraper and other news sources
        logger.debug("Collecting news...")
        await asyncio.sleep(0.1)
        return 20
    
    async def _collect_cer_data(self) -> int:
        """Collect CER certificate data."""
        # Would use CERScraper
        logger.debug("Collecting CER data...")
        await asyncio.sleep(0.1)
        return 10
    
    async def _collect_carbon_prices(self) -> int:
        """Collect carbon market prices."""
        logger.debug("Collecting carbon prices...")
        await asyncio.sleep(0.1)
        return 3
    
    async def _collect_government_data(self) -> int:
        """Collect government policy data."""
        # Would use GovernmentDataAggregator
        logger.debug("Collecting government data...")
        await asyncio.sleep(0.1)
        return 15
    
    async def _collect_financial_sentiment(self) -> int:
        """Collect financial sector sentiment."""
        # Would use FinancialIntelligenceAggregator
        logger.debug("Collecting financial sentiment...")
        await asyncio.sleep(0.1)
        return 8
    
    async def _collect_bank_data(self) -> int:
        """Collect bank lending analysis."""
        # Would use MajorBankScraper
        logger.debug("Collecting bank data...")
        await asyncio.sleep(0.1)
        return 5
    
    async def _run_deep_analysis(self) -> int:
        """Run deep market analysis."""
        logger.debug("Running deep analysis...")
        await asyncio.sleep(0.1)
        return 50


# Global scheduler instance
_scheduler: Optional[DataCollectionScheduler] = None


def get_scheduler() -> DataCollectionScheduler:
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = DataCollectionScheduler()
    return _scheduler


async def start_scheduler():
    """Start the global scheduler."""
    scheduler = get_scheduler()
    await scheduler.start()


async def stop_scheduler():
    """Stop the global scheduler."""
    scheduler = get_scheduler()
    await scheduler.stop()
