import { Card, CardContent, CardHeader } from "@mui/material";
import { DataGrid, type GridColDef } from "@mui/x-data-grid";

import type { MetricTrend } from "../types/financials";

type Props = {
  trends: MetricTrend[];
};

function asPercent(value: number | null): string {
  if (value === null) {
    return "N/A";
  }
  return `${(value * 100).toFixed(2)}%`;
}

function asValue(value: number | null): string {
  if (value === null) {
    return "N/A";
  }
  return value.toFixed(4);
}

function asGridValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "N/A";
  }
  return asValue(Number(value));
}

export function TrendAnalysisPanel({ trends }: Props) {
  const columns: GridColDef[] = [
    { field: "display_name", headerName: "Metric", minWidth: 220, flex: 1 },
    { field: "category", headerName: "Category", minWidth: 130 },
    { field: "trend_direction", headerName: "Direction", minWidth: 130 },
    { field: "latest_value", headerName: "Latest", minWidth: 130, valueFormatter: (value) => asGridValue(value) },
    { field: "previous_value", headerName: "Previous", minWidth: 130, valueFormatter: (value) => asGridValue(value) },
    { field: "cagr_3y", headerName: "3Y CAGR", minWidth: 120, valueFormatter: (value) => asPercent(value === null ? null : Number(value)) },
    { field: "cagr_5y", headerName: "5Y CAGR", minWidth: 120, valueFormatter: (value) => asPercent(value === null ? null : Number(value)) },
    {
      field: "rolling_average_3_periods",
      headerName: "Rolling Avg (3)",
      minWidth: 140,
      valueFormatter: (value) => asGridValue(value),
    },
  ];

  const rows = trends.map((item, index) => ({ id: `${item.metric_name}-${index}`, ...item }));

  return (
    <Card>
      <CardHeader title="Trend Analysis" subheader="3Y/5Y CAGR, rolling averages, and trend direction" />
      <CardContent>
        <DataGrid autoHeight rows={rows} columns={columns} disableRowSelectionOnClick pageSizeOptions={[5, 10, 20]} />
      </CardContent>
    </Card>
  );
}
