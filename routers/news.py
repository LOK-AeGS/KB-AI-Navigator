
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Optional
from pymongo.database import Database
import numpy as np
import requests
import json
import re

# auth_utils에서 현재 로그인된 사용자를 확인하는 함수를 가져옵니다.
from .auth_utils import get_current_user

# --- Pydantic 데이터 모델 정의 ---
class AnalysisResultItem(BaseModel):
    summary: str
    recommendation: str

# --- Helper Function: 페르소나 매칭 ---
def get_best_fit_persona(user_profile: dict) -> str:
    user_age = user_profile.get('age', 0)
    user_occupation = user_profile.get('occupation', '')
    def get_occupation_category(occupation: str) -> str:
        if occupation in ['학생', '대학생']: return '학생'
        if occupation in ['회사원', '공무원', '선생님', '전문직', '프리랜서']: return '직장인/전문직'
        if occupation in ['자영업', '소상공인']: return '자영업'
        return '기타'
    user_occ_category = get_occupation_category(user_occupation)
    personas = [
        {'name': '학생 (대학생)', 'age_range': (18, 24), 'occupation': '학생'},
        {'name': '20대 사회초년생', 'age_range': (25, 29), 'occupation': '직장인/전문직'},
        {'name': '30대 신혼부부/1인 가구', 'age_range': (30, 39), 'occupation': '직장인/전문직'},
        {'name': '40대 (자녀 양육기)', 'age_range': (40, 49), 'occupation': '직장인/전문직'},
        {'name': '50대 (은퇴 준비기)', 'age_range': (50, 59), 'occupation': '자영업'},
        {'name': '60대 이상 (은퇴 후)', 'age_range': (60, 100), 'occupation': '기타'},
    ]
    scores = {p['name']: 0 for p in personas}
    for p in personas:
        min_age, max_age = p['age_range']
        if min_age <= user_age <= max_age: scores[p['name']] += 100
        if user_occ_category == p['occupation']: scores[p['name']] += 50
    best_persona = max(scores, key=scores.get)
    return best_persona

# --- Helper Function: 외부 API 호출 ---
def fetch_and_process_life_plan(user_profile: dict) -> List[dict]:
    api_url = "http://54.147.135.201:8000/generate-life-plan"
    payload = user_profile.copy()
    if '_id' in payload:
        del payload['_id']
    try:
        print(f"외부 API 호출 시작: {api_url}")
        response = requests.post(api_url, json=payload, timeout=120)
        response.raise_for_status()
        api_data = response.json()
        
        processed_plans = []
        user_age = user_profile.get("age", 0)
        for age_group_key, tasks in api_data.items():
            plan = {"age_group": age_group_key, "tasks": tasks, "status": "예정"}
            age_range = re.findall(r'\((\d+)-(\d+)세\)', age_group_key)
            if age_range:
                min_age, max_age = map(int, age_range[0])
                if user_age > max_age: plan['status'] = '완료'
                elif min_age <= user_age <= max_age: plan['status'] = '진행중'
            processed_plans.append(plan)
        return processed_plans
    except requests.exceptions.RequestException as e:
        print(f"외부 API 호출 중 오류 발생: {e}")
        return []

# --- 라우터 및 API 정의 ---
router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db(request: Request) -> Database:
    return request.app.state.db

# --- 1. 결과 페이지 UI 뼈대를 보여주는 경로 ---
@router.get("/results", response_class=HTMLResponse, tags=["Results Dashboard"])
async def show_results_page(
    request: Request,
    current_user: str = Depends(get_current_user)
):
    """
    데이터 없이 HTML 뼈대와 프리로더만 먼저 렌더링합니다.
    실제 데이터는 페이지 로드 후 JavaScript가 /api/results-data로 요청합니다.
    """
    if not current_user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("results.html", {"request": request, "current_user": current_user})

# --- 2. 실제 데이터를 제공하는 API 엔드포인트 (신규) ---
@router.get("/api/results-data", response_class=JSONResponse, tags=["Results API"])
async def get_results_data(
    db: Database = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    로그인된 사용자의 모든 결과 데이터를 계산하여 JSON으로 반환합니다.
    """
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="인증되지 않은 사용자입니다.")

    try:
        user_profile = db.user_profiles.find_one({"user_id": current_user})
        if not user_profile:
            # 프로필이 없으면 설문조사 페이지로 보내도록 프론트엔드에 신호를 보낼 수 있습니다.
            # 여기서는 에러를 발생시켜 프론트엔드에서 처리하도록 합니다.
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="설문조사 결과가 없습니다. 다시 작성해주세요.")
        
        user_profile['_id'] = str(user_profile['_id'])

        lifecycle_plans = fetch_and_process_life_plan(user_profile)
        matched_persona_name = get_best_fit_persona(user_profile)
        all_articles_analysis = list(db.analysis_results.find({}))
        
        personalized_articles = []
        for article in all_articles_analysis:
            persona_result = article.get('analysis_results_by_persona', {}).get(matched_persona_name)
            if persona_result:
                personalized_articles.append({
                    "title": article.get("title", "제목 없음"),
                    "summary": persona_result.get("summary", ""),
                    "recommendation": persona_result.get("recommendation", "")
                })
        
        return {
            "user_profile": user_profile,
            "lifecycle_plans": lifecycle_plans,
            "personalized_articles": personalized_articles
        }
    except Exception as e:
        print(f"API 데이터 생성 중 오류 발생: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="데이터를 처리하는 중 서버 오류가 발생했습니다.")
