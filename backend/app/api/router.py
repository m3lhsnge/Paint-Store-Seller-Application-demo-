from fastapi import APIRouter
from app.api.endpoints import auth, materials, customers, recipes

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(materials.router)
api_router.include_router(customers.router)
api_router.include_router(recipes.router)
