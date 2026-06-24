export type Company = {
  id: number;
  ticker: string;
  company_name: string;
  cik: number | null;
};

export type IncomeStatement = {
  id: number;
  company_id: number;
  fiscal_year: number;
  fiscal_period: string;
  revenue: number;
  gross_profit: number;
  operating_income: number;
  net_income: number;
  eps: number;
};

export type BalanceSheet = {
  id: number;
  company_id: number;
  fiscal_year: number;
  fiscal_period: string;
  cash: number;
  total_assets: number;
  total_liabilities: number;
  shareholder_equity: number;
  total_debt: number;
};

export type CashFlowStatement = {
  id: number;
  company_id: number;
  fiscal_year: number;
  fiscal_period: string;
  operating_cash_flow: number;
  capex: number;
  free_cash_flow: number;
};

export type FinancialsResponse = {
  company: Company;
  income_statements: IncomeStatement[];
  balance_sheets: BalanceSheet[];
  cash_flow_statements: CashFlowStatement[];
};

export type QualityResponse = {
  quality_score: number;
  warnings: string[];
  errors: string[];
};

export type ValidationIssue = {
  id: number;
  severity: string;
  rule_name: string;
  description: string;
  filing_id: number | null;
  created_at: string;
};

export type MappingException = {
  id: number;
  xbrl_tag: string | null;
  attempted_field: string;
  confidence: number | null;
  notes: string | null;
  filing_id: number | null;
  created_at: string;
};

export type IssuesResponse = {
  validation_issues: ValidationIssue[];
  mapping_exceptions: MappingException[];
};

export type MetricPoint = {
  fiscal_year: number;
  fiscal_period: string;
  value: number | string | null;
};

export type RatioMetricSeries = {
  metric_name: string;
  display_name: string;
  category: string;
  unit: "percent" | "multiple" | "days" | "currency" | string;
  formula: string;
  source_metrics: string[];
  latest_inputs_used: Record<string, number | string | null>;
  history: MetricPoint[];
  latest_value: number | string | null;
  trend_direction: "Improving" | "Stable" | "Deteriorating" | null;
};

export type KPISummary = {
  metric_name: string;
  display_name: string;
  category: string;
  unit: "percent" | "multiple" | "days" | "currency" | string;
  value: number | string | null;
  trend_direction: "Improving" | "Stable" | "Deteriorating" | null;
};

export type RatiosResponse = {
  ticker: string;
  company_id: number;
  calculation_version: string;
  generated_at: string;
  historical_periods: Array<{
    fiscal_year: number;
    fiscal_period: string;
    metrics: Record<string, number | null>;
  }>;
  sections: Record<string, RatioMetricSeries[]>;
  kpi_summary: KPISummary[];
};

export type FinancialMetric = {
  id: number;
  company_id: number;
  fiscal_year: number;
  fiscal_period: string;
  period_type: "annual" | "quarterly";
  metric_name: string;
  metric_value: number | null;
  formula: string;
  inputs_used: Record<string, number | string | null>;
  source_metrics: string[];
  calculation_version: string;
  created_at: string;
};

export type MetricsResponse = {
  ticker: string;
  company_id: number;
  calculation_version: string;
  metrics: FinancialMetric[];
};

export type MetricTrend = {
  metric_name: string;
  display_name: string;
  category: string;
  latest_value: number | string | null;
  previous_value: number | string | null;
  cagr_3y: number | string | null;
  cagr_5y: number | string | null;
  rolling_average_3_periods: number | string | null;
  trend_direction: "Improving" | "Stable" | "Deteriorating" | null;
};

export type TrendsResponse = {
  ticker: string;
  company_id: number;
  calculation_version: string;
  trends: MetricTrend[];
};

export type ResearchDocument = {
  id: number;
  company_id: number;
  document_type: string;
  source: string;
  publication_date: string;
  title: string;
  summary: string;
  source_document_url: string | null;
  key_findings: Record<string, unknown>;
  extraction_timestamp: string;
  confidence_score: number;
  supporting_text_excerpt: string | null;
  created_at: string;
};

export type ResearchRisk = {
  id: number;
  company_id: number;
  publication_date: string;
  risk_category: string;
  description: string;
  severity: string;
  confidence: number;
  source_document: string;
  extraction_timestamp: string;
  supporting_text_excerpt: string | null;
  created_at: string;
};

export type GuidanceRecord = {
  id: number;
  company_id: number;
  publication_date: string;
  guidance_type: string;
  guidance_value: string;
  confidence: number;
  source_document: string;
  extraction_timestamp: string;
  supporting_text_excerpt: string | null;
  created_at: string;
};

export type NewsEvent = {
  id: number;
  company_id: number;
  publication_date: string;
  event_type: string;
  event_category: string;
  sentiment: "Positive" | "Neutral" | "Negative" | string;
  importance_score: number;
  confidence_score: number;
  source: string;
  headline: string;
  event_summary: string;
  source_document: string;
  extraction_timestamp: string;
  supporting_text_excerpt: string | null;
  created_at: string;
};

export type TimelineItem = {
  date: string;
  item_type: string;
  title: string;
  summary: string;
  filing_type?: string | null;
  sentiment?: string | null;
  importance_score?: number | null;
  confidence_score?: number | null;
  source_document?: string | null;
  source_document_url?: string | null;
};

export type ResearchSummaryCardData = {
  total_documents: number;
  total_risks: number;
  total_guidance_updates: number;
  total_news_events: number;
  negative_news_count: number;
};

export type ResearchResponse = {
  ticker: string;
  company_id: number;
  generated_at: string;
  summary_card: ResearchSummaryCardData;
  documents: ResearchDocument[];
  key_risks: ResearchRisk[];
  guidance_updates: GuidanceRecord[];
  recent_news_events: NewsEvent[];
};

export type RisksResponse = {
  ticker: string;
  company_id: number;
  risks: ResearchRisk[];
};

export type GuidanceResponse = {
  ticker: string;
  company_id: number;
  guidance: GuidanceRecord[];
};

export type NewsResponse = {
  ticker: string;
  company_id: number;
  news_events: NewsEvent[];
};

export type TimelineResponse = {
  ticker: string;
  company_id: number;
  timeline: TimelineItem[];
};
