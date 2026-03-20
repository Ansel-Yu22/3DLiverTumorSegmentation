from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from APP.persistence import crud, db
from APP.service import auth_service


router = APIRouter()


class UserAuthRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
def register(req: UserAuthRequest):
    username = req.username.strip()
    password = req.password
    if not username:
        raise HTTPException(status_code=400, detail="username cannot be empty")
    if not password:
        raise HTTPException(status_code=400, detail="password cannot be empty")

    with db.get_session() as session:
        if crud.get_user_by_username(session, username) is not None:
            raise HTTPException(status_code=409, detail="username already exists")
        user = crud.create_user(session, username, auth_service.hash_password(password))
    return user


@router.post("/login")
def login(req: UserAuthRequest):
    username = req.username.strip()
    password = req.password
    with db.get_session() as session:
        user = crud.get_user_entity_by_username(session, username)
    if user is None or not auth_service.verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return {"id": user.id, "username": user.username}


