import { Card, CardContent, CardHeader } from "@mui/material";
import { DataGrid, GridColDef } from "@mui/x-data-grid";

import type { IncomeStatement } from "../types/financials";

type Props = {
  rows: IncomeStatement[];
};

function asMillions(value: number): string {
  return `${(value / 1_000_000).toFixed(1)}M`;
}

export function IncomeStatementTable({ rows }: Props) {
  const columns: GridColDef[] = [
    { field: "fiscal_year", headerName: "Fiscal Year", minWidth: 110 },
    { field: "fiscal_period", headerName: "Period", minWidth: 90 },
    { field: "revenue", headerName: "Revenue", minWidth: 130, valueFormatter: (value) => asMillions(Number(value)) },
    { field: "gross_profit", headerName: "Gross Profit", minWidth: 130, valueFormatter: (value) => asMillions(Number(value)) },
    { field: "operating_income", headerName: "Operating Income", minWidth: 140, valueFormatter: (value) => asMillions(Number(value)) },
    { field: "net_income", headerName: "Net Income", minWidth: 120, valueFormatter: (value) => asMillions(Number(value)) },
    { field: "eps", headerName: "EPS", minWidth: 90 },
  ];

  return (
    <Card>
      <CardHeader title="Income Statement" />
      <CardContent>
        <DataGrid autoHeight rows={rows} columns={columns} disableRowSelectionOnClick pageSizeOptions={[5, 10, 20]} />
      </CardContent>
    </Card>
  );
}
