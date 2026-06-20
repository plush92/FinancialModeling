from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings

settings = get_settings()


class SECClientError(RuntimeError):
    pass


class SECClient:
    ticker_map_url = "https://www.sec.gov/files/company_tickers.json"
    submissions_url_template = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
    company_facts_url_template = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

    def _request_json(self, url: str) -> dict[str, Any]:
        request = Request(url, headers={"User-Agent": settings.sec_user_agent})
        try:
            with urlopen(request, timeout=settings.sec_request_timeout_seconds) as response:
                payload = response.read().decode("utf-8", errors="replace")
                return json.loads(payload)
        except (HTTPError, URLError) as exc:
            raise SECClientError(f"SEC request failed for {url}: {exc}") from exc

    def resolve_cik(self, ticker: str) -> int:
        payload = self._request_json(self.ticker_map_url)
        normalized = ticker.upper().strip()
        for row in payload.values():
            if str(row.get("ticker", "")).upper() == normalized:
                return int(row["cik_str"])
        raise SECClientError(f"Unable to resolve CIK for ticker {ticker}.")

    def get_submissions(self, cik: int) -> dict[str, Any]:
        return self._request_json(self.submissions_url_template.format(cik=cik))

    def get_company_facts(self, cik: int) -> dict[str, Any]:
        return self._request_json(self.company_facts_url_template.format(cik=cik))
