# notification_utils.py

import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 카카오톡 메시지 발송 함수 ---
def send_kakao_message(access_token: str, user_name: str):
    """지정된 사용자의 Access Token을 사용하여 카카오톡 메시지를 보냅니다."""
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 메시지 템플릿: 사용자 이름을 포함하여 개인화
    template = {
        "object_type": "feed",
        "content": {
            "title": f"📈 {user_name}님, 새로운 맞춤 리포트가 도착했어요!",
            "description": "최신 경제 뉴스를 바탕으로 회원님만을 위한 분석이 업데이트되었습니다.",
            "image_url": "https://i.imgur.com/8i7b2dC.png", # 대표 이미지 URL
            "link": {
                "web_url": "http://127.0.0.1:8000/results",
                "mobile_web_url": "http://127.0.0.1:8000/results"
            }
        },
        "buttons": [
            {
                "title": "지금 바로 확인하기",
                "link": {
                    "web_url": "http://127.0.0.1:8000/results",
                    "mobile_web_url": "http://127.0.0.1:8000/results"
                }
            }
        ]
    }
    
    response = requests.post(url, headers=headers, data={"template_object": json.dumps(template)})
    
    if response.json().get('result_code') == 0:
        print(f"✅ 카카오톡 알림 발송 성공: {user_name}님")
    else:
        print(f"❌ 카카오톡 알림 발송 실패: {user_name}님, 응답: {response.text}")

# --- 이메일 발송 함수 ---
def send_email_notification(recipient_email: str, user_name: str):
    """지정된 이메일 주소로 알림 메일을 보냅니다."""
    # !!! 중요: 이 정보들을 실제 운영 환경에서는 .env 파일 등으로 안전하게 관리해야 합니다. !!!
    # Gmail의 경우 '앱 비밀번호'를 생성하여 사용해야 합니다.
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SENDER_EMAIL = "YOUR_SENDER_EMAIL@gmail.com"  # 보내는 사람 Gmail 주소
    SENDER_PASSWORD = "YOUR_GMAIL_APP_PASSWORD" # Gmail 앱 비밀번호

    # 이메일 내용 구성
    subject = f"📈 {user_name}님, KB AI Navigator 맞춤 리포트가 도착했습니다."
    body = f"""
    <html>
    <body>
        <h2>{user_name}님, 안녕하세요!</h2>
        <p>최신 경제 뉴스와 회원님의 프로필을 반영한 새로운 맞춤 분석 리포트가 도착했습니다.</p>
        <p>아래 버튼을 클릭하여 지금 바로 확인해보세요.</p>
        <a href="http://127.0.0.1:8000/results" style="display: inline-block; padding: 12px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 8px; font-size: 16px;">내 리포트 확인하기</a>
        <p style="margin-top: 20px; font-size: 12px; color: #888;">본 메일은 KB AI Navigator 서비스 알림 메일입니다.</p>
    </body>
    </html>
    """
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()
        print(f"✅ 이메일 발송 성공: {recipient_email}")
    except Exception as e:
        print(f"❌ 이메일 발송 실패: {recipient_email}, 오류: {e}")
