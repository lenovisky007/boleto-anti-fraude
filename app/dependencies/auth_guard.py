from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth import decode_token

SECRET_KEY = "super-secret-key"
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        user = decode_token(token)
        return user

    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")