from fastapi import FastAPI
import uvicorn

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)