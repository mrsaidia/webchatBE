# app/api/auth/register.py

from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import database
from app.api.auth.models import UserCreate
import hashlib


router = APIRouter()

# Define the MongoDB collection
user_collection = database.get_collection("users")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@router.post("/register")
async def register(user: UserCreate):
    # Hash the password before saving it to the database (you should never save passwords in plain text)
    # You can use the security module from your core folder for password hashing
    hashed_password = user.password
    hashed_password = hash_password(hashed_password)
    # Create a user document
    user_document = {
        "username": user.username,
        "password": hashed_password,
    }

    # Insert the user document into the MongoDB collection
    result = await user_collection.insert_one(user_document)

    # Return the user_id and username
    return {"user_id": str(result.inserted_id), "username": user.username}
