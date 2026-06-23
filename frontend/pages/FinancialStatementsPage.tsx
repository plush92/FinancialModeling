import { Alert, Box, CircularProgress, Stack, Typography } from "@mui/material";
import { useState } from "react";

import { BalanceSheetTable } from "../components/BalanceSheetTable";
import { CashFlowTable } from "../components/CashFlowTable";
import { DataQualityCard } from "../components/DataQualityCard";
import { IncomeStatementTable } from "../components/IncomeStatementTable";
import { RatioDashboard } from "../components/RatioDashboard";
import { TickerSearch } from "../components/TickerSearch";
import { TrendAnalysisPanel } from "../components/TrendAnalysisPanel";
import { ValidationIssuesTable } from "../components/ValidationIssuesTable";
import { getFinancials, getIssues, getQuality, getRatios, getTrends, syncTicker } from "../services/api";
import type { FinancialsResponse, IssuesResponse, QualityResponse, RatiosResponse, TrendsResponse } from "../types/financials";

export function FinancialStatementsPage() {
  const [data, setData] = useState<FinancialsResponse | null>(null);
  const [quality, setQuality] = useState<QualityResponse | null>(null);
  const [issues, setIssues] = useState<IssuesResponse | null>(null);
  const [ratios, setRatios] = useState<RatiosResponse | null>(null);
  const [trends, setTrends] = useState<TrendsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (ticker: string) => {
    setLoading(true);
    setError(null);
    try {
      await syncTicker(ticker);
      const [financialsResponse, qualityResponse, issuesResponse, ratiosResponse, trendsResponse] = await Promise.all([
        getFinancials(ticker),
        getQuality(ticker),
        getIssues(ticker),
        getRatios(ticker),
        getTrends(ticker),
      ]);
      setData(financialsResponse);
      setQuality(qualityResponse);
      setIssues(issuesResponse);
      setRatios(ratiosResponse);
      setTrends(trendsResponse);
    } catch (err) {
      setData(null);
      setQuality(null);
      setIssues(null);
      setRatios(null);
      setTrends(null);
      setError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4" gutterBottom>
          Historical Financial Statements
        </Typography>
        <Typography color="text.secondary">
          Enter a ticker to sync SEC data and view historical income statement, balance sheet, and cash flow values.
        </Typography>
      </Box>

      <TickerSearch isLoading={loading} onSearch={handleSearch} />

      {loading && (
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <CircularProgress size={24} />
          <Typography>Loading financial statements...</Typography>
        </Box>
      )}

      {error && <Alert severity="error">{error}</Alert>}

      {data && (
        <Stack spacing={2}>
          <Alert severity="info">
            {data.company.company_name} ({data.company.ticker}) - CIK: {data.company.cik ?? "N/A"}
          </Alert>
          {quality && <DataQualityCard quality={quality} />}
          {ratios && <RatioDashboard ratios={ratios} />}
          {trends && <TrendAnalysisPanel trends={trends.trends} />}
          {issues && <ValidationIssuesTable issues={issues} />}
          <IncomeStatementTable rows={data.income_statements} />
          <BalanceSheetTable rows={data.balance_sheets} />
          <CashFlowTable rows={data.cash_flow_statements} />
        </Stack>
      )}
    </Stack>
  );
}
