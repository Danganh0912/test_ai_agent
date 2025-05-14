import math
import re
from typing import Any, Dict
import sys
import os
current_dir = os.path.dirname(__file__)  
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

class CalculateTool:
    name = "calculate"
    description ="""Performs mathematical calculations and evaluations of expressions.
        Supports basic arithmetic operations, absolute values, commas in numbers,
        and multiple sub-expressions separated by 'and'."""
    inputs = "string to calculate"
    output_type = "string"

    @staticmethod
    def execute(expression: str) -> str:
        try:
            if not isinstance(expression, str):
                raise ValueError("Expression must be a string")

            expr = expression.replace(",", "")
            abs_pattern = r"\|([^|]+)\|"
            segments = re.findall(abs_pattern, expr)
            for seg in segments:
                val = CalculateTool._safe_eval(seg)
                expr = expr.replace(f"|{seg}|", str(abs(val)))

            if " and " in expr:
                parts = expr.split(" and ")
                results = [str(CalculateTool._safe_eval(p)) for p in parts]
                return " and ".join(results)

            return str(CalculateTool._safe_eval(expr))

        except Exception as e:
            return f"Error evaluating expression: {e}"

    @staticmethod
    def _safe_eval(expr: str) -> float:
        expr = expr.replace("×", "*").replace("÷", "/")
        allowed = set("0123456789.+-*/() ")
        if not all(c in allowed for c in expr):
            raise ValueError("Expression contains invalid characters")
        for kw in ("__", "import", "eval", "exec", "compile"):
            if kw in expr:
                raise ValueError("Unsafe expression")
        return eval(expr)

# if __name__ == "__main__":
#     tests = [
#         "|1876 - 1865| and |1889 - 1876|",
#         "100000000 * 2",
#         "1,127 - 283",
#         "828 - 381 and 900 - 500",
#         "125000000 / 378000 and 1366000000 / 3287000"
#     ]
#     for expr in tests:
#         print(f"Expression: {expr} -> Result: {CalculateTool.execute(expr)}")
