import os
import streamlit as st

# Streamlit Cloud Secret 또는 로컬 환경변수 우선 사용
def get_secret(key, default):
    # 1. Streamlit Secrets 확인 (Cloud 배포용)
    if key in st.secrets:
        return st.secrets[key]
    # 2. 환경변수 확인
    return os.getenv(key, default)

# 네이버 데이터랩 API 키
NAVER_CLIENT_ID = get_secret("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = get_secret("NAVER_CLIENT_SECRET", "")

# 네이버 검색광고 API 키
SEARCH_AD_ACCESS_KEY = get_secret("SEARCH_AD_ACCESS_KEY", "")
SEARCH_AD_SECRET_KEY = get_secret("SEARCH_AD_SECRET_KEY", "")
SEARCH_AD_CUSTOMER_ID = get_secret("SEARCH_AD_CUSTOMER_ID", "")

# API 엔드포인트
DATALAB_SEARCH_URL = "https://openapi.naver.com/v1/datalab/search"
DATALAB_SHOPPING_URL = "https://openapi.naver.com/v1/datalab/shopping/categories"
DATALAB_SHOPPING_KEYWORD_URL = "https://openapi.naver.com/v1/datalab/shopping/category/keywords"
SHOPPING_SEARCH_URL = "https://openapi.naver.com/v1/search/shop.json"
SEARCH_AD_API_URL = "https://api.searchad.naver.com"

# API 호출 제한 (기본값)
DATALAB_DAILY_LIMIT = 1000
SEARCH_DAILY_LIMIT = 25000
