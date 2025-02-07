from fastapi import FastAPI
from injector import Binder, Injector, Module, provider

from users.config import UserServiceConfigurations
from users.core.tokens import TokenRepository, TokenServices
from users.core.users import UserRepository, UserServices

from .base import Controllers
from .health_controller import HealthCheckController
from .token_controller import TokenController
from .user_controller import AdminUserController, UserController


class ControllerModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(HealthCheckController)

    @provider
    def provide_admin_user_controller(
        self, user_repository: UserRepository
    ) -> AdminUserController:
        return AdminUserController(
            user_services=UserServices(user_repository=user_repository)
        )

    @provider
    def provide_user_controller(
        self, user_repository: UserRepository
    ) -> UserController:
        return UserController(
            user_services=UserServices(user_repository=user_repository)
        )

    @provider
    def provide_token_controller(
        self,
        token_repository: TokenRepository,
        config: UserServiceConfigurations,
    ) -> TokenController:
        return TokenController(
            service=TokenServices(token_repository=token_repository, config=config)
        )


def register_controllers_to_app(app: FastAPI, injector: Injector) -> FastAPI:
    for controller in Controllers.controllers:
        print(f"Discovered controller {controller}")
        app.include_router(injector.get(controller).router)
    return app
