from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from fastapi import UploadFile, File


class MessageModel(BaseModel):
    content: str
    sender: str  # Username của người gửi
    receiver: str  # Username của người nhận

    class Config:
        schema_extra = {
            "example": {
                "content": "Hello, there!",
                "sender": "alice",
                "receiver": "bob",
            }
        }


class MessageInDB(MessageModel):
    timestamp: datetime

    class Config:
        schema_extra = {
            "example": {
                "content": "Hello, there!",
                "sender": "alice",
                "receiver": "bob",
                "timestamp": "2021-07-15T10:00:00.000Z",
            }
        }


class conversation(BaseModel):
    sender: str
    receiver: str

    class Config:
        schema_extra = {
            "example": {
                "sender": "alice",
                "receiver": "bob",
            }
        }


class sendImage(BaseModel):
    receiver: str

    class Config:
        schema_extra = {
            "example": {
                "image": "image.png",
                "receiver": "bob",
            }
        }


class ImageData(BaseModel):
    sender: str
    receiver: str
