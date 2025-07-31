# main.py

import uvicorn
from fastapi import FastAPI
from pymongo import MongoClient
from routers import survey, news  # routers 폴더에서 survey.py와 news.py를 import

# --- FastAPI 앱 및 데이터베이스 설정 ---

app = FastAPI(
    title="맞춤형 금융 뉴스 분석 서비스",
    description="사용자 설문조사를 바탕으로 개인화된 금융 뉴스 분석을 제공합니다.",
    version="1.0.0"
)

# !!! 중요: MongoDB 연결 설정 !!!
MONGO_CONNECTION_STRING = "mongodb+srv://staran1227:Dksrbstmd122719!@cluster0.1vb2qmf.mongodb.net/"
client = MongoClient(MONGO_CONNECTION_STRING)
db = client["finance_article"]

# --- FastAPI 앱 이벤트 핸들러 ---

@app.on_event("startup")
def startup_db_client():
    # 앱 시작 시 MongoDB 연결 테스트 및 DB 객체를 앱 상태에 저장
    try:
        client.admin.command('ping')
        print("✅ MongoDB에 성공적으로 연결되었습니다.")
        # 라우터 파일에서 DB 커넥션을 사용할 수 있도록 app.state에 저장합니다.
        # 이것이 각 라우터의 Depends(get_db) 함수가 동작하는 원리입니다.
        app.state.db = db
    except Exception as e:
        print(f"❌ MongoDB 연결에 실패했습니다: {e}")

@app.on_event("shutdown")
def shutdown_db_client():
    # 앱 종료 시 MongoDB 연결 해제
    client.close()
    print("🔌 MongoDB 연결이 해제되었습니다.")


# --- 라우터 포함 (Include Routers) ---
# Express의 app.use()와 유사한 기능입니다.
# 각 파일에서 정의한 라우트들을 메인 앱에 등록합니다.
app.include_router(survey.router)
app.include_router(news.router)


# --- 서버 실행 ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

