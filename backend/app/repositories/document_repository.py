from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from app.db.mongodb import get_database

COLLECTION_NAME = "documents"
FEEDBACK_COLLECTION_NAME = "finding_feedback"

# Lists only need the score and file details; the full text and findings are
# loaded when a single report is opened.
LIST_PROJECTION = {"document_text": 0, "findings": 0}


def _to_response(document: dict) -> dict:
    document["document_id"] = str(document.pop("_id"))

    if hasattr(document.get("created_at"), "isoformat"):
        document["created_at"] = document["created_at"].isoformat()

    review = document.get("review")
    if review and hasattr(review.get("updated_at"), "isoformat"):
        review["updated_at"] = review["updated_at"].isoformat()

    return document


async def save_document_analysis(analysis_data: dict) -> str:
    database = get_database()
    collection = database[COLLECTION_NAME]

    document_to_save = {
        **analysis_data,
        "created_at": datetime.now(timezone.utc),
    }

    result = await collection.insert_one(document_to_save)

    return str(result.inserted_id)

async def get_document_history(user_id: str, limit: int = 20) -> list[dict]:
    database = get_database()
    collection = database[COLLECTION_NAME]

    cursor = (
        collection.find({"uploaded_by": user_id}, LIST_PROJECTION)
        .sort("created_at", -1)
        .limit(limit)
    )

    documents = []

    async for document in cursor:
        documents.append(_to_response(document))

    return documents

async def get_document_by_id(document_id: str) -> dict | None:
    database = get_database()
    collection = database[COLLECTION_NAME]

    try:
        object_id = ObjectId(document_id)
    except InvalidId:
        return None

    document = await collection.find_one({"_id": object_id})

    if not document:
        return None

    return _to_response(document)

async def get_all_documents(limit: int = 50) -> list[dict]:
    database = get_database()
    collection = database[COLLECTION_NAME]

    cursor = collection.find({}, LIST_PROJECTION).sort("created_at", -1).limit(limit)

    documents = []

    async for document in cursor:
        documents.append(_to_response(document))

    return documents

async def update_document_review(document_id: str, review: dict) -> None:
    database = get_database()
    await database[COLLECTION_NAME].update_one(
        {"_id": ObjectId(document_id)},
        {"$set": {"review": {**review, "updated_at": datetime.now(timezone.utc)}}},
    )


async def save_finding_feedback(document: dict, finding: dict, user: dict) -> None:
    """Keeps "not a risk" decisions (masked values only) to tune detection later."""
    database = get_database()
    await database[FEEDBACK_COLLECTION_NAME].update_one(
        {"document_id": document["document_id"], "finding_id": finding["id"]},
        {
            "$set": {
                "document_id": document["document_id"],
                "finding_id": finding["id"],
                "category": finding["category"],
                "type": finding["type"],
                "value": finding["value"],
                "context": finding["context"],
                "verdict": "not_a_risk",
                "user_id": user["user_id"],
                "created_at": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )


async def delete_finding_feedback(document_id: str, finding_id: str) -> None:
    database = get_database()
    await database[FEEDBACK_COLLECTION_NAME].delete_one(
        {"document_id": document_id, "finding_id": finding_id}
    )
