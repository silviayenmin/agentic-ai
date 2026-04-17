from fastapi import APIRouter, HTTPException
import json

router = APIRouter()

@router.post("/chennai")
async def handle_chennai_button_click():
    if request.json()["btn"] == "chennai":
        return {"text": "Hello Chennai"}
    else:
        raise HTTPException(status_code=404, detail="Button not found")