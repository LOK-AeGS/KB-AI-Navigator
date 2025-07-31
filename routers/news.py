# routers/news.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Optional
from pymongo.database import Database
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler

# --- Pydantic 모델 정의 ---
class AnalysisResultItem(BaseModel):
    summary: str
    recommendation: str

# --- Helper Function: 페르소나 매칭 ---
def get_best_fit_persona_by_similarity(user_profile: dict) -> str:
    representative_personas = [
        {'persona_name': '학생 (대학생)', 'age': 22, 'occupation': '학생'},
        {'persona_name': '20대 사회초년생', 'age': 28, 'occupation': '회사원'},
        {'persona_name': '30대 신혼부부/1인 가구', 'age': 35, 'occupation': '회사원'},
        {'persona_name': '40대 (자녀 양육기)', 'age': 45, 'occupation': '회사원'},
        {'persona_name': '50대 (은퇴 준비기)', 'age': 55, 'occupation': '자영업'},
        {'persona_name': '60대 이상 (은퇴 후)', 'age': 67, 'occupation': '은퇴자'},
    ]
    simplified_user_profile = {'age': user_profile.get('age'), 'occupation': user_profile.get('occupation')}
    all_profiles = [simplified_user_profile] + representative_personas
    categorical_features = ['occupation']
    numerical_features = ['age']
    categorical_data = [[p.get(f, '기타') for f in categorical_features] for p in all_profiles]
    numerical_data = np.array([[p.get(f, 0) for f in numerical_features] for p in all_profiles])
    encoder = OneHotEncoder(handle_unknown='ignore')
    categorical_vectors = encoder.fit_transform(categorical_data).toarray()
    scaler = MinMaxScaler()
    numerical_vectors = scaler.fit_transform(numerical_data)
    all_vectors = np.hstack((categorical_vectors, numerical_vectors))
    user_vector = all_vectors[0].reshape(1, -1)
    persona_vectors = all_vectors[1:]
    similarities = cosine_similarity(user_vector, persona_vectors)[0]
    best_match_index = np.argmax(similarities)
    best_persona = representative_personas[best_match_index]['persona_name']
    return best_persona

# --- 라우터 및 API 정의 ---
router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db(request: Request) -> Database:
    return request.app.state.db

@router.get("/results", response_class=HTMLResponse, tags=["Results Dashboard"])
async def show_results_dashboard(request: Request, db: Database = Depends(get_db)):
    try:
        # 1. 사용자 프로필 조회
        user_profile = db.user_profiles.find_one({}, sort=[('_id', -1)])
        if not user_profile:
            return templates.TemplateResponse("error.html", {"request": request, "message": "설문조사 결과가 없습니다."})

        # 2. 생애주기 계획 조회
        lifecycle_plans = list(db.lifecycle_plans.find({}))

        # 3. 맞춤 기사 요약 조회
        matched_persona_name = get_best_fit_persona_by_similarity(user_profile)
        all_articles_analysis = list(db.analysis_results.find({}))
        
        personalized_articles = []
        for article in all_articles_analysis:
            persona_result = article.get('analysis_results', {}).get(matched_persona_name)
            if persona_result:
                personalized_articles.append({
                    "title": article.get("title", "제목 없음"),
                    "summary": persona_result.get("summary", ""),
                    "recommendation": persona_result.get("recommendation", "")
                })
        
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
