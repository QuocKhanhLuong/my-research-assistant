"""
Pydantic schemas for Chat API requests and responses.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class Source(BaseModel):
    """Source document information."""
    content: str = Field(..., description="Content snippet from source document")
    page: int = Field(..., description="Page number in source document")
    source: str = Field(..., description="Source file path or name")


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""
    message: str = Field(..., min_length=1, description="User's question or message")
    include_sources: bool = Field(
        default=False, 
        description="Whether to include source documents in response"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Quy chế thi như thế nào?",
                    "include_sources": True
                }
            ]
        }
    }


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""
    response: str = Field(..., description="AI-generated response")
    sources: Optional[List[Source]] = Field(
        default=None, 
        description="Source documents used to generate response"
    )
    num_sources: Optional[int] = Field(
        default=None, 
        description="Number of source documents retrieved"
    )


class HealthResponse(BaseModel):
    """Response schema for health check endpoint."""
    status: str = Field(..., description="Health status")
    rag_initialized: bool = Field(..., description="Whether RAG engine is initialized")
    pdf_directory: Optional[str] = Field(
        default=None, 
        description="Path to PDF directory"
    )
    index_path: Optional[str] = Field(
        default=None, 
        description="Path to FAISS index"
    )
    num_documents: Optional[int] = Field(
        default=None, 
        description="Number of documents in index"
    )


class RebuildIndexRequest(BaseModel):
    """Request schema for rebuild index endpoint."""
    force: bool = Field(
        default=True, 
        description="Force rebuild even if index exists"
    )


class RebuildIndexResponse(BaseModel):
    """Response schema for rebuild index endpoint."""
    status: str = Field(..., description="Rebuild status")
    message: str = Field(..., description="Detailed message")
    num_documents: Optional[int] = Field(
        default=None, 
        description="Number of documents after rebuild"
    )


class SearchRequest(BaseModel):
    """Request schema for similarity search endpoint."""
    query: str = Field(..., min_length=1, description="Search query")
    k: int = Field(default=4, ge=1, le=20, description="Number of results to return")


class SearchResponse(BaseModel):
    """Response schema for similarity search endpoint."""
    results: List[Source] = Field(..., description="List of relevant document chunks")
    query: str = Field(..., description="Original query")
    num_results: int = Field(..., description="Number of results returned")
