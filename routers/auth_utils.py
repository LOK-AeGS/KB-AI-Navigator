# auth_utils.py

from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional

# --- 보안 설정 ---
# 비밀번호 암호화를 위한 설정 (bcrypt 알고리즘 사용)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT(JSON Web Token) 설정
# SECRET_KEY는 외부에 노출되면 안 되는 매우 중요한 값입니다.
# 실제 운영 환경에서는 .env 파일이나 다른 보안 방법을 통해 관리해야 합니다.
SECRET_KEY = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 토큰 유효 시간 (60분)

# --- 함수 정의 ---

def verify_password(plain_password, hashed_password):
    """입력된 비밀번호와 DB에 저장된 해시된 비밀번호를 비교합니다."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """비밀번호를 해시 처리하여 DB에 저장할 형태로 만듭니다."""
    return pwd_context.hash(password)

def create_access_token(data: dict):
    """
    사용자 정보(data)를 받아 JWT Access Token을 생성합니다.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(request: Request) -> Optional[str]:
    """
    요청에 포함된 쿠키에서 Access Token을 읽어 현재 로그인된 사용자의 ID(이메일)를 반환합니다.
    로그인되지 않았거나 토큰이 유효하지 않으면 None을 반환합니다.
    """
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        # 토큰을 디코딩하여 사용자 정보(payload)를 추출합니다.
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        # 토큰이 유효하지 않은 경우
        return None
