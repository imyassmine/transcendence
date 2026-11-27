from fastapi import FastAPI
from ia.api import ia_lifespan, router as ia_router

from .v1.notification_api import notif_router
from .v1.auth_api import auth_router

app = FastAPI(title="transcendence API", lifespan=ia_lifespan)
app.include_router(notif_router)
app.include_router(auth_router)
app.include_router(ia_router)


@app.get("/")
async def root():
    return {"message": "Hello from the trancendence"}
