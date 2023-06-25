from fastapi import APIRouter, UploadFile, File, Depends
import oauth2
import aiofiles
from bson.objectid import ObjectId
from datetime import datetime

from database import User, Video
from utils import generate_filename

router = APIRouter()

@router.post("/upload")
async def upload_videos(files: list[UploadFile] = File(...), user_id: str = Depends(oauth2.require_user)):
    current_time = datetime.utcnow()

    for file in files:
        generated_name = generate_filename(file.filename)
        destination_file_path = f"./static/uploads/{generated_name}"
        async with aiofiles.open(destination_file_path, 'wb') as out_file:
            while content := await file.read(1024):
                await out_file.write(content)
        new_video = {"filename": generated_name, "creator": ObjectId(user_id), "uploaded_at": current_time, "created_at": current_time, "updated_at": current_time}
        Video.insert_one(new_video)
        
    User.update_one({"_id": ObjectId(user_id)}, {"$inc": {"uploads": len(files)}, "$set": {"updated_at": current_time}})

    return {"status": "success"}

@router.get("/downloadable")
async def get_downloadable_videos(user_id: str = Depends(oauth2.require_user)):
    availables = Video.find({"$or": [{"marketeer": {"$exists": False}}, {"marketeer": {"$eq": None}}]})
    videos = []

    for row in availables:
        videos.append({"_id": str(row["_id"]), "src": row["filename"]})

    start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = datetime.utcnow()

    # define the aggregation pipeline for monthly downloads
    pipeline = [
        # filter the documents by the user ID and the date range
        {'$match': {'marketeer': ObjectId(user_id), 'created_at': {'$gte': start_date, '$lte': end_date}}},
        # project only the fields that we need (in this case just the post ID)
        # group the documents by user ID and count the number of posts for each user
        {'$group': {'_id': None, 'count': {'$sum': 1}}}
    ]

    # execute the monthly downloads aggregation pipeline and retrieve the result
    day_download = 0
    result = Video.aggregate(pipeline)
    for row in result:
        day_download = row["count"]

    return {"status": "success", "videos": videos, "day_download": day_download}

