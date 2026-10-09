"""Controlled Python and Pandas query execution engine for Excel data analysis."""

import io
import sys
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

from q1_excel_agent.data_loader import load_inventory_dataset


_CACHED_DF: Optional[pd.DataFrame] = None


def get_dataframe(df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Retrieve the working copy of the inventory DataFrame."""
    global _CACHED_DF
    if df is not None:
        return df
    if _CACHED_DF is None:
        _CACHED_DF = load_inventory_dataset()
    return _CACHED_DF


# Restricted built-ins to prevent arbitrary file or system calls
SAFE_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "filter": filter,
    "float": float,
    "int": int,
    "isinstance": isinstance,
    "len": len,
    "list": list,
    "map": map,
    "max": max,
    "min": min,
    "print": print,
    "range": range,
    "round": round,
    "set": set,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
    "True": True,
    "False": False,
    "None": None,
}

DISALLOWED_PATTERNS = [
    "__import__",
    "importlib",
    "os.",
    "sys.",
    "subprocess",
    "shutil",
    "open(",
    "socket",
    "requests",
    "eval(",
    "exec(",
]


def run_python_query(code: str, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Execute controlled Pandas and Python code against the inventory DataFrame.
    
    Parameters:
        code: Python snippet to run. The loaded DataFrame is available as `df`.
              If the code assigns to `result` or ends with an expression, that value is captured.
        df: Optional DataFrame to execute on. Defaults to cached inventory dataset.
        
    Returns:
        dict with keys:
            - success (bool): Whether execution completed without error
            - result (Any): Output value, dictionary, scalar, or serialized DataFrame/Series
            - stdout (str): Any printed standard output
            - error (Optional[str]): Error message if execution failed
    """
    # 1. Security pre-check
    for pattern in DISALLOWED_PATTERNS:
        if pattern in code:
            return {
                "success": False,
                "result": None,
                "stdout": "",
                "error": f"Security restriction: Operation '{pattern}' is not permitted.",
            }

    working_df = get_dataframe(df)
    # Use a copy so operations do not accidentally corrupt working dataset
    local_df = working_df.copy()

    local_vars: Dict[str, Any] = {
        "df": local_df,
        "pd": pd,
        "np": np,
        "result": None,
    }
    global_env: Dict[str, Any] = {
        "__builtins__": SAFE_BUILTINS,
    }

    stdout_capture = io.StringIO()
    old_stdout = sys.stdout

    try:
        sys.stdout = stdout_capture

        cleaned_code = code.strip()
        lines = cleaned_code.splitlines()

        # If it's a single expression, evaluate directly
        if len(lines) == 1 and not lines[0].startswith(("import ", "from ", "def ", "for ", "if ", "while ", "result =")):
            try:
                eval_val = eval(cleaned_code, global_env, local_vars)
                local_vars["result"] = eval_val
            except SyntaxError:
                exec(cleaned_code, global_env, local_vars)
        else:
            # If the last line looks like an expression (not an assignment or control flow), capture it as result
            last_line = lines[-1].strip()
            if (
                not last_line.startswith(("import ", "from ", "def ", "for ", "if ", "while ", "return ", "#"))
                and "=" not in last_line
            ):
                exec_code = "\n".join(lines[:-1]) + f"\nresult = ({last_line})"
            else:
                exec_code = cleaned_code

            exec(exec_code, global_env, local_vars)

        raw_result = local_vars.get("result")
        stdout_output = stdout_capture.getvalue()

        # Format result nicely for presentation and programmatic use
        formatted_result: Any = None
        if isinstance(raw_result, pd.DataFrame):
            formatted_result = {
                "type": "DataFrame",
                "shape": list(raw_result.shape),
                "columns": list(raw_result.columns),
                "records": raw_result.to_dict(orient="records"),
            }
        elif isinstance(raw_result, pd.Series):
            formatted_result = {
                "type": "Series",
                "name": raw_result.name,
                "data": raw_result.to_dict(),
            }
        elif isinstance(raw_result, (np.integer, np.floating)):
            formatted_result = raw_result.item()
        elif isinstance(raw_result, (int, float, str, bool, list, dict)):
            formatted_result = raw_result
        elif raw_result is None and stdout_output.strip():
            formatted_result = stdout_output.strip()
        else:
            formatted_result = str(raw_result)

        return {
            "success": True,
            "result": formatted_result,
            "stdout": stdout_output,
            "error": None,
        }

    except Exception as e:
        return {
            "success": False,
            "result": None,
            "stdout": stdout_capture.getvalue(),
            "error": f"{type(e).__name__}: {str(e)}",
        }
    finally:
        sys.stdout = old_stdout

