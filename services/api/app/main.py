from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse, HTMLResponse
from .logging_config import configure_logging
from .routers import campaign, leads, lists, messenger
from .settings import Settings

configure_logging()

settings = Settings()
app = FastAPI()

app.include_router(lists.router)
app.include_router(campaign.router)
app.include_router(leads.router)
app.include_router(messenger.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # ou ["*"] para liberar tudo (não recomendado em produção)
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
