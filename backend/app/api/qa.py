from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.qwen_tutor import tutor
from app.models import Chat, ChatMessage, Folder, User
from app.schemas.qa import (
    ChatListItem,
    ChatListResponse,
    ChatMessageResponse,
    ChatResponse,
    CreateFolderRequest,
    FolderListResponse,
    FolderResponse,
    MoveChatRequest,
    SendMessageRequest,
)

router = APIRouter(prefix="/api/qa", tags=["qa"])


def _chat_or_404(db: Session, current_user: User, chat_id: str) -> Chat:
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return chat


def _to_message_response(message: ChatMessage) -> ChatMessageResponse:
    return ChatMessageResponse(
        id=str(message.id),
        role=message.role,
        content=message.content,
        category=message.category,
        problem_completed=message.problem_completed == "yes",
        created_at=message.created_at,
    )


def _to_chat_response(chat: Chat) -> ChatResponse:
    return ChatResponse(
        id=str(chat.id),
        title=chat.title,
        folder_id=str(chat.folder_id) if chat.folder_id else None,
        is_completed=chat.is_completed,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        messages=[_to_message_response(msg) for msg in chat.messages],
    )


@router.post("/chats/start", response_model=ChatResponse)
def start_chat(
    payload: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    first_message = payload.message.strip()
    chat = Chat(user_id=current_user.id, title=first_message[:120], is_completed=False)
    db.add(chat)
    db.flush()

    user_msg = ChatMessage(
        chat_id=chat.id,
        role="user",
        content=first_message,
        category="problem_solving",
        problem_completed="no",
    )
    db.add(user_msg)
    db.flush()

    ai = tutor.reply([], first_message)
    assistant_text = str(ai["reply"])
    if bool(ai.get("problem_completed", False)) and "open a new chat" not in assistant_text.lower():
        assistant_text = assistant_text + " This problem seems completed. Please open a new chat for a new exercise."

    assistant_msg = ChatMessage(
        chat_id=chat.id,
        role="assistant",
        content=assistant_text,
        category=str(ai.get("category", "problem_solving")),
        problem_completed="yes" if bool(ai.get("problem_completed", False)) else "no",
    )
    db.add(assistant_msg)

    chat.is_completed = assistant_msg.problem_completed == "yes"
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return _to_chat_response(chat)


@router.post("/chats/{chat_id}/messages", response_model=ChatResponse)
def send_message(
    chat_id: str,
    payload: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = _chat_or_404(db, current_user, chat_id)
    user_text = payload.message.strip()

    user_msg = ChatMessage(
        chat_id=chat.id,
        role="user",
        content=user_text,
        category="follow_up",
        problem_completed="no",
    )
    db.add(user_msg)
    db.flush()

    history = [{"role": message.role, "content": message.content} for message in chat.messages]
    ai = tutor.reply(history, user_text)
    assistant_text = str(ai["reply"])
    completed = bool(ai.get("problem_completed", False))
    if completed and "open a new chat" not in assistant_text.lower():
        assistant_text = assistant_text + " This problem seems completed. Please open a new chat for a new exercise."

    assistant_msg = ChatMessage(
        chat_id=chat.id,
        role="assistant",
        content=assistant_text,
        category=str(ai.get("category", "follow_up")),
        problem_completed="yes" if completed else "no",
    )
    db.add(assistant_msg)

    if completed:
        chat.is_completed = True
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return _to_chat_response(chat)


@router.get("/chats", response_model=ChatListResponse)
def list_chats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chats = (
        db.query(Chat)
        .filter(Chat.user_id == current_user.id)
        .order_by(Chat.updated_at.desc())
        .all()
    )
    items = []
    for chat in chats:
        latest_assistant = next((msg for msg in reversed(chat.messages) if msg.role == "assistant"), None)
        preview = latest_assistant.content if latest_assistant else chat.title
        items.append(
            ChatListItem(
                id=str(chat.id),
                title=chat.title,
                folder_id=str(chat.folder_id) if chat.folder_id else None,
                is_completed=chat.is_completed,
                latest_preview=preview[:120],
                updated_at=chat.updated_at,
            )
        )
    return ChatListResponse(items=items)


@router.get("/chats/{chat_id}", response_model=ChatResponse)
def get_chat(chat_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat = _chat_or_404(db, current_user, chat_id)
    return _to_chat_response(chat)


@router.delete("/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(chat_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat = _chat_or_404(db, current_user, chat_id)
    db.delete(chat)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/chats/{chat_id}/folder", response_model=ChatResponse)
def move_chat(
    chat_id: str,
    payload: MoveChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = _chat_or_404(db, current_user, chat_id)
    if payload.folder_id is not None:
        folder = db.query(Folder).filter(Folder.id == payload.folder_id, Folder.user_id == current_user.id).first()
        if not folder:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
        chat.folder_id = folder.id
    else:
        chat.folder_id = None
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return _to_chat_response(chat)


@router.post("/folders", response_model=FolderResponse)
def create_folder(
    payload: CreateFolderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    folder = Folder(user_id=current_user.id, name=payload.name.strip())
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return FolderResponse(id=str(folder.id), name=folder.name, chat_count=0, created_at=folder.created_at)


@router.get("/folders", response_model=FolderListResponse)
def list_folders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    folders = (
        db.query(Folder)
        .filter(Folder.user_id == current_user.id)
        .order_by(Folder.created_at.desc())
        .all()
    )
    items = [
        FolderResponse(
            id=str(folder.id),
            name=folder.name,
            chat_count=len(folder.chats),
            created_at=folder.created_at,
        )
        for folder in folders
    ]
    return FolderListResponse(items=items)


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(folder_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    folder = db.query(Folder).filter(Folder.id == folder_id, Folder.user_id == current_user.id).first()
    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
    db.delete(folder)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/history", response_model=ChatListResponse)
def legacy_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return list_chats(db, current_user)
