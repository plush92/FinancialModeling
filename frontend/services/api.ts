import type {
  GuidanceResponse,
  ForecastResponse,
  ForecastScenario,
  ForecastScenariosResponse,
  FinancialsResponse,
  IssuesResponse,
  MetricsResponse,
  NewsResponse,
  QualityResponse,
  RatiosResponse,
  ResearchResponse,
  RisksResponse,
  TimelineResponse,
  TrendsResponse,
} from "../types/financials";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function syncTicker(ticker: string): Promise<void> {
  await request(`/sync/${ticker}`, { method: "POST" });
}

export async function getFinancials(ticker: string): Promise<FinancialsResponse> {
  return request<FinancialsResponse>(`/financials/${ticker}`);
}

export async function getQuality(ticker: string): Promise<QualityResponse> {
  return request<QualityResponse>(`/quality/${ticker}`);
}

export async function getIssues(ticker: string): Promise<IssuesResponse> {
  return request<IssuesResponse>(`/issues/${ticker}`);
}

export async function getRatios(ticker: string): Promise<RatiosResponse> {
  return request<RatiosResponse>(`/ratios/${ticker}`);
}

export async function getMetrics(ticker: string): Promise<MetricsResponse> {
  return request<MetricsResponse>(`/metrics/${ticker}`);
}

export async function getTrends(ticker: string): Promise<TrendsResponse> {
  return request<TrendsResponse>(`/trends/${ticker}`);
}

export async function getResearch(ticker: string): Promise<ResearchResponse> {
  return request<ResearchResponse>(`/research/${ticker}`);
}

export async function getRisks(ticker: string): Promise<RisksResponse> {
  return request<RisksResponse>(`/risks/${ticker}`);
}

export async function getGuidance(ticker: string): Promise<GuidanceResponse> {
  return request<GuidanceResponse>(`/guidance/${ticker}`);
}

export async function getNews(ticker: string): Promise<NewsResponse> {
  return request<NewsResponse>(`/news/${ticker}`);
}

export async function getTimeline(ticker: string): Promise<TimelineResponse> {
  return request<TimelineResponse>(`/timeline/${ticker}`);
}

export async function createForecast(
  ticker: string,
  payload: {
    scenario: ForecastScenario;
    assumptions_version: string;
    horizon_years?: number;
    assumptions_override?: Record<string, unknown>;
  },
): Promise<ForecastResponse> {
  return request<ForecastResponse>(`/forecast/${ticker}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getForecast(
  ticker: string,
  scenario: ForecastScenario = "base",
  assumptionsVersion: string = "latest",
): Promise<ForecastResponse> {
  const params = new URLSearchParams({ scenario, assumptions_version: assumptionsVersion });
  return request<ForecastResponse>(`/forecast/${ticker}?${params.toString()}`);
}

export async function getForecastScenarios(
  ticker: string,
  assumptionsVersion: string = "latest",
): Promise<ForecastScenariosResponse> {
  const params = new URLSearchParams({ assumptions_version: assumptionsVersion });
  return request<ForecastScenariosResponse>(`/forecast/${ticker}/scenarios?${params.toString()}`);
}

