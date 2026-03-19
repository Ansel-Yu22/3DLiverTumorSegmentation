from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasicCredentials

import crud
import db
from APP import state
from APP.services import auth_service


def require_user(credentials: HTTPBasicCredentials = Depends(state.security)) -> dict:
    username = (credentials.username or "").strip()
    password = credentials.password or ""
    with db.get_session() as session:
        user = crud.get_user_entity_by_username(session, username)
    if user is None or not auth_service.verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return {"id": user.id, "username": user.username}


