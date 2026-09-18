"""
Routes package.
"""

from app.routes.webhooks import router as webhook_router
from app.routes.dashboard import router as dashboard_router
from app.routes.customers import router as customer_router
from app.routes.ai_agent import router as ai_agent_router

__all__ = ["webhook_router", "dashboard_router", "customer_router", "ai_agent_router"]
