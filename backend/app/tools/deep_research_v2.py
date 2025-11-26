"""
Deep Recursive Research Tool v2.

Enhanced version inspired by dzhng/deep-research with:
- Follow-up questions to clarify research direction
- Pydantic structured output with validation
- Better concurrency control with asyncio.Semaphore
- Improved progress tracking with detailed metrics
- Learnings accumulation across iterations
- ArXiv paper search integration

Key Features:
- Generate clarifying questions before starting
- Structured output with Pydantic models
- Concurrent processing with rate limiting
- Recursive depth control with context preservation
- Comprehensive Markdown report generation
"""

import asyncio
import os
import json
from typing import List, Dict, Any, Optional, Callable, AsyncGenerator, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings


# =============================================================================
# Pydantic Models for Structured Output
# =============================================================================

class SerpQueryModel(BaseModel):
    """A search query with research goal."""
    query: str = Field(..., description="The search query to execute")
    research_goal: str = Field(..., description="Goal and how to advance research with this query")


class QueriesResponse(BaseModel):
    """Response containing generated SERP queries."""
    queries: List[SerpQueryModel] = Field(default_factory=list, description="List of search queries")


class LearningsResponse(BaseModel):
    """Response containing learnings and follow-up questions."""
    learnings: List[str] = Field(default_factory=list, description="Key learnings extracted from search results")
    follow_up_questions: List[str] = Field(default_factory=list, description="Follow-up questions to explore further")


class FeedbackResponse(BaseModel):
    """Response containing clarifying questions."""
    questions: List[str] = Field(default_factory=list, description="Clarifying questions to understand research needs")


class ResearchStage(str, Enum):
    """Stages of the research process."""
    INITIALIZING = "initializing"
    GENERATING_FEEDBACK = "generating_feedback"
    WAITING_FEEDBACK = "waiting_feedback"
    GENERATING_QUERIES = "generating_queries"
    SEARCHING = "searching"
    SEARCHING_WEB = "searching_web"
    SEARCHING_ARXIV = "searching_arxiv"
    PROCESSING = "processing"
    REFLECTING = "reflecting"
    RECURSING = "recursing"
    GENERATING_REPORT = "generating_report"
    COMPLETED = "completed"
    ERROR = "error"


# =============================================================================
# Enhanced Data Classes
# =============================================================================

@dataclass
class ResearchProgress:
    """Enhanced progress tracking for deep research."""
    current_depth: int
    total_depth: int
    current_breadth: int
    total_breadth: int
    total_queries: int = 0
    completed_queries: int = 0
    current_query: Optional[str] = None
    stage: ResearchStage = ResearchStage.INITIALIZING
    message: str = ""
    progress_percent: int = 0
    learnings_count: int = 0
    sources_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "current_depth": self.current_depth,
            "total_depth": self.total_depth,
            "current_breadth": self.current_breadth,
            "total_breadth": self.total_breadth,
            "total_queries": self.total_queries,
            "completed_queries": self.completed_queries,
            "current_query": self.current_query,
            "stage": self.stage.value if isinstance(self.stage, ResearchStage) else self.stage,
            "message": self.message,
            "progress_percent": self.progress_percent,
            "learnings_count": self.learnings_count,
            "sources_count": self.sources_count
        }


@dataclass
class ResearchResult:
    """Enhanced result from deep research."""
    learnings: List[str] = field(default_factory=list)
    visited_urls: List[str] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    total_searches: int = 0
    max_depth_reached: int = 0


@dataclass 
class ResearchConfig:
    """Configuration for research session."""
    breadth: int = 4
    depth: int = 2
    concurrency_limit: int = 2
    include_arxiv: bool = True
    language: str = "vi"
    max_results_per_search: int = 5
    max_learnings_per_result: int = 5
    timeout_seconds: int = 300


# =============================================================================
# LLM Setup
# =============================================================================

def get_llm(temperature: float = 0.3):
    """Get LLM based on configuration."""
    google_key = settings.effective_google_api_key
    
    if settings.llm_provider == "megallm" and settings.megallm_api_key:
        return ChatOpenAI(
            model=settings.megallm_model,
            temperature=temperature,
            api_key=settings.megallm_api_key,  # type: ignore
            base_url=settings.megallm_base_url
        )
    elif settings.openai_api_key:
        return ChatOpenAI(
            model=settings.model_name,
            temperature=temperature,
            api_key=settings.openai_api_key  # type: ignore
        )
    elif google_key:
        return ChatGoogleGenerativeAI(
            model=settings.google_model,
            temperature=temperature,
            google_api_key=google_key  # type: ignore
        )
    else:
        raise ValueError("No LLM API key configured")


# =============================================================================
# System Prompt
# =============================================================================

def get_system_prompt(language: str = "vi") -> str:
    """Get the system prompt for research."""
    now = datetime.now().isoformat()
    
    if language == "vi":
        return f"""Bạn là một nhà nghiên cứu chuyên gia. Hôm nay là {now}. Hãy tuân theo các hướng dẫn sau:
- Bạn có thể được yêu cầu nghiên cứu các chủ đề sau ngày cắt kiến thức của bạn, hãy giả định người dùng đúng khi được trình bày tin tức mới.
- Người dùng là một nhà phân tích có kinh nghiệm cao, không cần đơn giản hóa, hãy chi tiết nhất có thể.
- Hãy tổ chức tốt.
- Đề xuất các giải pháp mà người dùng chưa nghĩ đến.
- Chủ động và dự đoán nhu cầu.
- Coi người dùng như một chuyên gia trong tất cả các lĩnh vực.
- Sai sót làm giảm niềm tin, vì vậy hãy chính xác và kỹ lưỡng.
- Cung cấp giải thích chi tiết với nhiều thông tin.
- Đánh giá cao lập luận tốt hơn nguồn, nguồn không quan trọng.
- Xem xét các công nghệ mới và ý tưởng trái chiều, không chỉ quan điểm thông thường.
- Bạn có thể sử dụng mức độ suy đoán hoặc dự đoán cao, chỉ cần đánh dấu rõ."""
    else:
        return f"""You are an expert researcher. Today is {now}. Follow these instructions:
- You may be asked to research subjects after your knowledge cutoff, assume the user is right when presented with news.
- The user is a highly experienced analyst, no need to simplify, be as detailed as possible.
- Be highly organized.
- Suggest solutions that weren't thought about.
- Be proactive and anticipate needs.
- Treat the user as an expert in all subject matter.
- Mistakes erode trust, so be accurate and thorough.
- Provide detailed explanations with lots of detail.
- Value good arguments over authorities, the source is irrelevant.
- Consider new technologies and contrarian ideas, not just conventional wisdom.
- You may use high levels of speculation or prediction, just flag it."""


# =============================================================================
# Generate Follow-up Questions (from dzhng/deep-research feedback.ts)
# =============================================================================

FEEDBACK_PROMPT = """Given the following query from the user, generate follow-up questions to clarify the research direction. Return a maximum of {num_questions} questions, but feel free to return less if the original query is clear.

<query>{query}</query>

Return a JSON object with format:
{{
    "questions": ["question 1", "question 2", ...]
}}

Only return valid JSON, no other text."""


async def generate_feedback_questions(
    query: str,
    num_questions: int = 3,
    language: str = "vi"
) -> List[str]:
    """
    Generate clarifying questions to better understand research needs.
    
    This is called before starting deep research to refine the query.
    """
    llm = get_llm(temperature=0.5)
    
    prompt = FEEDBACK_PROMPT.format(
        query=query,
        num_questions=num_questions
    )
    
    try:
        response = await llm.ainvoke([
            SystemMessage(content=get_system_prompt(language)),
            HumanMessage(content=prompt)
        ])
        content = response.content
        
        if isinstance(content, str):
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                json_str = content[start:end]
                data = json.loads(json_str)
                return data.get("questions", [])[:num_questions]
        
        return []
        
    except Exception as e:
        print(f"Error generating feedback questions: {e}")
        return []


# =============================================================================
# Web Search with Tavily
# =============================================================================

async def search_tavily(
    query: str, 
    num_results: int = 5,
    timeout: int = 15
) -> Dict[str, Any]:
    """Search web using Tavily API with timeout."""
    if not settings.tavily_api_key:
        return {"data": [], "error": "Tavily API key not configured"}
    
    os.environ["TAVILY_API_KEY"] = settings.tavily_api_key
    
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults
        
        search_tool = TavilySearchResults(
            max_results=num_results,
            search_depth="advanced",
            include_raw_content=True,
        )
        
        # Run with timeout
        results = await asyncio.wait_for(
            asyncio.to_thread(search_tool.invoke, query),
            timeout=timeout
        )
        
        # Transform to format similar to Firecrawl
        data = []
        if isinstance(results, list):
            for r in results:
                data.append({
                    "url": r.get("url", ""),
                    "title": r.get("title", ""),
                    "markdown": r.get("content", ""),
                })
        
        return {"data": data}
        
    except asyncio.TimeoutError:
        print(f"Tavily search timeout for: {query}")
        return {"data": [], "error": "Search timeout"}
    except Exception as e:
        print(f"Tavily search error: {e}")
        return {"data": [], "error": str(e)}


# =============================================================================
# ArXiv Search Integration
# =============================================================================

async def search_arxiv(
    query: str,
    max_results: int = 3
) -> Dict[str, Any]:
    """Search ArXiv for academic papers."""
    try:
        import arxiv
        
        # Clean query for ArXiv
        clean_query = query.replace('"', '').replace("'", "")
        
        client = arxiv.Client()
        search = arxiv.Search(
            query=clean_query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        results = await asyncio.to_thread(lambda: list(client.results(search)))
        
        data = []
        for paper in results:
            data.append({
                "url": paper.entry_id,
                "title": paper.title,
                "markdown": f"**{paper.title}**\n\nAuthors: {', '.join(a.name for a in paper.authors)}\n\nAbstract: {paper.summary}\n\nPublished: {paper.published.strftime('%Y-%m-%d')}",
            })
        
        return {"data": data, "source": "arxiv"}
        
    except Exception as e:
        print(f"ArXiv search error: {e}")
        return {"data": [], "error": str(e)}


# =============================================================================
# Generate SERP Queries with Structured Output
# =============================================================================

GENERATE_QUERIES_PROMPT = """Given the following prompt from the user, generate a list of SERP queries to research the topic. Return a maximum of {num_queries} queries, but feel free to return less if the original prompt is clear. Make sure each query is unique and not similar to each other.

<prompt>{query}</prompt>

{learnings_section}

For each query, provide:
1. The actual search query
2. The research goal - what you're trying to discover and how to advance research

Return a JSON object with format:
{{
    "queries": [
        {{"query": "search query 1", "research_goal": "detailed goal and next steps"}},
        {{"query": "search query 2", "research_goal": "detailed goal and next steps"}}
    ]
}}

Only return valid JSON, no other text."""


async def generate_serp_queries(
    query: str,
    num_queries: int = 4,
    learnings: Optional[List[str]] = None,
    language: str = "vi"
) -> List[SerpQueryModel]:
    """Generate SERP queries for research topic with structured output."""
    llm = get_llm(temperature=0.4)
    
    learnings_section = ""
    if learnings and len(learnings) > 0:
        learnings_text = "\n".join(f"- {l}" for l in learnings[-10:])  # Last 10 learnings
        learnings_section = f"""Here are learnings from previous research. Use them to generate more specific and advanced queries:

<learnings>
{learnings_text}
</learnings>"""
    
    prompt = GENERATE_QUERIES_PROMPT.format(
        query=query,
        num_queries=num_queries,
        learnings_section=learnings_section
    )
    
    try:
        response = await llm.ainvoke([
            SystemMessage(content=get_system_prompt(language)),
            HumanMessage(content=prompt)
        ])
        content = response.content
        
        if isinstance(content, str):
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                json_str = content[start:end]
                data = json.loads(json_str)
                queries = data.get("queries", [])
                return [
                    SerpQueryModel(
                        query=q.get("query", ""),
                        research_goal=q.get("research_goal", q.get("researchGoal", ""))
                    )
                    for q in queries[:num_queries]
                    if q.get("query")
                ]
        
        # Fallback to original query
        return [SerpQueryModel(query=query, research_goal="Main research query")]
        
    except Exception as e:
        print(f"Error generating queries: {e}")
        return [SerpQueryModel(query=query, research_goal="Main research query")]


# =============================================================================
# Process Search Results with Structured Output
# =============================================================================

PROCESS_RESULTS_PROMPT = """Given the following contents from a search for the query <query>{query}</query>, extract key learnings and generate follow-up questions.

Rules:
1. Extract maximum {num_learnings} unique learnings
2. Each learning should be information-dense and include specific facts, numbers, dates, names
3. Generate {num_follow_up} follow-up questions to explore the topic further
4. Make learnings concise but detailed

<contents>
{contents}
</contents>

Return a JSON object with format:
{{
    "learnings": ["detailed learning 1 with specific facts", "detailed learning 2", ...],
    "follow_up_questions": ["follow-up question 1", "follow-up question 2", ...]
}}

Only return valid JSON, no other text."""


async def process_serp_result(
    query: str,
    search_result: Dict[str, Any],
    num_learnings: int = 5,
    num_follow_up_questions: int = 3,
    language: str = "vi"
) -> LearningsResponse:
    """Process search results to extract learnings with structured output."""
    data = search_result.get("data", [])
    if not data:
        return LearningsResponse()
    
    llm = get_llm(temperature=0.2)
    
    # Format contents with size limit
    contents = []
    total_chars = 0
    max_chars = 15000
    
    for item in data:
        markdown = item.get("markdown", "")
        title = item.get("title", "")
        url = item.get("url", "")
        
        if markdown:
            content_text = f"Source: {url}\nTitle: {title}\n{markdown}"
            if total_chars + len(content_text) <= max_chars:
                contents.append(f"<content>\n{content_text}\n</content>")
                total_chars += len(content_text)
    
    if not contents:
        return LearningsResponse()
    
    prompt = PROCESS_RESULTS_PROMPT.format(
        query=query,
        num_learnings=num_learnings,
        num_follow_up=num_follow_up_questions,
        contents="\n".join(contents)
    )
    
    try:
        response = await llm.ainvoke([
            SystemMessage(content=get_system_prompt(language)),
            HumanMessage(content=prompt)
        ])
        content = response.content
        
        if isinstance(content, str):
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                data = json.loads(content[start:end])
                return LearningsResponse(
                    learnings=data.get("learnings", []),
                    follow_up_questions=data.get("follow_up_questions", data.get("followUpQuestions", []))
                )
        
        return LearningsResponse()
        
    except Exception as e:
        print(f"Error processing results: {e}")
        return LearningsResponse()


# =============================================================================
# Write Final Report with Structured Format
# =============================================================================

FINAL_REPORT_PROMPT_VI = """Dựa trên yêu cầu nghiên cứu sau từ người dùng, hãy viết một báo cáo nghiên cứu toàn diện sử dụng các kết quả học được từ quá trình nghiên cứu.

<prompt>{prompt}</prompt>

Đây là tất cả các kết quả nghiên cứu:

<learnings>
{learnings}
</learnings>

Hãy viết báo cáo chi tiết bằng tiếng Việt theo cấu trúc Markdown:

# [Tiêu đề báo cáo]

## Tóm tắt điều hành
[Tóm tắt ngắn gọn các phát hiện chính]

## Các phát hiện chính
[Chi tiết các phát hiện quan trọng nhất]

## Phân tích chi tiết
[Phân tích sâu về các chủ đề nghiên cứu]

## Kết luận và Khuyến nghị
[Kết luận và các bước tiếp theo được đề xuất]

## Nguồn tham khảo
[Sẽ được thêm tự động]

Hãy viết chi tiết, ít nhất 1500 từ, bao gồm TẤT CẢ các learnings đã được cung cấp."""


FINAL_REPORT_PROMPT_EN = """Given the following research prompt from the user, write a comprehensive research report using the learnings from research.

<prompt>{prompt}</prompt>

Here are all the learnings from research:

<learnings>
{learnings}
</learnings>

Write a detailed report in Markdown format with the following structure:

# [Report Title]

## Executive Summary
[Brief summary of key findings]

## Key Findings
[Detailed key discoveries]

## Detailed Analysis
[In-depth analysis of research topics]

## Conclusions and Recommendations
[Conclusions and suggested next steps]

## References
[Will be added automatically]

Write in detail, at least 1500 words, including ALL the learnings provided."""


async def write_final_report(
    prompt: str,
    learnings: List[str],
    visited_urls: List[str],
    language: str = "vi"
) -> str:
    """Generate final research report with comprehensive structure."""
    llm = get_llm(temperature=0.4)
    
    learnings_text = "\n".join(f"<learning>{l}</learning>" for l in learnings)
    
    report_prompt = (FINAL_REPORT_PROMPT_VI if language == "vi" else FINAL_REPORT_PROMPT_EN).format(
        prompt=prompt,
        learnings=learnings_text
    )
    
    try:
        response = await llm.ainvoke([
            SystemMessage(content=get_system_prompt(language)),
            HumanMessage(content=report_prompt)
        ])
        report = response.content if isinstance(response.content, str) else str(response.content)
        
        # Append sources section
        if visited_urls:
            urls_section = "\n\n## Nguồn tham khảo\n\n" if language == "vi" else "\n\n## References\n\n"
            for url in visited_urls[:20]:  # Limit to 20 sources
                urls_section += f"- {url}\n"
            report += urls_section
        
        return report
        
    except Exception as e:
        return f"Error generating report: {str(e)}"


# =============================================================================
# Deep Research Core Function v2
# =============================================================================

async def deep_research_v2(
    query: str,
    config: Optional[ResearchConfig] = None,
    learnings: Optional[List[str]] = None,
    visited_urls: Optional[List[str]] = None,
    on_progress: Optional[Callable[[ResearchProgress], None]] = None,
    feedback_answers: Optional[List[str]] = None
) -> ResearchResult:
    """
    Enhanced deep recursive research on a topic.
    
    Args:
        query: Research query/topic
        config: Research configuration (breadth, depth, etc.)
        learnings: Previous learnings to build upon
        visited_urls: Already visited URLs
        on_progress: Callback for progress updates
        feedback_answers: Answers to clarifying questions
    
    Returns:
        ResearchResult with learnings, URLs, and follow-up questions
    """
    if config is None:
        config = ResearchConfig()
    
    if learnings is None:
        learnings = []
    if visited_urls is None:
        visited_urls = []
    
    # Build enhanced query with feedback answers
    enhanced_query = query
    if feedback_answers:
        enhanced_query = f"""Initial Query: {query}

Additional Context from user:
{chr(10).join(f'- {a}' for a in feedback_answers)}
"""
    
    progress = ResearchProgress(
        current_depth=config.depth,
        total_depth=config.depth,
        current_breadth=config.breadth,
        total_breadth=config.breadth,
        stage=ResearchStage.GENERATING_QUERIES,
        message="Generating search queries...",
        progress_percent=5,
        learnings_count=len(learnings),
        sources_count=len(visited_urls)
    )
    
    def report_progress(update: Dict[str, Any]):
        for key, value in update.items():
            if hasattr(progress, key):
                setattr(progress, key, value)
        if on_progress:
            on_progress(progress)
    
    # Generate search queries
    report_progress({
        "stage": ResearchStage.GENERATING_QUERIES,
        "message": f"Generating {config.breadth} search queries...",
        "progress_percent": 10
    })
    
    serp_queries = await generate_serp_queries(
        query=enhanced_query,
        learnings=learnings,
        num_queries=config.breadth,
        language=config.language
    )
    
    report_progress({
        "total_queries": len(serp_queries),
        "current_query": serp_queries[0].query if serp_queries else None,
        "stage": ResearchStage.SEARCHING,
        "message": f"Starting {len(serp_queries)} searches...",
        "progress_percent": 15
    })
    
    # Process queries with concurrency control
    semaphore = asyncio.Semaphore(config.concurrency_limit)
    total_searches = 0
    all_follow_ups: List[str] = []
    
    async def process_query(serp_query: SerpQueryModel, idx: int) -> ResearchResult:
        nonlocal total_searches
        
        async with semaphore:
            try:
                query_progress = 15 + (idx * 50 // max(1, len(serp_queries)))
                
                report_progress({
                    "current_query": serp_query.query,
                    "stage": ResearchStage.SEARCHING_WEB,
                    "message": f"[{idx+1}/{len(serp_queries)}] Searching: {serp_query.query[:50]}...",
                    "progress_percent": query_progress
                })
                
                # Web search
                web_result = await search_tavily(
                    serp_query.query, 
                    num_results=config.max_results_per_search
                )
                
                # Collect URLs
                new_urls = [
                    item.get("url", "") 
                    for item in web_result.get("data", []) 
                    if item.get("url")
                ]
                
                # ArXiv search if enabled
                arxiv_result: Dict[str, Any] = {"data": []}
                if config.include_arxiv:
                    report_progress({
                        "stage": ResearchStage.SEARCHING_ARXIV,
                        "message": f"Searching ArXiv for: {serp_query.query[:40]}..."
                    })
                    arxiv_result = await search_arxiv(serp_query.query, max_results=2)
                    new_urls.extend([
                        item.get("url", "") 
                        for item in arxiv_result.get("data", []) 
                        if item.get("url")
                    ])
                
                # Combine results
                combined_result = {
                    "data": web_result.get("data", []) + arxiv_result.get("data", [])
                }
                
                total_searches += 1
                
                # Process results
                report_progress({
                    "stage": ResearchStage.PROCESSING,
                    "message": f"Processing results for: {serp_query.query[:40]}...",
                    "progress_percent": query_progress + 10
                })
                
                processed = await process_serp_result(
                    query=serp_query.query,
                    search_result=combined_result,
                    num_learnings=config.max_learnings_per_result,
                    num_follow_up_questions=max(1, config.breadth // 2),
                    language=config.language
                )
                
                new_learnings = processed.learnings
                follow_up_questions = processed.follow_up_questions
                all_follow_ups.extend(follow_up_questions)
                
                all_learnings = learnings + new_learnings
                all_urls = visited_urls + new_urls
                
                report_progress({
                    "learnings_count": len(all_learnings),
                    "sources_count": len(all_urls)
                })
                
                # Calculate new depth
                new_breadth = max(1, config.breadth // 2)
                new_depth = config.depth - 1
                
                # Recurse if depth > 0 and we have follow-ups
                if new_depth > 0 and follow_up_questions:
                    report_progress({
                        "current_depth": new_depth,
                        "current_breadth": new_breadth,
                        "stage": ResearchStage.RECURSING,
                        "message": f"Diving deeper (depth={new_depth})..."
                    })
                    
                    # Build next query from follow-ups
                    next_query = f"""Previous research goal: {serp_query.research_goal}

Follow-up research directions:
{chr(10).join(f'- {q}' for q in follow_up_questions[:3])}

Key learnings so far:
{chr(10).join(f'- {l}' for l in new_learnings[:3])}
""".strip()
                    
                    # Create new config with reduced depth
                    new_config = ResearchConfig(
                        breadth=new_breadth,
                        depth=new_depth,
                        concurrency_limit=config.concurrency_limit,
                        include_arxiv=config.include_arxiv,
                        language=config.language,
                        max_results_per_search=config.max_results_per_search,
                        max_learnings_per_result=config.max_learnings_per_result
                    )
                    
                    return await deep_research_v2(
                        query=next_query,
                        config=new_config,
                        learnings=all_learnings,
                        visited_urls=all_urls,
                        on_progress=on_progress
                    )
                else:
                    report_progress({
                        "completed_queries": progress.completed_queries + 1,
                        "current_depth": 0,
                        "stage": ResearchStage.COMPLETED,
                        "message": f"Completed query: {serp_query.query[:40]}..."
                    })
                    
                    return ResearchResult(
                        learnings=all_learnings,
                        visited_urls=all_urls,
                        follow_up_questions=follow_up_questions,
                        total_searches=1,
                        max_depth_reached=config.depth
                    )
                    
            except Exception as e:
                print(f"Error processing query '{serp_query.query}': {e}")
                return ResearchResult(
                    learnings=learnings,
                    visited_urls=visited_urls,
                    follow_up_questions=[]
                )
    
    # Run all queries concurrently
    tasks = [process_query(sq, i) for i, sq in enumerate(serp_queries)]
    results = await asyncio.gather(*tasks)
    
    # Merge results (deduplicate)
    all_learnings = list(dict.fromkeys(
        learning
        for result in results
        for learning in result.learnings
    ))
    all_urls = list(dict.fromkeys(
        url
        for result in results
        for url in result.visited_urls
    ))
    total_searches_done = sum(r.total_searches for r in results)
    max_depth = max((r.max_depth_reached for r in results), default=0)
    
    report_progress({
        "stage": ResearchStage.COMPLETED,
        "message": f"Research completed. Found {len(all_learnings)} learnings from {len(all_urls)} sources.",
        "progress_percent": 100,
        "learnings_count": len(all_learnings),
        "sources_count": len(all_urls)
    })
    
    return ResearchResult(
        learnings=all_learnings,
        visited_urls=all_urls,
        follow_up_questions=list(dict.fromkeys(all_follow_ups))[:5],
        total_searches=total_searches_done,
        max_depth_reached=max_depth
    )


# =============================================================================
# Streaming API for Deep Research v2
# =============================================================================

async def deep_research_stream_v2(
    query: str,
    config: Optional[ResearchConfig] = None,
    skip_feedback: bool = False
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Perform deep research with streaming status updates.
    
    Yields status updates and final result.
    """
    if config is None:
        config = ResearchConfig()
    
    progress_updates: List[Dict[str, Any]] = []
    
    def on_progress(progress: ResearchProgress):
        progress_updates.append(progress.to_dict())
    
    # Generate feedback questions (unless skipped)
    feedback_questions: List[str] = []
    if not skip_feedback:
        yield {
            "type": "status",
            "stage": "generating_feedback",
            "message": "Analyzing query to generate clarifying questions...",
            "progress": 2
        }
        
        feedback_questions = await generate_feedback_questions(
            query=query,
            num_questions=3,
            language=config.language
        )
        
        if feedback_questions:
            yield {
                "type": "feedback_questions",
                "questions": feedback_questions,
                "message": "Please answer these questions to improve research quality"
            }
            # Note: In a real implementation, you'd wait for user response here
    
    # Start research
    yield {
        "type": "status",
        "stage": "starting",
        "message": f"Starting deep research: {query[:80]}...",
        "progress": 5
    }
    
    # Run research
    result = await deep_research_v2(
        query=query,
        config=config,
        on_progress=on_progress
    )
    
    # Yield progress updates
    for i, prog in enumerate(progress_updates):
        yield {
            "type": "status",
            **prog
        }
    
    # Generate report
    yield {
        "type": "status",
        "stage": "generating_report",
        "message": "Generating comprehensive report...",
        "progress": 90
    }
    
    report = await write_final_report(
        prompt=query,
        learnings=result.learnings,
        visited_urls=result.visited_urls,
        language=config.language
    )
    
    # Final result
    yield {
        "type": "result",
        "report": report,
        "learnings": result.learnings,
        "sources": result.visited_urls,
        "follow_up_questions": result.follow_up_questions,
        "total_sources": len(result.visited_urls),
        "total_learnings": len(result.learnings),
        "total_searches": result.total_searches,
        "max_depth_reached": result.max_depth_reached,
        "progress": 100
    }


# =============================================================================
# LangChain Tool Wrapper v2
# =============================================================================

@tool
async def deep_research_tool_v2(
    query: str,
    breadth: int = 4,
    depth: int = 2,
    include_arxiv: bool = True,
    language: str = "vi"
) -> str:
    """
    Perform enhanced deep recursive research on a topic.
    
    Use this tool for complex research queries that require:
    - Multiple search iterations with concurrent processing
    - Following up on findings with clarifying questions
    - Academic paper search from ArXiv
    - Building comprehensive understanding with learnings accumulation
    
    Args:
        query: The research query or topic
        breadth: Number of parallel searches (2-10, default 4)
        depth: How deep to research (1-5, default 2)
        include_arxiv: Whether to include ArXiv paper search (default True)
        language: Output language - 'vi' for Vietnamese, 'en' for English (default 'vi')
    
    Returns:
        A comprehensive research report in Markdown format
    """
    try:
        config = ResearchConfig(
            breadth=min(10, max(2, breadth)),
            depth=min(5, max(1, depth)),
            include_arxiv=include_arxiv,
            language=language
        )
        
        result = await deep_research_v2(
            query=query,
            config=config
        )
        
        report = await write_final_report(
            prompt=query,
            learnings=result.learnings,
            visited_urls=result.visited_urls,
            language=language
        )
        
        return report
        
    except Exception as e:
        return f"Research error: {str(e)}"


# =============================================================================
# Export compatibility with v1
# =============================================================================

# Alias for backward compatibility
deep_research = deep_research_v2
deep_research_stream = deep_research_stream_v2
deep_research_tool = deep_research_tool_v2
