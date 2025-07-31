# populate_personas.py

from pymongo import MongoClient

# --- MongoDB 연결 설정 ---
# main.py와 동일한 연결 정보를 사용합니다.
MONGO_CONNECTION_STRING = "mongodb+srv://staran1227:Dksrbstmd122719!@cluster0.1vb2qmf.mongodb.net/"
client = MongoClient(MONGO_CONNECTION_STRING)
db = client["finance_article"]
collection = db["standard_person"]

# --- 6가지 표준 페르소나 데이터 정의 ---
# 보내주신 이미지를 바탕으로 데이터를 구성했습니다.
personas = [
    {
        "persona_name": "학생 (대학생)",
        "description": "아직 소득은 없거나 적지만, 첫 금융 습관을 형성하는 가장 중요한 시기.",
        "financial_goal": "학자금 관리, 아르바이트 소득 관리, 건전한 소비 습관 형성.",
        "related_news_keywords": ["정부 청년 지원 정책", "체크카드 혜택", "소액 적금/투자"]
    },
    {
        "persona_name": "20대 사회초년생",
        "description": "첫 월급을 받기 시작하며 본격적인 자산 형성을 시작.",
        "financial_goal": "1,000만 원 종잣돈 모으기, 학자금 대출 상환.",
        "related_news_keywords": ["청년도약계좌", "예/적금 금리", "주식/코인 등 첫 투자"]
    },
    {
        "persona_name": "30대 신혼부부/1인 가구",
        "description": "결혼, 주택 구매 등 인생의 큰 재무 이벤트를 겪는 시기.",
        "financial_goal": "내 집 마련 (전세 또는 매매), 장기 자산 형성 시작.",
        "related_news_keywords": ["부동산 정책", "대출 규제(DSR, LTV)", "금리 변동"]
    },
    {
        "persona_name": "40대 (자녀 양육기)",
        "description": "소득이 가장 안정적이지만, 자녀 교육비 등 지출도 가장 많은 시기.",
        "financial_goal": "자녀 교육 자금 마련, 본격적인 노후 준비.",
        "related_news_keywords": ["세금 정책(연말정산)", "펀드/ETF 등 중위험 투자", "연금"]
    },
    {
        "persona_name": "50대 (은퇴 준비기)",
        "description": "은퇴가 가까워지며, 공격적인 투자보다는 자산을 지키는 데 집중.",
        "financial_goal": "안정적인 은퇴 자금 포트폴리오 완성, 부채 정리.",
        "related_news_keywords": ["퇴직연금(IRP) 및 국민연금", "배당주", "채권", "금융소득종합과세"]
    },
    {
        "persona_name": "60대 이상 (은퇴 후)",
        "description": "모아둔 자산을 효율적으로 사용하며, 안정적인 현금 흐름을 만드는 것이 중요.",
        "financial_goal": "안정적인 생활비 확보, 자산 상속 및 증여 계획.",
        "related_news_keywords": ["연금 수령 방법", "즉시연금", "주택연금", "건강보험", "상속세"]
    }
]

def populate_data():
    """
    'standard_person' 컬렉션에 6가지 페르소나 데이터를 삽입합니다.
    데이터가 이미 존재하면 중복 삽입을 방지합니다.
    """
    try:
        # 1. DB 연결 확인
        client.admin.command('ping')
        print("✅ MongoDB에 성공적으로 연결되었습니다.")

        # 2. 데이터 중복 확인
        if collection.count_documents({}) > 0:
            print("🟡 'standard_person' 컬렉션에 이미 데이터가 존재합니다. 작업을 중단합니다.")
            return

        # 3. 데이터 삽입
        result = collection.insert_many(personas)
        print(f"✅ 데이터 삽입 성공! {len(result.inserted_ids)}개의 페르소나를 'standard_person' 컬렉션에 추가했습니다.")

    except Exception as e:
        print(f"❌ 데이터 삽입 중 오류가 발생했습니다: {e}")
    finally:
        # 4. 연결 해제
        client.close()
        print("🔌 MongoDB 연결이 해제되었습니다.")

if __name__ == "__main__":
    populate_data()
