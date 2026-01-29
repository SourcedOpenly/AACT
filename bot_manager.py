"""
Bot Manager Module for Concurrent Task Execution

This module provides a framework for managing multiple bot instances
that execute tasks concurrently. Each bot manages its tasks independently
without interfering with others.
"""

import threading
import queue
import time
import logging
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BotState(Enum):
    """Enumeration of possible bot states"""
    IDLE = "idle"
    ACTIVE = "active"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class BotProgress:
    """Data class to track bot progress"""
    bot_id: int
    state: BotState = BotState.IDLE
    tasks_completed: int = 0
    tasks_failed: int = 0
    current_task: Optional[Any] = None
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    def get_elapsed_time(self) -> float:
        """Calculate elapsed time for the bot"""
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert progress to dictionary"""
        return {
            'bot_id': self.bot_id,
            'state': self.state.value,
            'tasks_completed': self.tasks_completed,
            'tasks_failed': self.tasks_failed,
            'current_task': str(self.current_task) if self.current_task else None,
            'error_message': self.error_message,
            'elapsed_time': self.get_elapsed_time()
        }


@dataclass
class TaskResult:
    """Data class to store task execution results"""
    bot_id: int
    task: Any
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0


class Bot:
    """
    Individual bot instance that processes tasks independently
    """
    
    def __init__(
        self,
        bot_id: int,
        task_processor: Callable[[Any], Any],
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize a bot instance
        
        Args:
            bot_id: Unique identifier for the bot
            task_processor: Function to process individual tasks
            max_retries: Maximum number of retry attempts for failed tasks
            retry_delay: Delay in seconds between retries
        """
        self.bot_id = bot_id
        self.task_processor = task_processor
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.progress = BotProgress(bot_id=bot_id)
        self.results: List[TaskResult] = []
        self._lock = threading.Lock()
    
    def process_tasks(self, tasks: List[Any]) -> List[TaskResult]:
        """
        Process a list of tasks assigned to this bot
        
        Args:
            tasks: List of tasks to process
            
        Returns:
            List of TaskResult objects
        """
        logger.info(f"Bot {self.bot_id}: Starting to process {len(tasks)} tasks")
        
        with self._lock:
            self.progress.state = BotState.ACTIVE
            self.progress.start_time = time.time()
        
        for task in tasks:
            result = self._process_single_task(task)
            self.results.append(result)
        
        with self._lock:
            self.progress.state = BotState.COMPLETED
            self.progress.end_time = time.time()
            self.progress.current_task = None
        
        logger.info(
            f"Bot {self.bot_id}: Completed processing. "
            f"Success: {self.progress.tasks_completed}, "
            f"Failed: {self.progress.tasks_failed}"
        )
        
        return self.results
    
    def _process_single_task(self, task: Any) -> TaskResult:
        """
        Process a single task with retry logic
        
        Args:
            task: Task to process
            
        Returns:
            TaskResult object
        """
        with self._lock:
            self.progress.current_task = task
        
        start_time = time.time()
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                result = self.task_processor(task)
                execution_time = time.time() - start_time
                
                with self._lock:
                    self.progress.tasks_completed += 1
                
                return TaskResult(
                    bot_id=self.bot_id,
                    task=task,
                    success=True,
                    result=result,
                    execution_time=execution_time
                )
            
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Bot {self.bot_id}: Task failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        
        # All retries failed
        execution_time = time.time() - start_time
        
        with self._lock:
            self.progress.tasks_failed += 1
            self.progress.error_message = last_error
        
        return TaskResult(
            bot_id=self.bot_id,
            task=task,
            success=False,
            error=last_error,
            execution_time=execution_time
        )
    
    def get_progress(self) -> BotProgress:
        """Get current progress of the bot"""
        with self._lock:
            # Create a snapshot of progress within the lock to ensure consistency
            return BotProgress(
                bot_id=self.progress.bot_id,
                state=self.progress.state,
                tasks_completed=self.progress.tasks_completed,
                tasks_failed=self.progress.tasks_failed,
                current_task=self.progress.current_task,
                error_message=self.progress.error_message,
                start_time=self.progress.start_time,
                end_time=self.progress.end_time
            )


class BotManager:
    """
    Manages multiple bot instances for concurrent task execution
    """
    
    def __init__(
        self,
        num_bots: int,
        task_processor: Callable[[Any], Any],
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize the Bot Manager
        
        Args:
            num_bots: Number of concurrent bots to create
            task_processor: Function to process individual tasks
            max_retries: Maximum number of retry attempts for failed tasks
            retry_delay: Delay in seconds between retries
        """
        if num_bots <= 0:
            raise ValueError(f"Number of bots must be greater than 0, got: {num_bots}")
        
        self.num_bots = num_bots
        self.task_processor = task_processor
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.bots: List[Bot] = []
        self.all_results: List[TaskResult] = []
        self._lock = threading.Lock()
        
        logger.info(f"BotManager initialized with {num_bots} bots")
    
    def _divide_tasks(self, tasks: List[Any]) -> List[List[Any]]:
        """
        Divide tasks into batches for each bot
        
        Args:
            tasks: List of all tasks to be distributed
            
        Returns:
            List of task batches, one per bot
        """
        if not tasks:
            return [[] for _ in range(self.num_bots)]
        
        # Divide tasks as evenly as possible
        batch_size = len(tasks) // self.num_bots
        remainder = len(tasks) % self.num_bots
        
        batches = []
        start_idx = 0
        
        for i in range(self.num_bots):
            # Distribute remainder across first bots
            current_batch_size = batch_size + (1 if i < remainder else 0)
            end_idx = start_idx + current_batch_size
            batches.append(tasks[start_idx:end_idx])
            start_idx = end_idx
        
        return batches
    
    def execute(self, tasks: List[Any]) -> Dict[str, Any]:
        """
        Execute tasks across multiple bots concurrently
        
        Args:
            tasks: List of tasks to be processed
            
        Returns:
            Dictionary containing execution results and statistics
        """
        if not tasks:
            logger.warning("No tasks provided to execute")
            return self._compile_results([])
        
        logger.info(f"Starting execution of {len(tasks)} tasks across {self.num_bots} bots")
        start_time = time.time()
        
        # Divide tasks into batches
        task_batches = self._divide_tasks(tasks)
        
        # Create bot instances
        self.bots = [
            Bot(
                bot_id=i,
                task_processor=self.task_processor,
                max_retries=self.max_retries,
                retry_delay=self.retry_delay
            )
            for i in range(self.num_bots)
        ]
        
        # Execute tasks concurrently using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.num_bots) as executor:
            # Submit tasks to bots
            future_to_bot = {
                executor.submit(bot.process_tasks, batch): bot
                for bot, batch in zip(self.bots, task_batches)
                if batch  # Only submit if batch is not empty
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_bot):
                bot = future_to_bot[future]
                try:
                    results = future.result()
                    with self._lock:
                        self.all_results.extend(results)
                except Exception as e:
                    logger.error(f"Bot {bot.bot_id} encountered an error: {e}")
        
        execution_time = time.time() - start_time
        logger.info(f"All tasks completed in {execution_time:.2f} seconds")
        
        return self._compile_results(self.all_results, execution_time)
    
    def _compile_results(
        self,
        results: List[TaskResult],
        execution_time: float = 0.0
    ) -> Dict[str, Any]:
        """
        Compile results from all bots
        
        Args:
            results: List of all task results
            execution_time: Total execution time
            
        Returns:
            Dictionary with compiled statistics and results
        """
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        return {
            'total_tasks': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / len(results) * 100 if results else 0,
            'execution_time': execution_time,
            'results': results,
            'bot_progress': [bot.get_progress().to_dict() for bot in self.bots],
            'failed_tasks': [
                {
                    'task': r.task,
                    'error': r.error,
                    'bot_id': r.bot_id
                }
                for r in failed
            ]
        }
    
    def get_progress(self) -> List[Dict[str, Any]]:
        """
        Get current progress of all bots
        
        Returns:
            List of progress dictionaries for each bot
        """
        return [bot.get_progress().to_dict() for bot in self.bots]
    
    def monitor_progress(self, interval: float = 1.0, callback: Optional[Callable] = None):
        """
        Monitor progress of bots in real-time
        
        Args:
            interval: Time interval in seconds between progress checks
            callback: Optional callback function to call with progress data
        """
        while any(bot.progress.state == BotState.ACTIVE for bot in self.bots):
            progress = self.get_progress()
            
            if callback:
                callback(progress)
            else:
                # Default: print progress
                for p in progress:
                    if p['state'] == 'active':
                        logger.info(
                            f"Bot {p['bot_id']}: "
                            f"Completed: {p['tasks_completed']}, "
                            f"Failed: {p['tasks_failed']}, "
                            f"Current: {p['current_task']}"
                        )
            
            time.sleep(interval)
