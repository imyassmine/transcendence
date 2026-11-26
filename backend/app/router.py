from fastapi import FastAPI

from .v1.notification_api import notif_router
from .v1.auth_api import auth_router

app = FastAPI(title="transcendence API")
app.include_router(notif_router)
app.include_router(auth_router)


@app.get("/")
async def root():
    return {"message": "Hello from the trancendence"}
