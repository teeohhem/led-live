"""
Common error handling utilities.

Provides decorators and context managers for consistent error handling
across the application.
"""
import asyncio
import functools
import logging
from typing import Callable, Optional, Any, TypeVar, Union
from contextlib import contextmanager

T = TypeVar('T')

logger = logging.getLogger(__name__)


def handle_errors(
    default_return: Any = None,
    log_level: int = logging.ERROR,
    reraise: bool = False,
    error_msg: Optional[str] = None
):
    """
    Decorator for consistent error handling.
    
    Usage:
        @handle_errors(default_return=[], log_level=logging.WARNING)
        async def fetch_data():
            return await api.get_data()
        
        # If error occurs, returns [] and logs warning
    
    Args:
        default_return: Value to return on error
        log_level: Logging level for errors
        reraise: Whether to reraise exception after logging
        error_msg: Custom error message prefix
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, Any]]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                func_name = func.__name__
                msg = error_msg or f"Error in {func_name}"
                logger.log(log_level, f"{msg}: {e}", exc_info=True)
                
                if reraise:
                    raise
                
                return default_return
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                func_name = func.__name__
                msg = error_msg or f"Error in {func_name}"
                logger.log(log_level, f"{msg}: {e}", exc_info=True)
                
                if reraise:
                    raise
                
                return default_return
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_exceptions(
    logger_name: Optional[str] = None,
    log_level: int = logging.ERROR,
    message: Optional[str] = None
):
    """
    Decorator to log exceptions without suppressing them.
    
    Usage:
        @log_exceptions(message="Failed to process data")
        async def process_data():
            return await process()
        
        # Exception is logged and re-raised
    
    Args:
        logger_name: Custom logger name (default: function's module)
        log_level: Logging level
        message: Custom error message prefix
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        func_logger = logging.getLogger(logger_name or func.__module__)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                msg = message or f"Exception in {func.__name__}"
                func_logger.log(log_level, f"{msg}: {e}", exc_info=True)
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                msg = message or f"Exception in {func.__name__}"
                func_logger.log(log_level, f"{msg}: {e}", exc_info=True)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def safe_async(
    default_return: Any = None,
    error_msg: Optional[str] = None,
    log_level: int = logging.ERROR
):
    """
    Decorator for async functions that should never crash.
    
    Perfect for background tasks, event handlers, etc.
    
    Usage:
        @safe_async(default_return=False)
        async def background_task():
            await do_something_risky()
            return True
        
        # Always returns without crashing, logs errors
    
    Args:
        default_return: Value to return on error
        error_msg: Custom error message
        log_level: Logging level
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, Any]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except asyncio.CancelledError:
                # Don't suppress cancellation
                raise
            except Exception as e:
                msg = error_msg or f"Error in {func.__name__}"
                logger.log(log_level, f"{msg}: {e}", exc_info=True)
                return default_return
        
        return wrapper
    
    return decorator


@contextmanager
def suppress_errors(
    log: bool = True,
    log_level: int = logging.WARNING,
    message: Optional[str] = None
):
    """
    Context manager to suppress errors with optional logging.
    
    Usage:
        with suppress_errors(message="Non-critical operation failed"):
            risky_operation()
        # Continues execution even if error occurs
    
    Args:
        log: Whether to log errors
        log_level: Logging level if log=True
        message: Custom error message
    """
    try:
        yield
    except Exception as e:
        if log:
            msg = message or "Suppressed error"
            logger.log(log_level, f"{msg}: {e}", exc_info=True)


class ErrorContext:
    """
    Context manager for tracking errors with metrics.
    
    Usage:
        with ErrorContext("data_fetch") as ctx:
            data = fetch_data()
        
        if ctx.had_error:
            logger.warning(f"Fetch failed after {ctx.duration}s")
    """
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.had_error = False
        self.error: Optional[Exception] = None
        self.start_time: Optional[float] = None
        self.duration: Optional[float] = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        self.duration = time.time() - self.start_time
        
        if exc_type is not None:
            self.had_error = True
            self.error = exc_val
            logger.error(
                f"Error in {self.operation_name} after {self.duration:.2f}s: {exc_val}",
                exc_info=True
            )
        
        # Don't suppress the exception
        return False


# Convenience function for retry with exponential backoff
async def retry_with_backoff(
    func: Callable,
    *args,
    max_retries: int = 3,
    backoff_factor: float = 1.5,
    exceptions: tuple = (Exception,),
    **kwargs
) -> Any:
    """
    Retry an async function with exponential backoff.
    
    Usage:
        result = await retry_with_backoff(
            api_call,
            max_retries=3,
            exceptions=(ConnectionError, TimeoutError)
        )
    
    Args:
        func: Async function to retry
        *args: Positional arguments for func
        max_retries: Maximum number of attempts
        backoff_factor: Multiplier for wait time
        exceptions: Tuple of exceptions to catch
        **kwargs: Keyword arguments for func
        
    Returns:
        Result from func
        
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            
            if attempt < max_retries - 1:
                wait_time = backoff_factor ** attempt
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Retrying in {wait_time:.1f}s..."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} attempts failed: {e}")
    
    # Raise the last exception
    raise last_exception

