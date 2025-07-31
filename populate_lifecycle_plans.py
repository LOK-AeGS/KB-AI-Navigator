# populate_lifecycle_plans.py

from pymongo import MongoClient

# --- MongoDB 연결 설정 ---
MONGO_CONNECTION_STRING = "mongodb+srv://staran1227:Dksrbstmd122719!@cluster0.1vb2qmf.mongodb.net/"
client = MongoClient(MONGO_CONNECTION_STRING)
db = client["finance_article"]
collection = db["lifecycle_plans"]

# --- 샘플 생애주기별 경제 계획 데이터 정의 ---

lifecycle_plans = [
    {
        "age_group": "20대 초반",
        "status": "완료",
        "tasks": [
            "비상금 100만원 이상 적립 (월수입의 3-6개월분)",
            "신용점수 관리 및 신용카드 사용 습관 형성",
            "투자 공부 시작 (주식, 펀드 기초 학습)",
            "목돈 마련을 위한 적금 가입"
        ],
        "milestone_age": None
    },
    {
        "age_group": "20대 후반",
        "status": "진행중",
        "tasks": [
            "월 60만원 이상 투자 시작",
            "연금저축 가입 (세액공제 혜택 활용)",
            "70% 안전자산, 30% 성장자산 포트폴리오",
            "부동산 관련 정보 수집 및 청약통장 가입"
        ],
        "milestone_age": None
    },
    {
        "age_group": "30대 초반",
        "status": "예정",
        "tasks": [
            "주택 구입 여부 검토",
            "월 저축액 90만원 이상 목표",
            "보험 포트폴리오 점검 (실손의료보험, 암보험)",
            "자녀 교육비 적립 시작"
        ],
        "milestone_age": "31-35세"
    },
    {
        "age_group": "30대 후반",
        "status": "예정",
        "tasks": [
            "은퇴 계획 구체화 (목표 은퇴 자금 설정)",
            "IRP, 개인연금 추가 가입 검토",
            "자녀 교육비 본격 적립",
            "부동산 투자 또는 업그레이드 검토"
        ],
        "milestone_age": "36-40세"
    },
    {
        "age_group": "40대 초반",
        "status": "예정",
        "tasks": [
            "은퇴 자금 집중 적립 (목표 금액의 50% 이상 달성)",
            "자녀 대학 진학 준비 (교육비 최대 소요 시기)",
            "건강관리 및 건강검진 정기적 실시",
            "투자 포트폴리오 안정성 강화"
        ],
        "milestone_age": "41-45세"
    },
    {
        "age_group": "40대 후반",
        "status": "예정",
        "tasks": [
            "은퇴 자금 집중 적립 (목표 금액의 70% 이상 달성)",
            "안정적인 포트폴리오 조정",
            "건강보험, 간병보험 가입 검토",
            "은퇴 시기 및 계획 구체화"
        ],
        "milestone_age": "46-50세"
    },
    {
        "age_group": "50대 이상",
        "status": "예정",
        "tasks": [
            "은퇴 자금 최종 점검 (목표 금액 90% 이상 달성)",
            "연금 수령 계획 및 세금 최적화",
            "상속, 증여 계획 수립",
            "노후 거주지 및 생활 패턴 계획"
        ],
        "milestone_age": "51세 이상"
    }
]

def populate_data():
    """
    'lifecycle_plans' 컬렉션에 데이터를 삽입합니다.
    """
    try:
        client.admin.command('ping')
        print("✅ MongoDB에 성공적으로 연결되었습니다.")

        if collection.count_documents({}) > 0:
            print("🟡 'lifecycle_plans' 컬렉션에 이미 데이터가 존재하여 기존 데이터를 삭제하고 새로 추가합니다.")
            collection.delete_many({})
        
        result = collection.insert_many(lifecycle_plans)
        print(f"✅ 데이터 삽입 성공! {len(result.inserted_ids)}개의 생애주기 계획을 'lifecycle_plans' 컬렉션에 추가했습니다.")

    except Exception as e:
        print(f"❌ 데이터 삽입 중 오류가 발생했습니다: {e}")
    finally:
        client.close()
        print("🔌 MongoDB 연결이 해제되었습니다.")

if __name__ == "__main__":
    populate_data()
