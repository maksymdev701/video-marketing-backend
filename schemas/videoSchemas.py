from datetime import datetime
from pydantic import BaseModel
from bson.objectid import ObjectId


class VideoBaseSchema(BaseModel):
    brand: str
    title: str
    creator: ObjectId
    uploaded_at: datetime | None = None
    downloaded_at: datetime | None = None
    views: int = 0
    tiktok: str | None = None
    youtube: str | None = None
    twitter: str | None = None
    facebook: str | None = None
    instagram: str | None = None
    created_at: datetime | None = None
