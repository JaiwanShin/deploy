#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
가격 비교 분석 대시보드 v3
====================================
재구성된 섹션 순서 + Mass/Premium/Luxury 기반 분석
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# =============================================================================
# 설정
# =============================================================================

st.set_page_config(
    page_title="가격 비교 분석 Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"

COLORS = {
    "Mass": "#3498db",
    "Premium": "#9b59b6", 
    "Luxury": "#2ecc71",  # 연한 초록색으로 변경
    "Unknown": "#95a5a6",
    "Calmf": "#f1c40f",
    "positive": "#27ae60",
    "negative": "#e74c3c",
    "warning": "#f39c12",
    "neutral": "#3498db"
}

# =============================================================================
# 데이터 로드
# =============================================================================

@st.cache_data
def load_csv_safe(filepath):
    try:
        return pd.read_csv(filepath)
    except Exception:
        return pd.DataFrame()

@st.cache_data
def load_all_data():
    data = {}
    files = {
        "clean_long": "clean_long.csv",
        "calmf_products": "calmf_products.csv",
        "calmf_vs_market": "calmf_vs_market.csv",
        "market_gap": "market_gap.csv",
        "category_sov": "category_sov.csv",
        "outliers": "outliers.csv",
        "data_quality": "data_quality.csv",
        "positioning_scatter": "positioning_scatter.csv",
        "corr_rank_price": "corr_rank_price.csv"
    }
    for key, filename in files.items():
        data[key] = load_csv_safe(OUTPUT_DIR / filename)
    return data

# =============================================================================
# CSS 스타일
# =============================================================================

def apply_css():
    st.markdown("""
    <style>
    .stApp { background-color: #1a1a2e; }
    
    .kpi-card {
        background: linear-gradient(135deg, #2d2d44 0%, #1a1a2e 100%);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 10px;
        position: relative;
    }
    .kpi-tooltip {
        position: absolute;
        top: 8px;
        right: 8px;
        width: 18px;
        height: 18px;
        border-radius: 50%;
        background: rgba(255,255,255,0.2);
        color: #ffffff;
        font-size: 11px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: help;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: bold;
        background: linear-gradient(90deg, #3498db, #2ecc71);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .kpi-label { color: #ffffff; font-size: 0.9rem; margin-top: 5px; }
    .kpi-desc { color: #b2bec3; font-size: 0.75rem; }
    
    .insight-box {
        background: rgba(52, 152, 219, 0.15);
        border-left: 4px solid #3498db;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        color: #ffffff;
    }
    .insight-box.warning {
        background: rgba(243, 156, 18, 0.15);
        border-left-color: #f39c12;
    }
    
    .dark-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
    }
    .dark-table th {
        background: #2d2d44;
        color: #ffffff;
        padding: 10px;
        text-align: left;
        border-bottom: 2px solid #3498db;
        position: sticky;
        top: 0;
    }
    .dark-table td {
        padding: 8px 10px;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        color: #ffffff;
    }
    .dark-table tr:hover { background: rgba(52, 152, 219, 0.1); }
    .calmf-row { background: rgba(241, 196, 15, 0.2) !important; }
    .threat-row { background: rgba(52, 152, 219, 0.1) !important; }
    
    .section-header {
        background: linear-gradient(90deg, rgba(52,152,219,0.2), transparent);
        padding: 15px 20px;
        border-radius: 10px;
        margin: 30px 0 20px 0;
        border-left: 4px solid #3498db;
    }
    .section-title { color: #ffffff; font-size: 1.3rem; font-weight: bold; margin: 0; }
    .section-desc { color: #b2bec3; font-size: 0.85rem; margin: 5px 0 0 0; }
    .metric-desc { color: #b2bec3; font-size: 0.85rem; }
    
    .segment-card {
        background: linear-gradient(135deg, #2d2d44 0%, #1a1a2e 100%);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Expander 스타일 - 흰색 글씨 */
    .streamlit-expanderHeader {
        color: #ffffff !important;
        font-weight: bold;
    }
    .streamlit-expanderHeader p {
        color: #ffffff !important;
    }
    .streamlit-expanderContent {
        color: #ffffff;
    }
    /* Streamlit 최신 버전 호환 */
    [data-testid="stExpander"] summary {
        color: #ffffff !important;
    }
    [data-testid="stExpander"] summary span {
        color: #ffffff !important;
    }
    [data-testid="stExpander"] div {
        color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 컴포넌트
# =============================================================================

def render_kpi(value, label, desc="", format_type="number"):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        formatted = "N/A"
    elif format_type == "number":
        formatted = f"{value:,.0f}"
    elif format_type == "decimal":
        formatted = f"{value:.2f}"
    elif format_type == "percent":
        formatted = f"{value*100:.1f}%"
    elif format_type == "currency":
        formatted = f"₩{value:,.0f}"
    else:
        formatted = str(value)
    
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{formatted}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-desc">{desc}</div>
    </div>
    """, unsafe_allow_html=True)

def render_section(title, desc="", icon="📊"):
    st.markdown(f"""
    <div class="section-header">
        <p class="section-title">{icon} {title}</p>
        <p class="section-desc">{desc}</p>
    </div>
    """, unsafe_allow_html=True)

def is_calmf(row):
    brand = str(row.get("brand", "")).lower()
    name = str(row.get("product_name", "")).lower()
    return "캄프" in brand or "calmf" in brand or "캄프" in name or "calmf" in name

# =============================================================================
# 차트 함수
# =============================================================================

def create_scatter_plot(df, calmf_df=None):
    if df.empty or "log_unit_price" not in df.columns or "page_rank" not in df.columns:
        return None
    
    fig = px.scatter(
        df,
        x="log_unit_price",
        y="page_rank",
        color="segment" if "segment" in df.columns else None,
        color_discrete_map=COLORS,
        hover_data=["brand", "product_name", "unit_price"] if all(c in df.columns for c in ["brand", "product_name", "unit_price"]) else None,
        title=""
    )
    
    # 호버 소수점 2자리 포맷
    fig.update_traces(
        hovertemplate="<b>%{customdata[1]}</b><br>" +
                      "Brand: %{customdata[0]}<br>" +
                      "Log 가격: %{x:.2f}<br>" +
                      "Unit Price: %{customdata[2]:.2f}<br>" +
                      "랭크: %{y}<extra></extra>"
    )
    
    # 캄프 강조
    if calmf_df is not None and not calmf_df.empty:
        for _, row in calmf_df.iterrows():
            if pd.notna(row.get("log_unit_price")) and pd.notna(row.get("page_rank")):
                fig.add_trace(go.Scatter(
                    x=[row["log_unit_price"]],
                    y=[row["page_rank"]],
                    mode="markers+text",
                    marker=dict(size=25, color=COLORS["Calmf"], symbol="star", line=dict(width=2, color="#fff")),
                    text="⭐ 캄프",
                    textposition="top center",
                    textfont=dict(size=12, color=COLORS["Calmf"]),
                    name="Calmf",
                    showlegend=True
                ))
    
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff"),
        height=500,
        xaxis_title="Log 가격",
        yaxis_title="검색 랭크 (낮을수록 상위)",
        legend=dict(font=dict(color="#ffffff"))
    )
    
    return fig

def create_pareto_chart(df, calmf_price, calmf_rank):
    if df.empty:
        return None, 0
    
    df_valid = df[(df["unit_price"].notna()) & (df["page_rank"].notna())].copy()
    
    # dominated_by 계산
    dominated_by = len(df_valid[
        (df_valid["unit_price"] <= calmf_price) & 
        (df_valid["page_rank"] < calmf_rank)
    ])
    
    fig = go.Figure()
    
    # 모든 상품 (호버에 제품명 포함)
    fig.add_trace(go.Scatter(
        x=df_valid["unit_price"],
        y=df_valid["page_rank"],
        mode="markers",
        marker=dict(size=8, color=COLORS["neutral"], opacity=0.5),
        name="시장 상품",
        customdata=df_valid[["product_name", "brand"]].values if "product_name" in df_valid.columns else None,
        hovertemplate="<b>제품명:</b> %{customdata[0]}<br><b>Rank:</b> %{y}<br><b>Unit Price:</b> ₩%{x:,.0f}<extra></extra>" if "product_name" in df_valid.columns else None
    ))
    
    # 캄프 강조
    fig.add_trace(go.Scatter(
        x=[calmf_price],
        y=[calmf_rank],
        mode="markers+text",
        marker=dict(size=20, color=COLORS["Calmf"], symbol="star"),
        text="캄프",
        textposition="top center",
        name="캄프"
    ))
    
    # Pareto frontier (제품명 포함)
    pareto_df = df_valid.sort_values("unit_price")
    pareto_points = []
    pareto_names = []
    min_rank = float("inf")
    for _, row in pareto_df.iterrows():
        if row["page_rank"] < min_rank:
            pareto_points.append((row["unit_price"], row["page_rank"]))
            pareto_names.append(row.get("product_name", "")[:30] if "product_name" in row else "")
            min_rank = row["page_rank"]
    
    if pareto_points:
        pareto_x, pareto_y = zip(*pareto_points)
        fig.add_trace(go.Scatter(
            x=pareto_x, y=pareto_y,
            mode="lines+markers",
            line=dict(color=COLORS["positive"], width=2, dash="dash"),
            marker=dict(size=10, color=COLORS["positive"]),
            name="Pareto Frontier",
            customdata=pareto_names,
            hovertemplate="<b>🏆 Frontier 상품</b><br><b>제품명:</b> %{customdata}<br><b>Rank:</b> %{y}<br><b>Unit Price:</b> ₩%{x:,.0f}<extra></extra>"
        ))
    
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff"),
        height=400,
        xaxis_title="1매당 가격 (₩)",
        yaxis_title="검색 랭크",
        legend=dict(
            font=dict(color="#ffffff", size=12),
            bgcolor="rgba(0,0,0,0.3)",
            bordercolor="rgba(255,255,255,0.2)",
            borderwidth=1
        )
    )
    
    return fig, dominated_by

# =============================================================================
# 테이블 함수
# =============================================================================

def render_competition_table(df, calmf_price=None, calmf_rank=None, max_rows=15, sort_by="rank"):
    if df.empty:
        st.info("데이터가 없습니다.")
        return
    
    df_copy = df.copy()
    
    # 단가차, 랭크차 계산
    if calmf_price and "unit_price" in df_copy.columns:
        df_copy["price_diff_pct"] = ((df_copy["unit_price"] - calmf_price) / calmf_price * 100)
    if calmf_rank and "page_rank" in df_copy.columns:
        df_copy["rank_diff"] = df_copy["page_rank"] - calmf_rank
    
    # 정렬: 기본 랭크순
    if sort_by == "rank" and "page_rank" in df_copy.columns:
        df_sorted = df_copy.sort_values("page_rank").head(max_rows)
    else:
        df_sorted = df_copy.sort_values("unit_price").head(max_rows)
    
    html = '<div style="max-height: 400px; overflow-y: auto;"><table class="dark-table"><thead><tr>'
    html += '<th></th><th>랭크</th><th>브랜드</th><th>상품명</th><th>단가</th><th>단가차</th><th>랭크차</th><th>세그먼트</th>'
    html += '</tr></thead><tbody>'
    
    for _, row in df_sorted.iterrows():
        is_calmf_row = is_calmf(row)
        is_threat = calmf_rank and pd.notna(row.get("page_rank")) and row["page_rank"] < calmf_rank and not is_calmf_row
        
        row_class = "calmf-row" if is_calmf_row else ("threat-row" if is_threat else "")
        icon = "⭐" if is_calmf_row else ""
        
        # 단가차 포맷
        price_diff = row.get("price_diff_pct", 0)
        if pd.notna(price_diff):
            price_diff_str = f"+{price_diff:.1f}%" if price_diff >= 0 else f"{price_diff:.1f}%"
            price_diff_color = "#27ae60" if price_diff > 0 else "#e74c3c" if price_diff < 0 else "#ffffff"
        else:
            price_diff_str = "-"
            price_diff_color = "#ffffff"
        
        # 랭크차 포맷
        rank_diff = row.get("rank_diff", 0)
        if pd.notna(rank_diff):
            rank_diff = int(rank_diff)
            if rank_diff < 0:
                rank_diff_str = f"{rank_diff}위 ↑"
                rank_diff_color = "#e74c3c"
            elif rank_diff > 0:
                rank_diff_str = f"+{rank_diff}위 ↓"
                rank_diff_color = "#27ae60"
            else:
                rank_diff_str = "동일"
                rank_diff_color = "#f39c12"
        else:
            rank_diff_str = "-"
            rank_diff_color = "#ffffff"
        
        html += f'<tr class="{row_class}">'
        html += f'<td>{icon}</td>'
        html += f'<td>{int(row["page_rank"])}</td>' if pd.notna(row.get("page_rank")) else '<td>-</td>'
        html += f'<td>{row.get("brand", "-")}</td>'
        html += f'<td style="max-width: 180px; overflow: hidden; text-overflow: ellipsis;">{str(row.get("product_name", "-"))[:30]}</td>'
        html += f'<td>₩{row["unit_price"]:,.0f}</td>' if pd.notna(row.get("unit_price")) else '<td>-</td>'
        html += f'<td style="color: {price_diff_color};">{price_diff_str}</td>'
        html += f'<td style="color: {rank_diff_color};">{rank_diff_str}</td>'
        html += f'<td>{row.get("segment", "-")}</td>'
        html += '</tr>'
    
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

# =============================================================================
# 메인 앱
# =============================================================================

def main():
    apply_css()
    
    st.markdown("""
    <h1 style='color: #ffffff; text-align: center; margin-bottom: 5px;'>
        📊 가격 비교 분석 Dashboard
    </h1>
    <p style='color: #b2bec3; text-align: center; margin-bottom: 30px;'>
        네이버 쇼핑 모니터링
    </p>
    """, unsafe_allow_html=True)
    
    data = load_all_data()
    df_main = data["clean_long"]
    calmf_products = data["calmf_products"]
    calmf_vs = data["calmf_vs_market"]
    gap_df = data["market_gap"]
    sov_df = data["category_sov"]
    dq_df = data["data_quality"]
    
    if df_main.empty:
        st.error("⚠️ 데이터를 찾을 수 없습니다. ./output/ 폴더 확인 필요")
        return
    
    # 캄프 정보
    calmf_price = calmf_products.iloc[0]["unit_price"] if not calmf_products.empty and "unit_price" in calmf_products.columns else None
    calmf_rank = calmf_products.iloc[0]["page_rank"] if not calmf_products.empty and "page_rank" in calmf_products.columns else None
    market_median = df_main["unit_price"].median() if "unit_price" in df_main.columns else None
    
    # =========================================================================
    # 1. 핵심 지표
    # =========================================================================
    
    st.markdown("<h2 style='color: #ffffff; margin: 30px 0 20px 0;'>📈 핵심 지표</h2>", unsafe_allow_html=True)
    
    cols = st.columns(5)
    with cols[0]:
        render_kpi(market_median, "시장 중앙값", "전체 상품", "currency")
    with cols[1]:
        render_kpi(calmf_price, "캄프 단가", "1매당 가격", "currency")
    with cols[2]:
        premium = calmf_price / market_median if calmf_price and market_median else None
        render_kpi(premium, "프리미엄 지수", "캄프/시장", "decimal")
    with cols[3]:
        render_kpi(calmf_rank, "캄프 랭크", "검색 순위", "number")
    with cols[4]:
        render_kpi(len(df_main), "총 상품수", "분석 대상", "number")
    
    # =========================================================================
    # 2. Calmf vs Market
    # =========================================================================
    
    render_section("Calmf vs Market", "캄프 상품의 시장 내 위치", "🎯")
    
    if not calmf_vs.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<h5 style='color: #ffffff;'>가격 비교</h5>", unsafe_allow_html=True)
            calmf_med = calmf_vs["calmf_median_unit_price"].iloc[0] if "calmf_median_unit_price" in calmf_vs.columns else calmf_price
            market_med = calmf_vs["market_median_unit_price"].iloc[0] if "market_median_unit_price" in calmf_vs.columns else market_median
            
            if calmf_med and market_med:
                premium_idx = calmf_med / market_med
                st.markdown(f"""
                <div class="insight-box" style="min-height: 70px;">
                    <strong>캄프 1매당 가격:</strong> ₩{calmf_med:,.0f}<br>
                    <strong>시장 중앙값:</strong> ₩{market_med:,.0f}<br>
                    <strong>프리미엄 지수:</strong> <span style="color: {COLORS['negative'] if premium_idx > 1 else COLORS['positive']}">{premium_idx:.2f}</span>
                    <span style="color: #b2bec3; font-size: 0.8rem;">({'+' if premium_idx > 1 else ''}{(premium_idx-1)*100:.1f}%)</span>
                </div>
                """, unsafe_allow_html=True)
            
            # 시장 통계 (별도 박스)
            market_mean = df_main["unit_price"].mean() if "unit_price" in df_main.columns else 0
            market_min = df_main["unit_price"].min() if "unit_price" in df_main.columns else 0
            market_max = df_main["unit_price"].max() if "unit_price" in df_main.columns else 0
            st.markdown(f"""
            <div class="insight-box" style="margin-top: 10px;">
                <strong>📈 시장 통계</strong><br>
                평균: ₩{market_mean:,.0f} | 최소: ₩{market_min:,.0f} | 최대: ₩{market_max:,.0f}
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("<h5 style='color: #ffffff;'>캄프 상품 목록</h5>", unsafe_allow_html=True)
            if not calmf_products.empty:
                for _, row in calmf_products.iterrows():
                    st.markdown(f"""
                    <div class="insight-box" style="min-height: 70px; margin-bottom: 10px;">
                        <strong style="color: {COLORS['Calmf']};">⭐ {row.get('product_name', 'N/A')}</strong><br>
                        <span style="color: #ffffff; margin-left: 20px;">₩{row.get('unit_price', 0):,.0f}/매 | 랭크 {int(row.get('page_rank', 0))}</span>
                    </div>
                    """, unsafe_allow_html=True)
    
    # =========================================================================
    # 3. Positioning Map
    # =========================================================================
    
    render_section("Positioning Map", "가격-랭크 포지셔닝 시각화", "🗺️")
    
    scatter_df = data.get("positioning_scatter", df_main)
    if scatter_df.empty:
        scatter_df = df_main
    
    # 3컬럼 레이아웃: 스캐터 | 세그먼트 파이 + 박스플롯
    col1, col2 = st.columns([2, 1])
    
    with col1:
        calmf_scatter = scatter_df[scatter_df.apply(is_calmf, axis=1)] if not scatter_df.empty else pd.DataFrame()
        fig_scatter = create_scatter_plot(scatter_df, calmf_scatter)
        if fig_scatter:
            fig_scatter.update_layout(height=650)  # 더 크게
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        # 세그먼트 분위수 정의 (스캐터플롯 바로 밑)
        st.markdown("""
        <p style="color: #b2bec3; font-size: 0.85rem; margin: -15px 0 0 0; padding-left: 15px;">
            📊 <strong style="color: #ffffff;">세그먼트 분위수 정의:</strong><br>
            • Mass: P0~P50 (하위 50%)<br>
            • Premium: P50~P85 (상위 15~50%)<br>
            • Luxury: P85~P100 (상위 15%)
        </p>
        """, unsafe_allow_html=True)
    
    with col2:
        # 세그먼트 분포 파이 차트
        st.markdown("<h5 style='color: #ffffff;'>세그먼트 분포</h5>", unsafe_allow_html=True)
        st.markdown("<p class='metric-desc'>가격 구간별 상품 비율 (Mass/Premium/Luxury)</p>", unsafe_allow_html=True)
        
        if "segment" in df_main.columns:
            seg_counts = df_main["segment"].value_counts().reset_index()
            seg_counts.columns = ["segment", "count"]
            
            fig_pie = px.pie(
                seg_counts,
                values="count",
                names="segment",
                color="segment",
                color_discrete_map=COLORS,
                hole=0.4
            )
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#ffffff"),
                height=350,
                margin=dict(t=10, b=10, l=10, r=10),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, font=dict(color="#ffffff"))
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # 세그먼트별 가격 분포 박스플롯 (3개 박스)
        st.markdown("<h5 style='color: #ffffff;'>세그먼트 가격 분포</h5>", unsafe_allow_html=True)
        st.markdown("<p class='metric-desc'>상자: 1~3분위수 | 선: 중앙값 | 점: 이상치</p>", unsafe_allow_html=True)
        
        if "segment" in df_main.columns and "unit_price" in df_main.columns:
            seg_order = ["Mass", "Premium", "Luxury"]
            df_seg_box = df_main[df_main["segment"].isin(seg_order)].copy()
            
            fig_box = px.box(
                df_seg_box,
                x="segment",
                y="unit_price",
                color="segment",
                category_orders={"segment": seg_order},
                color_discrete_map=COLORS,
                labels={"unit_price": "1매당 가격 (₩)", "segment": "세그먼트"}
            )
            
            fig_box.update_traces(hovertemplate="<b>%{x}</b><br>가격: ₩%{y:,.0f}<extra></extra>", width=0.6)
            
            fig_box.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#ffffff"),
                showlegend=False,
                height=500,
                boxgap=0.3,
                xaxis=dict(tickfont=dict(color="#ffffff"), title_font=dict(color="#ffffff")),
                yaxis=dict(tickfont=dict(color="#ffffff"), title_font=dict(color="#ffffff"), tickformat=",.0f")
            )
            st.plotly_chart(fig_box, use_container_width=True)
    
    # =========================================================================
    # 4. 세그먼트별 Premium Index (Mass/Premium/Luxury)
    # =========================================================================
    
    render_section("세그먼트별 Premium Index", "Mass/Premium/Luxury 가격 구간별 분석", "💎")
    
    if "segment" in df_main.columns and "unit_price" in df_main.columns and market_median:
        segments = ["Mass", "Premium", "Luxury"]
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("<h5 style='color: #ffffff;'>세그먼트별 Premium Index</h5>", unsafe_allow_html=True)
            st.markdown("<p class='metric-desc'>노란색 = 캄프가 속한 분위 | 빨간 점선 = 시장 평균(1.0)</p>", unsafe_allow_html=True)
            
            # 세그먼트별 데이터 준비
            segment_data = []
            for seg in segments:
                seg_df = df_main[df_main["segment"] == seg]
                if not seg_df.empty:
                    seg_median = seg_df["unit_price"].median()
                    premium_idx = seg_median / market_median if market_median else 1
                    avg_rank = seg_df["page_rank"].mean() if "page_rank" in seg_df.columns else None
                    calmf_in_seg = calmf_products[calmf_products["segment"] == seg] if not calmf_products.empty and "segment" in calmf_products.columns else pd.DataFrame()
                    
                    segment_data.append({
                        "세그먼트": seg,
                        "상품수": len(seg_df),
                        "중앙가격": seg_median,
                        "Premium Index": premium_idx,
                        "평균랭크": avg_rank,
                        "is_calmf": not calmf_in_seg.empty
                    })
            
            if segment_data:
                chart_df = pd.DataFrame(segment_data)
                
                # 바 차트 생성 - 세그먼트 색상 적용
                colors = [COLORS.get(row["세그먼트"], "#3498db") for _, row in chart_df.iterrows()]
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=chart_df["세그먼트"],
                        y=chart_df["Premium Index"],
                        marker_color=colors,
                        text=chart_df["Premium Index"].apply(lambda x: f"{x:.2f}"),
                        textposition="outside"
                    )
                ])
                
                # 시장 평균선 (1.0)
                fig.add_hline(y=1.0, line_dash="dash", line_color="#e74c3c", 
                             annotation_text="시장 평균(1.0)", annotation_position="top right")
                
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#ffffff"),
                    height=500,  # 더 크게
                    xaxis_title="가격 분위",
                    yaxis_title="Premium Index",
                    margin=dict(t=120)  # 상단 마진 더 늘림
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 제목 없이 테이블만 (바 차트와 높이 맞춤)
            if segment_data:
                # 상세 테이블 (아래로 이동)
                html = '<div style="margin-top: 280px;"><table class="dark-table"><thead><tr>'
                html += '<th>분위</th><th>상품수</th><th>중앙가격</th><th>Premium</th><th>평균랭크</th>'
                html += '</tr></thead><tbody>'
                
                for row in segment_data:
                    row_style = "background: rgba(241, 196, 15, 0.2);" if row["is_calmf"] else ""
                    star = "⭐" if row["is_calmf"] else ""
                    
                    html += f'<tr style="{row_style}">'
                    html += f'<td>{star} {row["세그먼트"]}</td>'
                    html += f'<td>{row["상품수"]}</td>'
                    html += f'<td>₩{row["중앙가격"]:,.0f}</td>'
                    html += f'<td>{row["Premium Index"]:.2f}</td>'
                    html += f'<td>{row["평균랭크"]:.0f}</td>' if row["평균랭크"] else '<td>-</td>'
                    html += '</tr>'
                
                html += '</tbody></table></div>'
                st.markdown(html, unsafe_allow_html=True)
    
    # =========================================================================
    # 5. 가격 밴드별 경쟁자 (전체 세그먼트)
    # =========================================================================
    
    render_section("가격 밴드별 경쟁자", "±20% 경쟁자 전체 세그먼트", "📊")
    
    if calmf_price and not df_main.empty:
        st.markdown(f"<h5 style='color: #ffffff;'>Band ±20% (₩{calmf_price*0.8:,.0f} ~ ₩{calmf_price*1.2:,.0f})</h5>", unsafe_allow_html=True)
        band20 = df_main[(df_main["unit_price"] >= calmf_price * 0.8) & (df_main["unit_price"] <= calmf_price * 1.2)]
        render_competition_table(band20, calmf_price, calmf_rank, max_rows=30)
    
    # =========================================================================
    # 6. Premium 세그먼트 직접 경쟁자
    # =========================================================================
    
    render_section("Premium 세그먼트 경쟁자", "캄프와 동일 세그먼트(Premium) + 단가 ±20% 경쟁자", "🎯")
    
    if calmf_price and calmf_rank and not df_main.empty and "segment" in df_main.columns:
        premium_15 = df_main[
            (df_main["segment"] == "Premium") &
            (df_main["unit_price"] >= calmf_price * 0.85) &
            (df_main["unit_price"] <= calmf_price * 1.15)
        ]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            render_competition_table(premium_15, calmf_price, calmf_rank, max_rows=20, sort_by="rank")
        
        with col2:
            # Premium 경쟁 요약 (v2 스타일)
            threats = premium_15[(premium_15["page_rank"] < calmf_rank) & (~premium_15.apply(is_calmf, axis=1))]
            cheaper_or_equal = premium_15[(premium_15["unit_price"] <= calmf_price) & (~premium_15.apply(is_calmf, axis=1))]
            total_competitors = len(premium_15) - len(premium_15[premium_15.apply(is_calmf, axis=1)])
            threat_pct = (len(threats) / total_competitors * 100) if total_competitors > 0 else 0
            
            st.markdown("<h5 style='color: #9b59b6;'>🏅 Premium 경쟁 요약</h5>", unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">랭크 우위 경쟁자</div>
                <div class="kpi-value" style="color: #e74c3c;">{len(threats)}</div>
                <div class="kpi-desc">Premium {total_competitors}개 중</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">같거나 저렴한 상품</div>
                <div class="kpi-value" style="color: #27ae60;">{len(cheaper_or_equal)}</div>
                <div class="kpi-desc">캄프 단가 이하 Premium 경쟁자</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 분석 및 액션 포인트
            st.markdown(f"""
            <div class="insight-box warning">
                <strong>⚠️ 분석:</strong> 비슷한 가격대 {total_competitors}개 중 {len(threats)}개({threat_pct:.0f}%)가 캄프보다 상위 노출<br><br>
                <strong>🚀 액션 포인트:</strong><br>
                • 상위 경쟁자(한율, 벤튼 등) 상품명/썸네일 벤치마킹<br>
                • 가격 인하보다 <strong>비가격 요인</strong>(리뷰, 제목 키워드) 개선 우선 검토
            </div>
            """, unsafe_allow_html=True)
    
    # =========================================================================
    # 7. 가격이 문제가 아닌 경쟁자
    # =========================================================================
    
    render_section("가격이 문제가 아닌 경쟁자", "캄프보다 비싸면서 상위 노출되는 상품 → 비가격 요인 분석 필요", "🚨")
    
    if calmf_price and calmf_rank and not df_main.empty:
        non_price = df_main[
            (df_main["unit_price"] >= calmf_price) &
            (df_main["page_rank"] < calmf_rank) &
            (~df_main.apply(is_calmf, axis=1))
        ]
        
        if not non_price.empty:
            render_competition_table(non_price, calmf_price, calmf_rank)
            st.markdown(f"""
            <div class="insight-box warning">
                <strong>📌 액션 포인트:</strong><br>
                • 위 {len(non_price)}개 상품의 썸네일, 제목, 리뷰 분석 필요<br>
                • 가격 인하가 아닌 비가격 요인 분석 필요
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("캄프보다 비싸면서 상위 노출되는 상품이 없습니다. 👍")
    
    # =========================================================================
    # 8. Pareto (가격 대비 노출 효율성)
    # =========================================================================
    
    st.markdown("""
    <h3 style='color: #ffffff; margin-top: 40px;'>📈 가격 대비 노출 효율성</h3>
    <p style='color: #2ecc71; font-size: 1rem; font-weight: bold; margin-bottom: 20px;'>
        🏆 Pareto Frontier: 가격 대비 랭크 최적 상품들 (초록 점선)
    </p>
    """, unsafe_allow_html=True)
    
    if calmf_price and calmf_rank:
        fig_pareto, dominated_by = create_pareto_chart(df_main, calmf_price, calmf_rank)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if fig_pareto:
                st.plotly_chart(fig_pareto, use_container_width=True)
        
        with col2:
            # dominated_pct 계산
            total = len(df_main)
            dominated_pct = (dominated_by / total * 100) if total > 0 else 0
            
            # 분석 및 액션 포인트 (v2 스타일)
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">DOMINATED BY</div>
                <div class="kpi-value" style="color: {'#e74c3c' if dominated_pct > 30 else '#27ae60'};">{dominated_by}</div>
                <div class="kpi-desc">캄프보다 싸거나 같고 + 랭크도 좋은 상품</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value" style="color: {'#e74c3c' if dominated_pct > 30 else '#27ae60'};">{dominated_pct:.1f}%</div>
                <div class="kpi-desc">전체 {total}개 중</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="insight-box {'warning' if dominated_pct > 30 else ''}">
                <strong>📊 해석:</strong><br>
                캄프는 시장 {total}개 상품 중 <strong style="color: #e74c3c;">{dominated_by}개({dominated_pct:.1f}%)</strong>에 의해 "지배"됨<br>
                <span style="color: #b2bec3;">(= 더 싸거나 같으면서 랭크도 좋은 상품)</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="insight-box">
                <strong>🚀 액션 포인트:</strong>
                <ul style="margin: 10px 0 0 0; padding-left: 20px; line-height: 1.8;">
                    <li><strong>Frontier 벤치마킹:</strong> 초록 경계선 근처 상품의 가격대/구성/리뷰수/키워드/썸네일/혜택 비교</li>
                    <li><strong>랭크 개선:</strong> 핵심 키워드 재정의 → 제목/속성/리뷰 유도/광고로 상위 노출 유도</li>
                    <li><strong>가격·구성 재설계:</strong> '1매당 가격' 기준 경쟁력 회복 (용량/묶음/프로모션)</li>
                    <li><strong>차별화 강화:</strong> 가격 경쟁이 어렵다면 효능·근거·소재로 "비싸도 사는 이유" 만들기</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # =========================================================================
    # 9. Elasticity & Spearman (참고용)
    # =========================================================================
    
    with st.expander("📐 Price-Rank Elasticity & Spearman (참고용 - 표본 부족)", expanded=False):
        st.markdown("""
        <div class="insight-box warning">
            <strong>⚠️ 주의:</strong> 표본 수(n)가 적어 통계적 검정력이 낮습니다. 방향성 참고용으로만 활용하세요.
        </div>
        """, unsafe_allow_html=True)
        
        try:
            from scipy import stats
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Spearman 상관계수
                st.markdown("<h5 style='color: #ffffff;'>📊 Spearman 상관계수</h5>", unsafe_allow_html=True)
                st.markdown("<p style='color: #b2bec3; font-size: 0.85rem;'>가격과 랭크 간 단조 관계 측정 (ρ: -1 ~ +1)</p>", unsafe_allow_html=True)
                
                spearman_results = []
                for label, cutoff in [("Top 20", 20), ("Top 50", 50), ("Top 100", 100)]:
                    df_cut = df_main[(df_main["page_rank"] <= cutoff) & 
                                     df_main["unit_price"].notna() & 
                                     df_main["page_rank"].notna()]
                    n = len(df_cut)
                    if n >= 3:
                        rho, p = stats.spearmanr(df_cut["unit_price"], df_cut["page_rank"])
                        spearman_results.append({
                            "구간": label,
                            "n": n,
                            "ρ": f"{rho:.3f}",
                            "p-value": f"{p:.4f}",
                            "유의성": "✓" if p < 0.05 else "✗"
                        })
                    else:
                        spearman_results.append({
                            "구간": label,
                            "n": n,
                            "ρ": "N/A",
                            "p-value": "N/A",
                            "유의성": "-"
                        })
                
                if spearman_results:
                    html = '<table class="dark-table"><thead><tr>'
                    html += '<th>구간</th><th>n</th><th>ρ</th><th>p-value</th><th>유의</th>'
                    html += '</tr></thead><tbody>'
                    for row in spearman_results:
                        html += f'<tr><td>{row["구간"]}</td><td>{row["n"]}</td><td>{row["ρ"]}</td><td>{row["p-value"]}</td><td>{row["유의성"]}</td></tr>'
                    html += '</tbody></table>'
                    st.markdown(html, unsafe_allow_html=True)
            
            with col2:
                # Regression (Log-Log)
                st.markdown("<h5 style='color: #ffffff;'>📈 Regression (Log-Log)</h5>", unsafe_allow_html=True)
                st.markdown("<p style='color: #b2bec3; font-size: 0.85rem;'>log(rank) = a + b×log(price) | b>0: 가격↑→노출↓</p>", unsafe_allow_html=True)
                
                regression_results = []
                for label, cutoff in [("Top 20", 20), ("Top 50", 50), ("Top 100", 100)]:
                    df_cut = df_main[(df_main["page_rank"] <= cutoff) & 
                                     df_main["unit_price"].notna() & 
                                     df_main["page_rank"].notna() &
                                     (df_main["unit_price"] > 0) &
                                     (df_main["page_rank"] > 0)]
                    n = len(df_cut)
                    if n >= 3:
                        log_price = np.log(df_cut["unit_price"])
                        log_rank = np.log(df_cut["page_rank"])
                        slope, intercept, r_value, p_value, std_err = stats.linregress(log_price, log_rank)
                        regression_results.append({
                            "구간": label,
                            "n": n,
                            "b (기울기)": f"{slope:.3f}",
                            "R²": f"{r_value**2:.3f}",
                            "p-value": f"{p_value:.4f}",
                            "유의성": "✓" if p_value < 0.05 else "✗"
                        })
                    else:
                        regression_results.append({
                            "구간": label,
                            "n": n,
                            "b (기울기)": "N/A",
                            "R²": "N/A",
                            "p-value": "N/A",
                            "유의성": "-"
                        })
                
                if regression_results:
                    html = '<table class="dark-table"><thead><tr>'
                    html += '<th>구간</th><th>n</th><th>b</th><th>R²</th><th>p-value</th><th>유의</th>'
                    html += '</tr></thead><tbody>'
                    for row in regression_results:
                        html += f'<tr><td>{row["구간"]}</td><td>{row["n"]}</td><td>{row["b (기울기)"]}</td><td>{row["R²"]}</td><td>{row["p-value"]}</td><td>{row["유의성"]}</td></tr>'
                    html += '</tbody></table>'
                    st.markdown(html, unsafe_allow_html=True)
            
            # 종합 분석 결과
            last_spearman = spearman_results[-1] if spearman_results else None
            last_reg = regression_results[-1] if regression_results else None
            
            corr_sig = last_spearman and last_spearman["유의성"] == "✓"
            reg_sig = last_reg and last_reg["유의성"] == "✓"
            
            if not corr_sig and not reg_sig:
                st.markdown(f"""
                <div class="insight-box warning" style="margin-top: 15px;">
                    <strong>📊 종합 분석:</strong> 상관분석 및 회귀분석 모두 <strong>통계적으로 유의하지 않음</strong><br>
                    → 가격이 랭크에 미치는 영향이 명확하지 않음 (표본 부족 가능성)
                </div>
                """, unsafe_allow_html=True)
            elif corr_sig and reg_sig:
                st.markdown("""
                <div class="insight-box" style="margin-top: 15px;">
                    <strong>📈 종합 분석:</strong> 상관분석 및 회귀분석 모두 <strong>통계적으로 유의함</strong><br>
                    → 가격과 랭크 간 유의한 관계 존재
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="insight-box" style="margin-top: 15px;">
                    <strong>📊 종합 분석:</strong> 일부 분석에서만 유의한 결과<br>
                    → 추가 데이터 확보 후 재분석 권장
                </div>
                """, unsafe_allow_html=True)
                    
        except ImportError:
            st.info("scipy 라이브러리가 필요합니다: pip install scipy")
        except Exception as e:
            st.error(f"분석 오류: {str(e)}")
    
    # =========================================================================
    # 10. SOV & Market Gap (참고용)
    # =========================================================================
    
    with st.expander("📊 SOV & Market Gap (참고용)", expanded=False):
        st.markdown("""
        <div class="insight-box">
            <strong>� SOV (Share of Voice) 설명:</strong><br>
            • SOV = 특정 브랜드의 검색결과 노출 비중<br>
            • 가중 SOV = 상위 랭크일수록 높은 가중치 부여한 노출 점유율<br>
            • 계산: Σ(1/√랭크) / 전체 합계<br><br>
            <strong>📐 Market Gap 수식:</strong><br>
            • gap_score = 노출 점유율(SOV) / 상품 공급 비율<br>
            • 점수 > 1: 노출 대비 상품 수 부족 → 진입 기회<br>
            • 점수 < 1: 노출 대비 상품 수 과잉 → 경쟁 치열
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<h5 style='color: #ffffff;'>Market Gap (가격대별)</h5>", unsafe_allow_html=True)
            if not gap_df.empty and "gap_score" in gap_df.columns:
                gap_sorted = gap_df.sort_values("gap_score", ascending=False).copy()
                
                # 가격 범위 계산해서 표시
                if "price_band" in gap_sorted.columns and "unit_price" in df_main.columns:
                    price_labels = []
                    for band in gap_sorted["price_band"]:
                        try:
                            # P60-80 같은 값에서 percentile 추출
                            parts = str(band).replace("P", "").split("-")
                            if len(parts) == 2:
                                p_low, p_high = int(parts[0]), int(parts[1])
                                price_low = df_main["unit_price"].quantile(p_low/100)
                                price_high = df_main["unit_price"].quantile(p_high/100)
                                price_labels.append(f"₩{price_low:,.0f}~{price_high:,.0f}")
                            else:
                                price_labels.append(str(band))
                        except:
                            price_labels.append(str(band))
                    gap_sorted["price_range"] = price_labels
                    x_col = "price_range"
                else:
                    x_col = "price_band"
                
                fig_gap = px.bar(gap_sorted, x=x_col, y="gap_score", color="gap_score",
                                color_continuous_scale=["#27ae60", "#f1c40f", "#e74c3c"])
                fig_gap.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#ffffff"),
                    height=300,
                    xaxis_title="가격대",
                    yaxis_title="Gap Score"
                )
                st.plotly_chart(fig_gap, use_container_width=True)
        
        with col2:
            st.markdown("<h5 style='color: #ffffff;'>브랜드 SOV (캄프 유사가격대 ±15%)</h5>", unsafe_allow_html=True)
            
            # 캄프 가격대 ±15% 내 브랜드 SOV 계산
            if calmf_price and not df_main.empty:
                price_low = calmf_price * 0.85
                price_high = calmf_price * 1.15
                
                # 해당 가격대 필터
                band_df = df_main[(df_main["unit_price"] >= price_low) & (df_main["unit_price"] <= price_high)].copy()
                
                if not band_df.empty and "brand" in band_df.columns and "page_rank" in band_df.columns:
                    # 가중 SOV 계산 (1/√rank)
                    band_df["weight"] = 1 / np.sqrt(band_df["page_rank"])
                    total_weight = band_df["weight"].sum()
                    
                    brand_sov = band_df.groupby("brand")["weight"].sum().reset_index()
                    brand_sov["sov"] = (brand_sov["weight"] / total_weight * 100).round(2)
                    brand_sov = brand_sov.sort_values("sov", ascending=False).head(10)
                    
                    # 캄프 강조
                    brand_sov["is_calmf"] = brand_sov["brand"].apply(lambda x: "캄프" in str(x).lower() or "calmf" in str(x).lower())
                    colors = [COLORS["Calmf"] if is_calmf else "#3498db" for is_calmf in brand_sov["is_calmf"]]
                    
                    fig_sov = go.Figure(data=[
                        go.Bar(
                            x=brand_sov["sov"],
                            y=brand_sov["brand"],
                            orientation="h",
                            marker_color=colors,
                            text=brand_sov["sov"].apply(lambda x: f"{x:.1f}%"),
                            textposition="outside"
                        )
                    ])
                    fig_sov.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#ffffff"),
                        height=450,  # 높이 늘림
                        xaxis_title="SOV (%)",
                        yaxis=dict(autorange="reversed")
                    )
                    st.plotly_chart(fig_sov, use_container_width=True)
                    
                    st.markdown(f"""
                    <p style="color: #b2bec3; font-size: 0.8rem;">
                    가격 범위: ₩{price_low:,.0f} ~ ₩{price_high:,.0f} (캄프 ±15%)
                    </p>
                    """, unsafe_allow_html=True)
                else:
                    st.info("해당 가격대 데이터가 없습니다.")
            else:
                st.info("캄프 가격 정보가 없습니다.")
    
    # =========================================================================
    # 11. Data Quality
    # =========================================================================
    
    render_section("Data Quality", "데이터 품질 지표 - 분석 신뢰도 참고", "⚠️")
    
    if not dq_df.empty:
        cols = st.columns(3)
        with cols[0]:
            has_sheets = dq_df["has_sheets_rate"].iloc[0] if "has_sheets_rate" in dq_df.columns else None
            render_kpi(has_sheets, "매수 추출 성공률", "정상 파싱 비율", "percent")
        with cols[1]:
            outlier_rate = dq_df["outlier_rate"].iloc[0] if "outlier_rate" in dq_df.columns else None
            render_kpi(outlier_rate, "이상치 비율", "가격 이상 상품", "percent")
        with cols[2]:
            parse_fail = 1 - has_sheets if has_sheets else None
            render_kpi(parse_fail, "Parse Fail", "매수 추출 실패", "percent")
    else:
        st.info("데이터 품질 정보가 없습니다.")
    
    # 푸터
    st.markdown("""
    <hr style='border-color: rgba(255,255,255,0.1); margin-top: 50px;'>
    <p style='color: #636e72; text-align: center; font-size: 0.8rem;'>
        📊 가격 비교 분석 Dashboard v3 | 2025
    </p>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
