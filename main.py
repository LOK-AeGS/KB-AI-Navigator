# main.py

import uvicorn
from fastapi import FastAPI
from pymongo import MongoClient
from routers import survey, news, auth  # auth 라우터 import

# --- FastAPI 앱 및 데이터베이스 설정 ---
app = FastAPI(title="KB AI Navigator")
MONGO_CONNECTION_STRING = "mongodb+srv://staran1227:Dksrbstmd122719!@cluster0.1vb2qmf.mongodb.net/"
client = MongoClient(MONGO_CONNECTION_STRING)
db = client["finance_article"]

# --- FastAPI 앱 이벤트 핸들러 ---
@app.on_event("startup")
def startup_db_client():
    try:
        client.admin.command('ping')
        print("✅ MongoDB에 성공적으로 연결되었습니다.")
        app.state.db = db
    except Exception as e:
        print(f"❌ MongoDB 연결에 실패했습니다: {e}")

@app.on_event("shutdown")
def shutdown_db_client():
    client.close()
    print("🔌 MongoDB 연결이 해제되었습니다.")

# --- 라우터 포함 ---
app.include_router(auth.router)  # auth 라우터 등록
app.include_router(survey.router)
app.include_router(news.router)

# --- 서버 실행 ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
