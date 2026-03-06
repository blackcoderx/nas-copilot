from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from nascopilot.services.auth import decode_token

_bearer = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    try:
        return decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
