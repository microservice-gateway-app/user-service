from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from injector import Binder
from pydantic_settings import BaseSettings


class UserServiceConfigurations(BaseSettings):
    DB_URI: str = "postgresql+asyncpg://users:users@localhost:54321/users"
    PRIVATE_KEYFILE: str = "private.pem"

    ALGORITHM: str = "HS256"
    SECRET_KEY: str = "user-secret"

    REFRESH_TOKEN_TTL_DAYS: int = 7
    ACCESS_TOKEN_TTL_SECONDS: int = 3_600

    PORT: int = 8001

    ADMIN_EMAIL: str = "admin@app.com"
    ADMIN_PASSWORD: str = "Admin@123"
    ADMIN_FIRST_NAME: str = "App"
    ADMIN_MIDDLE_NAME: str = "dot"
    ADMIN_LAST_NAME: str = "Admin"

    @property
    def private_key(self) -> RSAPrivateKey:
        with open(self.PRIVATE_KEYFILE, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=self.SECRET_KEY.encode(),
                backend=default_backend(),
            )
        if not isinstance(private_key, RSAPrivateKey):
            raise TypeError(
                f"Expected RSAPrivateKey, but got {type(private_key).__name__}"
            )

        return private_key


def provide_config(binder: Binder):
    binder.bind(UserServiceConfigurations)
