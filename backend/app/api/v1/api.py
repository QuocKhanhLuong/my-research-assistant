"""
API v1 Router Aggregator.
Combines all v1 endpoint routers.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import chat

api_router = APIRouter()

# Include chat endpoints (includes health, chat, search, rebuild-index)
api_router.include_router(chat.router, tags=["chat"])
