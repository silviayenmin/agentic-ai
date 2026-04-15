from fastapi import FastAPI
import json

app = FastAPI()

@app.get("/greet")
async def greet():
    try:
        return {"message": "Welcome to our API!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    try:
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))