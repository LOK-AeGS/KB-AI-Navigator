# notification_utils.py

import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 서비스의 기본 URL 설정 ---
# 실제 운영 도메인 주소를 변수로 관리하여 쉽게 변경할 수 있도록 합니다.
BASE_URL = "http://www.lifefinance.asia"

# --- 카카오톡 메시지 발송 함수 ---
def send_kakao_message(access_token: str, user_name: str):
    """지정된 사용자의 Access Token을 사용하여 카카오톡 메시지를 보냅니다."""
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send" # 기본 메시지 URL로 변경
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 결과 페이지 링크
    results_link = f"{BASE_URL}/results"
    
    # 메시지 템플릿을 'feed' (피드) 타입으로 변경합니다.
    # 이메일과 유사한 형태로 제목, 설명, 이미지, 버튼을 직접 구성할 수 있습니다.
    template = {
        "object_type": "feed",
        "content": {
            "title": f"📈 {user_name}님, 새로운 맞춤 리포트가 도착했어요!",
            "description": "최신 경제 뉴스를 바탕으로 회원님만을 위한 분석이 업데이트되었습니다. 아래 버튼을 클릭하여 지금 바로 확인해보세요.",
            "image_url": "https://i.imgur.com/8i7b2dC.png", # 대표 이미지 URL
            "link": {
                "web_url": results_link,
                "mobile_web_url": results_link
            }
        },
        "buttons": [
            {
                "title": "내 리포트 확인하기",
                "link": {
                    "web_url": results_link,
                    "mobile_web_url": results_link
                }
            }
        ]
    }
    
    # API 요청 시 template_object를 JSON 문자열로 변환하여 전달
    response = requests.post(url, headers=headers, data={"template_object": json.dumps(template)})
    
    if response.json().get('result_code') == 0:
        print(f"✅ 카카오톡 피드 메시지 발송 성공: {user_name}님")
    else:
        print(f"❌ 카카오톡 피드 메시지 발송 실패: {user_name}님, 응답: {response.text}")

# --- 이메일 발송 함수 ---
def send_email_notification(recipient_email: str, user_name: str):
    """지정된 이메일 주소로 알림 메일을 보냅니다."""
    # !!! 중요: 이 정보들을 실제 운영 환경에서는 .env 파일 등으로 안전하게 관리해야 합니다. !!!
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SENDER_EMAIL = "YOUR_SENDER_EMAIL@gmail.com"
    SENDER_PASSWORD = "YOUR_GMAIL_APP_PASSWORD"

    # 결과 페이지 링크
    results_link = f"{BASE_URL}/results"

    # 이메일 내용 구성
    subject = f"📈 {user_name}님, KB AI Navigator 맞춤 리포트가 도착했습니다."
    body = f"""
    <html>
    <body>
        <h2>{user_name}님, 안녕하세요!</h2>
        <p>최신 경제 뉴스와 회원님의 프로필을 반영한 새로운 맞춤 분석 리포트가 도착했습니다.</p>
        <p>아래 버튼을 클릭하여 지금 바로 확인해보세요.</p>
        <a href="{results_link}" style="display: inline-block; padding: 12px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 8px; font-size: 16px;">내 리포트 확인하기</a>
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
