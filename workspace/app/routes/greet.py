from fastapi import APIRouter

greet_router = APIRouter()

@greet_router.get("/hello")
async def greet():
    return {"message": "Hello, World!"}