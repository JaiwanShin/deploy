#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 쇼핑 모니터링 대시보드
============================

Streamlit 기반 인터랙티브 대시보드
./output/ 폴더의 CSV 파일들을 시각화합니다.

실행: streamlit run dashboard.py
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# =============================================================================
# 설정
# =============================================================================

st.set_page_config(
    page_title="네이버 모니터링 - Calmf",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

OUTPUT_DIR = "./output"

# 색상 팔레트
COLORS = {
    "Mass": "#3498db",      # 파랑
    "Premium": "#9b59b6",   # 보라
    "Luxury": "#e74c3c",    # 빨강
    "Unknown": "#95a5a6",   # 회색
    "primary": "#2c3e50",
    "success": "#27ae60",
    "warning": "#f39c12",
    "danger": "#e74c3c",
}

# =============================================================================
# 데이터 로드
# =============================================================================

@st.cache_data
def load_data():
    """CSV 파일들을 로드"""
    data = {}
    files = [
        "clean_long", "positioning_scatter", "positioning_summary",
        "corr_rank_price", "category_sov", "market_gap",
        "top_keywords", "calmf_products", "calmf_vs_market",
        "outliers", "data_quality"
    ]
    
    for name in files:
        path = Path(OUTPUT_DIR) / f"{name}.csv"
        if path.exists():
            data[name] = pd.read_csv(path)
        else:
            data[name] = pd.DataFrame()
    
    return data

# =============================================================================
# 커스텀 CSS
# =============================================================================

def apply_custom_css():
    st.markdown("""
    <style>
    /* 메인 배경 */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* KPI 카드 */
    .kpi-card {
        background: linear-gradient(145deg, #2d3436 0%, #1e272e 100%);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .kpi-value {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00d2ff, #3a7bd5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 10px 0;
    }
    .kpi-label {
        font-size: 0.9rem;
        color: #b2bec3;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .kpi-desc {
        font-size: 0.75rem;
        color: #636e72;
        margin-top: 8px;
    }
    
    /* 섹션 헤더 */
    .section-header {
        background: linear-gradient(90deg, rgba(52,152,219,0.2) 0%, rgba(155,89,182,0.2) 100%);
        border-left: 4px solid #3498db;
        padding: 15px 20px;
        margin: 30px 0 20px 0;
        border-radius: 0 8px 8px 0;
    }
    .section-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: #ecf0f1;
        margin: 0;
    }
    .section-desc {
        font-size: 0.85rem;
        color: #b2bec3;
        margin-top: 5px;
    }
    
    /* 인사이트 박스 */
    .insight-box {
        background: rgba(39, 174, 96, 0.15);
        border: 1px solid rgba(39, 174, 96, 0.3);
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .insight-box.warning {
        background: rgba(243, 156, 18, 0.15);
        border-color: rgba(243, 156, 18, 0.3);
    }
    .insight-box.danger {
        background: rgba(231, 76, 60, 0.15);
        border-color: rgba(231, 76, 60, 0.3);
    }
    
    /* 사이드바 */
    .css-1d391kg {
        background: #1e272e;
    }
    
    /* KPI 툴팁 */
    .kpi-help {
        display: inline-block;
        width: 18px;
        height: 18px;
        background: rgba(52, 152, 219, 0.3);
        border-radius: 50%;
        font-size: 0.7rem;
        color: #3498db;
        text-align: center;
        line-height: 18px;
        cursor: help;
        margin-left: 5px;
        position: relative;
    }
    .kpi-help:hover::after {
        content: attr(data-tooltip);
        position: absolute;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        background: #2d3436;
        color: #ecf0f1;
        padding: 10px 12px;
        border-radius: 8px;
        font-size: 0.75rem;
        white-space: pre-line;
        width: 220px;
        text-align: left;
        z-index: 1000;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        border: 1px solid rgba(52, 152, 219, 0.3);
    }
    .kpi-help:hover::before {
        content: '';
        position: absolute;
        bottom: 115%;
        left: 50%;
        transform: translateX(-50%);
        border: 6px solid transparent;
        border-top-color: #2d3436;
        z-index: 1001;
    }
    
    /* 섹션 제목 흰색 */
    h4, h5, .stMarkdown h4, .stMarkdown h5 {
        color: #ffffff !important;
    }
    
    /* 설명 텍스트 */
    .metric-desc {
        color: #b2bec3;
        font-size: 0.85rem;
        margin-bottom: 10px;
    }
    
    /* 다크 테마 데이터프레임 */
    .stDataFrame {
        background: rgba(45, 52, 54, 0.5) !important;
        border-radius: 8px;
    }
    .stDataFrame [data-testid="stDataFrameResizable"] {
        background: transparent !important;
    }
    
    /* 인사이트 박스 흰색 텍스트 */
    .insight-box, .insight-box.warning {
        color: #ffffff;
    }
    .insight-box code {
        color: #f1c40f;
        background: rgba(241, 196, 15, 0.2);
        padding: 2px 6px;
        border-radius: 4px;
    }
    
    /* 커스텀 다크 테이블 */
    .dark-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
        margin: 10px 0;
    }
    .dark-table th {
        background: linear-gradient(135deg, #2d3436 0%, #1e272e 100%);
        color: #ffffff;
        font-weight: 600;
        padding: 12px 15px;
        text-align: left;
        border-bottom: 2px solid #3498db;
    }
    .dark-table td {
        background: rgba(45, 52, 54, 0.6);
        color: #ecf0f1;
        padding: 10px 15px;
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    .dark-table tr:nth-child(even) td {
        background: rgba(52, 73, 94, 0.4);
    }
    .dark-table tr:hover td {
        background: rgba(52, 152, 219, 0.2);
    }
    .dark-table td.number {
        text-align: right;
        font-family: 'Consolas', monospace;
    }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# KPI 컴포넌트
# =============================================================================

def render_kpi(value, label, description="", format_type="number", prefix="", suffix="", tooltip=""):
    """KPI 카드 렌더링 (툴팁 지원)"""
    if pd.isna(value):
        formatted = "N/A"
    elif format_type == "number":
        formatted = f"{prefix}{value:,.0f}{suffix}"
    elif format_type == "currency":
        formatted = f"₩{value:,.0f}"
    elif format_type == "percent":
        formatted = f"{value:.1%}"
    elif format_type == "decimal":
        formatted = f"{value:.3f}"
    else:
        formatted = str(value)
    
    # 툴팁 아이콘 (있을 경우)
    help_icon = ""
    if tooltip:
        # HTML 특수문자 이스케이프 및 줄바꿈 처리
        tooltip_escaped = (
            tooltip
            .replace('"', '&quot;')
            .replace("'", "&#39;")
            .replace("\n", "&#10;")
        )
        help_icon = f'<span class="kpi-help" data-tooltip="{tooltip_escaped}">?</span>'
    
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}{help_icon}</div>
        <div class="kpi-value">{formatted}</div>
        <div class="kpi-desc">{description}</div>
    </div>
    """, unsafe_allow_html=True)

def render_section_header(title, description="", icon="📊"):
    """섹션 헤더 렌더링"""
    st.markdown(f"""
    <div class="section-header">
        <p class="section-title">{icon} {title}</p>
        <p class="section-desc">{description}</p>
    </div>
    """, unsafe_allow_html=True)

def render_dark_table(df, columns=None, rename_cols=None, number_cols=None):
    """다크 테마 테이블 렌더링
    
    Args:
        df: DataFrame
        columns: 표시할 컬럼 목록
        rename_cols: 컬럼명 변경 딕셔너리
        number_cols: 숫자 포맷팅할 컬럼 목록
    """
    if df.empty:
        st.info("데이터가 없습니다.")
        return
    
    if columns:
        df = df[columns].copy()
    if rename_cols:
        df = df.rename(columns=rename_cols)
    
    # 숫자 포맷팅
    if number_cols and rename_cols:
        for col in number_cols:
            new_col = rename_cols.get(col, col)
            if new_col in df.columns:
                df[new_col] = df[new_col].apply(
                    lambda x: f"{x:,.2f}" if pd.notna(x) and isinstance(x, (int, float)) else x
                )
    
    # HTML 테이블 생성
    html = '<table class="dark-table">'
    html += '<thead><tr>'
    for col in df.columns:
        html += f'<th>{col}</th>'
    html += '</tr></thead><tbody>'
    
    for _, row in df.iterrows():
        html += '<tr>'
        for col in df.columns:
            val = row[col]
            html += f'<td>{val}</td>'
        html += '</tr>'
    
    html += '</tbody></table>'
    st.markdown(html, unsafe_allow_html=True)

# =============================================================================
# 차트 함수
# =============================================================================

def create_scatter_plot(df, calmf_df=None):
    """포지셔닝 산점도 (캄프 강조 포함)
    
    Args:
        df: 전체 데이터
        calmf_df: 캄프 상품 데이터 (강조 표시용)
    """
    if df.empty:
        return None
    
    # 세그먼트 색상 매핑
    color_map = {
        "Mass": COLORS["Mass"],
        "Premium": COLORS["Premium"],
        "Luxury": COLORS["Luxury"],
        "Unknown": COLORS["Unknown"]
    }
    
    # 호버 데이터 소수점 2자리 포맷팅
    df_plot = df.copy()
    df_plot["unit_price_fmt"] = df_plot["unit_price"].apply(lambda x: f"₩{x:,.2f}" if pd.notna(x) else "N/A")
    df_plot["log_price_fmt"] = df_plot["log_unit_price"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
    
    fig = px.scatter(
        df_plot,
        x="log_unit_price",
        y="page_rank",
        color="segment",
        color_discrete_map=color_map,
        hover_data={"brand": True, "product_name": True, "unit_price_fmt": True, "total_sheets": True, "log_unit_price": False, "segment": False},
        title="",
        labels={
            "log_unit_price": "Log 가격 (분포 정규화용)",
            "page_rank": "검색 랭크 (낮을수록 상위)",
            "segment": "세그먼트",
            "unit_price_fmt": "1매당 가격"
        }
    )
    
    # 캄프 상품 강조 표시 (별 마커 + 큰 크기)
    if calmf_df is not None and not calmf_df.empty:
        # 캄프 상품 좌표 찾기
        for _, row in calmf_df.iterrows():
            if pd.notna(row.get("log_unit_price")) and pd.notna(row.get("page_rank")):
                fig.add_trace(
                    go.Scatter(
                        x=[row["log_unit_price"]],
                        y=[row["page_rank"]],
                        mode="markers+text",
                        marker=dict(
                            size=25,
                            color="#f1c40f",  # 노란색
                            symbol="star",
                            line=dict(width=2, color="#fff")
                        ),
                        text="⭐ 캄프",
                        textposition="top center",
                        textfont=dict(size=12, color="#f1c40f"),
                        name="Calmf",
                        showlegend=True,
                        hovertemplate=f"<b>캄프</b><br>{row.get('product_name', '')}<br>가격: ₩{row.get('unit_price', 0):,.0f}/매<extra></extra>"
                    )
                )
    
    # Y축 역순 (낮은 랭크가 위)
    fig.update_yaxes(autorange="reversed")
    
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#ffffff")
        ),
        height=500,
        xaxis=dict(tickfont=dict(color="#ffffff"), title_font=dict(color="#ffffff")),
        yaxis=dict(tickfont=dict(color="#ffffff"), title_font=dict(color="#ffffff"))
    )
    
    fig.update_traces(marker=dict(size=12, opacity=0.7, line=dict(width=1, color="#fff")), selector=dict(mode='markers'))
    
    return fig


def create_sov_bar_chart(df, top_n=15):
    """브랜드별 SOV 바 차트"""
    if df.empty:
        return None
    
    # 상위 N개 브랜드
    top_df = df.nlargest(top_n, "weighted_sov_1_over_rank")
    
    fig = px.bar(
        top_df,
        x="brand",
        y="weighted_sov_1_over_rank",
        title="",
        labels={"brand": "브랜드", "weighted_sov_1_over_rank": "가중 SOV (1/rank)"},
        color="weighted_sov_1_over_rank",
        color_continuous_scale="Blues"
    )
    
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ecf0f1"),
        showlegend=False,
        height=400,
        xaxis_tickangle=-45
    )
    
    return fig


def create_gap_heatmap(df):
    """Market Gap 히트맵"""
    if df.empty:
        return None
    
    # Gap Score로 색상
    fig = px.bar(
        df.sort_values("gap_score", ascending=False),
        x="price_band",
        y="gap_score",
        color="gap_score",
        title="",
        labels={"price_band": "가격대", "gap_score": "Gap Score"},
        color_continuous_scale="RdYlGn"
    )
    
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ecf0f1"),
        height=350
    )
    
    return fig


def create_keywords_chart(df, top_n=15):
    """키워드 빈도 차트"""
    if df.empty:
        return None
    
    top_df = df.nlargest(top_n, "count")
    
    fig = px.bar(
        top_df,
        y="token",
        x="count",
        orientation="h",
        title="",
        labels={"token": "키워드", "count": "빈도"},
        color="count",
        color_continuous_scale="Purples"
    )
    
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ecf0f1"),
        showlegend=False,
        height=400,
        yaxis=dict(autorange="reversed")
    )
    
    return fig


def create_segment_pie(df):
    """세그먼트 파이 차트"""
    if df.empty or "segment" not in df.columns:
        return None
    
    segment_counts = df["segment"].value_counts().reset_index()
    segment_counts.columns = ["segment", "count"]
    
    color_map = {
        "Mass": COLORS["Mass"],
        "Premium": COLORS["Premium"],
        "Luxury": COLORS["Luxury"],
        "Unknown": COLORS["Unknown"]
    }
    
    fig = px.pie(
        segment_counts,
        values="count",
        names="segment",
        color="segment",
        color_discrete_map=color_map,
        hole=0.4
    )
    
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff"),
        height=300,
        showlegend=True,
        legend=dict(font=dict(color="#ffffff"))
    )
    
    return fig


def create_rank_distribution(df):
    """랭크 구간별 가격 분포"""
    if df.empty:
        return None
    
    # 랭크 버킷 순서
    bucket_order = ["Top10", "Top20", "Top50", "Top100", "100+"]
    df_plot = df[df["rank_bucket"].isin(bucket_order)].copy()
    
    # 소수점 2자리로 반올림
    df_plot["unit_price"] = df_plot["unit_price"].round(2)
    
    fig = px.box(
        df_plot,
        x="rank_bucket",
        y="unit_price",
        color="rank_bucket",
        category_orders={"rank_bucket": bucket_order},
        title="",
        labels={"unit_price": "1매당 가격 (₩)", "rank_bucket": "랭크 구간"}
    )
    
    # 호버 템플릿 수정
    fig.update_traces(hovertemplate="<b>%{x}</b><br>가격: ₩%{y:,.2f}<extra></extra>")
    
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff"),
        showlegend=False,
        height=350,
        xaxis=dict(tickfont=dict(color="#ffffff"), title_font=dict(color="#ffffff")),
        yaxis=dict(tickfont=dict(color="#ffffff"), title_font=dict(color="#ffffff"), tickformat=",.0f")
    )
    
    return fig

# =============================================================================
# 메인 앱
# =============================================================================

def main():
    apply_custom_css()
    
    # 데이터 로드
    data = load_data()
    
    # 사이드바
    with st.sidebar:
        st.image("https://via.placeholder.com/200x60/2c3e50/ffffff?text=Calmf+Monitor", width=200)
        st.markdown("---")
        st.markdown("### 📅 데이터 정보")
        
        if not data["clean_long"].empty:
            weeks = data["clean_long"]["week_start_date"].unique()
            selected_week = st.selectbox("주차 선택", weeks)
            
            categories = data["clean_long"]["category_for_group"].dropna().unique()
            selected_category = st.selectbox("카테고리", ["전체"] + list(categories))
        else:
            selected_week = None
            selected_category = "전체"
        
        st.markdown("---")
        st.markdown("### ℹ️ 정보")
        st.markdown("""
        **데이터 파이프라인**
        - 입력: `./input/*.csv`
        - 출력: `./output/*.csv`
        
        **갱신**
        ```bash
        python build_datasets.py
        streamlit run dashboard.py
        ```
        """)
    
    # 메인 타이틀
    st.markdown("""
    <h1 style='text-align: center; color: #ecf0f1; margin-bottom: 0;'>
        📊 네이버 쇼핑 모니터링
    </h1>
    <p style='text-align: center; color: #b2bec3; font-size: 1.1rem;'>
        Calmf - 1매당 가격 포지셔닝 & 시장 분석
    </p>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 데이터 필터링
    df_main = data["clean_long"].copy()
    if selected_week:
        df_main = df_main[df_main["week_start_date"] == selected_week]
    if selected_category != "전체":
        df_main = df_main[df_main["category_for_group"] == selected_category]
    
    # ==========================================================================
    # KPI 섹션
    # ==========================================================================
    
    render_section_header(
        "핵심 지표 (KPI)",
        "이번 주/카테고리 기준 주요 성과 지표입니다.",
        "📈"
    )
    
    # 7개 KPI 컬럼 (캄프 1매당 가격 추가)
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    
    with col1:
        total_products = len(df_main)
        render_kpi(total_products, "상품 수", "분석 대상 상품")
    
    with col2:
        brands = df_main["brand"].nunique()
        render_kpi(brands, "브랜드", "중복 제거")
    
    with col3:
        median_price = df_main["unit_price"].median()
        render_kpi(median_price, "시장 중앙값", "1매당 가격", format_type="currency")
    
    with col4:
        # 캄프 1매당 가격 (신규 추가)
        calmf_vs = data["calmf_vs_market"]
        if not calmf_vs.empty:
            calmf_price = calmf_vs["calmf_median_unit_price"].iloc[0]
            render_kpi(calmf_price, "캄프 단가", "1매당 가격", format_type="currency")
        else:
            render_kpi(None, "캄프 단가", "1매당 가격")
    
    with col5:
        # 캄프 프리미엄 지수 (툴팁 추가)
        if not calmf_vs.empty:
            premium_idx = calmf_vs["premium_index"].iloc[0]
            render_kpi(
                premium_idx, 
                "프리미엄 지수", 
                "캄프/시장", 
                format_type="decimal",
                tooltip="📐 수식: 캄프 중앙값 ÷ 시장 중앙값\n\n해석:\n• = 1.0 → 시장 평균 가격\n• > 1.0 → 프리미엄 (비쌈)\n• < 1.0 → 가성비 (저렴)"
            )
        else:
            render_kpi(None, "프리미엄 지수", "캄프/시장")
    
    with col6:
        # Spearman 상관 (툴팁 추가)
        corr = data["corr_rank_price"]
        if not corr.empty:
            spearman = corr["spearman_rho"].iloc[0]
            spearman_p = corr["spearman_p"].iloc[0] if "spearman_p" in corr.columns else None
            
            # p-value 해석 포함
            if pd.notna(spearman_p):
                if spearman_p < 0.05:
                    p_text = f"\n\n✅ p-value={spearman_p:.4f}\n→ 상관관계 유의함 (p<0.05)"
                else:
                    p_text = f"\n\n⚠️ p-value={spearman_p:.4f}\n→ 상관관계 없음 (p≥0.05)"
            else:
                p_text = ""
            
            render_kpi(
                spearman, 
                "Spearman r", 
                "가격↔랭크", 
                format_type="decimal",
                tooltip=f"📐 Spearman 순위상관계수\n\n상관계수(r) 해석:\n• r > 0 → 양의 상관\n• r = 0 → 상관 없음\n• r < 0 → 음의 상관{p_text}"
            )
        else:
            render_kpi(None, "Spearman r", "가격↔랭크")
    
    with col7:
        # Parse fail rate
        dq = data["data_quality"]
        if not dq.empty:
            parse_fail = 1 - dq["has_sheets_rate"].iloc[0]
            render_kpi(parse_fail, "Parse Fail", "매수 추출 실패", format_type="percent")
        else:
            render_kpi(None, "Parse Fail", "매수 추출 실패")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ==========================================================================
    # 포지셔닝 섹션
    # ==========================================================================
    
    render_section_header(
        "Positioning Map",
        "랭크(선호도)와 1매당 가격으로 시장 포지션을 시각화합니다. 좌하단 = 저렴 + 상위 랭크 (가성비)",
        "📍"
    )
    
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        scatter_df = data["positioning_scatter"]
        if selected_week:
            scatter_df = scatter_df[scatter_df["week_start_date"] == selected_week]
        if selected_category != "전체":
            scatter_df = scatter_df[scatter_df["category_for_group"] == selected_category]
        
        # 캄프 상품 필터링 (scatter_df에서 직접 찾기)
        calmf_df = scatter_df[
            scatter_df["brand"].str.lower().str.contains("calmf|캄프", na=False) |
            scatter_df["product_name"].str.lower().str.contains("calmf|캄프", na=False)
        ]
        
        fig_scatter = create_scatter_plot(scatter_df, calmf_df)
        if fig_scatter:
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("데이터가 없습니다.")
    
    with col_right:
        st.markdown("<h4 style='color: #ffffff;'>세그먼트 분포</h4>", unsafe_allow_html=True)
        st.markdown("<p style='color: #b2bec3; font-size: 0.85rem;'>가격 구간별 상품 비율 (Mass/Premium/Luxury)</p>", unsafe_allow_html=True)
        fig_pie = create_segment_pie(df_main)
        if fig_pie:
            st.plotly_chart(fig_pie, use_container_width=True)
        
        st.markdown("<h4 style='color: #ffffff;'>랭크별 가격 분포</h4>", unsafe_allow_html=True)
        st.markdown("<p style='color: #b2bec3; font-size: 0.85rem;'>상자: 1~3분위수 | 선: 중앙값 | 점: 이상치</p>", unsafe_allow_html=True)
        fig_box = create_rank_distribution(df_main)
        if fig_box:
            st.plotly_chart(fig_box, use_container_width=True)
    
    # ==========================================================================
    # 시장 구조 섹션
    # ==========================================================================
    
    render_section_header(
        "Market Structure",
        "브랜드 노출 점유율(SOV)과 가격대별 진입 기회(Gap)를 분석합니다.",
        "🏢"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <h5 style='color: #ffffff;'>브랜드 SOV (Top 15) 
            <span class="kpi-help" data-tooltip="📐 수식: 가중 SOV = Σ(1/랭크)&#10;&#10;상위 랭크일수록 가중치가 높아 실제 노출 영향력을 반영합니다.">?</span>
        </h5>
        """, unsafe_allow_html=True)
        st.markdown("""
        <p class="metric-desc">
            <strong>SOV(Share of Voice)</strong>는 검색 결과에서 브랜드가 얼마나 자주, 상위에 노출되는지를 나타내는 지표입니다.
            랭크가 높은(숫자가 낮은) 상품일수록 더 큰 가중치를 부여하여 실제 소비자 눈에 띄는 영향력을 반영합니다.
        </p>
        """, unsafe_allow_html=True)
        
        sov_df = data["category_sov"]
        if selected_week and not sov_df.empty and "week_start_date" in sov_df.columns:
            sov_df = sov_df[sov_df["week_start_date"] == selected_week]
        
        fig_sov = create_sov_bar_chart(sov_df, top_n=15)
        if fig_sov:
            st.plotly_chart(fig_sov, use_container_width=True)
    
    with col2:
        st.markdown("""
        <h5 style='color: #ffffff;'>Market Gap (가격대별 기회) 
            <span class="kpi-help" data-tooltip="📐 수식: Gap Score = (1 - 상품 비율) × 평균 랭크점수&#10;&#10;점수가 높을수록 경쟁이 약하고 진입 기회가 큽니다.">?</span>
        </h5>
        """, unsafe_allow_html=True)
        st.markdown("""
        <p class="metric-desc">
            <strong>Market Gap</strong>은 특정 가격대에서 경쟁이 얼마나 치열한지를 분석합니다.
            상품이 적고 상위 랭크에 빈자리가 많은 가격대일수록 Gap Score가 높아 신규 진입에 유리합니다.
        </p>
        """, unsafe_allow_html=True)
        
        gap_df = data["market_gap"]
        if selected_week and not gap_df.empty and "week_start_date" in gap_df.columns:
            gap_df = gap_df[gap_df["week_start_date"] == selected_week]
        
        fig_gap = create_gap_heatmap(gap_df)
        if fig_gap:
            st.plotly_chart(fig_gap, use_container_width=True)
        
        # 가격대별 범위 표시
        if not gap_df.empty and "min_price" in gap_df.columns:
            price_ranges = []
            for _, row in gap_df.sort_values("price_band").iterrows():
                band = row["price_band"]
                min_p = row.get("min_price", 0)
                max_p = row.get("max_price", 0)
                if pd.notna(min_p) and pd.notna(max_p):
                    price_ranges.append(f"<b>{band}</b>: ₩{min_p:,.0f}~{max_p:,.0f}")
            if price_ranges:
                st.markdown(f"""
                <p style='color: #b2bec3; font-size: 0.75rem; margin-top: -10px;'>
                    {' | '.join(price_ranges)}
                </p>
                """, unsafe_allow_html=True)
        
        # Gap 해석
        if not gap_df.empty:
            top_gap = gap_df.nlargest(1, "gap_score")
            if not top_gap.empty:
                best_band = top_gap.iloc[0]["price_band"]
                min_p = top_gap.iloc[0].get("min_price", 0)
                max_p = top_gap.iloc[0].get("max_price", 0)
                price_info = f" (₩{min_p:,.0f}~{max_p:,.0f})" if pd.notna(min_p) and pd.notna(max_p) else ""
                st.markdown(f"""
                <div class="insight-box">
                    <strong>💡 인사이트:</strong> <code>{best_band}{price_info}</code> 가격대에서 
                    경쟁이 가장 약합니다. 진입 기회를 검토해보세요.
                </div>
                """, unsafe_allow_html=True)
    
    # ==========================================================================
    # 캄프 포커스 섹션
    # ==========================================================================
    
    render_section_header(
        "Calmf Focus",
        "캄프의 시장 대비 가격 위치와 상위 노출 가능성을 확인합니다.",
        "🎯"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h5 style='color: #ffffff;'>Calmf vs Market</h5>", unsafe_allow_html=True)
        calmf_vs = data["calmf_vs_market"]
        if not calmf_vs.empty:
            render_dark_table(
                calmf_vs,
                columns=["category", "calmf_count", "calmf_median_unit_price", "market_median_unit_price", "premium_index"],
                rename_cols={
                    "category": "카테고리",
                    "calmf_count": "캄프 상품수",
                    "calmf_median_unit_price": "캄프 중앙값",
                    "market_median_unit_price": "시장 중앙값",
                    "premium_index": "프리미엄 지수"
                },
                number_cols=["calmf_median_unit_price", "market_median_unit_price", "premium_index"]
            )
            
            # 프리미엄 지수 해석
            if not calmf_vs.empty:
                pi = calmf_vs["premium_index"].iloc[0]
                if pd.notna(pi):
                    if pi > 1.1:
                        st.markdown("""
                        <div class="insight-box warning">
                            <strong>⚠️ 프리미엄 포지션:</strong> 시장 대비 {:.1%} 높은 가격입니다.
                            가치 소구가 필요합니다.
                        </div>
                        """.format(pi - 1), unsafe_allow_html=True)
                    elif pi < 0.9:
                        st.markdown("""
                        <div class="insight-box">
                            <strong>✅ 가성비 포지션:</strong> 시장 대비 {:.1%} 낮은 가격입니다.
                            경쟁력을 강조하세요.
                        </div>
                        """.format(1 - pi), unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="insight-box">
                            <strong>📊 시장 평균:</strong> 시장 중앙값과 유사한 가격대입니다.
                        </div>
                        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("<h5 style='color: #ffffff;'>Calmf 상품 목록</h5>", unsafe_allow_html=True)
        calmf_products = data["calmf_products"]
        if not calmf_products.empty:
            render_dark_table(
                calmf_products,
                columns=["product_name", "unit_price", "segment", "page_rank", "z_log"],
                rename_cols={
                    "product_name": "상품명",
                    "unit_price": "1매당 가격",
                    "segment": "세그먼트",
                    "page_rank": "랭크",
                    "z_log": "Z-score"
                },
                number_cols=["unit_price", "z_log"]
            )
        else:
            st.info("캄프 상품이 없습니다.")
    
    # ==========================================================================
    # 데이터 품질 섹션
    # ==========================================================================
    
    render_section_header(
        "Data Quality",
        "파싱 실패율/이상치 비율이 높으면 결론 신뢰도를 낮춰 해석하세요.",
        "⚠️"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h5 style='color: #ffffff;'>품질 지표</h5>", unsafe_allow_html=True)
        dq = data["data_quality"]
        if not dq.empty:
            # 품질 지표 시각화
            metrics = {
                "매수 추출률": dq["has_sheets_rate"].iloc[0],
                "이상치 비율": dq["outlier_rate"].iloc[0],
                "비정상 패키지": dq["bad_pack_rate"].iloc[0],
                "랭크 누락": dq["missing_rank_rate"].iloc[0],
            }
            
            for name, value in metrics.items():
                if pd.notna(value):
                    color = "#27ae60" if (name == "매수 추출률" and value > 0.8) or (name != "매수 추출률" and value < 0.1) else "#e74c3c"
                    st.markdown(f"""
                    <div style='display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);'>
                        <span style='color: #b2bec3;'>{name}</span>
                        <span style='color: {color}; font-weight: bold;'>{value:.1%}</span>
                    </div>
                    """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("<h5 style='color: #ffffff;'>이상치 목록</h5>", unsafe_allow_html=True)
        outliers = data["outliers"]
        if not outliers.empty:
            render_dark_table(
                outliers.head(10),
                columns=["brand", "product_name", "unit_price", "z_log"],
                rename_cols={
                    "brand": "브랜드",
                    "product_name": "상품명",
                    "unit_price": "1매당 가격",
                    "z_log": "Z-score"
                },
                number_cols=["unit_price", "z_log"]
            )
        else:
            st.success("이상치가 없습니다! ✅")
    
    # 푸터
    st.markdown("---")
    st.markdown("""
    <p style='text-align: center; color: #636e72; font-size: 0.8rem;'>
        Built with ❤️ using Streamlit & Plotly | 
        Data: ./output/*.csv | 
        Last Updated: Auto-refresh on data change
    </p>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
