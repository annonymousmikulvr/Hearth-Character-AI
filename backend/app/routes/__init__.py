from fastapi import APIRouter

from . import (
    advanced,
    images,
    setup,
    settings,
    personas,
    characters,
    conversations,
    ai,
    worlds,
    memories,
    health,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(setup.router, prefix="/setup", tags=["setup"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(personas.router, prefix="/personas", tags=["personas"])
api_router.include_router(characters.router, prefix="/characters", tags=["characters"])
api_router.include_router(
    conversations.router, prefix="/conversations", tags=["conversations"]
)
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(worlds.router, prefix="/worlds", tags=["worlds"])
api_router.include_router(memories.router, prefix="/memories", tags=["memories"])
api_router.include_router(images.router, prefix="/images", tags=["images"])
api_router.include_router(advanced.router, prefix="/advanced", tags=["advanced"])
