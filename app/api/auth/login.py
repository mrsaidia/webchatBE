# app/api/auth/register.py

from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import database
from app.api.auth.models import UserLogin
import hashlib
router = APIRouter()

# Define the MongoDB collection
user_collection = database.get_collection("users")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

async def check_info_login(username, password):
    user = user_collection.find_one({"username": username})
    if user:
        if user["password"] == hash_password(password):
            return True
        else:
            return False
    else:
        return False
    
    

@router.get("/login")
async def login(user: UserLogin):
    # Hash the password before saving it to the database (you should never save passwords in plain text)
    # You can use the security module from your core folder for password hashing
    # Check user
    if not check_info_login(user.username, user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    # Return the user_id and username and "good"
    return {"user_id": str(user.username), "username": user.username, "status": "good"}