from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.api_endpoints.post_sign_up import router as sign_up_router

app = FastAPI()

# Allow React dev client to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dev only!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# DO NOT DELETE
@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}


app = FastAPI()
app.include_router(sign_up_router, prefix="/api")
