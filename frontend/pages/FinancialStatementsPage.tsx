import { Alert, Box, CircularProgress, Stack, Typography } from "@mui/material";
import { useState } from "react";

import { BalanceSheetTable } from "../components/BalanceSheetTable";
import { CashFlowTable } from "../components/CashFlowTable";
import { DataQualityCard } from "../components/DataQualityCard";
import { ForecastDashboard } from "../components/ForecastDashboard";
import { IncomeStatementTable } from "../components/IncomeStatementTable";
import { KeyMetricsChartsPanel } from "../components/KeyMetricsChartsPanel";
import { RatioDashboard } from "../components/RatioDashboard";
import { ResearchDashboard } from "../components/ResearchDashboard";
import { SummaryInsightsPanel } from "../components/SummaryInsightsPanel";
import { TickerSearch } from "../components/TickerSearch";
import { TrendAnalysisPanel } from "../components/TrendAnalysisPanel";
import { ValidationIssuesTable } from "../components/ValidationIssuesTable";
import {
  getFinancials,
  getGuidance,
  getIssues,
  getNews,
  getQuality,
  getRatios,
  getResearch,
  getRisks,
  getTimeline,
  getTrends,
  syncTicker,
} from "../services/api";
import type {
  FinancialsResponse,
  GuidanceResponse,
  IssuesResponse,
  NewsResponse,
  QualityResponse,
  RatiosResponse,
  ResearchResponse,
  RisksResponse,
  TimelineResponse,
  TrendsResponse,
} from "../types/financials";

export function FinancialStatementsPage() {
  const [activeTicker, setActiveTicker] = useState<string | null>(null);
  const [data, setData] = useState<FinancialsResponse | null>(null);
  const [quality, setQuality] = useState<QualityResponse | null>(null);
  const [issues, setIssues] = useState<IssuesResponse | null>(null);
  const [ratios, setRatios] = useState<RatiosResponse | null>(null);
  const [trends, setTrends] = useState<TrendsResponse | null>(null);
  const [research, setResearch] = useState<ResearchResponse | null>(null);
  const [risks, setRisks] = useState<RisksResponse | null>(null);
  const [guidance, setGuidance] = useState<GuidanceResponse | null>(null);
  const [news, setNews] = useState<NewsResponse | null>(null);
  const [timeline, setTimeline] = useState<TimelineResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (ticker: string) => {
    const normalizedTicker = ticker.trim().toUpperCase();
    setLoading(true);
    setError(null);
    try {
      await syncTicker(normalizedTicker);
      const [
        financialsResponse,
        qualityResponse,
        issuesResponse,
        ratiosResponse,
        trendsResponse,
        researchResponse,
        risksResponse,
        guidanceResponse,
        newsResponse,
        timelineResponse,
      ] = await Promise.all([
        getFinancials(normalizedTicker),
        getQuality(normalizedTicker),
        getIssues(normalizedTicker),
        getRatios(normalizedTicker),
        getTrends(normalizedTicker),
        getResearch(normalizedTicker),
        getRisks(normalizedTicker),
        getGuidance(normalizedTicker),
        getNews(normalizedTicker),
        getTimeline(normalizedTicker),
      ]);
      setActiveTicker(normalizedTicker);
      setData(financialsResponse);
      setQuality(qualityResponse);
      setIssues(issuesResponse);
      setRatios(ratiosResponse);
      setTrends(trendsResponse);
      setResearch(researchResponse);
      setRisks(risksResponse);
      setGuidance(guidanceResponse);
      setNews(newsResponse);
      setTimeline(timelineResponse);
    } catch (err) {
      setActiveTicker(null);
      setData(null);
      setQuality(null);
      setIssues(null);
      setRatios(null);
      setTrends(null);
      setResearch(null);
      setRisks(null);
      setGuidance(null);
      setNews(null);
      setTimeline(null);
      setError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshResearch = () => {
    if (!activeTicker || loading) {
      return;
    }
    void handleSearch(activeTicker);
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
          {ratios && (
            <Typography color="text.secondary">
              Engine v{ratios.calculation_version} | Generated {new Date(ratios.generated_at).toLocaleString()}
            </Typography>
          )}
          <SummaryInsightsPanel ratios={ratios} trends={trends} issues={issues} quality={quality} />
          <KeyMetricsChartsPanel financials={data} ratios={ratios} />
          {quality && <DataQualityCard quality={quality} />}
          {ratios && <RatioDashboard ratios={ratios} />}
          {trends && <TrendAnalysisPanel trends={trends.trends} />}
          {research && risks && guidance && news && timeline && (
            <ResearchDashboard
              research={research}
              risks={risks}
              guidance={guidance}
              news={news}
              timeline={timeline}
              onRefresh={handleRefreshResearch}
              isRefreshing={loading}
            />
          )}
          {issues && <ValidationIssuesTable issues={issues} />}
          {activeTicker && <ForecastDashboard ticker={activeTicker} />}
          <IncomeStatementTable rows={data.income_statements} />
          <BalanceSheetTable rows={data.balance_sheets} />
          <CashFlowTable rows={data.cash_flow_statements} />
        </Stack>
      )}
    </Stack>
  );
}
