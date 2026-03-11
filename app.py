import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_data

# --- Page Config ---
st.set_page_config(
    page_title="NCA 10-Year Financial Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Header ---
st.title("Financial Reports Analysis for FY 2012/13 - 2024/25")

# --- Load Data ---
income, expenditure, assets, liabilities = load_data()

# --- Sidebar ---
st.sidebar.image("assets/nca-logo.png", width=180)
st.sidebar.title("National Construction Authority")

# Unified list of years + "All Years"
all_years = sorted(
    set(income["Financial Year"].unique()) |
    set(expenditure["Financial Year"].unique()) |
    set(assets["Financial Year"].unique()) |
    set(liabilities["Financial Year"].unique())
)
years_options = ["All Years"] + all_years
selected_year = st.sidebar.selectbox("Select Financial Year", years_options)

# --- Filter Data ---
if selected_year == "All Years":
    income_filtered = income.copy()
    exp_filtered = expenditure.copy()
    assets_filtered = assets.copy()
    liab_filtered = liabilities.copy()
    show_trend = True
else:
    income_filtered = income[income["Financial Year"] == selected_year]
    exp_filtered = expenditure[expenditure["Financial Year"] == selected_year]
    assets_filtered = assets[assets["Financial Year"] == selected_year]
    liab_filtered = liabilities[liabilities["Financial Year"] == selected_year]
    show_trend = False

# --- KPI Card Function ---
def kpi_card(title, value, icon):
    st.markdown(f"""
        <div style="
        background-color:#f7f9fc;
        padding:20px;
        border-radius:12px;
        box-shadow:0px 2px 12px rgba(0,0,0,0.1);
        text-align:center;
        margin-bottom:15px;">
        <div style="font-size:36px">{icon}</div>
        <div style="font-size:14px;color:gray;margin-top:5px">{title}</div>
        <div style="font-size:28px;font-weight:bold;margin-top:5px">{value}</div>
        </div>
    """, unsafe_allow_html=True)

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview", "Income", "Expenditure", "Assets", "Liabilities"
])

# --- Tab 1: Overview ---
with tab1:
    st.header("Financial Overview")

    # --- KPI Cards Row 1 ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Total Income", f"KSh {income_filtered['Amount'].sum():,.0f}", "💰")
    with col2:
        kpi_card("Total Expenditure", f"KSh {exp_filtered['Amount'].sum():,.0f}", "💸")
    with col3:
        kpi_card("Total Assets", f"KSh {assets_filtered['Amount'].sum():,.0f}", "🏢")
    with col4:
        kpi_card("Total Liabilities", f"KSh {liab_filtered['Amount'].sum():,.0f}", "📉")

    # --- KPI Cards Row 2 (Ratios) ---
    asset_liab_ratio = assets_filtered["Amount"].sum() / liab_filtered["Amount"].sum() if liab_filtered["Amount"].sum() != 0 else 0
    income_exp_ratio = income_filtered["Amount"].sum() / exp_filtered["Amount"].sum() if exp_filtered["Amount"].sum() != 0 else 0
    col1, col2 = st.columns(2)
    with col1:
        kpi_card("Asset-to-Liability Ratio", f"{asset_liab_ratio:.2f}", "🏦")
    with col2:
        kpi_card("Income-to-Expenditure Ratio", f"{income_exp_ratio:.2f}", "📊")

    # --- Income vs Expenditure Trend (only for All Years) ---
    if show_trend:
        overview_trend = pd.DataFrame({
            "Financial Year": income.groupby("Financial Year")["Amount"].sum().index,
            "Income": income.groupby("Financial Year")["Amount"].sum().values,
            "Expenditure": expenditure.groupby("Financial Year")["Amount"].sum().values
        })
        fig_ie = px.bar(
            overview_trend,
            x="Financial Year",
            y=["Income", "Expenditure"],
            barmode="group",
            title="Income vs Expenditure Over Time",
            text_auto=True
        )
        st.plotly_chart(fig_ie, use_container_width=True)

        # --- Assets vs Liabilities Trend ---
        assets_liab_trend = pd.DataFrame({
            "Financial Year": assets.groupby("Financial Year")["Amount"].sum().index,
            "Assets": assets.groupby("Financial Year")["Amount"].sum().values,
            "Liabilities": liabilities.groupby("Financial Year")["Amount"].sum().values
        })
        fig_al = px.bar(
            assets_liab_trend,
            x="Financial Year",
            y=["Assets", "Liabilities"],
            barmode="group",
            title="Assets vs Liabilities Over Time",
            text_auto=True
        )
        st.plotly_chart(fig_al, use_container_width=True)

        # --- Net Position Line ---
        net_position = overview_trend.copy()
        net_position["Net"] = net_position["Income"] - net_position["Expenditure"]
        fig_net = px.line(net_position, x="Financial Year", y="Net", markers=True, title="Net Position (Income - Expenditure)")
        st.plotly_chart(fig_net, use_container_width=True)

    # --- Income & Expenditure Composition ---
    income_top = income_filtered.groupby("Category")["Amount"].sum().reset_index()
    fig_income_share = px.pie(
        income_top,
        names="Category",
        values="Amount",
        title="Income Share by Category",
        hole=0.4
    )
    st.plotly_chart(fig_income_share, use_container_width=True)

    exp_top = exp_filtered.groupby("Category")["Amount"].sum().reset_index()
    fig_exp_share = px.pie(
        exp_top,
        names="Category",
        values="Amount",
        title="Expenditure Share by Category",
        hole=0.4
    )
    st.plotly_chart(fig_exp_share, use_container_width=True)

    # --- Heatmap: Income Categories by Year ---
    heat_data = income.groupby(["Financial Year", "Category"])["Amount"].sum().reset_index()
    heatmap = heat_data.pivot(index="Category", columns="Financial Year", values="Amount").fillna(0)
    fig_heat = px.imshow(
        heatmap,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Blues",
        title="Income by Category Heatmap (All Years)"
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# --- Tab 2: Income ---
with tab2:
    st.header("Income Analysis")
    st.subheader("Income Composition")
    income_cat = income_filtered.groupby("Category")["Amount"].sum().reset_index()
    fig_income_cat = px.pie(income_cat, names="Category", values="Amount", title=f"Income by Category ({selected_year})")
    st.plotly_chart(fig_income_cat, use_container_width=True)

    if show_trend:
        st.subheader("Income Trend (10 Years)")
        income_trend = income_filtered.groupby("Financial Year")["Amount"].sum().reset_index()
        fig_income_trend = px.line(income_trend, x="Financial Year", y="Amount", markers=True, title="Total Income by Year")
        st.plotly_chart(fig_income_trend, use_container_width=True)

# --- Tab 3: Expenditure ---
with tab3:
    st.header("Expenditure Analysis")
    st.subheader("Expenditure Composition")
    exp_cat = exp_filtered.groupby("Category")["Amount"].sum().reset_index()
    fig_exp_cat = px.pie(exp_cat, names="Category", values="Amount", title=f"Expenditure by Category ({selected_year})")
    st.plotly_chart(fig_exp_cat, use_container_width=True)

    if show_trend:
        st.subheader("Expenditure Trend (10 Years)")
        exp_trend = exp_filtered.groupby("Financial Year")["Amount"].sum().reset_index()
        fig_exp_trend = px.line(exp_trend, x="Financial Year", y="Amount", markers=True, title="Total Expenditure by Year")
        st.plotly_chart(fig_exp_trend, use_container_width=True)

# --- Tab 4: Assets ---
with tab4:
    st.header("Assets Analysis")
    st.subheader("Asset Composition")
    asset_cat = assets_filtered.groupby("Category")["Amount"].sum().reset_index()
    fig_asset_cat = px.treemap(asset_cat, path=["Category"], values="Amount", title=f"Asset Structure ({selected_year})")
    st.plotly_chart(fig_asset_cat, use_container_width=True)

    if show_trend:
        st.subheader("Assets Trend (10 Years)")
        assets_trend = assets_filtered.groupby("Financial Year")["Amount"].sum().reset_index()
        fig_assets = px.line(assets_trend, x="Financial Year", y="Amount", markers=True, title="Assets Growth Over Time")
        st.plotly_chart(fig_assets, use_container_width=True)

# --- Tab 5: Liabilities ---
with tab5:
    st.header("Liabilities Analysis")
    if show_trend:
        liab_trend = liab_filtered.groupby("Financial Year")["Amount"].sum().reset_index()
        fig_liab = px.line(liab_trend, x="Financial Year", y="Amount", markers=True, title="Liabilities Growth Over Time")
        st.plotly_chart(fig_liab, use_container_width=True)
    else:
        st.write("Trend analysis not available for a single year.")