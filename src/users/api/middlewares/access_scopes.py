from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, SecurityScopes
from injector import Injector
from jose import JWTError, jwt

from users.config import UserServiceConfigurations
from users.core.access import Actor, UserScope
from users.core.shared import UserId

# Define the HTTPBearer method for token validation
access_token_method = HTTPBearer(
    scheme_name="AccessTokenAuth", description="Place access_token here"
)


async def has_any_scope(
    security_scopes: SecurityScopes,
    request: Request,
    token: Annotated[HTTPAuthorizationCredentials, Depends(access_token_method)],
) -> Actor:
    """Verify that an actor possesses some of the required scopes."""
    app: FastAPI = request.app
    injector: Injector = app.state.injector
    config = injector.get(UserServiceConfigurations)

    # Extract the token from the HTTPBearer Security method
    try:
        # Extract raw token
        token_str = token.credentials

        # Decode the JWT
        payload = jwt.decode(
            token_str, config.SECRET_KEY, algorithms=[config.ALGORITHM]
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Extract actor and scopes from the token
    actor = Actor(
        user_id=UserId(value=payload.get("sub", "")),
        scopes=[
            UserScope(s)
            for s in payload.get("scopes", ())
            if s in UserScope._value2member_map_
        ],
    )
    if not actor:
        raise HTTPException(status_code=403, detail="No actor information found")

    required_scopes = [UserScope(s) for s in security_scopes.scopes]

    # Check if the token has at least one required scope
    if not actor.has_any_scope(required_scopes):
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient scopes. Required either of: {required_scopes}",
        )

    # Add the actor to the request's state for later use
    request.state.actor = actor
    return actor
