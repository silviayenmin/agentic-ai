from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Feedback(BaseModel):
    name: str
    feedback_message: str
    rating: int
    category: str

@app.post("/feedback")
async def create_feedback(feedback: Feedback):
    # TO DO: Implement database operations to store the feedback data
    return {"message": "Feedback submitted successfully"}