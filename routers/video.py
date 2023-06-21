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
