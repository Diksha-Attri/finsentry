import pytest
from app.tools.code_sandbox import FinancialCodeSandbox, CodeSandboxExecutionError


def test_financial_sandbox_valid_calculation() -> None:
    code = """
current_assets = 145000.0
current_liabilities = 82000.0
current_ratio = round(current_assets / current_liabilities, 2)
working_capital = current_assets - current_liabilities
"""
    results = FinancialCodeSandbox.execute_calculation(code)
    assert results["current_ratio"] == 1.77
    assert results["working_capital"] == 63000.0


def test_financial_sandbox_blocks_dangerous_operations() -> None:
    dangerous_code = """
import os
os.listdir('/')
"""
    with pytest.raises(CodeSandboxExecutionError):
        FinancialCodeSandbox.execute_calculation(dangerous_code)
