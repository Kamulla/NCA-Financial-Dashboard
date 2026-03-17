import pandas as pd

def load_data():

    xls = pd.ExcelFile("data/Finance Research - Reports Data Collection Tool Updated.xlsx")

    income = pd.read_excel(xls, "Income")
    expenditure = pd.read_excel(xls, "Expenditure")
    assets = pd.read_excel(xls, "Assets")
    liabilities = pd.read_excel(xls, "Liabilities")
    try:
        cashflow = pd.read_excel(xls, "Cashflow")
    except ValueError:
        cashflow = pd.DataFrame(columns=["Financial Year", "Category", "SubCategory", "Amount"])

    try:
        budget_perf_xls = pd.ExcelFile("data/Finance Research Budget Performance.xlsx")
        budget_performance = pd.read_excel(budget_perf_xls, "Dataset")
    except (ValueError, FileNotFoundError):
        budget_performance = pd.DataFrame(columns=["Financial Year", "Category", "SubCategory", "Final Budget", "Actual"])

    # Clean column names (remove hidden spaces)
    for df in [income, expenditure, assets, liabilities, cashflow, budget_performance]:
        df.columns = df.columns.str.strip()

    # Standardize Amount column across sheets
    income = income.rename(columns=lambda x: "Amount" if "Amount" in x else x)
    expenditure = expenditure.rename(columns=lambda x: "Amount" if "Amount" in x else x)
    assets = assets.rename(columns=lambda x: "Amount" if "Amount" in x else x)
    liabilities = liabilities.rename(columns=lambda x: "Amount" if "Amount" in x else x)
    cashflow = cashflow.rename(columns=lambda x: "Amount" if "Amount" in x else x)
    budget_performance = budget_performance.rename(columns=lambda x: "Amount" if "Amount" in x else x)

    # Ensure numeric values
    income["Amount"] = pd.to_numeric(income["Amount"], errors="coerce")
    expenditure["Amount"] = pd.to_numeric(expenditure["Amount"], errors="coerce")
    assets["Amount"] = pd.to_numeric(assets["Amount"], errors="coerce")
    liabilities["Amount"] = pd.to_numeric(liabilities["Amount"], errors="coerce")
    if "Amount" in cashflow.columns:
        cashflow["Amount"] = pd.to_numeric(cashflow["Amount"], errors="coerce")
    if "Amount" in budget_performance.columns:
        budget_performance["Amount"] = pd.to_numeric(budget_performance["Amount"], errors="coerce")

    # Budget performance: normalize column names and derive metrics
    budget_performance = budget_performance.rename(columns={"Subcategory": "SubCategory"})
    if "Final Budget" in budget_performance.columns:
        budget_performance["Final Budget"] = pd.to_numeric(budget_performance["Final Budget"], errors="coerce")
    if "Actual" in budget_performance.columns:
        budget_performance["Actual"] = pd.to_numeric(budget_performance["Actual"], errors="coerce")
    if {"Final Budget", "Actual"}.issubset(budget_performance.columns):
        budget_performance["Difference"] = budget_performance["Actual"] - budget_performance["Final Budget"]
        budget_performance["Percentage Utilization"] = (
            budget_performance["Actual"] / budget_performance["Final Budget"]
        ) * 100

    return income, expenditure, assets, liabilities, cashflow, budget_performance
