import logging
import traceback
from importlib.metadata import version

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .logging_config import configure_logging
from .routers import campaign, client, leads, lists, messenger
from .settings import Settings

configure_logging()
logger = logging.getLogger(__name__)

settings = Settings()
app = FastAPI(version=version('listmonk'))


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if settings.ENVIRONMENT == 'DEV':
        return JSONResponse(
            status_code=500,
            content={'detail': str(exc), 'traceback': traceback.format_exc()},
        )
    logger.error('unhandled_exception', extra={'path': str(request.url), 'error': str(exc)}, exc_info=True)
    return JSONResponse(status_code=401, content={'detail': 'Unauthorized'})


v1 = APIRouter(prefix='/v1')
v1.include_router(client.router)
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
