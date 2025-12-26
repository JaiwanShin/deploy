# 📊 네이버 시장 트렌드 대시보드

네이버 검색어 트렌드, 쇼핑인사이트, 검색광고 API를 활용한 통합 시장 분석 도구입니다.

## ✨ 주요 기능

| 탭 | 기능 | 설명 |
|---|------|------|
| 🔍 키워드 트렌드 | 검색 트렌드 분석 | 키워드별 검색량 추이, **3개월 예측**, Excel 다운로드 |
| 🛒 쇼핑 트렌드 | 카테고리 분석 | 대분류/세부 카테고리 클릭 트렌드 |
| 📦 상품 검색 | 상품 조회 | 가격 분포, 브랜드/판매처 분석 |
| ⚔️ 경쟁 비교 | 브랜드 분석 | 다중 브랜드 비교, 월별 히트맵 |
| 📈 성별/연령 분석 | 타겟팅 | 인구통계별 분석 |
| 🔑 키워드 리서치 | 키워드 발굴 | 연관 키워드, 마케팅 추천 |
| 🚀 시장 진입 분석 | 시장 조사 | 시장 규모, 경쟁 강도 |
| 📊 실제 검색량 | 검색량 조회 | **월간 절대값**, PC/모바일 비율 |

### 🆕 신규 기능
- 🔮 **트렌드 예측**: 향후 3개월 검색량 예측
- 📥 **Excel 다운로드**: 분석 결과 리포트 저장
- ⭐ **즐겨찾기**: 자주 쓰는 키워드 저장

---

## 🚀 빠른 시작

### 1. 설치
```bash
pip install streamlit pandas plotly requests openpyxl
```

### 2. API 키 설정 (config.py)
```python
# 네이버 개발자 센터 (developers.naver.com)
NAVER_CLIENT_ID = "your_client_id"
NAVER_CLIENT_SECRET = "your_secret"

# 네이버 검색광고 API (searchad.naver.com)
SEARCH_AD_ACCESS_KEY = "your_access_key"
SEARCH_AD_SECRET_KEY = "your_secret_key"
SEARCH_AD_CUSTOMER_ID = "your_customer_id"
```

### 3. 실행
```bash
cd naver_api
streamlit run trend_dashboard.py
```

---

## 📁 파일 구조

```
naver_api/
├── trend_dashboard.py    # 메인 대시보드 (1,700줄)
├── api_client.py         # DataLab API 클라이언트
├── search_ad_client.py   # 검색광고 API 클라이언트
├── config.py             # API 인증 설정
├── components/
│   ├── __init__.py       # 패키지 초기화
│   └── utils.py          # 공통 유틸리티
├── favorites.json        # 즐겨찾기 저장 (자동 생성)
├── test_api.py           # API 테스트
└── README.md             # 이 문서
```

---

## 🔑 API 키 발급 방법

### 네이버 개발자 센터 (DataLab API)
1. [developers.naver.com](https://developers.naver.com) 가입
2. **Application → 애플리케이션 등록**
3. 사용 API 선택:
   - ✅ 데이터랩 (검색어트렌드)
   - ✅ 데이터랩 (쇼핑인사이트)
   - ✅ 검색 (쇼핑)
4. 웹 서비스 URL: `http://localhost`

### 네이버 검색광고 API (실제 검색량)
1. [searchad.naver.com](https://searchad.naver.com) 가입
2. **도구 → API 사용 관리**
3. Access Key, Secret Key, Customer ID 발급

---

## 📊 API 호출 한도
- 검색어 트렌드: 일 1,000회
- 쇼핑인사이트: 일 1,000회
- 쇼핑 검색: 일 25,000회
- 검색광고: 무제한 (계정당)

---

## 💡 사용 예시

### Python 직접 사용
```python
from api_client import NaverDataLabClient

client = NaverDataLabClient()

# 키워드 비교 (12개월)
df = client.compare_keywords(["삼성전자", "LG전자", "애플"], months=12)
print(df)

# 상품 검색
products = client.search_all_products("블루투스 이어폰", max_results=100)
print(products[["title", "lprice", "brand"]])
```

---

## 📝 라이센스
MIT License
