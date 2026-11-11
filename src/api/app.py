from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.concurrency import run_in_threadpool

from src.api.errors import register_error_handlers
from src.api.routes import router
from src.api.settings import APISettings
from src.llm_engine import OpenAIEngine
from src.pipeline import TicketPipeline


def create_app(
    pipeline: TicketPipeline | None = None,
) -> FastAPI:
    """Create the API with an optional externally owned test pipeline."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = None

        try:
            if pipeline is None:
                settings = APISettings.from_environment()

                engine = OpenAIEngine(
                    model_name=settings.model_name,
                    api_key=settings.api_key.get_secret_value(),
                    base_url=(
                        str(settings.base_url)
                        if settings.base_url is not None
                        else None
                    ),
                    timeout=settings.model_timeout_seconds,
                    max_retries=0,
                )

                app.state.pipeline = TicketPipeline(
                    llm_engine=engine,
                    max_retries=settings.output_retries,
                )
            else:
                app.state.pipeline = pipeline

            yield

        finally:
            if engine is not None:
                await run_in_threadpool(engine.close)

    app = FastAPI(
        title="Ticket Triage API",
        version="0.1.0",
        description="Single-ticket processing through the existing pipeline.",
        lifespan=lifespan,
    )

    register_error_handlers(app)
    app.include_router(router)

    return app


app = create_app()
