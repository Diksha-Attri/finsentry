from typing import Annotated, Literal
from pydantic import BaseModel, Field
import operator


class Citation(BaseModel):
    document_id: str = Field(description="Document reference or accession number.")
    section: str = Field(description="SEC item or footnote section, e.g., 'Item 8, Note 4'.")
    table_index: int | None = Field(default=None, description="Index of table if extracted from tabular data.")
    exact_quote_or_value: str = Field(description="Verbatim text quote or numerical figure cited.")


class QuantitativeMetric(BaseModel):
    name: str = Field(description="Name of metric, e.g., 'Current Ratio', 'Total Debt', 'Operating Margin'.")
    value_current_period: float = Field(description="Value in target fiscal period.")
    value_prior_period: float | None = Field(default=None, description="Value in preceding fiscal period.")
    yoy_change_percentage: float | None = Field(default=None, description="Year-over-Year percentage change.")
    formula_used: str = Field(description="Exact mathematical formula executed by python sandbox.")
    citation: Citation


class AuditFlag(BaseModel):
    id: str = Field(description="Unique flag identifier, e.g., 'FLAG-LIQ-001'.")
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(description="Severity assessment.")
    category: Literal["LIQUIDITY", "SOLVENCY", "DISCREPANCY", "COVENANT", "ACCOUNTING_POLICY"] = Field(
        description="Category of the audit observation."
    )
    narrative_claim: str = Field(description="Executive statement made in MD&A or Item 1/1A.")
    factual_reality: str = Field(description="Underlying financial reality discovered in statements/footnotes.")
    explanation: str = Field(description="Reasoning explaining why this constitutes a discrepancy or risk.")
    citations: list[Citation] = Field(default_factory=list, description="Grounding source citations.")


class FinSentryState(BaseModel):
    # Workflow Context
    ticker: str
    target_year: str
    comparison_year: str | None = None
    query: str
    
    # Trace & Session
    session_id: str = Field(default="default_session")
    
    # Agent Communication Log
    messages: Annotated[list[dict[str, str]], operator.add] = []
    
    # Financial Findings
    quantitative_metrics: Annotated[list[QuantitativeMetric], operator.add] = []
    audit_flags: Annotated[list[AuditFlag], operator.add] = []
    
    # Graph Control & Self-Healing
    retry_count: int = 0
    max_retries: int = 2
    validation_passed: bool = False
    validation_error: str | None = None
    requires_human_review: bool = False
    
    # Final Output
    final_audit_report: str | None = None
