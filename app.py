import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
compare_years = st.sidebar.multiselect(
    "Compare Financial Years (2+)",
    options=all_years,
    default=[]
)
comparison_mode = len(compare_years) >= 2
if comparison_mode:
    st.sidebar.selectbox("Select Financial Year", [""], disabled=True, index=0)
    selected_year = None
    selected_year_effective = compare_years[0]
else:
    selected_year = st.sidebar.selectbox("Select Financial Year", years_options)
    selected_year_effective = selected_year

# --- Filter Data ---
if selected_year_effective == "All Years":
    income_filtered = income.copy()
    exp_filtered = expenditure.copy()
    assets_filtered = assets.copy()
    liab_filtered = liabilities.copy()
    show_trend = True and not comparison_mode
else:
    income_filtered = income[income["Financial Year"] == selected_year_effective]
    exp_filtered = expenditure[expenditure["Financial Year"] == selected_year_effective]
    assets_filtered = assets[assets["Financial Year"] == selected_year_effective]
    liab_filtered = liabilities[liabilities["Financial Year"] == selected_year_effective]
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

def format_amount(value):
    if pd.isna(value):
        return ""
    abs_val = abs(value)
    if abs_val >= 1_000_000_000:
        return f"{value/1_000_000_000:.2f}B"
    if abs_val >= 1_000_000:
        return f"{value/1_000_000:.2f}M"
    if abs_val >= 1_000:
        return f"{value/1_000:.2f}K"
    return f"{value:.0f}"

def build_pie(df, title=None):
    data = df.groupby("Category")["Amount"].sum().reset_index()
    fig = px.pie(data, names="Category", values="Amount", title=title)
    return fig

def build_treemap(df, title=None):
    data = df.groupby("Category")["Amount"].sum().reset_index()
    data["Label"] = data["Amount"].apply(format_amount)
    fig = px.treemap(data, path=["Category"], values="Amount", title=title)
    fig.update_traces(textinfo="label+text", text=data["Label"])
    return fig

def build_waterfall(df, title=None, name="Series"):
    cat = df.groupby("Category")["Amount"].sum().reset_index()
    if cat.empty:
        return None
    cat = cat.sort_values("Amount", ascending=False)
    labels = cat["Category"].tolist() + ["Total"]
    values = cat["Amount"].tolist()
    total = sum(values)
    fig = go.Figure(
        go.Waterfall(
            name=name,
            orientation="v",
            measure=["relative"] * len(values) + ["total"],
            x=labels,
            y=values + [total],
            text=[format_amount(v) for v in values] + [format_amount(total)],
            textposition="outside",
            connector={"line": {"color": "rgba(63, 63, 63, 0.4)"}},
            decreasing={"marker": {"color": "#ef553b"}},
            increasing={"marker": {"color": "#636efa"}},
            totals={"marker": {"color": "#00cc96"}}
        )
    )
    fig.update_layout(title=title, yaxis_title="Amount (KSh)", showlegend=False)
    return fig

def render_comparison(title, years, chart_builder):
    st.subheader(title)
    if len(years) < 2:
        st.info("Select 2 or more years in the Compare Financial Years filter.")
        return
    for i in range(0, len(years), 3):
        row_years = years[i:i + 3]
        cols = st.columns(len(row_years))
        for col, year in zip(cols, row_years):
            with col:
                fig = chart_builder(year, f"{title} - FY {year}")
                if fig is None:
                    st.info("No data for this year.")
                else:
                    fig.update_layout(title=f"{title} - FY {year}")
                    st.plotly_chart(fig, use_container_width=True)

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview", "Income", "Expenditure", "Assets", "Liabilities"
])

# --- Tab 1: Overview ---
with tab1:
    st.header("Financial Overview")
    if comparison_mode:
        st.info("Comparison mode is enabled. Overview charts are hidden.")
    else:

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
        if selected_year == "All Years" and not comparison_mode:
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
    if not comparison_mode:
        st.subheader("Income Composition")
        income_cat = income_filtered.groupby("Category")["Amount"].sum().reset_index()
        fig_income_cat = px.pie(income_cat, names="Category", values="Amount", title=f"Income by Category ({selected_year_effective})")
        st.plotly_chart(fig_income_cat, use_container_width=True)

        st.subheader("Income Subcategories")
        income_subcat = income_filtered.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
        if income_subcat.empty:
            st.info("No income subcategory data available for the selected year.")
        else:
            subcat_count = income_subcat["SubCategory"].nunique()
            if subcat_count <= 12:
                income_subcat = income_subcat.sort_values("Amount", ascending=True)
                fig_income_sub = px.bar(
                    income_subcat,
                    x="Amount",
                    y="SubCategory",
                    color="Category",
                    orientation="h",
                    text=income_subcat["Amount"].apply(format_amount),
                    title=f"Income by Subcategory ({selected_year_effective})"
                )
                fig_income_sub.update_layout(
                    xaxis_title="Amount (KSh)",
                    yaxis_title=None,
                    showlegend=True,
                    height=max(350, 35 * len(income_subcat))
                )
                fig_income_sub.update_traces(textposition="outside", cliponaxis=False)
                st.plotly_chart(fig_income_sub, use_container_width=True)
            else:
                fig_income_sub = px.treemap(
                    income_subcat,
                    path=["Category", "SubCategory"],
                    values="Amount",
                    title=f"Income by Subcategory ({selected_year_effective})"
                )
                st.plotly_chart(fig_income_sub, use_container_width=True)

        if show_trend:
            st.subheader("Income Trend (10 Years)")
            income_trend = income_filtered.groupby("Financial Year")["Amount"].sum().reset_index()
            fig_income_trend = px.line(income_trend, x="Financial Year", y="Amount", markers=True, title="Total Income by Year")
            st.plotly_chart(fig_income_trend, use_container_width=True)

    render_comparison(
        "Income Composition Comparison",
        compare_years,
        lambda y, t: build_pie(income[income["Financial Year"] == y], title=t)
    )

# --- Tab 3: Expenditure ---
with tab3:
    st.header("Expenditure Analysis")
    if not comparison_mode:
        st.subheader("Expenditure Composition")
        exp_cat = exp_filtered.groupby("Category")["Amount"].sum().reset_index()
        fig_exp_cat = px.pie(exp_cat, names="Category", values="Amount", title=f"Expenditure by Category ({selected_year_effective})")
        st.plotly_chart(fig_exp_cat, use_container_width=True)

        if show_trend:
            st.subheader("Expenditure Trend (10 Years)")
            exp_trend = exp_filtered.groupby("Financial Year")["Amount"].sum().reset_index()
            fig_exp_trend = px.line(exp_trend, x="Financial Year", y="Amount", markers=True, title="Total Expenditure by Year")
            st.plotly_chart(fig_exp_trend, use_container_width=True)

    render_comparison(
        "Expenditure Composition Comparison",
        compare_years,
        lambda y, t: build_pie(expenditure[expenditure["Financial Year"] == y], title=t)
    )

# --- Tab 4: Assets ---
with tab4:
    st.header("Assets Analysis")
    if not comparison_mode:
        st.subheader("Asset Composition")
        asset_cat = assets_filtered.groupby("Category")["Amount"].sum().reset_index()
        asset_cat["Label"] = asset_cat["Amount"].apply(format_amount)
        fig_asset_cat = px.treemap(
            asset_cat,
            path=["Category"],
            values="Amount",
            title=f"Asset Structure ({selected_year_effective})"
        )
        fig_asset_cat.update_traces(textinfo="label+text", text=asset_cat["Label"])
        st.plotly_chart(fig_asset_cat, use_container_width=True)

        st.subheader("Asset Subcategories by Category")
        asset_subcat = assets_filtered.groupby(["Category", "SubCategory"])["Amount"].sum().reset_index()
        if asset_subcat.empty:
            st.info("No asset subcategory data available for the selected year.")
        else:
            for category in asset_subcat["Category"].unique():
                st.markdown(f"**{category}**")
                cat_data = asset_subcat[asset_subcat["Category"] == category].sort_values("Amount", ascending=True)
                fig_subcat = px.bar(
                    cat_data,
                    x="Amount",
                    y="SubCategory",
                    orientation="h",
                    title=None,
                    text=cat_data["Amount"].apply(format_amount)
                )
                fig_subcat.update_layout(
                    xaxis_title="Amount (KSh)",
                    yaxis_title=None,
                    showlegend=False,
                    height=max(300, 40 * len(cat_data))
                )
                fig_subcat.update_traces(textposition="outside", cliponaxis=False)
                st.plotly_chart(fig_subcat, use_container_width=True)

        if show_trend:
            st.subheader("Assets Trend (10 Years)")
            assets_trend = assets_filtered.groupby("Financial Year")["Amount"].sum().reset_index()
            fig_assets = px.line(assets_trend, x="Financial Year", y="Amount", markers=True, title="Assets Growth Over Time")
            fig_assets.update_traces(
                text=assets_trend["Amount"].apply(format_amount),
                textposition="top center"
            )
            st.plotly_chart(fig_assets, use_container_width=True)

        st.subheader("Assets Waterfall")
        fig_assets_wf = build_waterfall(assets_filtered, title=f"Assets Contribution by Category ({selected_year_effective})", name="Assets")
        if fig_assets_wf is None:
            st.info("No assets data available for the selected year.")
        else:
            st.plotly_chart(fig_assets_wf, use_container_width=True)

    render_comparison(
        "Assets Structure Comparison",
        compare_years,
        lambda y, t: build_treemap(assets[assets["Financial Year"] == y], title=t)
    )

    render_comparison(
        "Assets Waterfall Comparison",
        compare_years,
        lambda y, t: build_waterfall(assets[assets["Financial Year"] == y], title=t, name="Assets")
    )

# --- Tab 5: Liabilities ---
with tab5:
    st.header("Liabilities Analysis")
    if not comparison_mode:
        if show_trend:
            liab_trend = liab_filtered.groupby("Financial Year")["Amount"].sum().reset_index()
            fig_liab = px.line(liab_trend, x="Financial Year", y="Amount", markers=True, title="Liabilities Growth Over Time")
            st.plotly_chart(fig_liab, use_container_width=True)

        st.subheader("Liabilities Waterfall")
        fig_liab_wf = build_waterfall(liab_filtered, title=f"Liabilities Contribution by Category ({selected_year_effective})", name="Liabilities")
        if fig_liab_wf is None:
            st.info("No liabilities data available for the selected year.")
        else:
            st.plotly_chart(fig_liab_wf, use_container_width=True)

    render_comparison(
        "Liabilities Waterfall Comparison",
        compare_years,
        lambda y, t: build_waterfall(liabilities[liabilities["Financial Year"] == y], title=t, name="Liabilities")
    )
