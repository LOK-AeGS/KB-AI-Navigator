# routers/news.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Optional
from pymongo.database import Database
import numpy as np

# --- Pydantic 데이터 모델 정의 ---
class AnalysisResultItem(BaseModel):
    summary: str
    recommendation: str

# --- Helper Function: 페르소나 매칭 (규칙 기반 점수 시스템으로 변경) ---
def get_best_fit_persona(user_profile: dict) -> str:
    """
    사용자 프로필과 표준 페르소나를 비교하여 가장 적합한 페르소나를 찾습니다.
    나이와 직업군에 가중치를 둔 규칙 기반 점수 시스템을 사용합니다.
    """
    user_age = user_profile.get('age', 0)
    user_occupation = user_profile.get('occupation', '')

    # 직업을 더 넓은 카테고리로 매핑
    def get_occupation_category(occupation: str) -> str:
        if occupation in ['학생', '대학생']:
            return '학생'
        if occupation in ['회사원', '공무원', '선생님', '전문직', '프리랜서']:
            return '직장인/전문직'
        if occupation in ['자영업', '소상공인']:
            return '자영업'
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
        # 1. 나이 점수 (가장 높은 가중치)
        min_age, max_age = p['age_range']
        if min_age <= user_age <= max_age:
            scores[p['name']] += 100  # 나이 범위가 맞으면 큰 점수 부여

        # 2. 직업 점수
        if user_occ_category == p['occupation']:
            scores[p['name']] += 50 # 직업군이 맞으면 점수 부여

    # 가장 높은 점수를 받은 페르소나를 반환
    best_persona = max(scores, key=scores.get)
    
    print(f"규칙 기반 점수 계산 결과: {scores}")
    print(f"최종 매칭 페르소나: {best_persona}")

    return best_persona

# --- Helper Function: 생애주기 상태 동적 계산 ---
def calculate_lifecycle_status(user_age: int, plans: List[dict]) -> List[dict]:
    """
    사용자 나이를 기준으로 생애주기 계획의 상태를 동적으로 결정합니다.
    """
    age_map = {
        "20대 초반": (20, 24), "20대 후반": (25, 29),
        "30대 초반": (30, 34), "30대 후반": (35, 39),
        "40대 초반": (40, 44), "40대 후반": (45, 49),
        "50대 이상": (50, 100)
    }
    for plan in plans:
        min_age, max_age = age_map.get(plan['age_group'], (0, 0))
        if user_age > max_age:
            plan['status'] = '완료'
        elif min_age <= user_age <= max_age:
            plan['status'] = '진행중'
        else:
            plan['status'] = '예정'
    return plans

# --- 라우터 및 API 정의 ---
router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db(request: Request) -> Database:
    return request.app.state.db

@router.get("/results", response_class=HTMLResponse, tags=["Results Dashboard"])
async def show_results_dashboard(request: Request, db: Database = Depends(get_db)):
    """
    최종 결과 대시보드 페이지를 렌더링합니다.
    """
    try:
        # 1. 사용자 프로필 조회
        user_profile = db.user_profiles.find_one({}, sort=[('_id', -1)])
        if not user_profile:
            return templates.TemplateResponse("error.html", {"request": request, "message": "설문조사 결과가 없습니다."})

        # 2. 생애주기 계획 조회 및 상태 동적 계산
        lifecycle_plans_from_db = list(db.lifecycle_plans.find({}))
        lifecycle_plans = calculate_lifecycle_status(user_profile.get('age', 0), lifecycle_plans_from_db)

        # 3. 맞춤 기사 요약 조회
        matched_persona_name = get_best_fit_persona(user_profile)
        all_articles_analysis = list(db.analysis_results.find({}))
        
        personalized_articles = []
        for article in all_articles_analysis:
            persona_result = article.get('analysis_results_by_persona', {}).get(matched_persona_name)
            if persona_result:
                personalized_articles.append({
                    "title": article.get("title", "제목 없음"),
                    "summary": persona_result.get("summary", "요약 정보가 없습니다."),
                    "recommendation": persona_result.get("recommendation", "추천 정보가 없습니다.")
                })
        
        # 4. 템플릿에 데이터 전달 및 렌더링
        return templates.TemplateResponse(
            "results.html", 
            {
                "request": request,
                "user_profile": user_profile,
                "lifecycle_plans": lifecycle_plans,
                "personalized_articles": personalized_articles
            }
        )
    except Exception as e:
        print(f"결과 페이지 로딩 중 오류 발생: {e}")
        return templates.TemplateResponse("error.html", {"request": request, "message": "결과를 처리하는 중 오류가 발생했습니다."})
