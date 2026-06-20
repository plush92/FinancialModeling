import { Card, CardContent, CardHeader } from "@mui/material";
import { DataGrid, GridColDef } from "@mui/x-data-grid";

import type { BalanceSheet } from "../types/financials";

type Props = {
  rows: BalanceSheet[];
};

function asMillions(value: number): string {
  return `${(value / 1_000_000).toFixed(1)}M`;
}

export function BalanceSheetTable({ rows }: Props) {
  const columns: GridColDef[] = [
    { field: "fiscal_year", headerName: "Fiscal Year", minWidth: 110 },
    { field: "fiscal_period", headerName: "Period", minWidth: 90 },
    { field: "cash", headerName: "Cash", minWidth: 120, valueFormatter: (value) => asMillions(Number(value)) },
    { field: "total_assets", headerName: "Total Assets", minWidth: 130, valueFormatter: (value) => asMillions(Number(value)) },
    { field: "total_liabilities", headerName: "Total Liabilities", minWidth: 150, valueFormatter: (value) => asMillions(Number(value)) },
    { field: "shareholder_equity", headerName: "Shareholder Equity", minWidth: 155, valueFormatter: (value) => asMillions(Number(value)) },
    { field: "total_debt", headerName: "Total Debt", minWidth: 120, valueFormatter: (value) => asMillions(Number(value)) },
  ];

  return (
    <Card>
      <CardHeader title="Balance Sheet" />
      <CardContent>
        <DataGrid autoHeight rows={rows} columns={columns} disableRowSelectionOnClick pageSizeOptions={[5, 10, 20]} />
      </CardContent>
    </Card>
  );
}
