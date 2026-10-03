from dataclasses import dataclass
from pathlib import Path
import httpx
from app.core.config import get_settings

settings = get_settings()

SEC_SUBMISSIONS_API = "https://data.sec.gov/submissions/CIK{cik_10}.json"
SEC_ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{accession}.txt"


@dataclass(frozen=True)
class FilingMetadata:
    ticker: str
    cik: str
    accession_number: str
    form: str
    filing_date: str
    report_date: str


class EdgarClient:
    """Asynchronous client for retrieving filings directly from SEC EDGAR."""

    def __init__(self, user_agent: str | None = None) -> None:
        self.user_agent = user_agent or settings.SEC_EDGAR_USER_AGENT
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
        }

    async def get_company_cik(self, ticker: str) -> str:
        """Resolve a public ticker symbol to a zero-padded 10-digit SEC CIK."""
        ticker_upper = ticker.upper().strip()
        url = "https://www.sec.gov/files/company_tickers.json"

        async with httpx.AsyncClient(headers=self.headers, timeout=15.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        for entry in data.values():
            if entry.get("ticker") == ticker_upper:
                cik_int = entry["cik_str"]
                return str(cik_int).zfill(10)

        raise ValueError(f"Ticker symbol '{ticker}' not found in SEC database.")

    async def get_latest_10k_metadata(self, ticker: str) -> FilingMetadata:
        """Fetch metadata for the most recent 10-K filing of the given ticker."""
        cik_10 = await self.get_company_cik(ticker)
        url = SEC_SUBMISSIONS_API.format(cik_10=cik_10)

        async with httpx.AsyncClient(headers=self.headers, timeout=20.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        recent_filings = data["filings"]["recent"]
        forms = recent_filings["form"]

        for idx, form in enumerate(forms):
            if form == "10-K":
                accession = recent_filings["accessionNumber"][idx]
                return FilingMetadata(
                    ticker=ticker.upper(),
                    cik=str(int(cik_10)),
                    accession_number=accession,
                    form=form,
                    filing_date=recent_filings["filingDate"][idx],
                    report_date=recent_filings["reportDate"][idx],
                )

        raise FileNotFoundError(f"No 10-K filing found in recent submissions for {ticker}.")

    async def download_filing_raw(self, metadata: FilingMetadata, save_dir: Path | None = None) -> str:
        """Download raw filing content from SEC Archives."""
        accession_clean = metadata.accession_number.replace("-", "")
        url = SEC_ARCHIVES_BASE.format(
            cik=metadata.cik,
            accession_clean=accession_clean,
            accession=metadata.accession_number,
        )

        async with httpx.AsyncClient(headers=self.headers, timeout=60.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            content = response.text

        if save_dir:
            save_dir.mkdir(parents=True, exist_ok=True)
            output_file = save_dir / f"{metadata.ticker}_{metadata.report_date}_{metadata.form}.txt"
            output_file.write_text(content, encoding="utf-8")

        return content
