from app.db.mongodb import get_database

COLLECTION_NAME = "documents"


async def get_analytics_summary() -> dict:
    database = get_database()
    collection = database[COLLECTION_NAME]

    total_documents = await collection.count_documents({})

    green_count = await collection.count_documents(
        {"risk_analysis.alert_level": "Green"}
    )
    yellow_count = await collection.count_documents(
        {"risk_analysis.alert_level": "Yellow"}
    )
    red_count = await collection.count_documents(
        {"risk_analysis.alert_level": "Red"}
    )

    pipeline = [
        {
            "$group": {
                "_id": None,
                "average_risk_score": {
                    "$avg": "$risk_analysis.risk_score"
                },
            }
        }
    ]

    cursor = await collection.aggregate(pipeline)
    average_result = await cursor.to_list(length=1)
    average_risk_score = 0

    if average_result:
        average_risk_score = round(
            average_result[0].get("average_risk_score", 0),
            2,
        )

    return {
        "total_documents": total_documents,
        "green_count": green_count,
        "yellow_count": yellow_count,
        "red_count": red_count,
        "average_risk_score": average_risk_score,
    }

async def get_alert_distribution() -> list[dict]:
    database = get_database()
    collection = database[COLLECTION_NAME]

    pipeline = [
        {
            "$group": {
                "_id": "$risk_analysis.alert_level",
                "count": {"$sum": 1},
            }
        },
        {
            "$sort": {
                "_id": 1,
            }
        },
    ]

    cursor = await collection.aggregate(pipeline)
    results = await cursor.to_list(length=None)

    return [
        {
            "alert_level": item["_id"],
            "count": item["count"],
        }
        for item in results
    ]

async def get_recent_high_risk_documents(limit: int = 5) -> list[dict]:
    database = get_database()
    collection = database[COLLECTION_NAME]

    cursor = (
        collection.find(
            {"risk_analysis.alert_level": "Red"},
            {
                "filename": 1,
                "stored_filename": 1,
                "risk_analysis": 1,
                "summary": 1,
                "created_at": 1,
            },
        )
        .sort("created_at", -1)
        .limit(limit)
    )

    documents = []

    async for document in cursor:
        document["document_id"] = str(document["_id"])
        document.pop("_id", None)

        if "created_at" in document:
            document["created_at"] = document["created_at"].isoformat()

        documents.append(document)

    return documents