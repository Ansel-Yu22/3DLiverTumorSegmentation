from contextlib import asynccontextmanager

from fastapi import FastAPI

from APP.routers import auth, health, jobs, predict
from APP.services import inference_service


@asynccontextmanager
async def lifespan(_: FastAPI):
    inference_service.startup_init()
    yield


app = FastAPI(title="3D Liver Tumor Segmentation API (Minimal)", lifespan=lifespan)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(jobs.router)


