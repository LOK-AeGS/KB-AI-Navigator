# routers/auth.py

from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr
from pymongo.database import Database
import requests

# 'auth_utils'를 같은 폴더(.)에서 가져오도록 수정
from .auth_utils import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)

# --- 카카오 로그인 설정 ---
KAKAO_REST_API_KEY = "YOUR_KAKAO_REST_API_KEY"
KAKAO_REDIRECT_URI = "http://www.lifefinance.asia/auth/kakao/callback"

# --- 라우터 및 템플릿 설정 ---
router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db(request: Request) -> Database:
    return request.app.state.db

# --- 이메일 회원가입/로그인 ---
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

# --- 카카오 로그인 ---
@router.get("/login/kakao", tags=["Authentication"])
async def kakao_login():
    scope = "profile_nickname,account_email,talk_message,offline_access"
    kakao_auth_url = f"https://kauth.kakao.com/oauth/authorize?client_id={KAKAO_REST_API_KEY}&redirect_uri={KAKAO_REDIRECT_URI}&response_type=code&scope={scope}"
    return RedirectResponse(url=kakao_auth_url)

@router.get("/auth/kakao/callback", tags=["Authentication"])
async def kakao_auth_callback(code: str, db: Database = Depends(get_db)):
    try:
        token_url = "https://kauth.kakao.com/oauth/token"
        token_data = {
            "grant_type": "authorization_code", "client_id": KAKAO_REST_API_KEY,
            "redirect_uri": KAKAO_REDIRECT_URI, "code": code,
        }
        token_res = requests.post(token_url, data=token_data)
        token_json = token_res.json()
        
        kakao_access_token = token_json.get("access_token")
        kakao_refresh_token = token_json.get("refresh_token")

        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {"Authorization": f"Bearer {kakao_access_token}"}
        user_info_res = requests.get(user_info_url, headers=headers)
        email = user_info_res.json().get("kakao_account").get("email")

        if not email:
            return RedirectResponse(url="/login?error=kakao_email_required")

        user_data_to_update = {
            "signup_method": "kakao",
            "kakao_access_token": kakao_access_token,
            "kakao_refresh_token": kakao_refresh_token
        }
        db.users.update_one({"email": email}, {"$set": user_data_to_update}, upsert=True)

        app_access_token = create_access_token(data={"sub": email})
        response = RedirectResponse(url="/results", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="access_token", value=app_access_token, httponly=True)
        return response
    except Exception as e:
        print(f"카카오 로그인 처리 중 오류 발생: {e}")
        return RedirectResponse(url="/login?error=kakao_login_failed")

# --- 로그아웃 처리 ---
@router.get("/logout", tags=["Authentication"])
async def handle_logout(
    db: Database = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    if current_user:
        user = db.users.find_one({"email": current_user})
        if user and user.get("signup_method") == "kakao" and user.get("kakao_access_token"):
            kakao_logout_url = "https://kapi.kakao.com/v1/user/logout"
            headers = {"Authorization": f"Bearer {user['kakao_access_token']}"}
            try:
                response = requests.post(kakao_logout_url, headers=headers)
                if response.status_code == 200:
                    print(f"✅ 사용자 '{current_user}'의 카카오 계정 로그아웃 성공.")
                else:
                    print(f"⚠️ 사용자 '{current_user}'의 카카오 계정 로그아웃 실패: {response.text}")
            except Exception as e:
                print(f"❌ 카카오 로그아웃 API 호출 중 오류 발생: {e}")

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response
