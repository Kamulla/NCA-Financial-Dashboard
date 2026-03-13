import pandas as pd

def load_data():

    xls = pd.ExcelFile("data/Finance Research - Reports Data Collection Tool Updated.xlsx")

    income = pd.read_excel(xls, "Income")
    expenditure = pd.read_excel(xls, "Expenditure")
    assets = pd.read_excel(xls, "Assets")
    liabilities = pd.read_excel(xls, "Liabilities")
    cashflow = pd.read_excel(xls, "Cashflow")

    # Clean column names (remove hidden spaces)
    for df in [income, expenditure, assets, liabilities, cashflow]:
        df.columns = df.columns.str.strip()

    # Standardize Amount column across sheets
    income = income.rename(columns=lambda x: "Amount" if "Amount" in x else x)
    expenditure = expenditure.rename(columns=lambda x: "Amount" if "Amount" in x else x)
    assets = assets.rename(columns=lambda x: "Amount" if "Amount" in x else x)
    liabilities = liabilities.rename(columns=lambda x: "Amount" if "Amount" in x else x)
    cashflow = cashflow.rename(columns=lambda x: "Amount" if "Amount" in x else x)

    # Ensure numeric values
    income["Amount"] = pd.to_numeric(income["Amount"], errors="coerce")
    expenditure["Amount"] = pd.to_numeric(expenditure["Amount"], errors="coerce")
    assets["Amount"] = pd.to_numeric(assets["Amount"], errors="coerce")
    liabilities["Amount"] = pd.to_numeric(liabilities["Amount"], errors="coerce")
    cashflow["Amount"] = pd.to_numeric(cashflow["Amount"], errors="coerce")

    return income, expenditure, assets, liabilities, cashflow
