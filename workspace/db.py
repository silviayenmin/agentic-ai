import mysql.connector
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
    db = mysql.connector.connect(
        host="your_host",
        user="your_username",
        password="your_password",
        database="your_database"
    )
    cursor = db.cursor()
    
    query = "INSERT INTO feedback (name, feedback_message, rating, category) VALUES (%s, %s, %s, %s)"
    values = (feedback.name, feedback.feedback_message, feedback.rating, feedback.category)
    
    try:
        cursor.execute(query, values)
        db.commit()
        return {"message": "Feedback submitted successfully"}
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")
    finally:
        cursor.close()
        db.close()