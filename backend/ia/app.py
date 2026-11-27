from fastapi import FastAPI

from .api import ia_lifespan, router

app = FastAPI(title="Transcendence IA", lifespan=ia_lifespan)
app.include_router(router)
