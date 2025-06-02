from fastapi import APIRouter, HTTPException
from app.schemas.notification import NotificationCreate, NotificationRead
from app.crud.notification import create_notification, get_notifications
from typing import List

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.post("/", response_model=NotificationRead)
async def create_new_notification(notification: NotificationCreate):
    return await create_notification(notification)

@router.get("/", response_model=List[NotificationRead])
async def read_notifications(skip: int = 0, limit: int = 10):
    return await get_notifications(skip=skip, limit=limit)