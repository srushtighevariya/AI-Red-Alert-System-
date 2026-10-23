from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/")
def home():
    return {
        "message": "AI Document Red Alert Detection System API is running"
    }


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "backend"
    }