from pymongo import AsyncMongoClient

from app.core.config import settings

client: AsyncMongoClient | None = None
database = None


async def connect_to_mongodb() -> None:
    global client, database

    client = AsyncMongoClient(settings.MONGODB_URL)
    await client.admin.command("ping")

    database = client[settings.MONGODB_DB_NAME]
    print("Connected to MongoDB successfully")


async def close_mongodb_connection() -> None:
    global client, database

    if client is not None:
        await client.close()

    client = None
    database = None
    print("MongoDB connection closed")


def get_database():
    if database is None:
        raise RuntimeError("MongoDB is not connected")

    return database