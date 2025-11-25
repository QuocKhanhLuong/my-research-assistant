"""
Chat API Endpoints.
Handles chat, health check, search, and index management.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    RebuildIndexRequest,
    RebuildIndexResponse,
    SearchRequest,
    SearchResponse,
    Source,
)
from app.services.rag_service import RAGService, get_rag_service
from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    """
    Check API health and RAG service status.
    
    Returns:
        Health status including RAG initialization state.
    """
    return HealthResponse(
        status="healthy" if rag_service.is_initialized else "degraded",
        rag_initialized=rag_service.is_initialized,
        pdf_directory=settings.pdf_directory,
        index_path=settings.faiss_index_path,
        num_documents=rag_service.num_documents if rag_service.is_initialized else None,
    )


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    request: ChatRequest,
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
) -> ChatResponse:
    """
    Process a chat message and return AI-generated response.
    
    Uses RAG to retrieve relevant context from PDF documents
    and generate an informed response.
    
    Args:
        request: Chat request containing user message.
        
    Returns:
        AI-generated response with optional source documents.
        
    Raises:
        HTTPException: If RAG service not initialized or processing fails.
    """
    if not rag_service.is_initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service not initialized. Please try again later.",
        )
    
    try:
        logger.info(f"Processing chat request: {request.message[:50]}...")
        
        answer, sources = rag_service.get_answer(request.message)
        
        response = ChatResponse(response=answer)
        
        if request.include_sources and sources:
            response.sources = [
                Source(
                    content=s["content"],
                    page=s["page"],
                    source=s["source"],
                )
                for s in sources
            ]
            response.num_sources = len(sources)
        
        logger.info("Chat response generated successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}",
        )


@router.post("/search", response_model=SearchResponse, tags=["Search"])
async def search(
    request: SearchRequest,
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
) -> SearchResponse:
    """
    Search for similar documents without generating an answer.
    
    Performs similarity search on the vector store.
    
    Args:
        request: Search request with query and result count.
        
    Returns:
        List of relevant document chunks.
        
    Raises:
        HTTPException: If RAG service not initialized or search fails.
    """
    if not rag_service.is_initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service not initialized. Please try again later.",
        )
    
    try:
        results = rag_service.search_similar(request.query, k=request.k)
        
        return SearchResponse(
            results=[
                Source(
                    content=r["content"],
                    page=r["page"],
                    source=r["source"],
                )
                for r in results
            ],
            query=request.query,
            num_results=len(results),
        )
        
    except Exception as e:
        logger.error(f"Error processing search request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing search: {str(e)}",
        )


@router.post("/rebuild-index", response_model=RebuildIndexResponse, tags=["Admin"])
async def rebuild_index(
    request: RebuildIndexRequest,
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
) -> RebuildIndexResponse:
    """
    Rebuild the FAISS vector index from PDF documents.
    
    Use this endpoint to refresh the index after adding new PDFs.
    
    Args:
        request: Rebuild options (force flag).
        
    Returns:
        Rebuild status and document count.
        
    Raises:
        HTTPException: If rebuild fails.
    """
    try:
        logger.info(f"Rebuilding index (force={request.force})...")
        
        success = rag_service.initialize(force_rebuild=request.force)
        
        if success:
            return RebuildIndexResponse(
                status="success",
                message="Index rebuilt successfully",
                num_documents=rag_service.num_documents,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to rebuild index",
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rebuilding index: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rebuilding index: {str(e)}",
        )
