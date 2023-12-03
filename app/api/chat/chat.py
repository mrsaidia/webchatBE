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
import base64
from .saveDB import save_image_to_db, save_video_to_db, save_audio_to_db

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


@router.get("/get-messages/{room_id}", response_model=List[MessageModel])
async def get_messages(
    room_id: str,
    skip: int,  # Thêm tham số phân trang
    limit: int = 10,  # Giới hạn số lượng tin nhắn trả về
    current_user: str = Depends(get_current_user),
):
    # Lấy thông tin phòng từ cơ sở dữ liệu
    room = await database.rooms.find_one({"_id": ObjectId(room_id)})
    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found.",
        )

    # Kiểm tra xem người dùng hiện tại có là thành viên của phòng không
    if current_user["user_id"] not in room["members"]:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this room.",
        )

    # Truy vấn để lấy tin nhắn trong phòng với phân trang
    messages = (
        await messages_collection.find({"room_id": room_id})
        .skip(skip)
        .limit(limit)
        .to_list(limit)
    )

    # Xử lý từng tin nhắn
    for message in messages:
        if message["format"] in ["image", "audio", "video"]:
            # Giả sử 'content' chứa tên file
            file_path = os.path.join(UPLOAD_DIRECTORY, room_id, message["content"])
            if message["format"] == "image":
                with open(file_path + ".png", "rb") as f:
                    image_data = f.read()
                    message["content"] = base64.b64encode(image_data)
            elif message["format"] == "audio":
                with open(file_path + ".mp3", "rb") as f:
                    audio_data = f.read()
                    message["content"] = base64.b64encode(audio_data)
            elif message["format"] == "video":
                with open(file_path + ".mp4", "rb") as f:
                    video_data = f.read()
                    message["content"] = base64.b64encode(video_data)

    return messages


@router.post("/send-message", response_model=MessageModel)
async def send_message(
    message: MessageModel,
    sender: str = Depends(get_current_user),
):
    room_id = message.room_id
    print("check room_id", room_id)
    message_dict = message.dict(by_alias=True)

    # Lấy thông tin phòng từ cơ sở dữ liệu
    room = await database.rooms.find_one({"_id": ObjectId(room_id)})
    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found.",
        )

    # Kiểm tra xem người gửi có trong phòng không
    if sender["user_id"] not in room["members"]:
        raise HTTPException(
            status_code=400,
            detail="You are not a member of this room.",
        )

    # Cập nhật thông tin tin nhắn
    message_dict["sender"] = sender["user_id"]
    message_dict["room_id"] = room_id  # Sử dụng room_id thay vì receiver
    message_dict["timestamp"] = datetime.now()

    # Định dạng của tin nhắn được xác định bởi loại tin nhắn được gửi
    message_dict["format"] = "text"  # Hoặc cập nhật tùy thuộc vào loại tin nhắn

    # Thêm tin nhắn vào cơ sở dữ liệu
    new_message = await messages_collection.insert_one(message_dict)
    created_message = await messages_collection.find_one(
        {"_id": new_message.inserted_id}
    )

    return MessageModel(**created_message)


@router.post("/send-image")
async def send_image(
    room_id: str = Form(...),  # Thêm tham số này
    image: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
):
    image_data = await image.read()
    image_data_base64 = base64.b64encode(image_data)

    # Lấy thông tin phòng từ cơ sở dữ liệu
    room = await database.rooms.find_one({"_id": ObjectId(room_id)})
    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found.",
        )

    # Kiểm tra xem người dùng hiện tại có trong phòng không
    if current_user["user_id"] not in room["members"]:
        raise HTTPException(
            status_code=400,
            detail="You are not a member of this room.",
        )

    # Tạo đường dẫn folder dựa trên room_id
    folderPath = os.path.join(UPLOAD_DIRECTORY, room_id)

    # Lưu ảnh vào thư mục dựa trên room_id
    save_image_to_db(image_data_base64, folderPath, image.filename)

    # Tạo và lưu tin nhắn với ảnh
    message_dict = {
        "content": image.filename,
        "sender": current_user["user_id"],  # Sử dụng người dùng hiện tại làm người gửi
        "room_id": room_id,  # Sử dụng room_id
        "timestamp": datetime.now(),
        "format": "image",
    }

    new_message = await messages_collection.insert_one(message_dict)
    created_message = await messages_collection.find_one(
        {"_id": new_message.inserted_id}
    )

    return MessageModel(**created_message)


@router.post("/send-audio")
async def send_audio(
    room_id: str = Form(...),  # Sử dụng room_id thay vì sender và receiver
    audio: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
):
    print("check here")

    audio_data = await audio.read()

    # Lấy thông tin phòng từ cơ sở dữ liệu
    room = await database.rooms.find_one({"_id": ObjectId(room_id)})
    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found.",
        )

    # Kiểm tra xem người dùng hiện tại có trong phòng không
    if current_user["user_id"] not in room["members"]:
        raise HTTPException(
            status_code=400,
            detail="You are not a member of this room.",
        )

    # Tạo đường dẫn folder dựa trên room_id
    folderPath = os.path.join(UPLOAD_DIRECTORY, room_id)

    # Lưu âm thanh vào thư mục dựa trên room_id
    save_audio_to_db(audio_data, folderPath, audio.filename)

    # Tạo và lưu tin nhắn với âm thanh
    message_dict = {
        "content": audio.filename,
        "sender": current_user["user_id"],  # Sử dụng người dùng hiện tại làm người gửi
        "room_id": room_id,  # Sử dụng room_id
        "timestamp": datetime.now(),
        "format": "audio",
    }

    new_message = await messages_collection.insert_one(message_dict)
    created_message = await messages_collection.find_one(
        {"_id": new_message.inserted_id}
    )

    return MessageModel(**created_message)


@router.post("/send-video")
async def send_video(
    room_id: str = Form(...),  # Sử dụng room_id thay vì sender và receiver
    video: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
):
    video_data = await video.read()

    # Lấy thông tin phòng từ cơ sở dữ liệu
    room = await database.rooms.find_one({"_id": ObjectId(room_id)})
    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found.",
        )

    # Kiểm tra xem người dùng hiện tại có trong phòng không
    if current_user["user_id"] not in room["members"]:
        raise HTTPException(
            status_code=400,
            detail="You are not a member of this room.",
        )

    # Tạo đường dẫn folder dựa trên room_id
    folderPath = os.path.join(UPLOAD_DIRECTORY, room_id)

    # Lưu video vào thư mục dựa trên room_id
    save_video_to_db(video_data, folderPath, video.filename)

    # Tạo và lưu tin nhắn với video
    message_dict = {
        "content": video.filename,
        "sender": current_user["user_id"],  # Sử dụng người dùng hiện tại làm người gửi
        "room_id": room_id,  # Sử dụng room_id
        "timestamp": datetime.now(),
        "format": "video",
    }

    new_message = await messages_collection.insert_one(message_dict)
    created_message = await messages_collection.find_one(
        {"_id": new_message.inserted_id}
    )

    return MessageModel(**created_message)
