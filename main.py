

import uvicorn
from fastapi import FastAPI
from pymongo import MongoClient
from routers import survey, news, auth
from apscheduler.schedulers.background import BackgroundScheduler
from notification_utils import send_kakao_message, send_email_notification

# --- FastAPI 앱 및 데이터베이스 설정 ---
app = FastAPI(title="KB AI Navigator")
MONGO_CONNECTION_STRING = "mongodb+srv://staran1227:Dksrbstmd122719!@cluster0.1vb2qmf.mongodb.net/"
client = MongoClient(MONGO_CONNECTION_STRING)
db = client["finance_article"]

# --- 통합 알림 발송 함수 ---
def send_daily_notifications():
    """DB에서 모든 사용자를 조회하여 가입 방식에 따라 알림을 보냅니다."""
    all_users = list(db.users.find({}))
    
    for user in all_users:
        user_email = user.get("email")
        # 사용자 이름으로 프로필에서 직업 정보를 가져옵니다. 없으면 이메일 앞부분을 사용합니다.
        user_profile = db.user_profiles.find_one({"user_id": user_email})
        user_name = user_profile.get("occupation", user_email.split('@')[0]) if user_profile else user_email.split('@')[0]

        # 가입 방식에 따라 다른 알림 함수 호출
        if user.get("signup_method") == "kakao" and user.get("kakao_access_token"):
            send_kakao_message(user["kakao_access_token"], user_name)
        elif user.get("signup_method") == "email":
            send_email_notification(user_email, user_name)

    
    print(" 일일 알림 발송 작업 완료.\n")

# --- FastAPI 앱 이벤트 핸들러 ---
@app.on_event("startup")
def startup_db_client():
    try:
        client.admin.command('ping')
        print(" MongoDB에 성공적으로 연결되었습니다.")
        app.state.db = db
    except Exception as e:
        print(f" MongoDB 연결에 실패했습니다: {e}")

    # --- 스케줄러 시작 ---
    scheduler = BackgroundScheduler(timezone="Asia/Seoul")
    # 매일 오전 8시와 오후 6시에 알림 발송
    scheduler.add_job(send_daily_notifications, 'cron', hour='8,18', minute='0')
    scheduler.start()
    
    



@app.on_event("shutdown")
def shutdown_db_client():
    client.close()
    print(" MongoDB 연결이 해제되었습니다.")

# --- 라우터 포함 ---
app.include_router(auth.router)
app.include_router(survey.router)
app.include_router(news.router)

# --- 서버 실행 ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
