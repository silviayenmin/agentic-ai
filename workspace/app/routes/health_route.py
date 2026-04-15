from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/greet")
async def greet():
    try:
        return {"message": "Welcome to our API!"}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/health")
async def health():
    try:
        return {"status": "healthy"}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)