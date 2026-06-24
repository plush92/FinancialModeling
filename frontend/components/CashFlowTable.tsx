import { Card, CardContent, CardHeader } from "@mui/material";
import { DataGrid, GridColDef } from "@mui/x-data-grid";

import type { CashFlowStatement } from "../types/financials";

type Props = {
  rows: CashFlowStatement[];
};

function asMillions(value: number): string {
  return `${(value / 1_000_000).toFixed(1)}M`;
}

export function CashFlowTable({ rows }: Props) {
  const columns: GridColDef[] = [
    { field: "fiscal_year", headerName: "Fiscal Year", minWidth: 110 },
    { field: "fiscal_period", headerName: "Period", minWidth: 90 },
    { field: "operating_cash_flow", headerName: "Operating CF", minWidth: 140, valueFormatter: (value) => asMillions(Number(value)) },
    { field: "capex", headerName: "CapEx", minWidth: 120, valueFormatter: (value) => asMillions(Number(value)) },
    { field: "free_cash_flow", headerName: "Free Cash Flow", minWidth: 140, valueFormatter: (value) => asMillions(Number(value)) },
  ];

  return (
    <Card>
      <CardHeader title="Cash Flow Statement" />
      <CardContent>
        <DataGrid autoHeight rows={rows} columns={columns} disableRowSelectionOnClick pageSizeOptions={[5, 10, 20, 100]} />
      </CardContent>
    </Card>
  );
}
