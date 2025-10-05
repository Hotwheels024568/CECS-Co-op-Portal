from fastapi import APIRouter

router = APIRouter()


@router.post("/sign_up")
async def sign_up() -> int:
    pass
