import { Card, CardContent, CardHeader, Stack, ToggleButton, ToggleButtonGroup, Typography } from "@mui/material";
import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { FinancialsResponse, RatiosResponse } from "../types/financials";

type Props = {
  financials: FinancialsResponse;
  ratios: RatiosResponse | null;
};

type PeriodMode = "quarterly" | "annual" | "all";

type MetricKey = "revenue" | "gross_profit" | "net_income" | "free_cash_flow" | "debt_to_equity" | "roic";

type DataPoint = {
  periodKey: string;
  periodLabel: string;
  periodType: "quarterly" | "annual";
  revenue?: number;
  gross_profit?: number;
  net_income?: number;
  free_cash_flow?: number;
  debt_to_equity?: number;
  roic?: number;
};

type MetricMeta = {
  label: string;
  color: string;
  domain: "currency" | "ratio";
};

const QUARTER_ORDER: Record<string, number> = {
  Q1: 1,
  Q2: 2,
  Q3: 3,
  Q4: 4,
  FY: 5,
};

const METRICS: Record<MetricKey, MetricMeta> = {
  revenue: { label: "Revenue", color: "#1d4ed8", domain: "currency" },
  gross_profit: { label: "Gross Profit", color: "#0ea5e9", domain: "currency" },
  net_income: { label: "Net Income", color: "#14b8a6", domain: "currency" },
  free_cash_flow: { label: "Free Cash Flow", color: "#16a34a", domain: "currency" },
  debt_to_equity: { label: "Debt-to-Equity", color: "#f59e0b", domain: "ratio" },
  roic: { label: "ROIC", color: "#ef4444", domain: "ratio" },
};

const DEFAULT_SELECTED: MetricKey[] = [
  "revenue",
  "gross_profit",
  "net_income",
  "free_cash_flow",
  "debt_to_equity",
  "roic",
];

function toMillions(value: number): string {
  if (Math.abs(value) >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(1)}B`;
  }
  return `${(value / 1_000_000).toFixed(1)}M`;
}

function comparePeriod(a: { fiscal_year: number; fiscal_period: string }, b: { fiscal_year: number; fiscal_period: string }): number {
  if (a.fiscal_year !== b.fiscal_year) {
    return a.fiscal_year - b.fiscal_year;
  }
  return (QUARTER_ORDER[a.fiscal_period] ?? 0) - (QUARTER_ORDER[b.fiscal_period] ?? 0);
}

function getRatioHistory(ratios: RatiosResponse | null, metricName: string) {
  if (!ratios) {
    return [] as Array<{ fiscal_year: number; fiscal_period: string; value: number }>;
  }

  for (const section of Object.values(ratios.sections)) {
    const metric = section.find((item) => item.metric_name === metricName);
    if (metric) {
      return metric.history
        .map((point) => ({
          fiscal_year: point.fiscal_year,
          fiscal_period: point.fiscal_period,
          value: Number(point.value),
        }))
        .filter((point) => Number.isFinite(point.value));
    }
  }

  return [] as Array<{ fiscal_year: number; fiscal_period: string; value: number }>;
}

function buildChartData(financials: FinancialsResponse, ratios: RatiosResponse | null): DataPoint[] {
  const map = new Map<string, DataPoint>();

  const upsert = (fiscalYear: number, fiscalPeriod: string): DataPoint => {
    const key = `${fiscalYear}-${fiscalPeriod}`;
    const existing = map.get(key);
    if (existing) {
      return existing;
    }

    const row: DataPoint = {
      periodKey: key,
      periodLabel: `${fiscalYear} ${fiscalPeriod}`,
      periodType: fiscalPeriod === "FY" ? "annual" : "quarterly",
    };
    map.set(key, row);
    return row;
  };

  for (const row of financials.income_statements) {
    const data = upsert(row.fiscal_year, row.fiscal_period);
    data.revenue = Number(row.revenue);
    data.gross_profit = Number(row.gross_profit);
    data.net_income = Number(row.net_income);
  }

  for (const row of financials.cash_flow_statements) {
    const data = upsert(row.fiscal_year, row.fiscal_period);
    data.free_cash_flow = Number(row.free_cash_flow);
  }

  const debtToEquityHistory = getRatioHistory(ratios, "debt_to_equity");
  for (const point of debtToEquityHistory) {
    const data = upsert(point.fiscal_year, point.fiscal_period);
    data.debt_to_equity = point.value;
  }

  const roicHistory = getRatioHistory(ratios, "roic");
  for (const point of roicHistory) {
    const data = upsert(point.fiscal_year, point.fiscal_period);
    data.roic = point.value;
  }

  return Array.from(map.values()).sort((a, b) =>
    comparePeriod(
      { fiscal_year: Number(a.periodKey.split("-")[0]), fiscal_period: a.periodKey.split("-")[1] },
      { fiscal_year: Number(b.periodKey.split("-")[0]), fiscal_period: b.periodKey.split("-")[1] }
    )
  );
}

export function KeyMetricsChartsPanel({ financials, ratios }: Props) {
  const [periodMode, setPeriodMode] = useState<PeriodMode>("all");
  const [selected, setSelected] = useState<MetricKey[]>(DEFAULT_SELECTED);

  const baseData = useMemo(() => buildChartData(financials, ratios), [financials, ratios]);

  const data = useMemo(() => {
    if (periodMode === "all") {
      return baseData;
    }
    return baseData.filter((point) => point.periodType === periodMode);
  }, [baseData, periodMode]);

  const currencyMetrics = selected.filter((key) => METRICS[key].domain === "currency");
  const ratioMetrics = selected.filter((key) => METRICS[key].domain === "ratio");

  return (
    <Card>
      <CardHeader
        title="Key Metrics Charts"
        subheader="Interactive history for Revenue, Gross Profit, Net Income, Free Cash Flow, Debt-to-Equity, and ROIC"
      />
      <CardContent>
        <Stack spacing={2}>
          <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} justifyContent="space-between">
            <ToggleButtonGroup
              exclusive
              size="small"
              value={periodMode}
              onChange={(_, value: PeriodMode | null) => value && setPeriodMode(value)}
            >
              <ToggleButton value="quarterly">Quarterly</ToggleButton>
              <ToggleButton value="annual">Annual</ToggleButton>
              <ToggleButton value="all">All</ToggleButton>
            </ToggleButtonGroup>

            <ToggleButtonGroup
              size="small"
              value={selected}
              onChange={(_, value: MetricKey[]) => {
                if (value.length > 0) {
                  setSelected(value);
                }
              }}
            >
              {Object.entries(METRICS).map(([key, meta]) => (
                <ToggleButton key={key} value={key}>
                  {meta.label}
                </ToggleButton>
              ))}
            </ToggleButtonGroup>
          </Stack>

          <Stack spacing={1}>
            <Typography variant="subtitle2">Income & Cash Metrics</Typography>
            {currencyMetrics.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                Select at least one income or cash metric to render this chart.
              </Typography>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={data} margin={{ top: 8, right: 24, left: 8, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="periodLabel" minTickGap={18} />
                  <YAxis tickFormatter={(value) => toMillions(Number(value))} />
                  <Tooltip
                    labelFormatter={(label) => `Period: ${label}`}
                  />
                  <Legend />
                  {currencyMetrics.map((key) => (
                    <Line
                      key={key}
                      type="monotone"
                      dataKey={key}
                      name={METRICS[key].label}
                      stroke={METRICS[key].color}
                      strokeWidth={2}
                      dot={{ r: 2 }}
                      activeDot={{ r: 5 }}
                      connectNulls
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            )}
          </Stack>

          <Stack spacing={1}>
            <Typography variant="subtitle2">Capital Structure & Return Metrics</Typography>
            {ratioMetrics.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                Select Debt-to-Equity or ROIC to render this chart.
              </Typography>
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={data} margin={{ top: 8, right: 24, left: 8, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="periodLabel" minTickGap={18} />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(label) => `Period: ${label}`}
                  />
                  <Legend />
                  {ratioMetrics.map((key) => (
                    <Line
                      key={key}
                      type="monotone"
                      dataKey={key}
                      name={METRICS[key].label}
                      stroke={METRICS[key].color}
                      strokeWidth={2}
                      dot={{ r: 2 }}
                      activeDot={{ r: 5 }}
                      connectNulls
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            )}
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
}
