from fastapi import FastAPI, APIRouter
from app.routes.greet import greet_router

app = FastAPI()

router = APIRouter()

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

app.include_router(greet_router)