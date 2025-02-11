from fastapi import APIRouter

from backend.views.auth import auth_router
from backend.views.choices import choices_router
from backend.views.search import search_router
from backend.views.users import users_router

central_router = APIRouter()

central_router.include_router(auth_router)
central_router.include_router(users_router)
central_router.include_router(search_router)
central_router.include_router(choices_router)
