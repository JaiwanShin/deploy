"""
네이버 데이터랩 API 클라이언트 모듈
- 검색어 트렌드 API
- 쇼핑인사이트 API
- 쇼핑 검색 API
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
import pandas as pd

from config import (
    NAVER_CLIENT_ID, 
    NAVER_CLIENT_SECRET,
    DATALAB_SEARCH_URL,
    DATALAB_SHOPPING_URL,
    DATALAB_SHOPPING_KEYWORD_URL,
    SHOPPING_SEARCH_URL
)


class NaverDataLabClient:
    """네이버 데이터랩 API 클라이언트"""
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id = client_id or NAVER_CLIENT_ID
        self.client_secret = client_secret or NAVER_CLIENT_SECRET
        self.headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
            "Content-Type": "application/json"
        }
    
    def _make_request(self, url: str, body: dict) -> dict:
        """API 요청 공통 함수"""
        try:
            response = requests.post(url, headers=self.headers, data=json.dumps(body))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error: {e.response.status_code}"
            if e.response.text:
                error_msg += f" - {e.response.text}"
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request Error: {str(e)}")
    
    # ========== 검색어 트렌드 API ==========
    
    def get_search_trend(
        self,
        keywords: List[Dict[str, Union[str, List[str]]]],
        start_date: str,
        end_date: str,
        time_unit: str = "month",
        device: str = "",
        gender: str = "",
        ages: List[str] = None
    ) -> pd.DataFrame:
        """
        검색어 트렌드 조회
        
        Args:
            keywords: 검색어 그룹 리스트
                예: [{"groupName": "삼성", "keywords": ["삼성전자", "갤럭시"]},
                     {"groupName": "애플", "keywords": ["애플", "아이폰"]}]
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            time_unit: 구간 단위 (date: 일간, week: 주간, month: 월간)
            device: 기기 ("": 전체, "pc": PC, "mo": 모바일)
            gender: 성별 ("": 전체, "m": 남성, "f": 여성)
            ages: 연령대 리스트 예: ["1", "2"] (1: 0-12세, 2: 13-18세, ...)
            
        Returns:
            DataFrame with trend data
        """
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": time_unit,
            "keywordGroups": keywords
        }
        
        if device:
            body["device"] = device
        if gender:
            body["gender"] = gender
        if ages:
            body["ages"] = ages
        
        result = self._make_request(DATALAB_SEARCH_URL, body)
        return self._parse_search_trend(result)
    
    def _parse_search_trend(self, result: dict) -> pd.DataFrame:
        """검색어 트렌드 결과 파싱"""
        all_data = []
        
        for group in result.get("results", []):
            group_name = group["title"]
            for item in group.get("data", []):
                all_data.append({
                    "group": group_name,
                    "period": item["period"],
                    "ratio": item["ratio"]
                })
        
        df = pd.DataFrame(all_data)
        if not df.empty:
            df["period"] = pd.to_datetime(df["period"])
        return df
    
    # ========== 쇼핑인사이트 API ==========
    
    def get_shopping_category_trend(
        self,
        category_name: str,
        category_code: str,
        start_date: str,
        end_date: str,
        time_unit: str = "month",
        device: str = "",
        gender: str = "",
        ages: List[str] = None
    ) -> pd.DataFrame:
        """
        쇼핑 카테고리 클릭 트렌드 조회
        
        Args:
            category_name: 카테고리 이름 (예: "패션의류")
            category_code: 쇼핑 카테고리 코드 (예: "50000000")
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            time_unit: 구간 단위 (date: 일간, week: 주간, month: 월간)
            device: 기기 ("": 전체, "pc": PC, "mo": 모바일)
            gender: 성별 ("": 전체, "m": 남성, "f": 여성)
            ages: 연령대 리스트
            
        Returns:
            DataFrame with category trend data
        """
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": time_unit,
            "category": [{"name": category_name, "param": [category_code]}]
        }
        
        if device:
            body["device"] = device
        if gender:
            body["gender"] = gender
        if ages:
            body["ages"] = ages
        
        result = self._make_request(DATALAB_SHOPPING_URL, body)
        return self._parse_shopping_trend(result)
    
    def get_shopping_keyword_trend(
        self,
        category: str,
        keyword: str,
        start_date: str,
        end_date: str,
        time_unit: str = "month",
        device: str = "",
        gender: str = "",
        ages: List[str] = None
    ) -> pd.DataFrame:
        """
        쇼핑 키워드 클릭 트렌드 조회
        
        Args:
            category: 쇼핑 카테고리 코드
            keyword: 검색 키워드
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            time_unit: 구간 단위
            device: 기기
            gender: 성별
            ages: 연령대 리스트
            
        Returns:
            DataFrame with keyword trend data
        """
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": time_unit,
            "category": category,
            "keyword": keyword
        }
        
        if device:
            body["device"] = device
        if gender:
            body["gender"] = gender
        if ages:
            body["ages"] = ages
        
        result = self._make_request(DATALAB_SHOPPING_KEYWORD_URL, body)
        return self._parse_shopping_trend(result)
    
    def _parse_shopping_trend(self, result: dict) -> pd.DataFrame:
        """쇼핑 트렌드 결과 파싱"""
        all_data = []
        
        for group in result.get("results", []):
            group_name = group.get("title", "unknown")
            for item in group.get("data", []):
                all_data.append({
                    "group": group_name,
                    "period": item["period"],
                    "ratio": item["ratio"]
                })
        
        df = pd.DataFrame(all_data)
        if not df.empty:
            df["period"] = pd.to_datetime(df["period"])
        return df
    
    # ========== 편의 함수 ==========
    
    def compare_keywords(
        self,
        keywords: List[str],
        months: int = 12
    ) -> pd.DataFrame:
        """
        여러 키워드의 검색 트렌드 간편 비교
        
        Args:
            keywords: 비교할 키워드 리스트 (최대 5개)
            months: 조회 기간 (개월)
            
        Returns:
            DataFrame with comparison data
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=months*30)).strftime("%Y-%m-%d")
        
        keyword_groups = [
            {"groupName": kw, "keywords": [kw]} 
            for kw in keywords[:5]  # 최대 5개
        ]
        
        return self.get_search_trend(
            keywords=keyword_groups,
            start_date=start_date,
            end_date=end_date,
            time_unit="month"
        )
    
    # ========== 쇼핑 검색 API ==========
    
    def search_products(
        self,
        query: str,
        display: int = 100,
        start: int = 1,
        sort: str = "sim"
    ) -> pd.DataFrame:
        """
        네이버 쇼핑 상품 검색
        
        Args:
            query: 검색어
            display: 검색 결과 수 (기본 100, 최대 100)
            start: 검색 시작 위치 (기본 1, 최대 1000)
            sort: 정렬 옵션
                - sim: 정확도순 (기본값)
                - date: 날짜순
                - asc: 가격 오름차순
                - dsc: 가격 내림차순
                
        Returns:
            DataFrame with product data
        """
        params = {
            "query": query,
            "display": min(display, 100),
            "start": start,
            "sort": sort
        }
        
        try:
            response = requests.get(
                SHOPPING_SEARCH_URL, 
                headers=self.headers, 
                params=params
            )
            response.raise_for_status()
            result = response.json()
            return self._parse_products(result)
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error: {e.response.status_code}"
            if e.response.text:
                error_msg += f" - {e.response.text}"
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request Error: {str(e)}")
    
    def _parse_products(self, result: dict) -> pd.DataFrame:
        """쇼핑 검색 결과 파싱"""
        items = result.get("items", [])
        
        products = []
        for item in items:
            # HTML 태그 제거
            title = item.get("title", "").replace("<b>", "").replace("</b>", "")
            
            # 가격 파싱 (빈 문자열 처리)
            lprice = item.get("lprice", "0")
            hprice = item.get("hprice", "0")
            lprice = int(lprice) if lprice else 0
            hprice = int(hprice) if hprice else 0
            
            products.append({
                "title": title,
                "link": item.get("link", ""),
                "image": item.get("image", ""),
                "lprice": lprice,
                "hprice": hprice,
                "mall_name": item.get("mallName", ""),
                "product_id": item.get("productId", ""),
                "product_type": item.get("productType", ""),
                "brand": item.get("brand", ""),
                "maker": item.get("maker", ""),
                "category1": item.get("category1", ""),
                "category2": item.get("category2", ""),
                "category3": item.get("category3", ""),
                "category4": item.get("category4", ""),
            })
        
        return pd.DataFrame(products)
    
    def search_all_products(
        self,
        query: str,
        max_results: int = 500,
        sort: str = "sim"
    ) -> pd.DataFrame:
        """
        여러 페이지에 걸쳐 상품 검색 (최대 1000개)
        
        Args:
            query: 검색어
            max_results: 최대 결과 수 (기본 500, 최대 1000)
            sort: 정렬 옵션
            
        Returns:
            DataFrame with all product data
        """
        all_products = []
        max_results = min(max_results, 1000)  # API 한도
        
        for start in range(1, max_results, 100):
            df = self.search_products(
                query=query,
                display=100,
                start=start,
                sort=sort
            )
            if df.empty:
                break
            all_products.append(df)
        
        if all_products:
            return pd.concat(all_products, ignore_index=True)
        return pd.DataFrame()
    
    def get_price_stats(self, query: str, max_results: int = 500) -> dict:
        """
        상품 가격 통계 조회
        
        Args:
            query: 검색어
            max_results: 분석할 최대 상품 수
            
        Returns:
            dict with price statistics
        """
        df = self.search_all_products(query, max_results, sort="sim")
        
        if df.empty:
            return {}
        
        # 최저가가 0인 상품 제외
        df_valid = df[df["lprice"] > 0]
        
        if df_valid.empty:
            return {}
        
        return {
            "query": query,
            "total_products": len(df_valid),
            "min_price": int(df_valid["lprice"].min()),
            "max_price": int(df_valid["lprice"].max()),
            "avg_price": int(df_valid["lprice"].mean()),
            "median_price": int(df_valid["lprice"].median()),
            "std_price": int(df_valid["lprice"].std()),
            "top_malls": df_valid["mall_name"].value_counts().head(10).to_dict(),
            "top_brands": df_valid["brand"].value_counts().head(10).to_dict(),
            "price_distribution": {
                "q1": int(df_valid["lprice"].quantile(0.25)),
                "q2": int(df_valid["lprice"].quantile(0.50)),
                "q3": int(df_valid["lprice"].quantile(0.75)),
            }
        }


# 카테고리 코드 참조용 딕셔너리 (주요 카테고리)
SHOPPING_CATEGORIES = {
    "패션의류": "50000000",
    "패션잡화": "50000001",
    "화장품/미용": "50000002",
    "디지털/가전": "50000003",
    "가구/인테리어": "50000004",
    "출산/육아": "50000005",
    "식품": "50000006",
    "스포츠/레저": "50000007",
    "생활/건강": "50000008",
    "여가/생활편의": "50000009",
}

# 세분화된 하위 카테고리 (2단계)
SHOPPING_SUBCATEGORIES = {
    "디지털/가전": {
        "노트북": "50000151",
        "데스크탑": "50000152",
        "모니터": "50000153",
        "태블릿PC": "50000154",
        "스마트폰": "50000158",
        "휴대폰 액세서리": "50000159",
        "이어폰/헤드폰": "50000209",
        "스피커": "50000211",
        "블루투스 이어폰": "50005700",
        "스마트워치": "50000988",
        "TV": "50000162",
        "에어컨": "50000166",
        "냉장고": "50000167",
        "세탁기": "50000168",
        "청소기": "50000178",
        "공기청정기": "50000804",
        "카메라": "50000163",
        "게임기": "50000656",
    },
    "패션의류": {
        "여성의류 전체": "50000167",
        "티셔츠": "50010561",
        "원피스": "50010564",
        "블라우스": "50010562",
        "청바지": "50010572",
        "니트/스웨터": "50010567",
        "코트": "50010579",
        "패딩": "50010580",
        "자켓": "50010577",
        "남성의류 전체": "50000169",
    },
    "화장품/미용": {
        "스킨케어": "50000100",
        "마스크팩": "50000105",
        "클렌징": "50000101",
        "선케어": "50000104",
        "메이크업 전체": "50000106",
        "립스틱": "50000110",
        "파운데이션": "50000107",
        "향수": "50000119",
        "남성화장품": "50000102",
    },
    "식품": {
        "과일": "50001145",
        "채소": "50001147",
        "정육/계란": "50001149",
        "수산물": "50001152",
        "라면/면류": "50001159",
        "커피/차": "50001169",
        "과자/간식": "50001164",
        "건강식품": "50000903",
        "음료": "50001171",
    },
    "스포츠/레저": {
        "헬스/요가": "50000629",
        "골프": "50000622",
        "캠핑": "50000981",
        "자전거": "50000627",
        "등산": "50000623",
        "수영": "50000619",
        "축구": "50000614",
        "농구": "50000615",
        "테니스": "50000618",
        "러닝/마라톤": "50000630",
    },
    "가구/인테리어": {
        "침대": "50000282",
        "소파": "50000283",
        "책상": "50000284",
        "의자": "50000285",
        "수납장": "50000287",
        "조명": "50000289",
        "커튼/블라인드": "50000291",
        "침구": "50000264",
    },
    "출산/육아": {
        "유모차": "50000347",
        "카시트": "50000348",
        "기저귀": "50000351",
        "분유": "50000353",
        "유아동의류": "50000344",
        "장난감": "50000359",
    },
    "생활/건강": {
        "세제": "50000509",
        "욕실용품": "50000502",
        "주방용품": "50000487",
        "구강용품": "50000532",
        "의약품": "50000539",
        "안경/렌즈": "50000537",
    },
}


# 사용 예시
if __name__ == "__main__":
    # 클라이언트 초기화
    client = NaverDataLabClient()
    
    # 검색어 트렌드 조회 예시
    print("=== 검색어 트렌드 테스트 ===")
    try:
        df = client.compare_keywords(["삼성전자", "LG전자", "애플"], months=12)
        print(df.head(10))
    except Exception as e:
        print(f"Error: {e}")
        print("API 키를 config.py에 설정해주세요.")
