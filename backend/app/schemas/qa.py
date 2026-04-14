from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


MessageCategory = Literal["task_generation", "problem_solving", "follow_up", "non_math"]


class SendMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=600)


class MoveChatRequest(BaseModel):
    folder_id: Optional[str] = None


class CreateFolderRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class ChatMessageResponse(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    category: MessageCategory
    problem_completed: bool
    created_at: datetime


class ChatResponse(BaseModel):
    id: str
    title: str
    folder_id: Optional[str]
    is_completed: bool
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse]


class ChatListItem(BaseModel):
    id: str
    title: str
    folder_id: Optional[str]
    is_completed: bool
    latest_preview: str
    updated_at: datetime


class ChatListResponse(BaseModel):
    items: List[ChatListItem]


class FolderResponse(BaseModel):
    id: str
    name: str
    chat_count: int
    created_at: datetime


class FolderListResponse(BaseModel):
    items: List[FolderResponse]
