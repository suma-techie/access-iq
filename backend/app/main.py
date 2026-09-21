from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import (
    analytics,
    application_roles,
    applications,
    auth,
    catalog,
    delegations,
    documents,
    projects,
    requests,
    tickets,
    users,
    webhooks,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="AccessIQ", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(applications.router)
app.include_router(application_roles.router)
app.include_router(catalog.router)
app.include_router(documents.router)
app.include_router(requests.router)
app.include_router(tickets.router)
app.include_router(delegations.router)
app.include_router(analytics.router)
app.include_router(webhooks.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
