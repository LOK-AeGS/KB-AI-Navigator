# routers/auth.py

from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr
from pymongo.database import Database
import requests # 카카오 서버와 통신하기 위해 import

# 'auth_utils'를 같은 폴더(.)에서 가져오도록 수정
from .auth_utils import (
    get_password_hash,
    verify_password,
    create_access_token,
)

# --- 카카오 로그인 설정 ---
# !!! 중요: 이 값들을 카카오 개발자 사이트에서 발급받은 값으로 변경해야 합니다. !!!
KAKAO_REST_API_KEY = "2e4c8e208e182e59879c9c181bfc7c94" # 예: "a1b2c3d4e5f6..."
KAKAO_REDIRECT_URI = "http://127.0.0.1:8000/auth/kakao/callback"

# --- 라우터 및 템플릿 설정 ---
router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db(request: Request) -> Database:
    return request.app.state.db

# --- 기존 이메일 회원가입/로그인 ---
@router.get("/register", response_class=HTMLResponse, tags=["Authentication"])
async def show_register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register", tags=["Authentication"])
async def handle_registration(
    request: Request, email: EmailStr = Form(...), password: str = Form(...), db: Database = Depends(get_db)
):
    if db.users.find_one({"email": email}):
        return templates.TemplateResponse("register.html", {"request": request, "error": "이미 사용 중인 이메일입니다."}, status_code=400)
    
    hashed_password = get_password_hash(password)
    # 일반 회원가입 시 signup_method를 'email'로 지정
    db.users.insert_one({"email": email, "hashed_password": hashed_password, "signup_method": "email"})
    
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/login", response_class=HTMLResponse, tags=["Authentication"])
async def show_login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", tags=["Authentication"])
async def handle_login(
    request: Request, email: EmailStr = Form(...), password: str = Form(...), db: Database = Depends(get_db)
):
    user = db.users.find_one({"email": email})
    if not user or not verify_password(password, user["hashed_password"]):
        return templates.TemplateResponse("login.html", {"request": request, "error": "이메일 또는 비밀번호가 올바르지 않습니다."}, status_code=400)
    
    access_token = create_access_token(data={"sub": user["email"]})
    response = RedirectResponse(url="/results", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@router.get("/logout", tags=["Authentication"])
async def handle_logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response

# --- 카카오 로그인 관련 경로 (신규 추가) ---

@router.get("/login/kakao", tags=["Authentication"])
async def kakao_login():
    """사용자를 카카오 인증 페이지로 리디렉션합니다."""
    kakao_auth_url = f"https://kauth.kakao.com/oauth/authorize?client_id={KAKAO_REST_API_KEY}&redirect_uri={KAKAO_REDIRECT_URI}&response_type=code"
    return RedirectResponse(url=kakao_auth_url)

@router.get("/auth/kakao/callback", tags=["Authentication"])
async def kakao_auth_callback(code: str, db: Database = Depends(get_db)):
    """카카오 인증 후 콜백을 받아 토큰을 발급하고 사용자를 처리합니다."""
    try:
        # 1. 인가 코드로 카카오 토큰 받기
        token_url = "https://kauth.kakao.com/oauth/token"
        token_data = {
            "grant_type": "authorization_code",
            "client_id": KAKAO_REST_API_KEY,
            "redirect_uri": KAKAO_REDIRECT_URI,
            "code": code,
        }
        token_res = requests.post(token_url, data=token_data)
        token_json = token_res.json()
        
        kakao_access_token = token_json.get("access_token")
        if not kakao_access_token:
            raise Exception("카카오 토큰 발급 실패")

        # 2. 토큰으로 카카오 사용자 정보 가져오기
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {"Authorization": f"Bearer {kakao_access_token}"}
        user_info_res = requests.get(user_info_url, headers=headers)
        user_info_json = user_info_res.json()
        
        email = user_info_json.get("kakao_account").get("email")
        if not email:
            raise Exception("카카오 계정에서 이메일 정보를 가져올 수 없습니다.")

        # 3. 사용자 DB 처리
        user = db.users.find_one({"email": email})
        if not user:
            # 새로운 카카오 사용자이면 DB에 등록
            db.users.insert_one({
                "email": email,
                "signup_method": "kakao",
                "kakao_access_token": kakao_access_token
            })
        else:
            # 기존 사용자이면 카카오 토큰 정보 업데이트
            db.users.update_one({"email": email}, {"$set": {"kakao_access_token": kakao_access_token, "signup_method": "kakao"}})

        # 4. 우리 서비스의 JWT 생성 및 로그인 처리
        app_access_token = create_access_token(data={"sub": email})
        response = RedirectResponse(url="/results", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="access_token", value=app_access_token, httponly=True)
        return response

    except Exception as e:
        print(f"카카오 로그인 처리 중 오류 발생: {e}")
        return RedirectResponse(url="/login?error=kakao_login_failed")
