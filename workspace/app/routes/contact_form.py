from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import re

router = APIRouter()

class ContactForm(BaseModel):
    name: str
    email: str
    phone_number: str
    message: str

@router.post("/contact")
async def handle_contact_form_submission(form: ContactForm):
    if not form.name or not form.email or not form.phone_number or not form.message:
        raise HTTPException(status_code=400, detail="All fields are required.")

    if not re.match(r"[^@]+@[a-zA-Z0-9._]+\.[a-zA-Z]{2,}", form.email):
        raise HTTPException(status_code=400, detail="Invalid email format.")

    # Handle successful submission
    return {"message": "Thank you for contacting us!"}