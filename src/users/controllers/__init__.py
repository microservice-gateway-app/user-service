from fastapi import FastAPI
from injector import Binder, Injector, Module, provider

from users.config import UserServiceConfigurations
from users.core.services.token_repository import TokenRepository
from users.core.services.user_repository import UserRepository

from ..controllers.token_controller import TokenController
from ..controllers.user_controller import UserController
from ..core.services.token_services import TokenServices
from ..core.services.user_services import UserServices
from .base import Controllers
from .health_controller import HealthCheckController


class ControllerModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(HealthCheckController)

    @provider
    def provide_user_controller(
        self, user_repository: UserRepository
    ) -> UserController:
        return UserController(service=UserServices(repository=user_repository))

    @provider
    def provide_token_controller(
        self,
        token_repository: TokenRepository,
        user_repository: UserRepository,
        config: UserServiceConfigurations,
    ) -> TokenController:
        return TokenController(
            service=TokenServices(
                user_repository=user_repository,
                token_repository=token_repository,
                config=config,
            )
        )


def register_controllers_to_app(app: FastAPI, injector: Injector) -> FastAPI:
    for controller in Controllers.controllers:
        print(f"Discovered controller {controller}")
        app.include_router(injector.get(controller).router)
    return app
