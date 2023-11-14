from fastapi import APIRouter, Depends, HTTPException, Form
from app.core.database import database
from .models import MessageModel
from .models import MessageInDB
from .models import conversation
from .models import ImageData
from app.api.auth.dependencies import get_current_user
from datetime import datetime
from fastapi import UploadFile, File
import base64

router = APIRouter()

messages_collection = database.get_collection("messages")


@router.post("/send-message", response_model=MessageModel)
async def send_message(
    message: MessageModel,
    sender: str = Depends(get_current_user),
):
    message_dict = message.dict(by_alias=True)
    if sender != message.sender:
        raise HTTPException(
            status_code=400,
            detail="You are not authorized to send messages on behalf of another user.",
        )
    message_dict["sender"] = sender
    message_dict["receiver"] = message.receiver
    message_dict["timestamp"] = datetime.now()

    new_message = await messages_collection.insert_one(message_dict)
    created_message = await messages_collection.find_one(
        {"_id": new_message.inserted_id}
    )
    return MessageModel(**created_message)


@router.get("/get-messages/{receiver}", response_model=list[MessageInDB])
async def get_messages(
    chat: conversation,
    sender: str = Depends(get_current_user),
):
    if sender != chat.sender:
        raise HTTPException(
            status_code=400,
            detail="You are not authorized to send messages on behalf of another user.",
        )
    list = await messages_collection.find(
        {"sender": sender, "receiver": chat.receiver}
    ).to_list(length=100)
    list2 = await messages_collection.find(
        {"sender": chat.receiver, "receiver": sender}
    ).to_list(length=100)
    list.extend(list2)
    list.sort(key=lambda x: x["timestamp"])

    return list


@router.post("/send-image")
async def send_image(
    sender: str = Form(...),
    receiver: str = Form(...),
    image: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
):
    image_data = await image.read()
    image_data = base64.b64encode(image_data)
    # image_data = image_data.decode("utf-8")

    if current_user != sender:
        raise HTTPException(
            status_code=400,
            detail="You are not authorized to send messages on behalf of another user.",
        )

    message_dict = {
        "content": image_data,
        "sender": sender,
        "receiver": receiver,
        "timestamp": datetime.now(),
    }

    new_message = await messages_collection.insert_one(message_dict)
    created_message = await messages_collection.find_one(
        {"_id": new_message.inserted_id}
    )

    return MessageModel(**created_message)
