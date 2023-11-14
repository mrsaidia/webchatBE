# app/chat/models.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MessageModel(BaseModel):
    content: str
    username: str
