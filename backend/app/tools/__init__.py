"""
Tools package for AI Research Assistant.
"""

from .base import (
    get_search_tool,
    get_python_repl_tool,
    search_arxiv,
    search_arxiv_structured,
    execute_python,
    DocumentRetrieverTool,
    get_all_tools,
)

from .deep_research import (
    deep_research,
    deep_research_tool,
    deep_research_stream,
    write_final_report,
    ResearchProgress,
    ResearchResult,
)

# Deep Research V2 - Enhanced version with Pydantic, follow-up questions, etc.
from .deep_research_v2 import (
    # Main functions
    deep_research_v2,
    deep_research_stream_v2,
    deep_research_tool_v2,
    generate_feedback_questions,
    write_final_report as write_final_report_v2,
    # Pydantic models
    SerpQueryModel,
    QueriesResponse,
    LearningsResponse,
    FeedbackResponse,
    ResearchStage,
    # Data classes
    ResearchProgress as ResearchProgressV2,
    ResearchResult as ResearchResultV2,
    ResearchConfig,
)

__all__ = [
    # Base tools
    "get_search_tool",
    "get_python_repl_tool",
    "search_arxiv",
    "search_arxiv_structured",
    "execute_python",
    "DocumentRetrieverTool",
    "get_all_tools",
    # Deep research (original)
    "deep_research",
    "deep_research_tool",
    "deep_research_stream",
    "write_final_report",
    "ResearchProgress",
    "ResearchResult",
    # Deep research V2 (enhanced)
    "deep_research_v2",
    "deep_research_stream_v2",
    "deep_research_tool_v2",
    "generate_feedback_questions",
    "write_final_report_v2",
    "SerpQueryModel",
    "QueriesResponse",
    "LearningsResponse",
    "FeedbackResponse",
    "ResearchStage",
    "ResearchProgressV2",
    "ResearchResultV2",
    "ResearchConfig",
]
