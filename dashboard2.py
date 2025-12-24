#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 쇼핑 모니터링 대시보드 (가격 비교 분석2)
============================

Streamlit 기반 인터랙티브 대시보드
./output/ 폴더의 CSV 파일들을 시각화합니다.

실행: streamlit run dashboard2.py
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

# 스크립트 파일 위치 기준 output 폴더 경로 (Streamlit Cloud 배포 호환)
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"

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
        path = OUTPUT_DIR / f"{name}.csv"
        if path.exists():
            try:
                data[name] = pd.read_csv(path)
            except Exception as e:
                st.warning(f"파일 로드 실패: {name}.csv - {e}")
                data[name] = pd.DataFrame()
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
    
    # 컬럼 필터링 - 존재하는 컬럼만 사용
    if columns:
        existing_cols = [c for c in columns if c in df.columns]
        if existing_cols:
            df = df[existing_cols].copy()
    else:
        df = df.copy()
        
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
    
    # total_sheets 컬럼이 없을 수 있으므로 처리
    hover_data = {"brand": True, "product_name": True, "unit_price_fmt": True, "log_unit_price": False, "segment": False}
    if "total_sheets" in df_plot.columns:
        hover_data["total_sheets"] = True
    
    fig = px.scatter(
        df_plot,
        x="log_unit_price",
        y="page_rank",
        color="segment",
        color_discrete_map=color_map,
        hover_data=hover_data,
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
    
    # 가중 SOV 컬럼 선택 (데이터에 맞게 수정)
    sov_col = None
    for col in ["weighted_sov_1_over_rank", "weighted_sov_inv_rank", "weighted_sov_inv_sqrt"]:
        if col in df.columns:
            sov_col = col
            break
    
    if sov_col is None:
        return None
    
    # 상위 N개 브랜드
    top_df = df.nlargest(top_n, sov_col)
    
    fig = px.bar(
        top_df,
        x="brand",
        y=sov_col,
        title="",
        labels={"brand": "브랜드", sov_col: "가중 SOV (1/rank)"},
        color=sov_col,
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


def create_gap_heatmap(df, price_ranges=None):
    """Market Gap 히트맵 (가격 범위 표시)"""
    if df.empty:
        return None
    
    df_plot = df.copy()
    
    # 가격 범위가 있으면 라벨 변환
    if price_ranges:
        df_plot["price_label"] = df_plot["price_band"].map(
            lambda x: price_ranges.get(x, x)
        )
    else:
        df_plot["price_label"] = df_plot["price_band"]
    
    # Gap Score로 색상
    fig = px.bar(
        df_plot.sort_values("gap_score", ascending=False),
        x="price_label",
        y="gap_score",
        color="gap_score",
        title="",
        labels={"price_label": "가격대", "gap_score": "Gap Score"},
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
        height=380,
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
        height=420,
        xaxis=dict(tickfont=dict(color="#ffffff"), title_font=dict(color="#ffffff")),
        yaxis=dict(tickfont=dict(color="#ffffff"), title_font=dict(color="#ffffff"), tickformat=",.0f")
    )
    
    return fig

# =============================================================================
# 경쟁 분석 함수
# =============================================================================

def render_competition_table(df, title, highlight_top=3):
    """경쟁 밴드 테이블 렌더링 (상위 N개 하이라이트, 캄프 강조)"""
    if df.empty:
        st.info("해당 조건의 상품이 없습니다.")
        return
    
    df_sorted = df.sort_values("page_rank").head(20).copy()
    
    # HTML 테이블 생성
    html = f'<p style="color: #b2bec3; font-size: 0.85rem; margin-bottom: 5px;">밴드 내 상품 수: <strong style="color: #3498db;">{len(df)}</strong>개</p>'
    html += '<table class="dark-table">'
    html += '<thead><tr>'
    cols = ["", "랭크", "구간", "브랜드", "상품명", "제조사", "단가(₩)", "가격(₩)", "링크"]
    for col in cols:
        html += f'<th>{col}</th>'
    html += '</tr></thead><tbody>'
    
    for idx, (_, row) in enumerate(df_sorted.iterrows()):
        brand = str(row.get("brand", "")).lower()
        product_name = str(row.get("product_name", "")).lower()
        is_calmf = "캄프" in brand or "calmf" in brand or "캄프" in product_name or "calmf" in product_name
        
        # 캄프는 노란색, 상위 N개는 파란색
        if is_calmf:
            row_style = "background: rgba(241, 196, 15, 0.4);"
            star = "⭐"
        elif idx < highlight_top:
            row_style = "background: rgba(52, 152, 219, 0.3);"
            star = ""
        else:
            row_style = ""
            star = ""
        
        html += f'<tr style="{row_style}">'
        html += f'<td style="text-align: center;">{star}</td>'
        html += f'<td>{int(row["page_rank"]) if pd.notna(row.get("page_rank")) else "N/A"}</td>'
        html += f'<td>{row.get("rank_bucket", "N/A")}</td>'
        html += f'<td>{"<strong>" if is_calmf else ""}{row.get("brand", "N/A")}{"</strong>" if is_calmf else ""}</td>'
        html += f'<td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{row.get("product_name", "N/A")[:40]}</td>'
        html += f'<td>{row.get("maker", "N/A")}</td>'
        html += f'<td style="text-align: right;">{row["unit_price"]:,.1f}</td>'
        html += f'<td style="text-align: right;">{int(row["price"]):,}</td>'
        link = row.get("link", "")
        html += f'<td><a href="{link}" target="_blank" style="color: #3498db;">🔗</a></td>'
        html += '</tr>'
    
    html += '</tbody></table>'
    st.markdown(html, unsafe_allow_html=True)


def create_price_quintile_chart(df, calmf_unit_price, market_median):
    """가격대별 프리미엄 분석 (Q1-Q5 또는 Q1-Q3) - 가격 범위 포함"""
    if df.empty or "unit_price" not in df.columns:
        return None, None
    
    prices = df["unit_price"].dropna()
    if len(prices) < 5:
        return None, None
    
    # 5분위 시도, 실패시 3분위
    try:
        df_analysis = df.dropna(subset=["unit_price", "page_rank"]).copy()
        df_analysis["bucket"] = pd.qcut(df_analysis["unit_price"], q=5, labels=["Q1(저가)", "Q2", "Q3", "Q4", "Q5(고가)"], duplicates='drop')
    except ValueError:
        try:
            df_analysis = df.dropna(subset=["unit_price", "page_rank"]).copy()
            df_analysis["bucket"] = pd.qcut(df_analysis["unit_price"], q=3, labels=["Q1(저가)", "Q2(중간)", "Q3(고가)"], duplicates='drop')
        except ValueError:
            return None, None
    
    # 버킷별 집계 (가격 범위 포함)
    summary = df_analysis.groupby("bucket", observed=True).agg(
        n=("unit_price", "count"),
        min_price=("unit_price", "min"),
        max_price=("unit_price", "max"),
        median_unit_price=("unit_price", "median"),
        median_rank=("page_rank", "median")
    ).reset_index()
    
    # 가격 범위 포맷팅
    summary["price_range"] = summary.apply(
        lambda row: f"₩{row['min_price']:.0f}~₩{row['max_price']:.0f}", axis=1
    )
    
    summary["premium_index"] = summary["median_unit_price"] / market_median
    
    # 캄프가 속한 버킷 찾기
    calmf_bucket = None
    for _, row in summary.iterrows():
        if row["min_price"] <= calmf_unit_price <= row["max_price"]:
            calmf_bucket = row["bucket"]
            break
    
    # 차트 생성
    colors = ["#3498db" if b != calmf_bucket else "#f1c40f" for b in summary["bucket"]]
    
    fig = px.bar(
        summary,
        x="bucket",
        y="premium_index",
        title="",
        labels={"bucket": "가격 분위", "premium_index": "Premium Index"},
        text=summary["premium_index"].apply(lambda x: f"{x:.2f}")
    )
    
    fig.update_traces(marker_color=colors, textposition="outside")
    
    # 기준선 1.0 추가
    fig.add_hline(y=1.0, line_dash="dash", line_color="#e74c3c", 
                  annotation_text="시장 평균=1.0", annotation_position="right")
    
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff"),
        height=350,
        showlegend=False,
        xaxis=dict(tickfont=dict(color="#ffffff")),
        yaxis=dict(tickfont=dict(color="#ffffff"), title_font=dict(color="#ffffff"))
    )
    
    return fig, summary


def render_elasticity_card(label, b_value, r2, n, direction, p_value=None, has_data=True):
    """탄력도 KPI 카드 렌더링"""
    if not has_data or n < 5:
        st.markdown(f"""
        <div class="kpi-card" style="border-color: rgba(149, 165, 166, 0.3);">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value" style="font-size: 1.5rem; background: linear-gradient(90deg, #95a5a6, #7f8c8d); -webkit-background-clip: text;">표본 부족</div>
            <div class="kpi-desc">n={n} (최소 5 필요)</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        dir_icon = "📈" if direction == "up" else "📉"
        # b > 0: 가격↑ → rank숫자↑ (악화) / b < 0: 가격↑ → rank숫자↓ (개선)
        dir_text = "가격↑ → 랭크숫자↑(노출 악화)" if direction == "up" else "가격↑ → 랭크숫자↓(노출 개선)"
        color_grad = "linear-gradient(90deg, #e74c3c, #c0392b)" if direction == "up" else "linear-gradient(90deg, #27ae60, #2ecc71)"
        
        # p-value 유의성 표시
        if p_value is not None:
            if p_value < 0.05:
                p_badge = f'<span style="color: #27ae60;">p={p_value:.3f} ✓</span>'
            else:
                p_badge = f'<span style="color: #e74c3c;">p={p_value:.3f} ✗</span>'
        else:
            p_badge = ""
        
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value" style="font-size: 2rem; background: {color_grad}; -webkit-background-clip: text;">{dir_icon} {b_value:.3f}</div>
            <div class="kpi-desc">R²={r2:.3f} | n={n} | {p_badge}<br><span style="font-size: 0.7rem;">{dir_text}</span></div>
        </div>
        """, unsafe_allow_html=True)


def calculate_elasticity(df, cutoff):
    """지정된 rank cutoff에서 탄력도 계산 (p-value 포함)"""
    df_cut = df[(df["page_rank"] <= cutoff) & df["unit_price"].notna() & df["page_rank"].notna()].copy()
    n = len(df_cut)
    
    if n < 5:
        return {"n": n, "b": None, "r2": None, "p_value": None, "direction": None, "has_data": False}
    
    # log-log 회귀
    try:
        df_cut["log_price"] = np.log(df_cut["unit_price"])
        df_cut["log_rank"] = np.log(df_cut["page_rank"])
        
        # OLS 계산
        x = df_cut["log_price"].values
        y = df_cut["log_rank"].values
        
        x_mean = x.mean()
        y_mean = y.mean()
        
        b = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2)
        a = y_mean - b * x_mean
        
        y_pred = a + b * x
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y_mean) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # p-value 계산 (t-test for slope)
        # SE(b) = sqrt(MSE / sum((x - x_mean)^2))
        mse = ss_res / (n - 2)  # degrees of freedom = n - 2
        se_b = np.sqrt(mse / np.sum((x - x_mean) ** 2))
        t_stat = b / se_b if se_b > 0 else 0
        
        # t-분포에서 p-value 계산 (양측)
        # scipy 없이 근사 계산 또는 lookup table 사용
        # 간단히 t-분포 CDF 근사
        df_t = n - 2
        t_abs = abs(t_stat)
        # 근사 p-value (정규분포 근사, df > 30이면 좋음)
        if df_t > 30:
            from math import erf, sqrt
            p_value = 2 * (1 - 0.5 * (1 + erf(t_abs / sqrt(2))))
        else:
            # 작은 표본에서는 scipy 사용 시도, 없으면 None
            try:
                from scipy import stats
                p_value = 2 * (1 - stats.t.cdf(t_abs, df_t))
            except ImportError:
                p_value = None
        
        direction = "up" if b > 0 else "down"
        
        return {"n": n, "b": b, "r2": r2, "p_value": p_value, "direction": direction, "has_data": True}
    except Exception:
        return {"n": n, "b": None, "r2": None, "p_value": None, "direction": None, "has_data": False}


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
            
            # category_for_group 또는 category_group 사용
            cat_col = "category_for_group" if "category_for_group" in data["clean_long"].columns else "category_group"
            if cat_col in data["clean_long"].columns:
                categories = data["clean_long"][cat_col].dropna().unique()
                selected_category = st.selectbox("카테고리", ["전체"] + list(categories))
            else:
                selected_category = "전체"
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
        python build_outputs.py
        streamlit run dashboard2.py
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
    cat_col = "category_for_group" if "category_for_group" in df_main.columns else "category_group"
    
    if selected_week:
        df_main = df_main[df_main["week_start_date"] == selected_week]
    if selected_category != "전체" and cat_col in df_main.columns:
        df_main = df_main[df_main[cat_col] == selected_category]
    
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
        if "brand" in df_main.columns:
            brands = df_main["brand"].nunique()
        else:
            brands = 0
        render_kpi(brands, "브랜드", "중복 제거")
    
    with col3:
        if "unit_price" in df_main.columns:
            median_price = df_main["unit_price"].median()
        else:
            median_price = None
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
        # Spearman 상관 (툴팁 추가) - 컬럼명 수정
        corr = data["corr_rank_price"]
        if not corr.empty:
            # spearman_corr 또는 spearman_rho 사용
            spearman_col = "spearman_corr" if "spearman_corr" in corr.columns else "spearman_rho"
            spearman_p_col = "spearman_p" if "spearman_p" in corr.columns else "spearman_p"
            
            spearman = corr[spearman_col].iloc[0] if spearman_col in corr.columns else None
            spearman_p = corr[spearman_p_col].iloc[0] if spearman_p_col in corr.columns else None
            
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
        
        # 카테고리 컬럼 찾기
        cat_col_scatter = None
        for c in ["category_for_group", "category_group"]:
            if c in scatter_df.columns:
                cat_col_scatter = c
                break
        
        if selected_week and not scatter_df.empty and "week_start_date" in scatter_df.columns:
            scatter_df = scatter_df[scatter_df["week_start_date"] == selected_week]
        if selected_category != "전체" and cat_col_scatter and not scatter_df.empty:
            scatter_df = scatter_df[scatter_df[cat_col_scatter] == selected_category]
        
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
        
        # price_band별 실제 가격 범위 계산
        price_ranges = {}
        if not df_main.empty and "price_band" in df_main.columns and "unit_price" in df_main.columns:
            for band in df_main["price_band"].dropna().unique():
                band_prices = df_main[df_main["price_band"] == band]["unit_price"].dropna()
                if len(band_prices) > 0:
                    min_p = int(band_prices.min())
                    max_p = int(band_prices.max())
                    price_ranges[band] = f"₩{min_p:,}~{max_p:,}"
        
        fig_gap = create_gap_heatmap(gap_df, price_ranges)
        if fig_gap:
            st.plotly_chart(fig_gap, use_container_width=True)
        
        # Gap 해석
        if not gap_df.empty:
            top_gap = gap_df.nlargest(1, "gap_score")
            if not top_gap.empty:
                best_band = top_gap.iloc[0]["price_band"]
                # 실제 가격 범위로 표시
                price_label = price_ranges.get(best_band, best_band)
                st.markdown(f"""
                <div class="insight-box">
                    <strong>💡 인사이트:</strong> <code>{price_label}</code> 가격대에서 
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
            # 데이터에 맞게 컬럼 조정
            available_cols = []
            rename_dict = {}
            number_cols = []
            
            # category 또는 category_group
            cat_col = "category" if "category" in calmf_vs.columns else "category_group"
            if cat_col in calmf_vs.columns:
                available_cols.append(cat_col)
                rename_dict[cat_col] = "카테고리"
            
            # calmf_count 또는 calmf_item_count
            count_col = "calmf_count" if "calmf_count" in calmf_vs.columns else "calmf_item_count"
            if count_col in calmf_vs.columns:
                available_cols.append(count_col)
                rename_dict[count_col] = "캄프 상품수"
            
            if "calmf_median_unit_price" in calmf_vs.columns:
                available_cols.append("calmf_median_unit_price")
                rename_dict["calmf_median_unit_price"] = "캄프 중앙값"
                number_cols.append("calmf_median_unit_price")
            
            if "market_median_unit_price" in calmf_vs.columns:
                available_cols.append("market_median_unit_price")
                rename_dict["market_median_unit_price"] = "시장 중앙값"
                number_cols.append("market_median_unit_price")
            
            if "premium_index" in calmf_vs.columns:
                available_cols.append("premium_index")
                rename_dict["premium_index"] = "프리미엄 지수"
                number_cols.append("premium_index")
            
            render_dark_table(
                calmf_vs,
                columns=available_cols,
                rename_cols=rename_dict,
                number_cols=number_cols
            )
            
            # 프리미엄 지수 해석
            if not calmf_vs.empty and "premium_index" in calmf_vs.columns:
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
    # Competition Analysis 섹션 (경쟁 밴드 분석)
    # ==========================================================================
    
    render_section_header(
        "Competition Analysis",
        "캄프 1매당 가격 기준 경쟁자 분석 (±10%, ±20% 가격 밴드)",
        "🎯"
    )
    
    # 캄프 상품 정보 가져오기
    calmf_products = data["calmf_products"]
    if not calmf_products.empty:
        calmf_row = calmf_products.iloc[0]
        calmf_unit_price = calmf_row["unit_price"]
        calmf_rank = calmf_row["page_rank"]
        
        # unit_price 기반이므로 전체 데이터 사용 (동일 매수 필터링 불필요)
        analysis_df = df_main[df_main["unit_price"].notna()].copy()
        
        if not analysis_df.empty:
            # 시장 중앙값
            market_median = analysis_df["unit_price"].median()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <h5 style='color: #ffffff;'>Band ±10% (₩{:.0f} ~ ₩{:.0f})
                    <span class="kpi-help" data-tooltip="캄프 단가의 90%~110% 범위 내 경쟁자&#10;직접 경쟁 상품군">?</span>
                </h5>
                """.format(calmf_unit_price * 0.9, calmf_unit_price * 1.1), unsafe_allow_html=True)
                
                band10_df = analysis_df[
                    (analysis_df["unit_price"] >= calmf_unit_price * 0.9) &
                    (analysis_df["unit_price"] <= calmf_unit_price * 1.1)
                ]
                render_competition_table(band10_df, "Band 10%", highlight_top=3)
            
            with col2:
                st.markdown("""
                <h5 style='color: #ffffff;'>Band 10~20% (₩{:.0f}~₩{:.0f} 또는 ₩{:.0f}~₩{:.0f})
                    <span class="kpi-help" data-tooltip="캄프 단가 기준 10~20% 차이 범위&#10;±10% 밴드 제외한 확장 경쟁군">?</span>
                </h5>
                """.format(
                    calmf_unit_price * 0.8, calmf_unit_price * 0.9,
                    calmf_unit_price * 1.1, calmf_unit_price * 1.2
                ), unsafe_allow_html=True)
                
                # 10~20% 구간만 (±10% 제외)
                band20_df = analysis_df[
                    ((analysis_df["unit_price"] >= calmf_unit_price * 0.8) & 
                     (analysis_df["unit_price"] < calmf_unit_price * 0.9)) |
                    ((analysis_df["unit_price"] > calmf_unit_price * 1.1) & 
                     (analysis_df["unit_price"] <= calmf_unit_price * 1.2))
                ]
                render_competition_table(band20_df, "Band 10~20%", highlight_top=3)
            
            # 가격이 문제가 아닌 경쟁자
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <h5 style='color: #ffffff;'>🚨 가격이 문제가 아닌 경쟁자
                <span class="kpi-help" data-tooltip="캄프보다 비싸거나 같은데도 상위 노출되는 상품&#10;가격 외 경쟁력 분석 필요">?</span>
            </h5>
            <p class="metric-desc">캄프보다 <strong>높은 가격</strong>인데도 <strong>상위 노출</strong>되는 경쟁자 → 가격 외 요인 분석 필요</p>
            """, unsafe_allow_html=True)
            
            non_price_competitors = analysis_df[
                (analysis_df["page_rank"] < calmf_rank) &
                (analysis_df["unit_price"] >= calmf_unit_price)
            ]
            render_competition_table(non_price_competitors, "Non-price Competitors", highlight_top=3)
        else:
            st.info("분석 가능한 데이터가 없습니다.")
    else:
        st.info("캄프 상품 데이터가 없습니다.")
    
    # ==========================================================================
    # Price-tier Premium 섹션 (가격대별 프리미엄 분석)
    # ==========================================================================
    
    render_section_header(
        "Price-tier Premium Analysis",
        "시장 전체 가격 분위별 프리미엄 지수와 랭크 분포를 분석합니다.",
        "💎"
    )
    
    if not calmf_products.empty and "analysis_df" in dir() and not analysis_df.empty:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("<h5 style='color: #ffffff;'>가격 분위별 Premium Index</h5>", unsafe_allow_html=True)
            st.markdown("<p class='metric-desc'>노란색 = 캄프가 속한 분위 | 빨간 점선 = 시장 평균(1.0)</p>", unsafe_allow_html=True)
            
            fig_quintile, quintile_summary = create_price_quintile_chart(
                analysis_df, 
                calmf_unit_price, 
                market_median
            )
            if fig_quintile:
                st.plotly_chart(fig_quintile, use_container_width=True)
            else:
                st.info("분위 분석을 위한 데이터가 부족합니다.")
        
        with col2:
            st.markdown("<h5 style='color: #ffffff;'>분위별 상세 정보</h5>", unsafe_allow_html=True)
            if quintile_summary is not None and not quintile_summary.empty:
                render_dark_table(
                    quintile_summary,
                    columns=["bucket", "n", "price_range", "median_unit_price", "premium_index", "median_rank"],
                    rename_cols={
                        "bucket": "분위",
                        "n": "수",
                        "price_range": "가격 범위",
                        "median_unit_price": "중앙가격",
                        "premium_index": "Premium",
                        "median_rank": "중앙랭크"
                    },
                    number_cols=["median_unit_price", "premium_index", "median_rank"]
                )
            
            # Mass/Premium/Luxury 분위수 정의 설명
            st.markdown("""
            <div class="insight-box" style="margin-top: 10px; font-size: 0.85rem;">
                <strong>📊 세그먼트 분위수 정의:</strong><br>
                • <strong>Mass</strong>: P0~P50 (하위 50%)<br>
                • <strong>Premium</strong>: P50~P85 (상위 15~50%)<br>
                • <strong>Luxury</strong>: P85~P100 (상위 15%)
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("프리미엄 분석을 위한 데이터가 없습니다.")
    
    # ==========================================================================
    # Elasticity Analysis 섹션 (가격-랭크 탄력도 분석)
    # ==========================================================================
    
    render_section_header(
        "Price-Rank Elasticity (Mini)",
        "가격이 랭크에 미치는 영향도를 컷오프별로 분석합니다. (단면 데이터 한계로 방향성 참고용)",
        "📐"
    )
    
    st.markdown("""
    <p class="metric-desc">
        <strong>모델:</strong> log(page_rank) ~ a + b × log(unit_price) | 
        <strong>해석:</strong> b > 0이면 가격↑ → 랭크 숫자↑(노출 악화) | b < 0이면 반대
    </p>
    """, unsafe_allow_html=True)
    
    if "analysis_df" in dir() and not analysis_df.empty:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            result_20 = calculate_elasticity(analysis_df, 20)
            render_elasticity_card(
                "Top 20", 
                result_20.get("b", 0) or 0, 
                result_20.get("r2", 0) or 0, 
                result_20["n"], 
                result_20.get("direction", "up"),
                result_20.get("p_value"),
                result_20["has_data"]
            )
        
        with col2:
            result_50 = calculate_elasticity(analysis_df, 50)
            render_elasticity_card(
                "Top 50", 
                result_50.get("b", 0) or 0, 
                result_50.get("r2", 0) or 0, 
                result_50["n"], 
                result_50.get("direction", "up"),
                result_50.get("p_value"),
                result_50["has_data"]
            )
        
        with col3:
            result_100 = calculate_elasticity(analysis_df, 100)
            render_elasticity_card(
                "Top 100", 
                result_100.get("b", 0) or 0, 
                result_100.get("r2", 0) or 0, 
                result_100["n"], 
                result_100.get("direction", "up"),
                result_100.get("p_value"),
                result_100["has_data"]
            )
        
        # Spearman 상관계수 추가 표시
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h5 style='color: #ffffff;'>📊 Spearman 상관계수</h5>", unsafe_allow_html=True)
        
        try:
            from scipy import stats
            
            # 각 cutoff별 Spearman 계산
            spearman_results = []
            spearman_p_values = []
            for label, cutoff in [("Top 20", 20), ("Top 50", 50), ("Top 100", 100)]:
                df_cut = analysis_df[(analysis_df["page_rank"] <= cutoff) & 
                                     analysis_df["unit_price"].notna() & 
                                     analysis_df["page_rank"].notna()]
                n = len(df_cut)
                if n >= 3:
                    rho, p = stats.spearmanr(df_cut["unit_price"], df_cut["page_rank"])
                    spearman_results.append({
                        "구간": label,
                        "n": n,
                        "Spearman ρ": f"{rho:.3f}",
                        "p-value": f"{p:.4f}",
                        "유의성": "✓ 유의" if p < 0.05 else "✗ 무의미"
                    })
                    spearman_p_values.append(p)
                else:
                    spearman_results.append({
                        "구간": label,
                        "n": n,
                        "Spearman ρ": "N/A",
                        "p-value": "N/A",
                        "유의성": "표본 부족"
                    })
            
            # 테이블로 표시
            spearman_df = pd.DataFrame(spearman_results)
            render_dark_table(spearman_df)
            
            # 회귀분석 p-value 가져오기 (Top 100 기준)
            reg_p = result_100.get("p_value") if result_100["has_data"] else None
            corr_p = spearman_p_values[-1] if spearman_p_values else None
            
            # 유의성 판단
            corr_sig = corr_p is not None and corr_p < 0.05
            reg_sig = reg_p is not None and reg_p < 0.05
            
            if not corr_sig and not reg_sig:
                corr_p_str = f"{corr_p:.4f}" if corr_p else "N/A"
                reg_p_str = f"{reg_p:.4f}" if reg_p else "N/A"
                st.markdown(f"""
                <div class="insight-box warning" style="margin-top: 15px;">
                    <strong>� 분석 결과:</strong> 상관분석 및 가격 탄력 회귀분석 결과, 
                    가격과 랭크의 <strong>상관관계 및 인과관계가 통계적으로 유의하지 않음</strong> 
                    (상관계수 p={corr_p_str}; 회귀 p={reg_p_str})<br><br>
                    <strong>* 유의사항:</strong> 표본 수(N)의 절대적 부족으로 인한 결과일 수 있음
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="insight-box" style="margin-top: 15px;">
                    <strong>📈 분석 결과:</strong> 가격과 랭크 간 통계적으로 유의한 관계가 확인됨
                </div>
                """, unsafe_allow_html=True)
            
        except ImportError:
            st.info("scipy 라이브러리가 필요합니다: pip install scipy")
    else:
        st.info("탄력도 분석을 위한 데이터가 없습니다.")
    
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
            # 품질 지표 시각화 - 데이터에 맞게 수정
            metrics = {}
            
            if "has_sheets_rate" in dq.columns:
                metrics["매수 추출률"] = dq["has_sheets_rate"].iloc[0]
            if "outlier_rate" in dq.columns:
                metrics["이상치 비율"] = dq["outlier_rate"].iloc[0]
            if "invalid_sheets_rate" in dq.columns:
                metrics["비정상 패키지"] = dq["invalid_sheets_rate"].iloc[0]
            if "missing_sheets_rate" in dq.columns:
                metrics["매수 누락"] = dq["missing_sheets_rate"].iloc[0]
            
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
            # z_log 컬럼이 없을 수 있으므로 처리
            available_cols = ["brand", "product_name", "unit_price"]
            if "z_log" in outliers.columns:
                available_cols.append("z_log")
            elif "log_unit_price" in outliers.columns:
                available_cols.append("log_unit_price")
            
            rename_dict = {
                "brand": "브랜드",
                "product_name": "상품명",
                "unit_price": "1매당 가격",
                "z_log": "Z-score",
                "log_unit_price": "Log Price"
            }
            
            number_cols = ["unit_price"]
            if "z_log" in outliers.columns:
                number_cols.append("z_log")
            elif "log_unit_price" in outliers.columns:
                number_cols.append("log_unit_price")
            
            render_dark_table(
                outliers.head(10),
                columns=available_cols,
                rename_cols=rename_dict,
                number_cols=number_cols
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
