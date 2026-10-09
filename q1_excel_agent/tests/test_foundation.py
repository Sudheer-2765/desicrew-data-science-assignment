"""Test suite for Q1 dataset loading and query engine foundation."""

import pytest
import pandas as pd
from q1_excel_agent.data_loader import load_inventory_dataset, inspect_dataset
from q1_excel_agent.query_engine import run_python_query


@pytest.fixture(scope="module")
def inventory_df():
    """Fixture providing loaded inventory DataFrame."""
    return load_inventory_dataset()


def test_load_inventory_dataset(inventory_df):
    """Verify dataset loads cleanly with expected shape, columns, and data types."""
    assert inventory_df is not None
    assert inventory_df.shape == (46, 8)
    expected_cols = [
        "Product ID",
        "Product Name",
        "Opening Stock",
        "Purchase/Stock in",
        "Number of Units Sold",
        "Hand-In-Stock",
        "Cost Price Per Unit (USD)",
        "Cost Price Total (USD)",
    ]
    assert list(inventory_df.columns) == expected_cols
    assert inventory_df.isnull().sum().sum() == 0
    assert inventory_df["Product ID"].iloc[0] == "P101"
    assert inventory_df["Product ID"].iloc[-1] == "P146"


def test_dataset_metadata_inspection(inventory_df):
    """Verify inspection metadata, summary statistics, and anomaly identification."""
    metadata = inspect_dataset(inventory_df)
    assert metadata["row_count"] == 46
    assert metadata["column_count"] == 8
    assert metadata["total_missing_values"] == 0
    assert metadata["cost_total_discrepancies_count"] == 0
    # 12 records have formula discrepancies in Hand-In-Stock
    assert metadata["stock_formula_discrepancies_count"] == 12
    assert metadata["summary_statistics"]["total_inventory_valuation_usd"] > 0
    assert metadata["summary_statistics"]["unique_products"] == 46


def test_query_filtering(inventory_df):
    """Verify run_python_query handles filtering operations."""
    code = "df[df['Hand-In-Stock'] < 20][['Product ID', 'Product Name', 'Hand-In-Stock']]"
    res = run_python_query(code, inventory_df)
    assert res["success"] is True
    assert res["result"]["type"] == "DataFrame"
    assert len(res["result"]["records"]) > 0
    for row in res["result"]["records"]:
        assert row["Hand-In-Stock"] < 20


def test_query_aggregation(inventory_df):
    """Verify run_python_query handles aggregation calculations."""
    code = "df['Cost Price Total (USD)'].sum()"
    res = run_python_query(code, inventory_df)
    assert res["success"] is True
    assert isinstance(res["result"], (int, float))
    assert res["result"] == 359760


def test_query_sorting(inventory_df):
    """Verify run_python_query handles sorting and head operations."""
    code = "df.sort_values(by='Number of Units Sold', ascending=False).head(3)[['Product ID', 'Product Name', 'Number of Units Sold']]"
    res = run_python_query(code, inventory_df)
    assert res["success"] is True
    assert len(res["result"]["records"]) == 3
    # Check descending order
    units = [r["Number of Units Sold"] for r in res["result"]["records"]]
    assert units == sorted(units, reverse=True)


def test_query_custom_calculation(inventory_df):
    """Verify run_python_query can execute multi-line calculations with intermediate variables."""
    code = """
total_cost = df['Cost Price Total (USD)'].sum()
total_stock = df['Hand-In-Stock'].sum()
avg_cost_per_item = total_cost / total_stock
result = round(avg_cost_per_item, 2)
"""
    res = run_python_query(code, inventory_df)
    assert res["success"] is True
    assert isinstance(res["result"], float)
    assert res["result"] > 0


def test_query_syntax_error():
    """Verify graceful handling of syntax errors."""
    code = "df[df['Opening Stock' > 10"  # Unclosed bracket
    res = run_python_query(code)
    assert res["success"] is False
    assert "SyntaxError" in res["error"]


def test_query_key_error():
    """Verify graceful handling of invalid column reference."""
    code = "df['NonExistentColumn'].mean()"
    res = run_python_query(code)
    assert res["success"] is False
    assert "KeyError" in res["error"]


def test_query_security_restriction():
    """Verify blocked imports and dangerous system operations."""
    code = "import os; os.listdir('.')"
    res = run_python_query(code)
    assert res["success"] is False
    assert "Security restriction" in res["error"]
