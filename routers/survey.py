# routers/survey.py

from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pymongo.database import Database
from typing import List, Optional
import json

# 'auth_utils'를 같은 폴더(.)에서 가져오도록 수정
from .auth_utils import get_current_user

# --- Pydantic 모델 정의 ---
class UserProfile(BaseModel):
    user_id: str
    age: int
    gender: str
    occupation: str
    residence: str
    monthly_income: int
    dependents: int
    investment_style: str
    financial_goal: List[str]

# --- 라우터 및 템플릿 설정 ---
router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db(request: Request) -> Database:
    return request.app.state.db

# --- 라우트 정의 (수정됨) ---
@router.get("/", response_class=RedirectResponse, tags=["Entry Point"])
async def root(current_user: Optional[str] = Depends(get_current_user)):
    """
    웹사이트의 가장 기본 경로.
    - 로그인 상태이면: 결과 페이지(/results)로 이동합니다.
    - 로그아웃 상태이면: 로그인 페이지(/login)로 이동합니다.
    """
    if current_user:
        return RedirectResponse(url="/results")
    return RedirectResponse(url="/login") # <-- 이 부분을 /survey에서 /login으로 변경했습니다.

@router.get("/survey", response_class=HTMLResponse, tags=["Survey UI"])
async def show_new_survey_form(request: Request, db: Database = Depends(get_db), current_user: Optional[str] = Depends(get_current_user)):
    # 새로운 설문조사 페이지. 만약 이미 프로필이 있다면 수정 페이지로 보낸다.
    if current_user:
        user_profile = db.user_profiles.find_one({"user_id": current_user})
        if user_profile:
            return RedirectResponse(url="/survey/edit")
    return templates.TemplateResponse("survey.html", {"request": request, "current_user": current_user, "user_profile_json": "null"})

@router.get("/survey/edit", response_class=HTMLResponse, tags=["Survey UI"])
async def show_edit_survey_form(request: Request, db: Database = Depends(get_db), current_user: Optional[str] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login")

    user_profile = db.user_profiles.find_one({"user_id": current_user})
    
    if not user_profile:
        return RedirectResponse(url="/survey")

    user_profile['_id'] = str(user_profile['_id'])
    
    return templates.TemplateResponse("survey.html", {
        "request": request, 
        "current_user": current_user,
        "user_profile_json": json.dumps(user_profile)
    })


@router.post("/survey", tags=["Survey Logic"])
async def submit_survey_form(
    age: int = Form(...),
    gender: str = Form(...),
    occupation: str = Form(...),
    residence: str = Form(...),
    monthly_income: int = Form(...),
    dependents: int = Form(...),
    investment_style: str = Form(...),
    financial_goal: List[str] = Form(...),
    db: Database = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인이 필요합니다.")

    profile_data = {
        "user_id": current_user,
        "age": age, "gender": gender, "occupation": occupation, "residence": residence,
        "monthly_income": monthly_income, "dependents": dependents,
        "investment_style": investment_style, "financial_goal": financial_goal
    }
    
    db.user_profiles.update_one(
        {"user_id": current_user},
        {"$set": profile_data},
        upsert=True
    )
    
    print(f"--- 👤 사용자 '{current_user}' 프로필 저장/업데이트 완료 ---")
    return RedirectResponse(url="/results", status_code=303)
