from datetime import datetime
from pydantic import BaseModel
from bson.objectid import ObjectId


class VideoBaseSchema(BaseModel):
    brand: str | None
    title: str | None
    filename: str
    creator: ObjectId
    marketeer: ObjectId | None = None
    uploaded_at: datetime | None = None
    downloaded_at: datetime | None = None
    views: int = 0
    likes: int = 0
    tiktok: str | None = None
    youtube: str | None = None
    twitter: str | None = None
    facebook: str | None = None
    instagram: str | None = None
    created_at: datetime | None = None

    class Config:
        orm_mode = True
        allow_population_by_filed_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
