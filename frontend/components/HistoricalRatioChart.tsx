import { Box, Stack, Typography } from "@mui/material";

import type { MetricPoint } from "../types/financials";

type Props = {
  points: MetricPoint[];
  unit: string;
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

function normalize(points: MetricPoint[]): number[] {
  const values = points
    .map((point) => toFiniteNumber(point.value))
    .filter((value): value is number => value !== null);
  if (values.length === 0) {
    return [];
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  if (min === max) {
    return points.map(() => 50);
  }

  return points.map((point) => {
    const numericValue = toFiniteNumber(point.value);
    if (numericValue === null) {
      return 50;
    }
    return ((numericValue - min) / (max - min)) * 100;
  });
}

function formatPoint(value: number | string | null, unit: string): string {
  const numericValue = toFiniteNumber(value);
  if (numericValue === null) {
    return "N/A";
  }
  if (unit === "percent") {
    return `${(numericValue * 100).toFixed(1)}%`;
  }
  if (unit === "days") {
    return `${numericValue.toFixed(1)}d`;
  }
  if (unit === "currency") {
    return `$${(numericValue / 1_000_000).toFixed(1)}M`;
  }
  return numericValue.toFixed(2);
}

export function HistoricalRatioChart({ points, unit }: Props) {
  if (points.length === 0) {
    return <Typography variant="body2" color="text.secondary">No historical points.</Typography>;
  }

  const normalized = normalize(points);
  const width = 250;
  const height = 90;
  const step = points.length > 1 ? width / (points.length - 1) : width;

  const coordinates = normalized
    .map((value, index) => {
      const x = index * step;
      const y = height - (value / 100) * height;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <Stack spacing={0.5}>
      <Box sx={{ width: "100%", overflowX: "auto" }}>
        <svg width={width} height={height + 10} role="img" aria-label="Historical metric line chart">
          <polyline
            fill="none"
            stroke="#0f4c81"
            strokeWidth={2}
            points={coordinates}
          />
          {normalized.map((value, index) => {
            const x = index * step;
            const y = height - (value / 100) * height;
            return <circle key={`${x}-${y}`} cx={x} cy={y} r={2.8} fill="#2a9d8f" />;
          })}
        </svg>
      </Box>
      <Typography variant="caption" color="text.secondary">
        {points
          .map((point) => `${point.fiscal_year} ${point.fiscal_period}: ${formatPoint(point.value, unit)}`)
          .join(" | ")}
      </Typography>
    </Stack>
  );
}
