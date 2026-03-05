from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse, HTMLResponse
from .routers import campaign, lists
from .settings import Settings

settings = Settings()
app = FastAPI()

app.include_router(lists.router)
app.include_router(campaign.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # ou ["*"] para liberar tudo (não recomendado em produção)
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
