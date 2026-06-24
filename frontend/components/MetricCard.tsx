import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import TrendingFlatIcon from "@mui/icons-material/TrendingFlat";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import { Card, CardContent, Chip, Divider, Stack, Tooltip, Typography } from "@mui/material";

import type { RatioMetricSeries } from "../types/financials";
import { HistoricalRatioChart } from "./HistoricalRatioChart";

type Props = {
  metric: RatioMetricSeries;
};

function toFiniteNumber(value: number | string | null): number | null {
  if (value === null) {
    return null;
  }
  const parsed = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(parsed)) {
    return null;
  }
  return parsed;
}

function formatMetric(value: number | string | null, unit: string): string {
  const numericValue = toFiniteNumber(value);
  if (numericValue === null) {
    return "N/A";
  }
  if (unit === "percent") {
    return `${(numericValue * 100).toFixed(1)}%`;
  }
  if (unit === "currency") {
    return `$${(numericValue / 1_000_000).toFixed(1)}M`;
  }
  if (unit === "days") {
    return `${numericValue.toFixed(1)} days`;
  }
  return numericValue.toFixed(2);
}

function trendVisual(direction: RatioMetricSeries["trend_direction"]) {
  if (direction === "Improving") {
    return <Chip size="small" icon={<TrendingUpIcon />} color="success" label="Improving" />;
  }
  if (direction === "Deteriorating") {
    return <Chip size="small" icon={<TrendingDownIcon />} color="error" label="Deteriorating" />;
  }
  if (direction === "Stable") {
    return <Chip size="small" icon={<TrendingFlatIcon />} color="default" label="Stable" />;
  }
  return <Chip size="small" variant="outlined" label="Insufficient history" />;
}

export function MetricCard({ metric }: Props) {
  return (
    <Card variant="outlined" sx={{ height: "100%" }}>
      <CardContent>
        <Stack spacing={1.25}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
            <Tooltip title={`Formula: ${metric.formula} | Source metrics: ${metric.source_metrics.join(", ")}`}>
              <Typography variant="subtitle1" sx={{ cursor: "help" }}>
                {metric.display_name}
              </Typography>
            </Tooltip>
            {trendVisual(metric.trend_direction)}
          </Stack>

          <Typography variant="h5">{formatMetric(metric.latest_value, metric.unit)}</Typography>

          <Divider />
          <HistoricalRatioChart points={metric.history} unit={metric.unit} />

          <Typography variant="caption" color="text.secondary">
            Inputs used: {Object.entries(metric.latest_inputs_used)
              .map(([key, value]) => `${key}=${value ?? "N/A"}`)
              .join(", ")}
          </Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}
