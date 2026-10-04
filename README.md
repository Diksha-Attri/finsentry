# FinSentry
# FinSentry: Autonomous Multi-Agent Financial Due Diligence Engine

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-FF6F00.svg?style=flat)](https://github.com/langchain-ai/langgraph)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20Store-DC382D.svg?style=flat&logo=qdrant)](https://qdrant.tech/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://img.shields.io/badge/mypy-strict-blue.svg)](https://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **FinSentry** is an enterprise-grade AI system designed for automated financial auditing and forensic due diligence across SEC EDGAR filings (Forms 10-K and 10-Q). Combining **Layout-Aware Ingestion**, **Hybrid RAG (Dense Qdrant + BM25 Lexical + FlashRank Re-ranking)**, and a **Cyclic Multi-Agent LangGraph Engine**, FinSentry automatically identifies material narrative-reality discrepancies, computes audited balance sheet metrics inside a sandboxed Python runtime, and enforces strict citation grounding.

---

## Key Differentiators

* **Layout-Aware Financial Matrix Normalization:** Converts complex HTML filing tables into structured Markdown matrices without decoupling line items from fiscal period headers.
* **Hybrid Retrieval (RRF k=60):** Fuses dense semantic vector representations in Qdrant with sparse BM25 token matching, re-ranked via a cross-encoder (FlashRank) to eliminate semantic dilution of exact numerical data.
* **Deterministic Math Sandbox:** Financial ratios (Current Ratio, Working Capital, Net Debt) are calculated via an isolated RestrictedPython runtime, completely removing probabilistic LLM math hallucinations.
* **Forensic Discrepancy Auditing:** Systematically contrasts executive claims in Item 7 (MD&A) with empirical balance sheet disclosures and statutory risk factors in Item 1A.
* **Self-Healing Reflection Loop:** If generated audit observations lack direct citations or fail consistency checks, the state graph routes through an automated self-healing validator loop.
* **Real-Time SSE Streaming:** Asynchronous FastAPI gateway pushing live agent execution states via Server-Sent Events (SSE).

---

## System Architecture

```text
                                  +---------------------------+
                                  |      SEC EDGAR API        |
                                  +-------------+-------------+
                                                | (Fair-Access Rate Limited)
                                                v
                                  +---------------------------+
                                  |    Layout-Aware Parser    |
                                  +------+-------------+------+
                                         |             |
                    +--------------------+             +--------------------+
                    v                                                       v
        +-------------------------+                             +-------------------------+
        | Structured Tables (.md) |                             |   Narrative Text (.p)   |
        +-----------+-------------+                             +-----------+-------------+
                    |                                                       |
                    v                                                       v
        +-------------------------+                             +-------------------------+
        |  Dense Qdrant Index     |                             |   Sparse BM25 Index     |
        |  (text-embedding-3)     |                             |   (Exact Token Match)   |
        +-----------+-------------+                             +-----------+-------------+
                    |                                                       |
                    +--------------------+             +--------------------+
                                         v             v
                                  +---------------------------+
                                  |  Reciprocal Rank Fusion   |
                                  |      (RRF Metric k=60)    |
                                  +-------------+-------------+
                                                | Top 20 Candidates
                                                v
                                  +---------------------------+
                                  |   FlashRank Cross-Encoder |
                                  |  (ms-marco-TinyBERT-L-2)  |
                                  +-------------+-------------+
                                                | Top 5 Compressed Context
                                                v
                                  +---------------------------+
                                  |  Supervisor Router Node   |
                                  +------+-------------+------+
                                         |             |
                   "FACTUAL_LOOKUP"      |             | "FULL_AUDIT"
                   (Direct Pass)         |             v
                         +---------------+   +-----------------------------------+
                         |                   | Quantitative Extraction Agent     |
                         |                   | (RestrictedPython Math Sandbox)   |
                         |                   +-----------------+-----------------+
                         |                                     v
                         |                   +-----------------------------------+
                         |                   | Qualitative Risk Auditor Agent    |
                         |                   | (Item 1A Covenants & Litigations) |
                         |                   +-----------------+-----------------+
                         |                                     v
                         |                   +-----------------------------------+
                         |                   | Discrepancy Cross-Auditor Agent   |
                         |                   | (Narrative Optimism vs Reality)   |
                         |                   +-----------------+-----------------+
                         |                                     v
                         |                   +-----------------------------------+
                         |       +-----------+   Guardrail Validator Node        |
                         |       | (Retries) +-----------------+-----------------+
                         |       v                             | (Validated)
                         |  [Retry Loop]                       v
                         +-------> +---------------------------------------------+
                                   |      FastAPI Gateway (SSE Stream / Sync)    |
                                   +---------------------------------------------+

PROJECT STRUCTURE 

finsentry/
├── backend/
│   ├── app/
│   │   ├── agents/            # LangGraph multi-agent orchestration
│   │   │   ├── discrepancy.py # Cross-audits rhetoric against metrics
│   │   │   ├── graph.py       # Compiled state machine & conditional edges
│   │   │   ├── llm_factory.py # Resilient LLM client with test fallbacks
│   │   │   ├── qual_agent.py  # Risk factor and covenant auditor
│   │   │   ├── quant_agent.py # Balance sheet and metric extractor
│   │   │   ├── router.py      # Query complexity supervisor router
│   │   │   ├── state.py       # Pydantic v2 multi-agent state definitions
│   │   │   └── validator.py   # Citation grounding and guardrail loop
│   │   ├── core/              # Global settings and environment config
│   │   ├── ingestion/         # SEC EDGAR client and layout-aware parser
│   │   ├── rag/               # Dense (Qdrant), Sparse (BM25), Hybrid RRF
│   │   ├── tools/             # RestrictedPython financial sandbox
│   │   └── main.py            # FastAPI gateway with SSE streaming
│   ├── evals/                 # Golden dataset & continuous evaluation runner
│   ├── tests/                 # Comprehensive pytest suite (10 unit/integration tests)
│   └── pyproject.toml         # Pinned project dependencies and tool configs
├── docker-compose.yml         # Local Qdrant and Redis infrastructure
├── Makefile                   # Developer automation lifecycle
└── README.md

Quickstart & Local Installation
Prerequisites
Python 3.12+

Docker & Docker Compose

Linux / macOS or Windows WSL2

1. Clone & Set Up Virtual Environment
git clone [https://github.com/Diksha-Attri/finsentry.git](https://github.com/Diksha-Attri/finsentry.git)
cd finsentry
make install
2. Configure Environment Variables
Bash
cp .env.example .env
3. Launch Local Infrastructure
Start the Qdrant vector database and Redis cache:

Bash
make up
Verify services:

Qdrant Web UI: http://localhost:6333/dashboard

Redis: localhost:6379

4. Run Verification Suite
Execute type-checking and automated test suites:

Bash
make typecheck
make test
Expected output:

Plaintext
Success: no issues found in 24 source files
======================== 10 passed in 7.31s ========================
Coverage: 83% across active packages
Running the API Gateway
Start the FastAPI development server:

Bash
make run
Access the interactive OpenAPI Swagger docs at: http://localhost:8000/docs

API Examples
1. Synchronous Audit Endpoint (POST /api/v1/audit/sync)
Bash
curl -X POST "http://localhost:8000/api/v1/audit/sync" \
     -H "Content-Type: application/json" \
     -d '{
       "ticker": "AAPL",
       "target_year": "2024",
       "query": "Verify balance sheet working capital and evaluate if management claims regarding sufficient liquidity match reality."
     }'
2. Real-Time SSE Stream (POST /api/v1/audit/stream)
Bash
curl -N -X POST "http://localhost:8000/api/v1/audit/stream" \
     -H "Content-Type: application/json" \
     -d '{
       "ticker": "AAPL",
       "target_year": "2024",
       "query": "Stream audit progress and risk findings."
     }'
Evaluation Benchmark
FinSentry uses an automated benchmark suite (backend/evals/eval_runner.py) running against a golden dataset to evaluate:

Faithfulness / Citation Grounding: 100% of generated audit flags must trace back to verbatim filing context.

Deterministic Metric Precision: 100% of ratio calculations must match balance sheet ground truth within acceptable ranges.

Discrepancy Recall: Successful detection of contradictions between MD&A claims and quantitative metrics.

To execute evaluations:

Bash
.venv/bin/pytest backend/tests/test_evals.py -v
License
Distributed under the MIT License.


---

