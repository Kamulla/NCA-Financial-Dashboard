import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data

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
income, expenditure, assets, liabilities = load_data()

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
    set(liabilities["Financial Year"].unique())
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
    nav_items = ["Overview", "Income", "Expenditure", "Assets", "Liabilities"]

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
                    <span style='color: rgba(255,255,255,0.6); font-size: 0.75rem;'>Denomination</span>
                    <span style='color: white; font-size: 0.75rem; font-weight: 700;'>Millions/Billions</span>
                </div>
                <div style='display: flex; justify-content: space-between;'>
                    <span style='color: rgba(255,255,255,0.6); font-size: 0.75rem;'>Status</span>
                    <span style='color: {NCA_ORANGE}; font-size: 0.75rem; font-weight: 700;'>Audited Accounts</span>
                </div>
            </div>
            <div style='margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);'>
                 <span style='color: rgba(255,255,255,0.5); font-size: 0.65rem; font-style: italic;'>Data current as of FY {all_years[-1]}</span>
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
def kpi_card(title, value, sub_value, icon, color=NCA_BLUE):
    st.markdown(f"""
        <div class="metric-card">
            <div class="status-bar" style="background: {color};"></div>
            <div style="float: right; font-size: 1.5rem; opacity: 0.4;">{icon}</div>
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub-value">{sub_value}</div>
        </div>
    """, unsafe_allow_html=True)


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
    else:
        st.markdown(f"#### Performance Snapshot: FY {base_year}")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            kpi_card("Revenue", format_amount(current_stats['income']),
                     format_yoy(current_stats['income'], previous_stats['income'] if previous_stats else None), "💹")

        with col2:
            kpi_card("Expenditure", format_amount(current_stats['expenditure']),
                     format_yoy(current_stats['expenditure'], previous_stats['expenditure'] if previous_stats else None),
                     "💸", NCA_ORANGE)

        with col3:
            kpi_card("Assets", format_amount(current_stats['assets']),
                     format_yoy(current_stats['assets'], previous_stats['assets'] if previous_stats else None), "🏢")

        with col4:
            kpi_card("Liabilities", format_amount(current_stats['liabilities']),
                     format_yoy(current_stats['liabilities'], previous_stats['liabilities'] if previous_stats else None),
                     "🧾", "#64748B")

        st.markdown("---")
        if show_trend:
            st.markdown("#### Growth Trajectory")
            overview_trend = pd.DataFrame({
                "Financial Year": income.groupby("Financial Year")["Amount"].sum().index,
                "Income": income.groupby("Financial Year")["Amount"].sum().values,
                "Expenditure": expenditure.groupby("Financial Year")["Amount"].sum().values
            })
            fig_ie = px.line(overview_trend, x="Financial Year", y=["Income", "Expenditure"],
                             title="Revenue vs Expenditure",
                             markers=True, color_discrete_map={"Income": NCA_BLUE, "Expenditure": NCA_ORANGE})
            st.plotly_chart(apply_executive_style(fig_ie), use_container_width=True)

            assets_trend = pd.DataFrame({
                "Financial Year": assets.groupby("Financial Year")["Amount"].sum().index,
                "Assets": assets.groupby("Financial Year")["Amount"].sum().values,
                "Liabilities": liabilities.groupby("Financial Year")["Amount"].sum().values
            })
            fig_al = px.line(assets_trend, x="Financial Year", y=["Assets", "Liabilities"],
                             title="Assets vs Liabilities",
                             markers=True, color_discrete_map={"Assets": NCA_BLUE, "Liabilities": NCA_ORANGE})
            st.plotly_chart(apply_executive_style(fig_al), use_container_width=True)
        else:
            st.markdown(f"#### Capital Breakdown: FY {base_year}")
            cl, cr = st.columns(2)
            with cl:
                fig_inc = px.pie(income_filtered.groupby("Category")["Amount"].sum().reset_index(),
                                 names="Category", values="Amount", hole=0.7, title="Revenue Allocation",
                                 color_discrete_sequence=[NCA_BLUE, NCA_ORANGE, "#334155", "#94A3B8"])
                st.plotly_chart(apply_executive_style(fig_inc), use_container_width=True)
            with cr:
                fig_exp = px.pie(exp_filtered.groupby("Category")["Amount"].sum().reset_index(),
                                 names="Category", values="Amount", hole=0.7, title="Expenditure Profile",
                                 color_discrete_sequence=[NCA_ORANGE, NCA_BLUE, "#64748B", "#CBD5E1"])
                st.plotly_chart(apply_executive_style(fig_exp), use_container_width=True)

            st.markdown(f"#### Balance Sheet Composition: FY {base_year}")
            al, ar = st.columns(2)
            with al:
                fig_ast = px.pie(assets_filtered.groupby("Category")["Amount"].sum().reset_index(),
                                 names="Category", values="Amount", hole=0.7, title="Assets Allocation",
                                 color_discrete_sequence=[NCA_BLUE, NCA_ORANGE, "#334155", "#94A3B8"])
                st.plotly_chart(apply_executive_style(fig_ast), use_container_width=True)
            with ar:
                fig_liab = px.pie(liab_filtered.groupby("Category")["Amount"].sum().reset_index(),
                                  names="Category", values="Amount", hole=0.7, title="Liabilities Profile",
                                  color_discrete_sequence=[NCA_ORANGE, NCA_BLUE, "#64748B", "#CBD5E1"])
                st.plotly_chart(apply_executive_style(fig_liab), use_container_width=True)

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
        section_header("FY Snapshot", f"Distribution and top sub-categories for FY {effective_year_for_tabs}.")
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

elif active == "Expenditure":
    if not comparison_mode:
        section_header("FY Snapshot", f"Distribution and top sub-categories for FY {effective_year_for_tabs}.")
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
        section_header("FY Snapshot", f"Distribution and top sub-categories for FY {effective_year_for_tabs}.")
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
        section_header("FY Snapshot", f"Distribution and top sub-categories for FY {effective_year_for_tabs}.")
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

# --- 8. Board-Ready Footer ---
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown(f"""
    <div style='display: flex; justify-content: space-between; align-items: center; color: {NCA_BLUE}; opacity: 0.6; font-size: 0.75rem;'>
        <span>NATIONAL CONSTRUCTION AUTHORITY</span>
        <span>FOR INTERNAL USE ONLY</span>
    </div>
""", unsafe_allow_html=True)
