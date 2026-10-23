from datetime import datetime, timezone

from app.db.mongodb import get_database
from bson import ObjectId
from bson.errors import InvalidId

COLLECTION_NAME = "users"


async def create_user(user_data: dict) -> str:
    database = get_database()
    collection = database[COLLECTION_NAME]

    document_to_save = {
        **user_data,
        "created_at": datetime.now(timezone.utc),
    }

    result = await collection.insert_one(document_to_save)

    return str(result.inserted_id)


async def find_user_by_email(email: str) -> dict | None:
    database = get_database()
    collection = database[COLLECTION_NAME]

    user = await collection.find_one({"email": email.lower()})

    if not user:
        return None

    user["user_id"] = str(user["_id"])
    user.pop("_id", None)

    return user

async def find_user_by_id(user_id: str) -> dict | None:
    database = get_database()
    collection = database[COLLECTION_NAME]

    try:
        object_id = ObjectId(user_id)
    except InvalidId:
        return None

    user = await collection.find_one({"_id": object_id})

    if not user:
        return None

    user["user_id"] = str(user["_id"])
    user.pop("_id", None)

    return user