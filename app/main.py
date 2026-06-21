import secrets
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine, get_db
from app.models import SessionToken, User
from app.schemas import LoginPayload


app = FastAPI(title="yanshi backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "null",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8001",
        "http://localhost:8001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def api_response(data=None, message="success", code=0):
    return {"code": code, "message": message, "data": data}


def bootstrap_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.username == "admin").first()
        if existing_user is None:
            db.add(
                User(
                    username="admin",
                    password="admin123",
                    nickname="演示管理员",
                    role_name="管理员",
                )
            )
            db.commit()
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    bootstrap_data()


def extract_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或登录已失效")
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证信息格式错误")
    return authorization[len(prefix):].strip()


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    token = extract_token(authorization)
    session_token = db.query(SessionToken).filter(SessionToken.token == token).first()
    if session_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录状态不存在")
    user = db.query(User).filter(User.id == session_token.user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user


@app.get("/health")
def health_check():
    return api_response({"status": "ok"})


@app.post("/api/auth/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or user.password != payload.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")

    token = secrets.token_urlsafe(32)
    db.add(SessionToken(token=token, user_id=user.id))
    db.commit()

    return api_response(
        {
            "token": token,
            "user": {
                "username": user.username,
                "nickname": user.nickname,
                "roleName": user.role_name,
            },
        }
    )


@app.get("/api/auth/me")
def get_me(user: User = Depends(get_current_user)):
    return api_response(
        {
            "username": user.username,
            "nickname": user.nickname,
            "roleName": user.role_name,
        }
    )


@app.post("/api/auth/logout")
def logout(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    token = extract_token(authorization)
    session_token = db.query(SessionToken).filter(SessionToken.token == token).first()
    if session_token is not None:
        db.delete(session_token)
        db.commit()
    return api_response({"success": True})


@app.get("/api/home/overview")
def home_overview(user: User = Depends(get_current_user)):
    return api_response(
        {
            "welcomeText": f"欢迎回来，{user.nickname}",
            "quickActions": ["查看首页", "刷新用户信息", "退出登录"],
        }
    )
