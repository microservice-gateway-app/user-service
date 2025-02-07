from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import FastAPI
from injector import Injector, Module, provider, singleton
from sqlalchemy.ext.asyncio import AsyncSession

from .api.controllers import ControllerModule, register_controllers_to_app
from .config import provide_config
from .infrastructure.db import DatabaseModule


class ProductionModule(Module):
    @singleton
    @provider
    def provide_fastapi_app(self, injector: Injector) -> FastAPI:
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            yield
            await injector.get(AsyncSession).close_all()

        app = FastAPI(
            title="User Service", ignore_trailing_slash=True, lifespan=lifespan
        )

        return register_controllers_to_app(app=app, injector=injector)


@lru_cache
def provide_injector() -> Injector:
    injector = Injector(
        modules=[
            provide_config,
            DatabaseModule,
            ControllerModule,
            ProductionModule,
        ]
    )
    injector.get(FastAPI).state.injector = injector
    return injector
