# routers/survey.py

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from pymongo.database import Database
from typing import List # List 타입을 사용하기 위해 import

# --- Pydantic 모델 정의 (수정됨) ---
class UserProfile(BaseModel):
    age: int
    gender: str
    occupation: str
    residence: str
    monthly_income: int
    dependents: int
    investment_style: str
    financial_goal: List[str] # 경제 목표를 문자열 리스트로 받도록 변경

# APIRouter 인스턴스 생성
router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db(request: Request) -> Database:
    return request.app.state.db

# --- 라우트 정의 (수정됨) ---
@router.get("/", response_class=RedirectResponse, tags=["Survey UI"])
async def root():
    return RedirectResponse(url="/survey")

@router.get("/survey", response_class=HTMLResponse, tags=["Survey UI"])
async def show_survey_form(request: Request):
    return templates.TemplateResponse("survey.html", {"request": request})

@router.post("/survey", tags=["Survey Logic"])
async def submit_survey_form(
    age: int = Form(...),
    gender: str = Form(...),
    occupation: str = Form(...),
    residence: str = Form(...),
    monthly_income: int = Form(...),
    dependents: int = Form(...),
    investment_style: str = Form(...),
    financial_goal: List[str] = Form(...), # 폼에서 여러 개의 목표 데이터를 리스트로 받기
    db: Database = Depends(get_db)
):
    user_profile = UserProfile(
        age=age,
        gender=gender,
        occupation=occupation,
        residence=residence,
        monthly_income=monthly_income,
        dependents=dependents,
        investment_style=investment_style,
        financial_goal=financial_goal
    )
    
    result = db.user_profiles.insert_one(user_profile.dict())
    
    print("--- 👤 새로운 사용자 프로필 MongoDB에 저장됨 ---")
    print(f"저장된 Document ID: {result.inserted_id}")

    # 결과 페이지로 리디렉션
    return RedirectResponse(url="/results", status_code=303)
