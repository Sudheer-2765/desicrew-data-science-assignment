"""Data loader and inspector for the Inventory Records dataset."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd


DEFAULT_EXCEL_PATH = Path(__file__).resolve().parent / "input" / "Inventory-Records-Sample-Data.xlsx"


def clean_column_name(col: str) -> str:
    """Normalize Excel column headers by removing newline characters and extra spaces."""
    cleaned = " ".join(str(col).replace("\n", " ").split())
    # Standardize common slash and hyphen spacings
    cleaned = cleaned.replace("/ ", "/").replace(" /", "/").replace("- ", "-").replace(" -", "-")
    return cleaned


def load_inventory_dataset(excel_path: Optional[str | Path] = None) -> pd.DataFrame:
    """
    Load and clean the Inventory Records sample data.
    
    The original Excel workbook contains title/header banners in rows 0-4.
    Data headers start at row 5 (row 6 in 1-indexed Excel).
    Column 0 is completely empty and gets dropped.
    """
    path = Path(excel_path) if excel_path else DEFAULT_EXCEL_PATH
    if not path.exists():
        raise FileNotFoundError(f"Inventory Excel file not found at: {path}")

    # Read starting from header row 5
    df = pd.read_excel(path, sheet_name="Inventory Records Data", header=5)
    
    # Drop all-null columns and rows
    df = df.dropna(how="all", axis=1)
    df = df.dropna(how="all", axis=0)

    # Normalize column names
    df.columns = [clean_column_name(col) for col in df.columns]

    # Standardize known column names
    column_mapping = {
        "Product ID": "Product ID",
        "Product Name": "Product Name",
        "Opening Stock": "Opening Stock",
        "Purchase/Stock in": "Purchase/Stock in",
        "Number of Units Sold": "Number of Units Sold",
        "Hand-In-Stock": "Hand-In-Stock",
        "Cost Price Per Unit (USD)": "Cost Price Per Unit (USD)",
        "Cost Price Total (USD)": "Cost Price Total (USD)",
    }
    df = df.rename(columns=column_mapping)

    # Ensure integer data types for counts and amounts
    int_columns = [
        "Opening Stock",
        "Purchase/Stock in",
        "Number of Units Sold",
        "Hand-In-Stock",
        "Cost Price Per Unit (USD)",
        "Cost Price Total (USD)",
    ]
    for col in int_columns:
        if col in df.columns:
            df[col] = df[col].astype("int64")

    # Reset index cleanly
    df = df.reset_index(drop=True)
    return df


def inspect_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Inspect the loaded DataFrame and return dataset metrics and quality findings.
    """
    missing_counts = df.isnull().sum().to_dict()
    dtypes_dict = {col: str(dtype) for col, dtype in df.dtypes.items()}

    # Check stock balance rule: Hand-In-Stock == Opening Stock + Purchase/Stock in - Number of Units Sold
    expected_stock = df["Opening Stock"] + df["Purchase/Stock in"] - df["Number of Units Sold"]
    stock_mismatches = df[df["Hand-In-Stock"] != expected_stock]
    stock_anomalies = []
    for _, row in stock_mismatches.iterrows():
        exp = int(row["Opening Stock"] + row["Purchase/Stock in"] - row["Number of Units Sold"])
        stock_anomalies.append({
            "product_id": row["Product ID"],
            "product_name": row["Product Name"],
            "reported_hand_in_stock": int(row["Hand-In-Stock"]),
            "expected_hand_in_stock": exp,
            "discrepancy": int(row["Hand-In-Stock"] - exp),
        })

    # Check valuation rule: Cost Price Total == Hand-In-Stock * Cost Price Per Unit
    expected_cost = df["Hand-In-Stock"] * df["Cost Price Per Unit (USD)"]
    cost_mismatches = df[df["Cost Price Total (USD)"] != expected_cost]

    return {
        "sheet_name": "Inventory Records Data",
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
        "data_types": dtypes_dict,
        "missing_values": missing_counts,
        "total_missing_values": int(sum(missing_counts.values())),
        "stock_formula_discrepancies_count": len(stock_anomalies),
        "stock_formula_discrepancies": stock_anomalies,
        "cost_total_discrepancies_count": len(cost_mismatches),
        "summary_statistics": {
            "total_inventory_valuation_usd": int(df["Cost Price Total (USD)"].sum()),
            "total_hand_in_stock_units": int(df["Hand-In-Stock"].sum()),
            "total_units_sold": int(df["Number of Units Sold"].sum()),
            "unique_products": int(df["Product ID"].nunique()),
        },
    }

