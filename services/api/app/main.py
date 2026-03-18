import traceback
from importlib.metadata import version

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .context import enrich_wide_event
from .logging_config import configure_logging
from .middleware import WideEventMiddleware
from .routers import campaign, client, leads, lists, messenger
from .settings import Settings
from .telemetry import configure_telemetry

configure_logging()

settings = Settings()
app = FastAPI(version=version('listmonk'))

app.add_middleware(WideEventMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Must be called after middleware is registered: instrument_app() adds its own
# middleware and must be outermost so spans are active when WideEventMiddleware logs.
configure_telemetry(app)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    enrich_wide_event({'error': {'type': type(exc).__name__, 'message': str(exc)}})
    if settings.ENVIRONMENT == 'DEV':
        return JSONResponse(
            status_code=500,
            content={'detail': str(exc), 'traceback': traceback.format_exc()},
        )
    return JSONResponse(status_code=401, content={'detail': 'Unauthorized'})


v1 = APIRouter(prefix='/v1')
v1.include_router(client.router)
v1.include_router(lists.router)
v1.include_router(campaign.router)
v1.include_router(leads.router)
v1.include_router(messenger.router)

app.include_router(v1)
