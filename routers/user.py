from fastapi import APIRouter, Depends, HTTPException, status
from bson.objectid import ObjectId
from serializers.userSerializers import userResponseEntity
from datetime import datetime, timedelta

from database import User, Video
from schemas import userSchemas
import oauth2
import utils

router = APIRouter()


@router.get('/me', response_model=userSchemas.UserResponse, description="gets profile from cookie")
def get_me(user_id: str = Depends(oauth2.require_user)):
    user = userResponseEntity(User.find_one({'_id': ObjectId(user_id)}))
    return {"status": "success", "user": user}

@router.get('/stats', description="gets marketeer stats")
def get_stats(user_id: str = Depends(oauth2.require_user)):
    user = User.find_one({'_id': ObjectId(user_id)})

    stats = {"downloads": 0, "month_downloads": 0, "total_views": 0, "total_likes": 0, "first_posts": 0}    
    stats["downloads"] = Video.count_documents({"marketeer": ObjectId(user_id)})
    
    start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
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
    result = Video.aggregate(pipeline)
    for row in result:
        stats["month_downloads"] = row["count"]

    stats["total_views"] = user["views"]
    stats["total_likes"] = user["likes"]

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

    stats["days_left"] = (end_date - datetime.utcnow()).days        

    return {"status": "success", "stats": stats}

@router.get('/creator', description="gets creator stats")
def get_creator_stats(user_id: str = Depends(oauth2.require_user)):
    user = userResponseEntity(User.find_one({'_id': ObjectId(user_id)}))
    if user["role"] != "creator":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='You are not creator!')
    
    stats = {"jackpot": 12000, "cash_prize_1": 2000, "month_uploads": 0, "total_uploads": 0, "champion_bonus": 3000, "cash_prize_2": 0, "ranking": 1, "creators": 0, "champions": [], "uploads": 0, "total_views": 0, "total_likes": 0}
    stats["total_uploads"] = Video.count_documents({})
    stats["creators"] = User.count_documents({"role": "creator"})

    start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_date = datetime.utcnow()

    # define the aggregation pipeline for monthly uploads
    pipeline = [
        # filter the documents by the user ID and the date range
        {'$match': {'creator': ObjectId(user_id), 'created_at': {'$gte': start_date, '$lte': end_date}}},
        # project only the fields that we need (in this case just the post ID)
        # group the documents by user ID and count the number of posts for each user
        {'$group': {'_id': None, 'count': {'$sum': 1}}}
    ]

    # execute the monthly uploads aggregation pipeline and retrieve the result
    result = Video.aggregate(pipeline)
    for row in result:
        stats["month_uploads"] = row["count"]

    result = Video.aggregate([
        {
            "$group": {
                "_id": '$creator',
                "count": {"$sum": 1}
            }
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "_id",
                "foreignField": "_id",
                "as": "user_info"
            }
        },
        {
            "$unwind": "$user_info"
        },
        {
            "$sort": {"count": -1}
        },
        {
            "$project": {
                "user_info.name": 1,
                "count": 1
            }
        },
        {
            "$limit": 5
        }
    ])

    champions = []
    for doc in result:
        champions.append({"creator": doc["user_info"]["name"], "uploads": doc["count"]})
    stats["champions"] = champions

    # define the aggregation pipeline for views and likes sumup
    pipeline = [
        # match documents belonging to the given user
        {'$match': {'creator': ObjectId(user_id)}},
        # group by null and sum up the likes count
        {'$group': {'_id': None, 'uploads': {'$sum': 1}}}
    ]

    stats["total_views"] = user["views"]
    stats["total_likes"] = user["likes"]
    stats["uploads"] = Video.count_documents({"creator": ObjectId(user_id)})

    return {"status": "success", "stats": stats}

@router.get('/', description="gets users list")
def get_users(user_id: str=Depends(oauth2.require_user)):
    user = User.find_one({'_id': ObjectId(user_id)})
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='You have no permission to get users list.')
    # Set the date range (first 40 days)
    start_date = datetime.now() - timedelta(days=40)

    # Define the pipeline stages for aggregation
    pipeline = [
        {
            '$lookup': {
                'from': 'videos',
                'localField': '_id',
                'foreignField': 'creator',
                'as': 'uploads'
            }
        },
        {
            '$lookup': {
                'from': 'videos',
                'localField': '_id',
                'foreignField': 'marketeer',
                'as': 'downloads'
            }
        },
        {
            '$project': {
                'name': 1,
                'role': 1,
                'tiktok': 1,
                'youtube': 1,
                'twitter': 1,
                'facebook': 1,
                'instagram': 1,
                'views': 1,
                'likes': 1,
                'upload_count': {'$size': '$uploads'},
                'download_count': {'$size': '$downloads'},
                'created_at': 1,
                'first_40d_download_count': {
                    '$reduce': {
                        'input': '$downloads',
                        'initialValue': 0,
                        'in': {
                            '$cond': [
                                {'$gte': ['$this.created_at', start_date]},
                                {'$add': ['$$value', 1]},
                                '$$value'
                            ]
                        }
                    }
                }
            }
        }
    ]
    users = User.aggregate(pipeline)
    users_list = []
    for user in users:
        user.pop('_id')
        users_list.append(user)
    return {"status": "success", "users": users_list}

@router.post('/', description="create new user")
def create_user(payload: userSchemas.CreateUserSchema, user_id: str=Depends(oauth2.require_user)):
    user = User.find_one({"_id": ObjectId(user_id)})
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You have no permission to create new user!")
    
    # Check if user already exist
    user = User.find_one({'email': payload.email.lower()})

    if user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail='Account already exist')
    
    #  Hash the password
    payload.password = utils.hash_password(payload.password)
    payload.verified = False
    del payload.passwordConfirm
    payload.email = payload.email.lower()
    payload.created_at = datetime.utcnow()
    payload.updated_at = payload.created_at

    User.insert_one(payload.dict())

    return {'status': 'success', 'message': 'User created successfully!'}
