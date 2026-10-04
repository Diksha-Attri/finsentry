import math
from typing import Any
from RestrictedPython import compile_restricted, safe_globals  # type: ignore[import-untyped]
from RestrictedPython.PrintCollector import PrintCollector  # type: ignore[import-untyped]


class CodeSandboxExecutionError(Exception):
    """Raised when Python code in sandbox fails execution."""
    pass


class FinancialCodeSandbox:
    """Safe, isolated Python runtime for deterministic financial ratio calculations."""

    @staticmethod
    def execute_calculation(code_str: str) -> dict[str, Any]:
        """
        Executes restricted python code.
        Returns a dictionary of all computed local variables.
        """
        try:
            byte_code = compile_restricted(
                code_str,
                filename="<financial_calc>",
                mode="exec",
            )
        except SyntaxError as e:
            raise CodeSandboxExecutionError(f"Syntax error in calculation code: {e}") from e

        # Explicitly declare as dict[str, object] to satisfy strict mypy typing
        exec_globals: dict[str, object] = dict(safe_globals)
        exec_globals["_print_"] = PrintCollector
        exec_globals["math"] = math
        exec_globals["round"] = round
        exec_globals["abs"] = abs
        exec_globals["min"] = min
        exec_globals["max"] = max

        exec_locals: dict[str, Any] = {}

        try:
            exec(byte_code, exec_globals, exec_locals)  # noqa: S102
        except Exception as e:
            raise CodeSandboxExecutionError(f"Execution error in financial calculation: {e}") from e

        return {
            k: v
            for k, v in exec_locals.items()
            if not k.startswith("_") and not callable(v)
        }
