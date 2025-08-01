# routers/auth.py

from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr
from pymongo.database import Database

# auth_utils.py에서 필요한 함수들을 가져옵니다.
from .auth_utils import (
    get_password_hash,
    verify_password,
    create_access_token,
)

# --- 라우터 및 템플릿 설정 ---
router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db(request: Request) -> Database:
    return request.app.state.db

# --- 라우트 정의 ---

# 회원가입 페이지를 보여줍니다. (GET)
@router.get("/register", response_class=HTMLResponse, tags=["Authentication"])
async def show_register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# 회원가입 요청을 처리합니다. (POST)
@router.post("/register", tags=["Authentication"])
async def handle_registration(
    request: Request,
    email: EmailStr = Form(...),
    password: str = Form(...),
    db: Database = Depends(get_db)
):
    # 이메일 중복 확인
    if db.users.find_one({"email": email}):
        error_msg = "이미 사용 중인 이메일입니다."
        return templates.TemplateResponse("register.html", {"request": request, "error": error_msg}, status_code=400)
    
    # 비밀번호를 암호화하여 사용자 정보를 DB에 저장
    hashed_password = get_password_hash(password)
    db.users.insert_one({"email": email, "hashed_password": hashed_password})
    
    # 회원가입 성공 시 로그인 페이지로 이동
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

# 로그인 페이지를 보여줍니다. (GET)
@router.get("/login", response_class=HTMLResponse, tags=["Authentication"])
async def show_login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# 로그인 요청을 처리합니다. (POST)
@router.post("/login", tags=["Authentication"])
async def handle_login(
    request: Request,
    email: EmailStr = Form(...),
    password: str = Form(...),
    db: Database = Depends(get_db)
):
    user = db.users.find_one({"email": email})
    # 사용자 확인 및 비밀번호 검증
    if not user or not verify_password(password, user["hashed_password"]):
        error_msg = "이메일 또는 비밀번호가 올바르지 않습니다."
        return templates.TemplateResponse("login.html", {"request": request, "error": error_msg}, status_code=400)
    
    # JWT Access Token 생성
    access_token = create_access_token(data={"sub": user["email"]})
    
    # JWT를 httponly 쿠키에 저장하여 보안을 강화하고, 결과 페이지로 이동
    response = RedirectResponse(url="/results", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

# 로그아웃 요청을 처리합니다.
@router.get("/logout", tags=["Authentication"])
async def handle_logout():
    # 쿠키를 삭제하고 메인 페이지로 이동
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response
