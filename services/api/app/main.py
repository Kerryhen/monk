from importlib.metadata import version

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse, HTMLResponse
from .logging_config import configure_logging
from .routers import campaign, leads, lists, messenger
from .settings import Settings

configure_logging()

settings = Settings()
app = FastAPI(version=version('listmonk'))

v1 = APIRouter(prefix='/v1')
v1.include_router(lists.router)
v1.include_router(campaign.router)
v1.include_router(leads.router)
v1.include_router(messenger.router)

app.include_router(v1)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # ou ["*"] para liberar tudo (não recomendado em produção)
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
