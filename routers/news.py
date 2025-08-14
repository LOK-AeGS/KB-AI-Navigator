
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Optional
from pymongo.database import Database
import requests
import json
import re

# auth_utils에서 현재 로그인된 사용자를 확인하는 함수를 가져옵니다.
from .auth_utils import get_current_user

# --- Pydantic 데이터 모델 정의 ---
class AnalysisResultItem(BaseModel):
    summary: str
    recommendation: str

# --- Helper Function: 나이 기반 페르소나 매칭 ---
def get_persona_by_age(age: int) -> str:
    """사용자 나이를 기준으로 가장 적합한 페르소나 그룹 이름을 반환합니다."""
    # DB의 키 이름과 정확히 일치하도록 수정 (예: '20대 사회초년생' -> '20대')
    if 20 <= age <= 29: return '20대'
    if 30 <= age <= 39: return '30대'
    if 40 <= age <= 49: return '40대'
    if 50 <= age <= 59: return '50대'
    if age >= 60: return '60대 이후'
    return '20대' # 기본값

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
        print(f" 외부 API 호출 중 오류 발생: {e}")
        return []

# --- 라우터 및 API 정의 ---
router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db(request: Request) -> Database:
    return request.app.state.db

# --- 1. 결과 페이지 UI 뼈대를 보여주는 경로 ---
@router.get("/results", response_class=HTMLResponse, tags=["Results Dashboard"])
async def show_results_page(request: Request, current_user: str = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("results.html", {"request": request, "current_user": current_user})

# --- 2. 실제 데이터를 제공하는 API 엔드포인트 ---
@router.get("/api/results-data", response_class=JSONResponse, tags=["Results API"])
async def get_results_data(db: Database = Depends(get_db), current_user: str = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="인증되지 않은 사용자입니다.")

    try:
        user_profile = db.user_profiles.find_one({"user_id": current_user})
        if not user_profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="설문조사 결과가 없습니다. 다시 작성해주세요.")
        
        user_profile['_id'] = str(user_profile['_id'])

        lifecycle_plans = fetch_and_process_life_plan(user_profile)
        
       
        # 1. 나이로 페르소나 그룹 매칭
        matched_persona_group = get_persona_by_age(user_profile.get('age', 0))
        
        # 2. 사용자가 선택한 목표 리스트 가져오기
        user_goals = user_profile.get("financial_goal", []) 

        all_articles_analysis = list(db.analysis_results.find({}))
        
        personalized_articles = []
        for article in all_articles_analysis:
            # 3. 기사의 분석 결과에서, 매칭된 나이 그룹의 데이터를 먼저 찾음
            age_group_analysis = article.get('analysis_results', {}).get(matched_persona_group)
            
            if age_group_analysis:
                # 4. 사용자가 선택한 모든 목표에 대해 반복
                for goal in user_goals:
                    # 5. 그 안에서, 각 경제 목표와 일치하는 데이터를 최종적으로 찾음
                    final_result = age_group_analysis.get(goal)
                    if final_result:
                        # 일치하는 기사를 찾으면, 중복 추가를 방지하고 다음 기사로 넘어감
                        personalized_articles.append({
                            "title": article.get("title", "제목 없음"),
                            "summary": final_result.get("summary", ""),
                            "recommendation": final_result.get("recommendation", "")
                        })
                        # 이 기사에서는 목표를 찾았으므로, 다음 기사로 넘어감
                        break 
        
        return {
            "user_profile": user_profile,
            "lifecycle_plans": lifecycle_plans,
            "personalized_articles": personalized_articles
        }
    except Exception as e:
        print(f"API 데이터 생성 중 오류 발생: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="데이터를 처리하는 중 서버 오류가 발생했습니다.")
