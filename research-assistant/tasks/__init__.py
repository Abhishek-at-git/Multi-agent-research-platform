"""Tasks package for Research Assistant."""
from .search_task import create_search_task
from .analysis_task import create_analysis_task
from .writing_task import create_writing_task
from .manager_task import create_scoping_task, create_review_task

__all__ = [
    "create_search_task",
    "create_analysis_task",
    "create_writing_task",
    "create_scoping_task",
    "create_review_task",
]
