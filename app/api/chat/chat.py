from fastapi import APIRouter, Depends
from app.core.database import database
from .models import MessageModel
from app.api.auth.dependencies import get_current_user

router = APIRouter()

messages_collection = database.get_collection("messages")


@router.post("/send-message/", response_model=MessageModel)
async def send_message(
    message: MessageModel, username: str = Depends(get_current_user)
):
    message_dict = message.dict(by_alias=True)
    message_dict["username"] = username
    new_message = await messages_collection.insert_one(message_dict)
    created_message = await messages_collection.find_one(
        {"_id": new_message.inserted_id}
    )
    return MessageModel(**created_message)


@router.get("/get-messages/", response_model=list[MessageModel])
async def get_messages():
    messages = await messages_collection.find().to_list(100)
    return [MessageModel(**message) for message in messages]
