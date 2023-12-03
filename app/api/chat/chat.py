from fastapi import APIRouter, Depends, HTTPException, Form
from app.core.database import database
from .models import MessageModel, ImageData, MessageInDB, conversation, RoomModel
from app.api.auth.dependencies import get_current_user
from datetime import datetime
from fastapi import UploadFile, File
import base64
from PIL import Image
import io
import os
import uuid
from bson import ObjectId
from typing import List

router = APIRouter()

messages_collection = database.get_collection("messages")
UPLOAD_DIRECTORY = "./data/"


@router.post("/create-room", response_model=RoomModel)
async def create_room(
    members: List[str] = Form(...),
    current_user: str = Depends(get_current_user),
):
    # check current user is in members
    if current_user["user_id"] not in members:
        raise HTTPException(
            status_code=400,
            detail="You must be a member of the room to create it.",
        )
    # Xác định xem đây có phải là nhóm trò chuyện không
    is_group = len(members) > 2

    # check room is existed
    room = await database.rooms.find_one({"members": members})
    if room:
        if is_group == room["is_group"]:
            raise HTTPException(
                status_code=400,
                detail="Room is existed.",
            )

    # Tạo phòng mới
    new_room = await database.rooms.insert_one(
        {"members": members, "is_group": is_group}
    )
    created_room = await database.rooms.find_one({"_id": new_room.inserted_id})
    return RoomModel(**created_room)
