import { Box, Stack, Typography } from "@mui/material";

import type { MetricPoint } from "../types/financials";

type Props = {
  points: MetricPoint[];
  unit: string;
};

function normalize(points: MetricPoint[]): number[] {
  const values = points.map((point) => point.value).filter((value): value is number => value !== null);
  if (values.length === 0) {
    return [];
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  if (min === max) {
    return points.map(() => 50);
  }

  return points.map((point) => {
    if (point.value === null) {
      return 50;
    }
    return ((point.value - min) / (max - min)) * 100;
  });
}

function formatPoint(value: number | null, unit: string): string {
  if (value === null) {
    return "N/A";
  }
  if (unit === "percent") {
    return `${(value * 100).toFixed(1)}%`;
  }
  if (unit === "days") {
    return `${value.toFixed(1)}d`;
  }
  if (unit === "currency") {
    return `$${(value / 1_000_000).toFixed(1)}M`;
  }
  return value.toFixed(2);
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
        {points.map((point) => `${point.fiscal_year} ${point.fiscal_period}: ${formatPoint(point.value, unit)}`).join(" | ")}
      </Typography>
    </Stack>
  );
}
