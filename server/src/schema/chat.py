from datetime import datetime
from pydantic import BaseModel, Field
from typing import List
import uuid

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    msg: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class Chat(BaseModel):
    token: str
    messages: List[Message]
    name: str
    session_start: str = Field(default_factory=lambda: datetime.now().isoformat())
