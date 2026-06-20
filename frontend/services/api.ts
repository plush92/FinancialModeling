import type { FinancialsResponse, IssuesResponse, QualityResponse } from "../types/financials";

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

