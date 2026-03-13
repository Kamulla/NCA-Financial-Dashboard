import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data
from pathlib import Path
from datetime import datetime

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="NCA Financial Performance",
    page_icon="assets/nca_logo_mark.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# NCA Branding Colors
NCA_BLUE = "#0070C0"  # Light/Royal Blue
NCA_ORANGE = "#F7941D"  # Light Orange
NCA_BG_BLUE = "#F0F9FF"  # Very Light Blue Background
NCA_DARK = "#334155"
NCA_TEAL = "#0EA5A4"
NCA_PURPLE = "#6366F1"

def build_category_color_map(categories, preferred=None):
    preferred = preferred or {}
    palette = [NCA_BLUE, NCA_ORANGE, NCA_DARK, NCA_TEAL, NCA_PURPLE]
    used = {color for cat, color in preferred.items() if cat in categories}
    remaining = [c for c in palette if c not in used]
    mapping = {}
    for cat, color in preferred.items():
        if cat in categories:
            mapping[cat] = color
    idx = 0
    for cat in categories:
        if cat not in mapping:
            mapping[cat] = remaining[idx % len(remaining)] if remaining else NCA_BLUE
            idx += 1
    return mapping

# Placeholder (rebuilt after data load)
INCOME_COLOR_MAP = {}
EXP_COLOR_MAP = {}

# --- 2. Enhanced Professional CSS (NCA Kenya Branding + Liquid Glass) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="st-"] {{
        font-family: 'Inter', sans-serif;
    }}

    .stApp {{
        background: radial-gradient(circle at top left, {NCA_BG_BLUE} 0%, #E0F2FE 100%);
    }}

    /* Executive KPI Card - Liquid Glass Effect */
    .metric-card {{
        background: rgba(255, 255, 255, 0.45);
        padding: 1.5rem;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(12px) saturate(160%);
        -webkit-backdrop-filter: blur(12px) saturate(160%);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05);
        position: relative;
        overflow: hidden;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }}

    .metric-card:hover {{
        transform: translateY(-2px);
        background: rgba(255, 255, 255, 0.6);
        box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.1);
    }}

    .status-bar {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 5px;
        background: {NCA_ORANGE};
        opacity: 0.8;
    }}

    .metric-title {{
        color: #475569;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.75rem;
    }}

    .metric-value {{
        color: {NCA_BLUE};
        font-size: 1.85rem;
        font-weight: 800;
        letter-spacing: -0.03em;
    }}

    .metric-sub-value {{
        color: #64748B;
        font-size: 0.8rem;
        font-weight: 600;
        margin-top: 0.25rem;
    }}

    /* Sidebar Refinements - Using NCA Blue */
    section[data-testid="stSidebar"] {{
        background-color: {NCA_BLUE};
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }}

    section[data-testid="stSidebar"] .stMarkdown h2 {{
        color: white !important;
        font-size: 1.4rem;
        font-weight: 800;
        letter-spacing: -0.02em;
    }}

    /* Sidebar collapse control: visible, centered, not clipped */
    [data-testid="stSidebarHeader"] {{
        display: flex;
        justify-content: flex-end;
        align-items: center;
        padding: 8px 12px 6px 12px;
        background: transparent;
    }}

    [data-testid="stSidebarHeader"] button {{
        width: 34px !important;
        height: 34px !important;
        padding: 0 !important;
        margin: 0 !important;
        border-radius: 10px !important;
        background: rgba(255, 255, 255, 0.18) !important;
        border: none !important;
        font-size: 0 !important;
        line-height: 0 !important;
        color: transparent !important;
        display: grid !important;
        place-items: center !important;
        overflow: hidden !important;
        outline: none !important;
    }}

    [data-testid="stSidebarHeader"] button * {{
        opacity: 0 !important;
        display: none !important;
    }}

    [data-testid="stSidebarHeader"] button::before {{
        content: "≡";
        font-size: 20px;
        line-height: 1;
        color: #FFFFFF;
    }}

    [data-testid="stSidebarHeader"] button[aria-expanded="false"]::before {{
        content: "≡";
    }}

    .menu-title {{
        text-align: center;
        color: rgba(255, 255, 255, 0.9);
        font-size: 0.9rem;
        font-weight: 700;
        letter-spacing: 0.25em;
        text-transform: uppercase;
        margin-bottom: 10px;
    }}

    .menu-separator {{
        height: 1px;
        margin: 0 12px 20px 12px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
    }}

    /* Sidebar Navigation - Glass Tabs */
    .stButton > button {{
        width: 100%;
        text-align: left !important;
        justify-content: flex-start !important;
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        padding: 14px 20px !important;
        font-weight: 500 !important;
        border-radius: 14px !important;
        transition: all 0.3s ease !important;
        margin-bottom: 8px !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 0.8rem !important;
    }}

    .stButton > button:hover {{
        background: rgba(255, 255, 255, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        transform: translateX(4px);
    }}

    /* Active Tab - Vibrant Liquid Glass */
    button[kind="primary"] {{
        background: linear-gradient(135deg, rgba(247, 148, 29, 0.9), rgba(247, 148, 29, 0.7)) !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        color: white !important;
        font-weight: 700 !important;
        box-shadow: 0 8px 20px rgba(247, 148, 29, 0.25) !important;
        transform: scale(1.02);
    }}

    /* Input Surfaces - Glass */
    .stSelectbox div[data-baseweb="select"], .stMultiSelect div[role="combobox"] {{
        background: rgba(255, 255, 255, 0.5) !important;
        border-radius: 15px !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
    }}

    /* Custom Header Style */
    .main-header {{
        background: linear-gradient(90deg, {NCA_BLUE}, #2563EB);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        text-align: center;
        padding: 10px 0 30px 0;
    }}

    .main-subtitle {{
        text-align: center;
        color: #64748B;
        font-size: 0.95rem;
        font-weight: 500;
        margin-top: -18px;
        margin-bottom: 24px;
    }}

    /* Chart Containers - Subtle Glass */
    .chart-container {{
        background: rgba(255, 255, 255, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.4);
        border-radius: 20px;
        padding: 20px;
        backdrop-filter: blur(5px);
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. Data Loading & Initial Logic ---
app_last_updated = datetime.fromtimestamp(Path(__file__).stat().st_mtime).strftime("%Y-%m-%d %H:%M")
income, expenditure, assets, liabilities, cashflow, budget_performance = load_data()

# Category color maps (consistent across charts)
income_categories = sorted(income["Category"].dropna().unique())
INCOME_COLOR_MAP = build_category_color_map(
    income_categories,
    preferred={"Miscellaneous Revenue": NCA_TEAL, "Revenue from Non-Exchange": NCA_PURPLE},
)
INCOME_CATEGORY_ORDER = {"Category": income_categories}

exp_categories = sorted(expenditure["Category"].dropna().unique())
EXP_COLOR_MAP = build_category_color_map(exp_categories)
EXP_CATEGORY_ORDER = {"Category": exp_categories}

# Pre-calculate year options for filters and sidebar intelligence
all_years = sorted(
    set(income["Financial Year"].unique()) |
    set(expenditure["Financial Year"].unique()) |
    set(assets["Financial Year"].unique()) |
    set(liabilities["Financial Year"].unique()) |
    set(cashflow["Financial Year"].unique()) |
    set(budget_performance["Financial Year"].unique())
)
years_options = ["All Years"] + all_years

# Ensure session state for selection exists early for sidebar use
if 'selected_year' not in st.session_state:
    st.session_state.selected_year = years_options[-1]

# --- 4. Sidebar (NCA Branded Navigation) ---
with st.sidebar:
    st.markdown("<div class='menu-title'>NAVIGATION</div>", unsafe_allow_html=True)
    st.markdown("<div class='menu-separator'></div>", unsafe_allow_html=True)

    # Navigation logic
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Overview"


    def set_tab(name):
        st.session_state.active_tab = name


    # Navigation Menu
    nav_items = ["Overview", "Income", "Expenditure", "Assets", "Liabilities", "Cashflow", "Budget Performance"]

    for item in nav_items:
        is_active = st.session_state.active_tab == item
        st.button(
            item,
            key=f"nav_{item}",
            on_click=set_tab,
            args=(item,),
            use_container_width=True,
            type="primary" if is_active else "secondary"
        )

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Reporting Intelligence (Replaced Health Check)
    st.markdown(f"""
        <div style='background: rgba(255, 255, 255, 0.1); padding: 18px; border-radius: 18px; border: 1px solid rgba(255, 255, 255, 0.2); backdrop-filter: blur(8px);'>
            <p style='color: rgba(255, 255, 255, 0.7); font-size: 0.65rem; font-weight: 700; margin-bottom: 10px; letter-spacing: 0.12em;'>REPORTING CONTEXT</p>
            <div style='display: flex; flex-direction: column; gap: 8px;'>
                <div style='display: flex; justify-content: space-between;'>
                    <span style='color: rgba(255,255,255,0.6); font-size: 0.75rem;'>Currency</span>
                    <span style='color: white; font-size: 0.75rem; font-weight: 700;'>KES (KSh)</span>
                </div>
                <div style='display: flex; justify-content: space-between;'>
                    <span style='color: rgba(255,255,255,0.6); font-size: 0.75rem;'>Source</span>
                    <span style='color: {NCA_ORANGE}; font-size: 0.75rem; font-weight: 700;'>Audited Accounts</span>
                </div>
            </div>
            <div style='margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);'>
                 <span style='color: rgba(255,255,255,0.5); font-size: 0.65rem; font-style: italic;'>Data current as of FY {all_years[-1]}</span>
                 <div style='color: rgba(255,255,255,0.5); font-size: 0.65rem; font-style: italic; margin-top: 4px;'>Last updated on: {app_last_updated}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 5. Integrated Header & Filter Logic ---
header_logo_col, header_text_col = st.columns([1, 4])
with header_logo_col:
    try:
        st.image("assets/nca-logo.png", width=400)
    except:
        st.markdown("## NCA")
with header_text_col:
    st.markdown(
        f"<h2 class='main-header' style='text-align:left; margin-top:-6px; margin-bottom:6px;'>NATIONAL CONSTRUCTION AUTHORITY FINANCIAL ANALYSIS</h2>"
        f"<div class='main-subtitle' style='text-align:left; margin-top:-14px;'>Summary Financial Analysis over the period FY 2012/2013 - 2024/2025</div>",
        unsafe_allow_html=True)

header_col, filter_col = st.columns([1.5, 1])

with header_col:
    st.title(st.session_state.active_tab)
    st.markdown(f"Strategic Intelligence • **Operational Metrics**")

with filter_col:
    f_col1, f_col2 = st.columns(2)

    with f_col1:
        # Use session state to link selection
        selected_year = st.selectbox("Select Period", years_options,
                                     index=years_options.index(st.session_state.selected_year),
                                     label_visibility="collapsed", key="year_selector")
        st.session_state.selected_year = selected_year

    with f_col2:
        compare_years = st.multiselect(
            "Comparison",
            options=all_years,
            placeholder="Benchmarking",
            label_visibility="collapsed"
        )

# Filter Logic
comparison_mode = len(compare_years) >= 2
selected_year_effective = compare_years[0] if comparison_mode else selected_year

# Determine Base Year
latest_year = all_years[-1]
base_year = latest_year if selected_year_effective == "All Years" else selected_year_effective

# Locate previous year
try:
    current_idx = all_years.index(base_year)
    prev_year = all_years[current_idx - 1] if current_idx > 0 else None
except ValueError:
    prev_year = None


def get_prev_year(year, years_list):
    try:
        idx = years_list.index(year)
        return years_list[idx - 1] if idx > 0 else None
    except ValueError:
        return None


def get_stats(year):
    if year is None: return None
    inc = income[income["Financial Year"] == year]["Amount"].sum()
    exp = expenditure[expenditure["Financial Year"] == year]["Amount"].sum()
    ast = assets[assets["Financial Year"] == year]["Amount"].sum()
    lib = liabilities[liabilities["Financial Year"] == year]["Amount"].sum()
    return {"income": inc, "expenditure": exp, "assets": ast, "liabilities": lib, "surplus": inc - exp}


current_stats = get_stats(base_year)
previous_stats = get_stats(prev_year)

# Filtered data
show_trend = selected_year_effective == "All Years" and not comparison_mode

# For non-Overview tabs, default to current FY when "All Years" is selected
effective_year_for_tabs = latest_year if selected_year_effective == "All Years" else selected_year_effective

income_filtered = income[income["Financial Year"] == effective_year_for_tabs]
exp_filtered = expenditure[expenditure["Financial Year"] == effective_year_for_tabs]
assets_filtered = assets[assets["Financial Year"] == effective_year_for_tabs]
liab_filtered = liabilities[liabilities["Financial Year"] == effective_year_for_tabs]


# --- 6. Executive UI Helpers ---
def kpi_card(title, value, sub_value, icon_html, color=NCA_BLUE):
    st.markdown(f"""
        <div class="metric-card">
            <div class="status-bar" style="background: {color};"></div>
            <div style="float: right; width: 28px; height: 28px; opacity: 0.7;">{icon_html}</div>
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub-value">{sub_value}</div>
        </div>
    """, unsafe_allow_html=True)


def icon_svg(kind, color):
    if kind == "income":
        return f"""<svg viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2v20"/><path d="M17 7H9.5a3.5 3.5 0 0 0 0 7H14a3.5 3.5 0 0 1 0 7H6"/>
        </svg>"""
    if kind == "top":
        return f"""<svg viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 20h16"/><path d="M7 20V10"/><path d="M12 20V6"/><path d="M17 20V13"/>
        </svg>"""
    if kind == "up":
        return f"""<svg viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 16l6-6 4 4 6-8"/><path d="M14 6h6v6"/>
        </svg>"""
    if kind == "down":
        return f"""<svg viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 8l6 6 4-4 6 8"/><path d="M14 18h6v-6"/>
        </svg>"""
    return ""


def format_amount(value):
    if pd.isna(value): return "KSh 0"
    abs_val = abs(value)
    if abs_val >= 1_000_000_000: return f"KSh {value / 1_000_000_000:.2f}B"
    if abs_val >= 1_000_000: return f"KSh {value / 1_000_000:.2f}M"
    if abs_val >= 1_000: return f"KSh {value / 1_000:.1f}K"
    return f"KSh {value:,.0f}"


def format_yoy(curr, prev):
    if not prev or prev == 0: return "N/A"
    variance = ((curr - prev) / prev) * 100
    color = "#10B981" if variance >= 0 else "#F43F5E"
    arrow = "↑" if variance >= 0 else "↓"
    return f"<span style='color: {color}; font-weight: 700;'>{arrow} {abs(variance):.1f}%</span> vs Previous FY"


def apply_executive_style(fig):
    fig.update_layout(
        font_family="Inter",
        font_color="#475569",
        title_font_color=NCA_BLUE,
        title_font_size=16,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=80, b=60, l=90, r=120),
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Inter"),
        uniformtext_minsize=10,
        uniformtext_mode="show"
    )
    fig.update_xaxes(showgrid=False, tickfont=dict(size=11, color="#64748B"), automargin=True)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(203, 213, 225, 0.4)", tickfont=dict(size=11, color="#64748B"), automargin=True)
    fig.update_traces(cliponaxis=False, selector=dict(type="bar"))
    return fig


def render_comparison(title, years, chart_builder):
    st.markdown(f"### {title}")
    if len(years) < 2:
        st.info("Comparison mode: Select 2+ years in the top filter bar.")
        return
    for i in range(0, len(years), 3):
        row_years = years[i:i + 3]
        cols = st.columns(len(row_years))
        for col, year in zip(cols, row_years):
            with col:
                fig = chart_builder(year, f"FY {year}")
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"No data for {year}")


def section_header(title, subtitle=None):
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)


# --- 7. Tab Rendering ---
active = st.session_state.active_tab

if active == "Overview":
    if comparison_mode:
        st.warning("Strategic Benchmarking enabled. Cross-period analysis active.")

    st.markdown("#### Portfolio Snapshot: All Years")

    income_yearly = income.groupby("Financial Year")["Amount"].sum().sort_index()
    exp_yearly = expenditure.groupby("Financial Year")["Amount"].sum().sort_index()
    assets_yearly = assets.groupby("Financial Year")["Amount"].sum().sort_index()
    liab_yearly = liabilities.groupby("Financial Year")["Amount"].sum().sort_index()
    surplus_yearly = income_yearly.subtract(exp_yearly, fill_value=0)

    total_income_all = income_yearly.sum()
    total_exp_all = exp_yearly.sum()
    avg_surplus = surplus_yearly.mean() if not surplus_yearly.empty else 0

    def calc_cagr(series):
        if series is None or series.empty:
            return None
        start = series.iloc[0]
        end = series.iloc[-1]
        periods = max(len(series) - 1, 0)
        if start <= 0 or periods == 0:
            return None
        return (end / start) ** (1 / periods) - 1

    income_cagr = calc_cagr(income_yearly)
    exp_cagr = calc_cagr(exp_yearly)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card(
            "Total Revenue",
            format_amount(total_income_all),
            "All Fiscal Years",
            icon_svg("income", NCA_BLUE)
        )
    with col2:
        kpi_card(
            "Total Expenditure",
            format_amount(total_exp_all),
            "All Fiscal Years",
            icon_svg("down", NCA_ORANGE),
            NCA_ORANGE
        )
    with col3:
        kpi_card(
            "Avg Annual Surplus",
            format_amount(avg_surplus),
            f"FY {all_years[0]} - {all_years[-1]}",
            icon_svg("top", NCA_TEAL),
            NCA_TEAL
        )
    with col4:
        cagr_label = "N/A" if income_cagr is None else f"{income_cagr * 100:.1f}% CAGR"
        kpi_card(
            "Revenue Growth",
            cagr_label,
            "Across period",
            icon_svg("up", NCA_PURPLE),
            NCA_PURPLE
        )

    coverage_series = assets_yearly.divide(liab_yearly.replace(0, pd.NA))
    latest_coverage = coverage_series.get(latest_year, pd.NA)
    avg_coverage = coverage_series.dropna().mean() if coverage_series is not None else pd.NA

    cov_col1, cov_col2 = st.columns(2)
    with cov_col1:
        kpi_card(
            "Debt Coverage (Latest FY)",
            f"{latest_coverage:.2f}x" if pd.notna(latest_coverage) else "N/A",
            f"FY {latest_year}",
            icon_svg("top", NCA_TEAL),
            NCA_TEAL
        )
    with cov_col2:
        kpi_card(
            "Avg Coverage (All Years)",
            f"{avg_coverage:.2f}x" if pd.notna(avg_coverage) else "N/A",
            "Assets / Liabilities",
            icon_svg("top", NCA_BLUE),
            NCA_BLUE
        )

    st.markdown("---")
    st.markdown("#### Revenue and Expenditure Trend")
    overview_trend = pd.DataFrame({
        "Financial Year": income_yearly.index,
        "Income": income_yearly.values,
        "Expenditure": exp_yearly.reindex(income_yearly.index).fillna(0).values
    })
    fig_ie = px.line(
        overview_trend,
        x="Financial Year",
        y=["Income", "Expenditure"],
        title="Revenue vs Expenditure (All Years)",
        markers=True,
        color_discrete_map={"Income": NCA_BLUE, "Expenditure": NCA_ORANGE}
    )
    st.plotly_chart(apply_executive_style(fig_ie), use_container_width=True)

    st.markdown("#### Balance Sheet Trend")
    assets_trend = pd.DataFrame({
        "Financial Year": assets_yearly.index,
        "Assets": assets_yearly.values,
        "Liabilities": liab_yearly.reindex(assets_yearly.index).fillna(0).values
    })
    fig_al = px.line(
        assets_trend,
        x="Financial Year",
        y=["Assets", "Liabilities"],
        title="Assets vs Liabilities (All Years)",
        markers=True,
        color_discrete_map={"Assets": NCA_BLUE, "Liabilities": NCA_ORANGE}
    )
    st.plotly_chart(apply_executive_style(fig_al), use_container_width=True)

    st.markdown("#### Surplus Trajectory")
    surplus_df = pd.DataFrame({
        "Financial Year": surplus_yearly.index,
        "Surplus": surplus_yearly.values
    })
    fig_surplus = px.bar(
        surplus_df,
        x="Financial Year",
        y="Surplus",
        title="Annual Surplus (Income - Expenditure)",
        color_discrete_sequence=[NCA_TEAL]
    )
    st.plotly_chart(apply_executive_style(fig_surplus), use_container_width=True)

elif active == "Income":
    if comparison_mode:
        section_header("Revenue Comparison", "Side-by-side FY distributions and top sub-categories.")
        for i in range(0, len(compare_years), 3):
            row_years = compare_years[i:i + 3]
            cols = st.columns(len(row_years))
            for col, year in zip(cols, row_years):
                with col:
                    st.markdown(f"**FY {year}**")
                    income_year = income[income["Financial Year"] == year]
                    data = income_year.groupby("Category")["Amount"].sum().reset_index()
                    fig = px.pie(
                        data,
                        names="Category",
                        values="Amount",
                        hole=0.6,
                        color_discrete_map=INCOME_COLOR_MAP,
                        category_orders=INCOME_CATEGORY_ORDER,
                        title=f"Income Distribution - {year}"
                    )
                    st.plotly_chart(apply_executive_style(fig), use_container_width=True)

                    income_subcat = income_year.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
                    income_subcat = income_subcat[income_subcat["Amount"] > 0]
                    income_subcat = income_subcat.sort_values(["Category", "Amount"], ascending=[True, False]) \
                                                 .groupby("Category", as_index=False).head(3)
                    if not income_subcat.empty:
                        income_subcat["Label"] = income_subcat["SubCategory"]
                        income_subcat["AmountLabel"] = income_subcat["Amount"].apply(
                            lambda v: f"{v / 1_000_000_000:.2f}B" if abs(v) >= 1_000_000_000 else f"{v / 1_000_000:.2f}M"
                        )
                        fig_bar = px.bar(
                            income_subcat.sort_values("Amount"),
                            x="Amount",
                            y="Label",
                            color="Category",
                            orientation="h",
                            color_discrete_map=INCOME_COLOR_MAP,
                            category_orders=INCOME_CATEGORY_ORDER,
                            text="AmountLabel",
                            title="Revenue by Sub-Category (Top Earners)"
                        )
                        fig_bar.update_traces(texttemplate="%{text}", textposition="outside")
                        fig_bar.update_layout(showlegend=False)
                        fig_bar.update_layout(yaxis_title="", xaxis_title="Amount")
                        st.plotly_chart(apply_executive_style(fig_bar), use_container_width=True)
    else:
        income_prev_year = get_prev_year(effective_year_for_tabs, all_years)
        income_prev_df = income[income["Financial Year"] == income_prev_year] if income_prev_year else pd.DataFrame()
        income_curr_total = income_filtered["Amount"].sum()
        income_prev_total = income_prev_df["Amount"].sum() if not income_prev_df.empty else None

        income_cat = income_filtered.groupby(["Category"])["Amount"].sum().reset_index()
        prev_cat = (
            income_prev_df.groupby(["Category"])["Amount"].sum().reset_index()
            if not income_prev_df.empty else pd.DataFrame(columns=["Category", "Amount"])
        )

        top_cat_label = None
        top_cat_amount = None
        top_cat_prev_amount = None
        if not income_cat.empty:
            top_cat_row = income_cat.sort_values("Amount", ascending=False).iloc[0]
            top_cat_label = f"{top_cat_row['Category']}"
            top_cat_amount = top_cat_row["Amount"]
            if not prev_cat.empty:
                top_cat_prev_amount = prev_cat[prev_cat["Category"] == top_cat_row["Category"]]["Amount"].sum()

        income_subcat = income_filtered.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
        prev_subcat = (
            income_prev_df.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
            if not income_prev_df.empty else pd.DataFrame(columns=["Category", "SubCategory", "Amount"])
        )

        subcat_delta = None
        if not income_subcat.empty and not prev_subcat.empty:
            subcat_delta = income_subcat.merge(
                prev_subcat, on=["Category", "SubCategory"], how="left", suffixes=("_curr", "_prev")
            )
            subcat_delta["Amount_prev"] = subcat_delta["Amount_prev"].fillna(0)
            subcat_delta["Delta"] = subcat_delta["Amount_curr"] - subcat_delta["Amount_prev"]

        largest_increase_label = None
        largest_increase_curr = None
        largest_increase_prev = None
        largest_decrease_label = None
        largest_decrease_curr = None
        largest_decrease_prev = None

        if subcat_delta is not None and not subcat_delta.empty:
            inc_row = subcat_delta.sort_values("Delta", ascending=False).iloc[0]
            largest_increase_label = f"{inc_row['SubCategory']}"
            largest_increase_curr = inc_row["Amount_curr"]
            largest_increase_prev = inc_row["Amount_prev"]

            dec_row = subcat_delta.sort_values("Delta", ascending=True).iloc[0]
            largest_decrease_label = f"{dec_row['SubCategory']}"
            largest_decrease_curr = dec_row["Amount_curr"]
            largest_decrease_prev = dec_row["Amount_prev"]

        st.markdown(f"#### FY Snapshot: {effective_year_for_tabs}")
        kpi_cols = st.columns(4)
        with kpi_cols[0]:
            kpi_card(
                "Income",
                format_amount(income_curr_total),
                f"Overall<br>{format_yoy(income_curr_total, income_prev_total)}",
                icon_svg("income", NCA_BLUE)
            )
        with kpi_cols[1]:
            kpi_card(
                "Top Category",
                format_amount(top_cat_amount) if top_cat_amount is not None else "N/A",
                f"{top_cat_label}<br>{format_yoy(top_cat_amount, top_cat_prev_amount)}" if top_cat_label else "N/A",
                icon_svg("top", NCA_TEAL),
                NCA_TEAL
            )
        with kpi_cols[2]:
            kpi_card(
                "Largest Increase",
                format_amount(largest_increase_curr - largest_increase_prev) if largest_increase_label else "N/A",
                f"{largest_increase_label}<br>{format_yoy(largest_increase_curr, largest_increase_prev)}" if largest_increase_label else "N/A",
                icon_svg("up", NCA_PURPLE),
                NCA_PURPLE
            )
        with kpi_cols[3]:
            kpi_card(
                "Largest Decrease",
                format_amount(largest_decrease_curr - largest_decrease_prev) if largest_decrease_label else "N/A",
                f"{largest_decrease_label}<br>{format_yoy(largest_decrease_curr, largest_decrease_prev)}" if largest_decrease_label else "N/A",
                icon_svg("down", NCA_ORANGE),
                NCA_ORANGE
            )

        section_header("FY Distribution", f"Distribution and top sub-categories for FY {effective_year_for_tabs}.")
        snap_left, snap_right = st.columns(2)
        with snap_left:
            data = income_filtered.groupby("Category")["Amount"].sum().reset_index()
            fig = px.pie(data, names="Category", values="Amount", hole=0.6,
                         color_discrete_map=INCOME_COLOR_MAP,
                         category_orders=INCOME_CATEGORY_ORDER,
                         title=f"Income Distribution - {effective_year_for_tabs}")
            st.plotly_chart(apply_executive_style(fig), use_container_width=True)

        with snap_right:
            income_subcat = income_filtered.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
            income_subcat = income_subcat[income_subcat["Amount"] > 0]
            income_subcat = income_subcat.sort_values(["Category", "Amount"], ascending=[True, False]) \
                                         .groupby("Category", as_index=False).head(3)
            if not income_subcat.empty:
                income_subcat["Label"] = income_subcat["SubCategory"]
                income_subcat["AmountLabel"] = income_subcat["Amount"].apply(
                    lambda v: f"{v / 1_000_000_000:.2f}B" if abs(v) >= 1_000_000_000 else f"{v / 1_000_000:.2f}M"
                )
                fig_bar = px.bar(
                    income_subcat.sort_values("Amount"),
                    x="Amount",
                    y="Label",
                    color="Category",
                    orientation="h",
                    color_discrete_map=INCOME_COLOR_MAP,
                    category_orders=INCOME_CATEGORY_ORDER,
                    text="AmountLabel",
                    title="Revenue by Sub-Category (Top Earners)"
                )
                fig_bar.update_traces(texttemplate="%{text}", textposition="outside")
                fig_bar.update_layout(showlegend=False)
                fig_bar.update_layout(yaxis_title="", xaxis_title="Amount")
                st.plotly_chart(apply_executive_style(fig_bar), use_container_width=True)

        st.markdown("---")
        section_header("Trend Explorer", "Compare categories or sub-categories across the full time period.")
        trend_col1, trend_col2 = st.columns([1, 2])
        with trend_col1:
            trend_level = st.selectbox(
                "Trend Level",
                ["Category", "Sub-Category"],
                key="income_trend_level"
            )
        with trend_col2:
            if trend_level == "Category":
                trend_source = income.dropna(subset=["Category"])
                trend_items = sorted(trend_source["Category"].unique())
                trend_data = trend_source.groupby(["Financial Year", "Category"])["Amount"].sum().reset_index()
                trend_data["Item"] = trend_data["Category"]
                default_items = (
                    trend_source.groupby("Category")["Amount"].sum()
                    .sort_values(ascending=False).head(3).index.tolist()
                )
                color_map = {item: INCOME_COLOR_MAP.get(item, NCA_BLUE) for item in trend_items}
            else:
                trend_source = income.dropna(subset=["Category", "SubCategory"]).copy()
                trend_source["Item"] = trend_source["Category"].astype(str) + " - " + trend_source["SubCategory"].astype(str)
                trend_items = sorted(trend_source["Item"].unique())
                trend_data = trend_source.groupby(["Financial Year", "Item"])["Amount"].sum().reset_index()
                default_items = (
                    trend_source.groupby("Item")["Amount"].sum()
                    .sort_values(ascending=False).head(4).index.tolist()
                )
                palette = px.colors.qualitative.Safe
                color_map = {item: palette[i % len(palette)] for i, item in enumerate(trend_items)}

            selected_items = st.multiselect(
                "Compare Items (add multiple)",
                options=trend_items,
                default=default_items,
                key="income_trend_items"
            )

        if selected_items:
            trend_filtered = trend_data[trend_data["Item"].isin(selected_items)]
            fig_trend = px.line(
                trend_filtered,
                x="Financial Year",
                y="Amount",
                color="Item",
                markers=True,
                color_discrete_map=color_map,
                title="Income Trend Over Time"
            )
            st.plotly_chart(apply_executive_style(fig_trend), use_container_width=True)
        else:
            st.info("Select at least one item to view the trend.")

        st.markdown("---")
        section_header("Income Detail Table", f"Category and sub-category snapshot for FY {effective_year_for_tabs}.")
        income_table = income_filtered.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
        income_table = income_table.sort_values(["Category", "Amount"], ascending=[True, False])
        st.dataframe(income_table, use_container_width=True)
        csv_income = income_table.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Income Snapshot (CSV)",
            data=csv_income,
            file_name=f"income_snapshot_FY_{effective_year_for_tabs}.csv",
            mime="text/csv",
            use_container_width=False
        )

elif active == "Expenditure":
    if not comparison_mode:
        exp_prev_year = get_prev_year(effective_year_for_tabs, all_years)
        exp_prev_df = expenditure[expenditure["Financial Year"] == exp_prev_year] if exp_prev_year else pd.DataFrame()
        exp_curr_total = exp_filtered["Amount"].sum()
        exp_prev_total = exp_prev_df["Amount"].sum() if not exp_prev_df.empty else None

        exp_cat = exp_filtered.groupby(["Category"])["Amount"].sum().reset_index()
        prev_exp_cat = (
            exp_prev_df.groupby(["Category"])["Amount"].sum().reset_index()
            if not exp_prev_df.empty else pd.DataFrame(columns=["Category", "Amount"])
        )

        top_exp_cat_label = None
        top_exp_cat_amount = None
        top_exp_cat_prev_amount = None
        if not exp_cat.empty:
            top_exp_cat_row = exp_cat.sort_values("Amount", ascending=False).iloc[0]
            top_exp_cat_label = f"{top_exp_cat_row['Category']}"
            top_exp_cat_amount = top_exp_cat_row["Amount"]
            if not prev_exp_cat.empty:
                top_exp_cat_prev_amount = prev_exp_cat[prev_exp_cat["Category"] == top_exp_cat_row["Category"]]["Amount"].sum()

        exp_subcat = exp_filtered.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
        prev_exp_subcat = (
            exp_prev_df.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
            if not exp_prev_df.empty else pd.DataFrame(columns=["Category", "SubCategory", "Amount"])
        )

        exp_subcat_delta = None
        if not exp_subcat.empty and not prev_exp_subcat.empty:
            exp_subcat_delta = exp_subcat.merge(
                prev_exp_subcat, on=["Category", "SubCategory"], how="left", suffixes=("_curr", "_prev")
            )
            exp_subcat_delta["Amount_prev"] = exp_subcat_delta["Amount_prev"].fillna(0)
            exp_subcat_delta["Delta"] = exp_subcat_delta["Amount_curr"] - exp_subcat_delta["Amount_prev"]

        exp_largest_increase_label = None
        exp_largest_increase_curr = None
        exp_largest_increase_prev = None
        exp_largest_decrease_label = None
        exp_largest_decrease_curr = None
        exp_largest_decrease_prev = None

        if exp_subcat_delta is not None and not exp_subcat_delta.empty:
            inc_row = exp_subcat_delta.sort_values("Delta", ascending=False).iloc[0]
            exp_largest_increase_label = f"{inc_row['SubCategory']}"
            exp_largest_increase_curr = inc_row["Amount_curr"]
            exp_largest_increase_prev = inc_row["Amount_prev"]

            dec_row = exp_subcat_delta.sort_values("Delta", ascending=True).iloc[0]
            exp_largest_decrease_label = f"{dec_row['SubCategory']}"
            exp_largest_decrease_curr = dec_row["Amount_curr"]
            exp_largest_decrease_prev = dec_row["Amount_prev"]

        st.markdown(f"#### FY Snapshot: {effective_year_for_tabs}")
        exp_kpi_cols = st.columns(4)
        with exp_kpi_cols[0]:
            kpi_card(
                "Expenditure",
                format_amount(exp_curr_total),
                f"Overall<br>{format_yoy(exp_curr_total, exp_prev_total)}",
                icon_svg("down", NCA_ORANGE),
                NCA_ORANGE
            )
        with exp_kpi_cols[1]:
            kpi_card(
                "Top Category",
                format_amount(top_exp_cat_amount) if top_exp_cat_amount is not None else "N/A",
                f"{top_exp_cat_label}<br>{format_yoy(top_exp_cat_amount, top_exp_cat_prev_amount)}" if top_exp_cat_label else "N/A",
                icon_svg("top", NCA_TEAL),
                NCA_TEAL
            )
        with exp_kpi_cols[2]:
            kpi_card(
                "Largest Increase",
                format_amount(exp_largest_increase_curr - exp_largest_increase_prev) if exp_largest_increase_label else "N/A",
                f"{exp_largest_increase_label}<br>{format_yoy(exp_largest_increase_curr, exp_largest_increase_prev)}" if exp_largest_increase_label else "N/A",
                icon_svg("up", NCA_PURPLE),
                NCA_PURPLE
            )
        with exp_kpi_cols[3]:
            kpi_card(
                "Largest Decrease",
                format_amount(exp_largest_decrease_curr - exp_largest_decrease_prev) if exp_largest_decrease_label else "N/A",
                f"{exp_largest_decrease_label}<br>{format_yoy(exp_largest_decrease_curr, exp_largest_decrease_prev)}" if exp_largest_decrease_label else "N/A",
                icon_svg("down", NCA_ORANGE),
                NCA_ORANGE
            )

        section_header("FY Distribution", f"Distribution and top sub-categories for FY {effective_year_for_tabs}.")
        snap_left, snap_right = st.columns(2)
        with snap_left:
            fig_exp = px.pie(exp_filtered.groupby("Category")["Amount"].sum().reset_index(),
                             names="Category", values="Amount", hole=0.6, title=f"Operational Spend - {effective_year_for_tabs}",
                             color_discrete_map=EXP_COLOR_MAP,
                             category_orders=EXP_CATEGORY_ORDER)
            st.plotly_chart(apply_executive_style(fig_exp), use_container_width=True)

        with snap_right:
            exp_subcat = exp_filtered.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
            exp_subcat = exp_subcat[exp_subcat["Amount"] > 0]
            exp_subcat = exp_subcat.sort_values("Amount", ascending=False).head(15)
            if not exp_subcat.empty:
                exp_subcat["Label"] = exp_subcat["SubCategory"]
                exp_subcat["AmountLabel"] = exp_subcat["Amount"].apply(
                    lambda v: f"{v / 1_000_000_000:.2f}B" if abs(v) >= 1_000_000_000 else f"{v / 1_000_000:.2f}M"
                )
                exp_subcat_sorted = exp_subcat.sort_values("Amount", ascending=False)
                fig_exp_sub = px.bar(
                    exp_subcat_sorted,
                    x="Amount",
                    y="Label",
                    color="Category",
                    orientation="h",
                    color_discrete_map=EXP_COLOR_MAP,
                    category_orders=EXP_CATEGORY_ORDER,
                    text="AmountLabel",
                    title="Expenditure by Sub-Category (Top Spend)"
                )
                fig_exp_sub.update_traces(texttemplate="%{text}", textposition="outside")
                fig_exp_sub.update_layout(showlegend=False)
                fig_exp_sub.update_layout(
                    yaxis_title="",
                    xaxis_title="Amount",
                    yaxis=dict(categoryorder="array", categoryarray=exp_subcat_sorted["Label"].tolist(), autorange="reversed"),
                    margin=dict(l=80, r=80, t=80, b=60)
                )
                st.plotly_chart(apply_executive_style(fig_exp_sub), use_container_width=True)

        st.markdown("---")
        section_header("Trend Explorer", "Compare categories or sub-categories across the full time period.")
        trend_col1, trend_col2 = st.columns([1, 2])
        with trend_col1:
            trend_level = st.selectbox(
                "Trend Level",
                ["Category", "Sub-Category"],
                key="exp_trend_level"
            )
        with trend_col2:
            if trend_level == "Category":
                trend_source = expenditure.dropna(subset=["Category"])
                trend_items = sorted(trend_source["Category"].unique())
                trend_data = trend_source.groupby(["Financial Year", "Category"])["Amount"].sum().reset_index()
                trend_data["Item"] = trend_data["Category"]
                default_items = (
                    trend_source.groupby("Category")["Amount"].sum()
                    .sort_values(ascending=False).head(3).index.tolist()
                )
                color_map = {item: EXP_COLOR_MAP.get(item, NCA_BLUE) for item in trend_items}
            else:
                trend_source = expenditure.dropna(subset=["Category", "SubCategory"]).copy()
                trend_source["Item"] = trend_source["Category"].astype(str) + " - " + trend_source["SubCategory"].astype(str)
                trend_items = sorted(trend_source["Item"].unique())
                trend_data = trend_source.groupby(["Financial Year", "Item"])["Amount"].sum().reset_index()
                default_items = (
                    trend_source.groupby("Item")["Amount"].sum()
                    .sort_values(ascending=False).head(4).index.tolist()
                )
                palette = px.colors.qualitative.Safe
                color_map = {item: palette[i % len(palette)] for i, item in enumerate(trend_items)}

            selected_items = st.multiselect(
                "Compare Items (add multiple)",
                options=trend_items,
                default=default_items,
                key="exp_trend_items"
            )

        if selected_items:
            trend_filtered = trend_data[trend_data["Item"].isin(selected_items)]
            fig_trend = px.line(
                trend_filtered,
                x="Financial Year",
                y="Amount",
                color="Item",
                markers=True,
                color_discrete_map=color_map,
                title="Expenditure Trend Over Time"
            )
            st.plotly_chart(apply_executive_style(fig_trend), use_container_width=True)
        else:
            st.info("Select at least one item to view the trend.")

        st.markdown("---")
        section_header("Expenditure Detail Table", f"Category and sub-category snapshot for FY {effective_year_for_tabs}.")
        exp_table = exp_filtered.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
        exp_table = exp_table.sort_values(["Category", "Amount"], ascending=[True, False])
        st.dataframe(exp_table, use_container_width=True)
        csv_exp = exp_table.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Expenditure Snapshot (CSV)",
            data=csv_exp,
            file_name=f"expenditure_snapshot_FY_{effective_year_for_tabs}.csv",
            mime="text/csv",
            use_container_width=False
        )

    if comparison_mode:
        section_header("Expenditure Benchmarking", "Side-by-side FY distributions and top sub-categories.")
        for i in range(0, len(compare_years), 3):
            row_years = compare_years[i:i + 3]
            cols = st.columns(len(row_years))
            for col, year in zip(cols, row_years):
                with col:
                    st.markdown(f"**FY {year}**")
                    exp_year = expenditure[expenditure["Financial Year"] == year]
                    fig_exp = px.pie(
                        exp_year.groupby("Category")["Amount"].sum().reset_index(),
                        names="Category",
                        values="Amount",
                        hole=0.6,
                        title=f"Operational Spend - {year}",
                        color_discrete_map=EXP_COLOR_MAP,
                        category_orders=EXP_CATEGORY_ORDER
                    )
                    st.plotly_chart(apply_executive_style(fig_exp), use_container_width=True)

                    exp_subcat = exp_year.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
                    exp_subcat = exp_subcat[exp_subcat["Amount"] > 0]
                    exp_subcat = exp_subcat.sort_values("Amount", ascending=False).head(15)
                    if not exp_subcat.empty:
                        exp_subcat["Label"] = exp_subcat["SubCategory"]
                        exp_subcat["AmountLabel"] = exp_subcat["Amount"].apply(
                            lambda v: f"{v / 1_000_000_000:.2f}B" if abs(v) >= 1_000_000_000 else f"{v / 1_000_000:.2f}M"
                        )
                        exp_subcat_sorted = exp_subcat.sort_values("Amount", ascending=False)
                        fig_exp_sub = px.bar(
                            exp_subcat_sorted,
                            x="Amount",
                            y="Label",
                            color="Category",
                            orientation="h",
                            color_discrete_map=EXP_COLOR_MAP,
                            category_orders=EXP_CATEGORY_ORDER,
                            text="AmountLabel",
                            title="Expenditure by Sub-Category (Top Spend)"
                        )
                        fig_exp_sub.update_traces(texttemplate="%{text}", textposition="outside")
                        fig_exp_sub.update_layout(showlegend=False)
                        fig_exp_sub.update_layout(
                            yaxis_title="",
                            xaxis_title="Amount",
                            yaxis=dict(categoryorder="array", categoryarray=exp_subcat_sorted["Label"].tolist(), autorange="reversed"),
                            margin=dict(l=80, r=80, t=80, b=60)
                        )
                        st.plotly_chart(apply_executive_style(fig_exp_sub), use_container_width=True)

elif active == "Assets":
    if not comparison_mode:
        asset_prev_year = get_prev_year(effective_year_for_tabs, all_years)
        asset_prev_df = assets[assets["Financial Year"] == asset_prev_year] if asset_prev_year else pd.DataFrame()
        asset_curr_total = assets_filtered["Amount"].sum()
        asset_prev_total = asset_prev_df["Amount"].sum() if not asset_prev_df.empty else None

        asset_cat = assets_filtered.groupby(["Category"])["Amount"].sum().reset_index()
        prev_asset_cat = (
            asset_prev_df.groupby(["Category"])["Amount"].sum().reset_index()
            if not asset_prev_df.empty else pd.DataFrame(columns=["Category", "Amount"])
        )

        top_asset_cat_label = None
        top_asset_cat_amount = None
        top_asset_cat_prev_amount = None
        if not asset_cat.empty:
            top_asset_cat_row = asset_cat.sort_values("Amount", ascending=False).iloc[0]
            top_asset_cat_label = f"{top_asset_cat_row['Category']}"
            top_asset_cat_amount = top_asset_cat_row["Amount"]
            if not prev_asset_cat.empty:
                top_asset_cat_prev_amount = prev_asset_cat[prev_asset_cat["Category"] == top_asset_cat_row["Category"]]["Amount"].sum()

        asset_subcat = assets_filtered.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
        prev_asset_subcat = (
            asset_prev_df.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
            if not asset_prev_df.empty else pd.DataFrame(columns=["Category", "SubCategory", "Amount"])
        )

        asset_subcat_delta = None
        if not asset_subcat.empty and not prev_asset_subcat.empty:
            asset_subcat_delta = asset_subcat.merge(
                prev_asset_subcat, on=["Category", "SubCategory"], how="left", suffixes=("_curr", "_prev")
            )
            asset_subcat_delta["Amount_prev"] = asset_subcat_delta["Amount_prev"].fillna(0)
            asset_subcat_delta["Delta"] = asset_subcat_delta["Amount_curr"] - asset_subcat_delta["Amount_prev"]

        asset_largest_increase_label = None
        asset_largest_increase_curr = None
        asset_largest_increase_prev = None
        asset_largest_decrease_label = None
        asset_largest_decrease_curr = None
        asset_largest_decrease_prev = None

        if asset_subcat_delta is not None and not asset_subcat_delta.empty:
            inc_row = asset_subcat_delta.sort_values("Delta", ascending=False).iloc[0]
            asset_largest_increase_label = f"{inc_row['SubCategory']}"
            asset_largest_increase_curr = inc_row["Amount_curr"]
            asset_largest_increase_prev = inc_row["Amount_prev"]

            dec_row = asset_subcat_delta.sort_values("Delta", ascending=True).iloc[0]
            asset_largest_decrease_label = f"{dec_row['SubCategory']}"
            asset_largest_decrease_curr = dec_row["Amount_curr"]
            asset_largest_decrease_prev = dec_row["Amount_prev"]

        st.markdown(f"#### FY Snapshot: {effective_year_for_tabs}")
        asset_kpi_cols = st.columns(4)
        with asset_kpi_cols[0]:
            kpi_card(
                "Assets",
                format_amount(asset_curr_total),
                f"Overall<br>{format_yoy(asset_curr_total, asset_prev_total)}",
                icon_svg("top", NCA_BLUE),
                NCA_BLUE
            )
        with asset_kpi_cols[1]:
            kpi_card(
                "Top Category",
                format_amount(top_asset_cat_amount) if top_asset_cat_amount is not None else "N/A",
                f"{top_asset_cat_label}<br>{format_yoy(top_asset_cat_amount, top_asset_cat_prev_amount)}" if top_asset_cat_label else "N/A",
                icon_svg("top", NCA_TEAL),
                NCA_TEAL
            )
        with asset_kpi_cols[2]:
            kpi_card(
                "Largest Increase",
                format_amount(asset_largest_increase_curr - asset_largest_increase_prev) if asset_largest_increase_label else "N/A",
                f"{asset_largest_increase_label}<br>{format_yoy(asset_largest_increase_curr, asset_largest_increase_prev)}" if asset_largest_increase_label else "N/A",
                icon_svg("up", NCA_PURPLE),
                NCA_PURPLE
            )
        with asset_kpi_cols[3]:
            kpi_card(
                "Largest Decrease",
                format_amount(asset_largest_decrease_curr - asset_largest_decrease_prev) if asset_largest_decrease_label else "N/A",
                f"{asset_largest_decrease_label}<br>{format_yoy(asset_largest_decrease_curr, asset_largest_decrease_prev)}" if asset_largest_decrease_label else "N/A",
                icon_svg("down", NCA_ORANGE),
                NCA_ORANGE
            )

        section_header("FY Distribution", f"Distribution and top sub-categories for FY {effective_year_for_tabs}.")
        snap_left, snap_right = st.columns(2)
        with snap_left:
            asset_cat = assets_filtered.groupby("Category")["Amount"].sum().reset_index()
            fig_assets = px.pie(
                asset_cat,
                names="Category",
                values="Amount",
                hole=0.6,
                title=f"Asset Categories - {effective_year_for_tabs}",
                color_discrete_map=EXP_COLOR_MAP,
                category_orders=EXP_CATEGORY_ORDER,
            )
            st.plotly_chart(apply_executive_style(fig_assets), use_container_width=True)

        with snap_right:
            asset_subcat = assets_filtered.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
            asset_subcat = asset_subcat[asset_subcat["Amount"] > 0]
            asset_subcat = asset_subcat.sort_values("Amount", ascending=False).head(15)
            if not asset_subcat.empty:
                asset_subcat["Label"] = asset_subcat["SubCategory"]
                asset_subcat["AmountLabel"] = asset_subcat["Amount"].apply(
                    lambda v: f"{v / 1_000_000_000:.2f}B" if abs(v) >= 1_000_000_000 else f"{v / 1_000_000:.2f}M"
                )
                asset_subcat_sorted = asset_subcat.sort_values("Amount", ascending=False)
                fig_asset_sub = px.bar(
                    asset_subcat_sorted,
                    x="Amount",
                    y="Label",
                    color="Category",
                    orientation="h",
                    color_discrete_map=EXP_COLOR_MAP,
                    category_orders=EXP_CATEGORY_ORDER,
                    text="AmountLabel",
                    title="Assets by Sub-Category (Top Holdings)"
                )
                fig_asset_sub.update_traces(texttemplate="%{text}", textposition="outside")
                fig_asset_sub.update_layout(showlegend=False)
                fig_asset_sub.update_layout(
                    yaxis_title="",
                    xaxis_title="Amount",
                    yaxis=dict(categoryorder="array", categoryarray=asset_subcat_sorted["Label"].tolist(), autorange="reversed"),
                    margin=dict(l=80, r=80, t=80, b=60)
                )
                st.plotly_chart(apply_executive_style(fig_asset_sub), use_container_width=True)

        st.markdown("---")
        section_header("Trend Explorer", "Compare categories or sub-categories across the full time period.")
        trend_col1, trend_col2 = st.columns([1, 2])
        with trend_col1:
            trend_level = st.selectbox(
                "Trend Level",
                ["Category", "Sub-Category"],
                key="asset_trend_level"
            )
        with trend_col2:
            if trend_level == "Category":
                trend_source = assets.dropna(subset=["Category"])
                trend_items = sorted(trend_source["Category"].unique())
                trend_data = trend_source.groupby(["Financial Year", "Category"])["Amount"].sum().reset_index()
                trend_data["Item"] = trend_data["Category"]
                default_items = (
                    trend_source.groupby("Category")["Amount"].sum()
                    .sort_values(ascending=False).head(3).index.tolist()
                )
                color_map = {item: EXP_COLOR_MAP.get(item, NCA_BLUE) for item in trend_items}
            else:
                trend_source = assets.dropna(subset=["Category", "SubCategory"]).copy()
                trend_source["Item"] = trend_source["Category"].astype(str) + " - " + trend_source["SubCategory"].astype(str)
                trend_items = sorted(trend_source["Item"].unique())
                trend_data = trend_source.groupby(["Financial Year", "Item"])["Amount"].sum().reset_index()
                default_items = (
                    trend_source.groupby("Item")["Amount"].sum()
                    .sort_values(ascending=False).head(4).index.tolist()
                )
                palette = px.colors.qualitative.Safe
                color_map = {item: palette[i % len(palette)] for i, item in enumerate(trend_items)}

            selected_items = st.multiselect(
                "Compare Items (add multiple)",
                options=trend_items,
                default=default_items,
                key="asset_trend_items"
            )

        if selected_items:
            trend_filtered = trend_data[trend_data["Item"].isin(selected_items)]
            fig_trend = px.line(
                trend_filtered,
                x="Financial Year",
                y="Amount",
                color="Item",
                markers=True,
                color_discrete_map=color_map,
                title="Assets Trend Over Time"
            )
            st.plotly_chart(apply_executive_style(fig_trend), use_container_width=True)
        else:
            st.info("Select at least one item to view the trend.")

        st.markdown("---")
        section_header("Assets Detail Table", f"Category and sub-category snapshot for FY {effective_year_for_tabs}.")
        asset_table = assets_filtered.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
        asset_table = asset_table.sort_values(["Category", "Amount"], ascending=[True, False])
        st.dataframe(asset_table, use_container_width=True)
        csv_assets = asset_table.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Assets Snapshot (CSV)",
            data=csv_assets,
            file_name=f"assets_snapshot_FY_{effective_year_for_tabs}.csv",
            mime="text/csv",
            use_container_width=False
        )

    if comparison_mode:
        section_header("Asset Comparison", "Side-by-side FY distributions and top sub-categories.")
        for i in range(0, len(compare_years), 3):
            row_years = compare_years[i:i + 3]
            cols = st.columns(len(row_years))
            for col, year in zip(cols, row_years):
                with col:
                    st.markdown(f"**FY {year}**")
                    assets_year = assets[assets["Financial Year"] == year]
                    asset_cat = assets_year.groupby("Category")["Amount"].sum().reset_index()
                    fig_assets = px.pie(
                        asset_cat,
                        names="Category",
                        values="Amount",
                        hole=0.6,
                        title=f"Asset Categories - {year}",
                        color_discrete_map=EXP_COLOR_MAP,
                        category_orders=EXP_CATEGORY_ORDER,
                    )
                    st.plotly_chart(apply_executive_style(fig_assets), use_container_width=True)

                    asset_subcat = assets_year.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
                    asset_subcat = asset_subcat[asset_subcat["Amount"] > 0]
                    asset_subcat = asset_subcat.sort_values("Amount", ascending=False).head(15)
                    if not asset_subcat.empty:
                        asset_subcat["Label"] = asset_subcat["SubCategory"]
                        asset_subcat["AmountLabel"] = asset_subcat["Amount"].apply(
                            lambda v: f"{v / 1_000_000_000:.2f}B" if abs(v) >= 1_000_000_000 else f"{v / 1_000_000:.2f}M"
                        )
                        asset_subcat_sorted = asset_subcat.sort_values("Amount", ascending=False)
                        fig_asset_sub = px.bar(
                            asset_subcat_sorted,
                            x="Amount",
                            y="Label",
                            color="Category",
                            orientation="h",
                            color_discrete_map=EXP_COLOR_MAP,
                            category_orders=EXP_CATEGORY_ORDER,
                            text="AmountLabel",
                            title="Assets by Sub-Category (Top Holdings)"
                        )
                        fig_asset_sub.update_traces(texttemplate="%{text}", textposition="outside")
                        fig_asset_sub.update_layout(
                            showlegend=False,
                            yaxis_title="",
                            xaxis_title="Amount",
                            yaxis=dict(categoryorder="array", categoryarray=asset_subcat_sorted["Label"].tolist(), autorange="reversed"),
                            margin=dict(l=80, r=80, t=80, b=60)
                        )
                        st.plotly_chart(apply_executive_style(fig_asset_sub), use_container_width=True)

elif active == "Liabilities":
    if not comparison_mode:
        liab_prev_year = get_prev_year(effective_year_for_tabs, all_years)
        liab_prev_df = liabilities[liabilities["Financial Year"] == liab_prev_year] if liab_prev_year else pd.DataFrame()
        liab_curr_total = liab_filtered["Amount"].sum()
        liab_prev_total = liab_prev_df["Amount"].sum() if not liab_prev_df.empty else None

        liab_cat = liab_filtered.groupby(["Category"])["Amount"].sum().reset_index()
        prev_liab_cat = (
            liab_prev_df.groupby(["Category"])["Amount"].sum().reset_index()
            if not liab_prev_df.empty else pd.DataFrame(columns=["Category", "Amount"])
        )

        top_liab_cat_label = None
        top_liab_cat_amount = None
        top_liab_cat_prev_amount = None
        if not liab_cat.empty:
            top_liab_cat_row = liab_cat.sort_values("Amount", ascending=False).iloc[0]
            top_liab_cat_label = f"{top_liab_cat_row['Category']}"
            top_liab_cat_amount = top_liab_cat_row["Amount"]
            if not prev_liab_cat.empty:
                top_liab_cat_prev_amount = prev_liab_cat[prev_liab_cat["Category"] == top_liab_cat_row["Category"]]["Amount"].sum()

        liab_subcat = liab_filtered.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
        prev_liab_subcat = (
            liab_prev_df.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
            if not liab_prev_df.empty else pd.DataFrame(columns=["Category", "SubCategory", "Amount"])
        )

        liab_subcat_delta = None
        if not liab_subcat.empty and not prev_liab_subcat.empty:
            liab_subcat_delta = liab_subcat.merge(
                prev_liab_subcat, on=["Category", "SubCategory"], how="left", suffixes=("_curr", "_prev")
            )
            liab_subcat_delta["Amount_prev"] = liab_subcat_delta["Amount_prev"].fillna(0)
            liab_subcat_delta["Delta"] = liab_subcat_delta["Amount_curr"] - liab_subcat_delta["Amount_prev"]

        liab_largest_increase_label = None
        liab_largest_increase_curr = None
        liab_largest_increase_prev = None
        liab_largest_decrease_label = None
        liab_largest_decrease_curr = None
        liab_largest_decrease_prev = None

        if liab_subcat_delta is not None and not liab_subcat_delta.empty:
            inc_row = liab_subcat_delta.sort_values("Delta", ascending=False).iloc[0]
            liab_largest_increase_label = f"{inc_row['SubCategory']}"
            liab_largest_increase_curr = inc_row["Amount_curr"]
            liab_largest_increase_prev = inc_row["Amount_prev"]

            dec_row = liab_subcat_delta.sort_values("Delta", ascending=True).iloc[0]
            liab_largest_decrease_label = f"{dec_row['SubCategory']}"
            liab_largest_decrease_curr = dec_row["Amount_curr"]
            liab_largest_decrease_prev = dec_row["Amount_prev"]

        st.markdown(f"#### FY Snapshot: {effective_year_for_tabs}")
        liab_kpi_cols = st.columns(4)
        with liab_kpi_cols[0]:
            kpi_card(
                "Liabilities",
                format_amount(liab_curr_total),
                f"Overall<br>{format_yoy(liab_curr_total, liab_prev_total)}",
                icon_svg("down", "#64748B"),
                "#64748B"
            )
        with liab_kpi_cols[1]:
            kpi_card(
                "Top Category",
                format_amount(top_liab_cat_amount) if top_liab_cat_amount is not None else "N/A",
                f"{top_liab_cat_label}<br>{format_yoy(top_liab_cat_amount, top_liab_cat_prev_amount)}" if top_liab_cat_label else "N/A",
                icon_svg("top", NCA_TEAL),
                NCA_TEAL
            )
        with liab_kpi_cols[2]:
            kpi_card(
                "Largest Increase",
                format_amount(liab_largest_increase_curr - liab_largest_increase_prev) if liab_largest_increase_label else "N/A",
                f"{liab_largest_increase_label}<br>{format_yoy(liab_largest_increase_curr, liab_largest_increase_prev)}" if liab_largest_increase_label else "N/A",
                icon_svg("up", NCA_PURPLE),
                NCA_PURPLE
            )
        with liab_kpi_cols[3]:
            kpi_card(
                "Largest Decrease",
                format_amount(liab_largest_decrease_curr - liab_largest_decrease_prev) if liab_largest_decrease_label else "N/A",
                f"{liab_largest_decrease_label}<br>{format_yoy(liab_largest_decrease_curr, liab_largest_decrease_prev)}" if liab_largest_decrease_label else "N/A",
                icon_svg("down", NCA_ORANGE),
                NCA_ORANGE
            )

        section_header("FY Distribution", f"Distribution and top sub-categories for FY {effective_year_for_tabs}.")
        snap_left, snap_right = st.columns(2)
        with snap_left:
            liab_cat = liab_filtered.groupby("Category")["Amount"].sum().reset_index()
            fig_liab = px.pie(
                liab_cat,
                names="Category",
                values="Amount",
                hole=0.6,
                title=f"Liabilities Categories - {effective_year_for_tabs}",
                color_discrete_map=EXP_COLOR_MAP,
                category_orders=EXP_CATEGORY_ORDER,
            )
            st.plotly_chart(apply_executive_style(fig_liab), use_container_width=True)

        with snap_right:
            liab_subcat = liab_filtered.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
            liab_subcat = liab_subcat[liab_subcat["Amount"] > 0]
            liab_subcat = liab_subcat.sort_values("Amount", ascending=False).head(10)
            if not liab_subcat.empty:
                liab_subcat["Label"] = liab_subcat["SubCategory"]
                liab_subcat["AmountLabel"] = liab_subcat["Amount"].apply(
                    lambda v: f"{v / 1_000_000_000:.2f}B" if abs(v) >= 1_000_000_000 else f"{v / 1_000_000:.2f}M"
                )
                liab_subcat_sorted = liab_subcat.sort_values("Amount", ascending=False)
                fig_liab_sub = px.bar(
                    liab_subcat_sorted,
                    x="Amount",
                    y="Label",
                    color="Category",
                    orientation="h",
                    color_discrete_map=EXP_COLOR_MAP,
                    category_orders=EXP_CATEGORY_ORDER,
                    text="AmountLabel",
                    title="Top Liabilities by Sub-Category"
                )
                fig_liab_sub.update_traces(texttemplate="%{text}", textposition="outside")
                fig_liab_sub.update_layout(showlegend=False)
                fig_liab_sub.update_layout(
                    yaxis_title="",
                    xaxis_title="Amount",
                    yaxis=dict(categoryorder="array", categoryarray=liab_subcat_sorted["Label"].tolist(), autorange="reversed"),
                    margin=dict(l=80, r=80, t=80, b=60)
                )
                st.plotly_chart(apply_executive_style(fig_liab_sub), use_container_width=True)

        st.markdown("---")
        section_header("Trend Explorer", "Compare categories or sub-categories across the full time period.")
        trend_col1, trend_col2 = st.columns([1, 2])
        with trend_col1:
            trend_level = st.selectbox(
                "Trend Level",
                ["Category", "Sub-Category"],
                key="liab_trend_level"
            )
        with trend_col2:
            if trend_level == "Category":
                trend_source = liabilities.dropna(subset=["Category"])
                trend_items = sorted(trend_source["Category"].unique())
                trend_data = trend_source.groupby(["Financial Year", "Category"])["Amount"].sum().reset_index()
                trend_data["Item"] = trend_data["Category"]
                default_items = (
                    trend_source.groupby("Category")["Amount"].sum()
                    .sort_values(ascending=False).head(3).index.tolist()
                )
                color_map = {item: EXP_COLOR_MAP.get(item, NCA_BLUE) for item in trend_items}
            else:
                trend_source = liabilities.dropna(subset=["Category", "SubCategory"]).copy()
                trend_source["Item"] = trend_source["Category"].astype(str) + " - " + trend_source["SubCategory"].astype(str)
                trend_items = sorted(trend_source["Item"].unique())
                trend_data = trend_source.groupby(["Financial Year", "Item"])["Amount"].sum().reset_index()
                default_items = (
                    trend_source.groupby("Item")["Amount"].sum()
                    .sort_values(ascending=False).head(4).index.tolist()
                )
                palette = px.colors.qualitative.Safe
                color_map = {item: palette[i % len(palette)] for i, item in enumerate(trend_items)}

            selected_items = st.multiselect(
                "Compare Items (add multiple)",
                options=trend_items,
                default=default_items,
                key="liab_trend_items"
            )

        if selected_items:
            trend_filtered = trend_data[trend_data["Item"].isin(selected_items)]
            fig_trend = px.line(
                trend_filtered,
                x="Financial Year",
                y="Amount",
                color="Item",
                markers=True,
                color_discrete_map=color_map,
                title="Liabilities Trend Over Time"
            )
            st.plotly_chart(apply_executive_style(fig_trend), use_container_width=True)
        else:
            st.info("Select at least one item to view the trend.")

        st.markdown("---")
        section_header("Liabilities Detail Table", f"Category and sub-category snapshot for FY {effective_year_for_tabs}.")
        liab_table = liab_filtered.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
        liab_table = liab_table.sort_values(["Category", "Amount"], ascending=[True, False])
        st.dataframe(liab_table, use_container_width=True)
        csv_liab = liab_table.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Liabilities Snapshot (CSV)",
            data=csv_liab,
            file_name=f"liabilities_snapshot_FY_{effective_year_for_tabs}.csv",
            mime="text/csv",
            use_container_width=False
        )

    if comparison_mode:
        section_header("Liabilities Comparison", "Side-by-side FY distributions and top sub-categories.")
        for i in range(0, len(compare_years), 3):
            row_years = compare_years[i:i + 3]
            cols = st.columns(len(row_years))
            for col, year in zip(cols, row_years):
                with col:
                    st.markdown(f"**FY {year}**")
                    liab_year = liabilities[liabilities["Financial Year"] == year]
                    liab_cat = liab_year.groupby("Category")["Amount"].sum().reset_index()
                    fig_liab = px.pie(
                        liab_cat,
                        names="Category",
                        values="Amount",
                        hole=0.6,
                        title=f"Liabilities Categories - {year}",
                        color_discrete_map=EXP_COLOR_MAP,
                        category_orders=EXP_CATEGORY_ORDER,
                    )
                    st.plotly_chart(apply_executive_style(fig_liab), use_container_width=True)

                    liab_subcat = liab_year.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
                    liab_subcat = liab_subcat[liab_subcat["Amount"] > 0]
                    liab_subcat = liab_subcat.sort_values("Amount", ascending=False).head(10)
                    if not liab_subcat.empty:
                        liab_subcat["Label"] = liab_subcat["SubCategory"]
                        liab_subcat["AmountLabel"] = liab_subcat["Amount"].apply(
                            lambda v: f"{v / 1_000_000_000:.2f}B" if abs(v) >= 1_000_000_000 else f"{v / 1_000_000:.2f}M"
                        )
                        liab_subcat_sorted = liab_subcat.sort_values("Amount", ascending=False)
                        fig_liab_sub = px.bar(
                            liab_subcat_sorted,
                            x="Amount",
                            y="Label",
                            color="Category",
                            orientation="h",
                            color_discrete_map=EXP_COLOR_MAP,
                            category_orders=EXP_CATEGORY_ORDER,
                            text="AmountLabel",
                            title="Top Liabilities by Sub-Category"
                        )
                        fig_liab_sub.update_traces(texttemplate="%{text}", textposition="outside")
                        fig_liab_sub.update_layout(
                            showlegend=False,
                            yaxis_title="",
                            xaxis_title="Amount",
                            yaxis=dict(categoryorder="array", categoryarray=liab_subcat_sorted["Label"].tolist(), autorange="reversed"),
                            margin=dict(l=80, r=80, t=80, b=60)
                        )
                        st.plotly_chart(apply_executive_style(fig_liab_sub), use_container_width=True)

elif active == "Cashflow":
    section_header("Cashflow", "Data coming soon.")
    st.markdown("""
        <div style='background: rgba(255,255,255,0.35); border: 1px dashed rgba(148,163,184,0.6);
                    border-radius: 22px; padding: 26px; margin-top: 10px;'>
            <div style='display:flex; align-items:center; justify-content:space-between; gap:16px;'>
                <div>
                    <div style='font-size:0.9rem; font-weight:700; letter-spacing:0.12em; color:#64748B;'>CASHFLOW MODULE</div>
                    <div style='font-size:1.6rem; font-weight:800; color:#0F172A; margin-top:6px;'>Coming Soon</div>
                    <div style='font-size:0.85rem; color:#64748B; margin-top:8px; max-width:560px;'>
                        We are preparing the cashflow dataset and executive visuals. This area will include
                        operating, investing, and financing cashflows, plus trend and coverage metrics.
                    </div>
                </div>
                <div style='width:120px; height:120px; border-radius:18px; background: linear-gradient(135deg, rgba(0,112,192,0.15), rgba(247,148,29,0.18));
                            border:1px solid rgba(148,163,184,0.5); display:grid; place-items:center;'>
                    <div style='width:68px; height:68px; border-radius:12px; background: rgba(255,255,255,0.6);
                                display:grid; place-items:center; border:1px solid rgba(148,163,184,0.4);'>
                        <div style='font-size:28px; color:#64748B; font-weight:700;'>CF</div>
                    </div>
                </div>
            </div>
        </div>
        <div style='display:grid; grid-template-columns:repeat(3, 1fr); gap:14px; margin-top:16px;'>
            <div class='metric-card' style='min-height:140px; opacity:0.6;'>
                <div class='status-bar'></div>
                <div class='metric-title'>Operating Cashflow</div>
                <div class='metric-value'>--</div>
                <div class='metric-sub-value'>Awaiting dataset</div>
            </div>
            <div class='metric-card' style='min-height:140px; opacity:0.6;'>
                <div class='status-bar'></div>
                <div class='metric-title'>Investing Cashflow</div>
                <div class='metric-value'>--</div>
                <div class='metric-sub-value'>Awaiting dataset</div>
            </div>
            <div class='metric-card' style='min-height:140px; opacity:0.6;'>
                <div class='status-bar'></div>
                <div class='metric-title'>Financing Cashflow</div>
                <div class='metric-value'>--</div>
                <div class='metric-sub-value'>Awaiting dataset</div>
            </div>
        </div>
        <div style='margin-top:18px; padding:18px; border-radius:18px; background: rgba(255,255,255,0.35);
                    border:1px solid rgba(148,163,184,0.5); color:#64748B;'>
            <div style='font-size:0.75rem; font-weight:700; letter-spacing:0.12em; margin-bottom:6px;'>WHAT TO EXPECT</div>
            <div style='display:flex; gap:14px; flex-wrap:wrap; font-size:0.85rem;'>
                <div>Cashflow trend (all years)</div>
                <div>Operating margin proxy</div>
                <div>Capex intensity</div>
                <div>Free cashflow bridge</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

elif active == "Budget Performance":
    section_header("Budget Performance", "Data coming soon.")
    st.markdown("""
        <div style='background: rgba(255,255,255,0.35); border: 1px dashed rgba(148,163,184,0.6);
                    border-radius: 22px; padding: 26px; margin-top: 10px;'>
            <div style='display:flex; align-items:center; justify-content:space-between; gap:16px;'>
                <div>
                    <div style='font-size:0.9rem; font-weight:700; letter-spacing:0.12em; color:#64748B;'>BUDGET PERFORMANCE</div>
                    <div style='font-size:1.6rem; font-weight:800; color:#0F172A; margin-top:6px;'>Coming Soon</div>
                    <div style='font-size:0.85rem; color:#64748B; margin-top:8px; max-width:560px;'>
                        This module will compare actuals to budget by category and sub-category, highlighting variances,
                        under-spend and over-spend patterns, and fiscal discipline indicators.
                    </div>
                </div>
                <div style='width:120px; height:120px; border-radius:18px; background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(247,148,29,0.18));
                            border:1px solid rgba(148,163,184,0.5); display:grid; place-items:center;'>
                    <div style='width:68px; height:68px; border-radius:12px; background: rgba(255,255,255,0.6);
                                display:grid; place-items:center; border:1px solid rgba(148,163,184,0.4);'>
                        <div style='font-size:24px; color:#64748B; font-weight:700;'>B/A</div>
                    </div>
                </div>
            </div>
        </div>
        <div style='display:grid; grid-template-columns:repeat(3, 1fr); gap:14px; margin-top:16px;'>
            <div class='metric-card' style='min-height:140px; opacity:0.6;'>
                <div class='status-bar'></div>
                <div class='metric-title'>Total Budget</div>
                <div class='metric-value'>--</div>
                <div class='metric-sub-value'>Awaiting dataset</div>
            </div>
            <div class='metric-card' style='min-height:140px; opacity:0.6;'>
                <div class='status-bar'></div>
                <div class='metric-title'>Total Actuals</div>
                <div class='metric-value'>--</div>
                <div class='metric-sub-value'>Awaiting dataset</div>
            </div>
            <div class='metric-card' style='min-height:140px; opacity:0.6;'>
                <div class='status-bar'></div>
                <div class='metric-title'>Variance</div>
                <div class='metric-value'>--</div>
                <div class='metric-sub-value'>Awaiting dataset</div>
            </div>
        </div>
        <div style='margin-top:18px; padding:18px; border-radius:18px; background: rgba(255,255,255,0.35);
                    border:1px solid rgba(148,163,184,0.5); color:#64748B;'>
            <div style='font-size:0.75rem; font-weight:700; letter-spacing:0.12em; margin-bottom:6px;'>WHAT TO EXPECT</div>
            <div style='display:flex; gap:14px; flex-wrap:wrap; font-size:0.85rem;'>
                <div>Budget vs actual by category</div>
                <div>Variance waterfall</div>
                <div>Under/over spend highlights</div>
                <div>Compliance against targets</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 8. Board-Ready Footer ---
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown(f"""
    <div style='display: flex; justify-content: space-between; align-items: center; color: {NCA_BLUE}; opacity: 0.6; font-size: 0.75rem;'>
        <span>NATIONAL CONSTRUCTION AUTHORITY</span>
        <span>FOR INTERNAL USE ONLY</span>
    </div>
""", unsafe_allow_html=True)
