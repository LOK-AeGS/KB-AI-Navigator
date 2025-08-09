# routers/auth.py

from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr
from pymongo.database import Database
import requests

from .auth_utils import get_password_hash, verify_password, create_access_token

# --- 카카오 로그인 설정 ---
KAKAO_REST_API_KEY = "YOUR_KAKAO_REST_API_KEY"
KAKAO_REDIRECT_URI = "http://www.lifefinance.asia/auth/kakao/callback"

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db(request: Request) -> Database:
    return request.app.state.db

# ... (기존 이메일 회원가입/로그인 생략) ...

@router.get("/login/kakao", tags=["Authentication"])
async def kakao_login():
    """사용자를 카카오 인증 페이지로 리디렉션합니다."""
    # --- 핵심 수정: scope에 'offline_access'를 추가하여 Refresh Token 발급을 요청합니다. ---
    scope = "profile_nickname,account_email,talk_message,offline_access"
    kakao_auth_url = f"https://kauth.kakao.com/oauth/authorize?client_id={KAKAO_REST_API_KEY}&redirect_uri={KAKAO_REDIRECT_URI}&response_type=code&scope={scope}"
    return RedirectResponse(url=kakao_auth_url)

@router.get("/auth/kakao/callback", tags=["Authentication"])
async def kakao_auth_callback(code: str, db: Database = Depends(get_db)):
    """카카오 인증 후 콜백을 받아 토큰을 발급하고 사용자를 처리합니다."""
    try:
        token_url = "https://kauth.kakao.com/oauth/token"
        token_data = {
            "grant_type": "authorization_code", "client_id": KAKAO_REST_API_KEY,
            "redirect_uri": KAKAO_REDIRECT_URI, "code": code,
        }
        token_res = requests.post(token_url, data=token_data)
        token_json = token_res.json()
        
        kakao_access_token = token_json.get("access_token")
        kakao_refresh_token = token_json.get("refresh_token") # Refresh Token 저장

        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {"Authorization": f"Bearer {kakao_access_token}"}
        user_info_res = requests.get(user_info_url, headers=headers)
        email = user_info_res.json().get("kakao_account").get("email")

        if not email:
            return RedirectResponse(url="/login?error=kakao_email_required")

        # DB에 Access Token과 Refresh Token을 모두 저장/업데이트합니다.
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
