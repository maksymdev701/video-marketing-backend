from fastapi import APIRouter, Depends
from bson.objectid import ObjectId
from serializers.userSerializers import userResponseEntity
from datetime import datetime, timedelta

from database import User, Video
from schemas import userSchemas
import oauth2

router = APIRouter()


@router.get('/me', response_model=userSchemas.UserResponse, description="gets profile from cookie")
def get_me(user_id: str = Depends(oauth2.require_user)):
    user = userResponseEntity(User.find_one({'_id': ObjectId(user_id)}))
    return {"status": "success", "user": user}

@router.get('/stats', description="gets marketeer stats")
def get_stats(user_id: str = Depends(oauth2.require_user)):
    stats = {"downloads": 0, "month_downloads": 0, "total_views": 0, "total_likes": 0, "first_posts": 0}
    user = User.find_one({'_id': ObjectId(user_id)})
    stats["downloads"] = Video.count_documents({"creator": ObjectId(user_id)})
    start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_date = datetime.utcnow()

    # define the aggregation pipeline
    pipeline = [
        # filter the documents by the user ID and the date range
        {'$match': {'marketeer': ObjectId(user_id), 'created_at': {'$gte': start_date, '$lte': end_date}}},
        # project only the fields that we need (in this case just the post ID)
        # group the documents by user ID and count the number of posts for each user
        {'$group': {'_id': None, 'count': {'$sum': 1}}}
    ]

    # execute the aggregation pipeline and retrieve the result
    result = Video.aggregate(pipeline)
    for row in result:
        stats["month_downloads"] = row["count"]
        break

    # define the aggregation pipeline
    pipeline = [
        # match documents belonging to the given user
        {'$match': {'marketeer': ObjectId(user_id)}},
        # group by null and sum up the likes count
        {'$group': {'_id': None, 'total_views': {'$sum': '$views'}, 'total_likes': {'$sum': '$likes'}}}
    ]

    # execute the aggregation pipeline and retrieve the result
    result = Video.aggregate(pipeline)
    
    for row in result:
        stats["total_views"] = row["total_views"]
        stats["total_likes"] = row["total_likes"]    
        break

    # specify the start date and calculate the end date (40 days later)
    start_date = user["created_at"]
    end_date = start_date + timedelta(days=40)

    # construct the aggregation pipeline
    pipeline = [
        # match documents with created_at field within the specified period
        {'$match': {'created_at': {'$gte': start_date, '$lte': end_date}}},
        # group by null to count the number of matching documents
        {'$group': {'_id': None, 'count': {'$sum': 1}}}
    ]

    # execute the pipeline and retrieve the result
    result = Video.aggregate(pipeline)
    
    for row in result:
        stats["first_posts"] = row["count"]
        break

    stats["days_left"] = (end_date - datetime.utcnow()).days        

    return {"status": "success", "stats": stats}

@router.get('/creator', description="gets creator stats")
def get_creator_stats(user_id: str = Depends(oauth2.require_user)):
    user = userResponseEntity(User.find_one({'_id': ObjectId(user_id)}))
    
    return {"status": "success"}