import { Card, CardContent, CardHeader, Divider, Stack, Typography } from "@mui/material";
import { DataGrid, type GridColDef } from "@mui/x-data-grid";
import { useMemo } from "react";

import type { ForecastPeriod } from "../types/financials";

type Props = {
  projections: ForecastPeriod[];
};

function asMillions(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(2)}B`;
  }
  return `${(value / 1_000_000).toFixed(2)}M`;
}

export function ThreeStatementTable({ projections }: Props) {
  const incomeRows = useMemo(
    () =>
      projections.map((period) => ({
        id: `is-${period.fiscal_year}`,
        fiscal_year: period.fiscal_year,
        ...period.income_statement,
      })),
    [projections]
  );

  const balanceRows = useMemo(
    () =>
      projections.map((period) => ({
        id: `bs-${period.fiscal_year}`,
        fiscal_year: period.fiscal_year,
        ...period.balance_sheet,
      })),
    [projections]
  );

  const cashRows = useMemo(
    () =>
      projections.map((period) => ({
        id: `cf-${period.fiscal_year}`,
        fiscal_year: period.fiscal_year,
        ...period.cash_flow_statement,
      })),
    [projections]
  );

  const incomeColumns: GridColDef[] = [
    { field: "fiscal_year", headerName: "Year", minWidth: 90 },
    { field: "revenue", headerName: "Revenue", minWidth: 130, valueFormatter: (v) => asMillions(Number(v)) },
    { field: "gross_profit", headerName: "Gross Profit", minWidth: 130, valueFormatter: (v) => asMillions(Number(v)) },
    { field: "operating_income", headerName: "Operating Income", minWidth: 145, valueFormatter: (v) => asMillions(Number(v)) },
    { field: "net_income", headerName: "Net Income", minWidth: 120, valueFormatter: (v) => asMillions(Number(v)) },
    { field: "eps", headerName: "EPS", minWidth: 90, valueFormatter: (v) => Number(v).toFixed(2) },
  ];

  const balanceColumns: GridColDef[] = [
    { field: "fiscal_year", headerName: "Year", minWidth: 90 },
    { field: "cash", headerName: "Cash", minWidth: 120, valueFormatter: (v) => asMillions(Number(v)) },
    { field: "accounts_receivable", headerName: "A/R", minWidth: 120, valueFormatter: (v) => asMillions(Number(v)) },
    { field: "inventory", headerName: "Inventory", minWidth: 120, valueFormatter: (v) => asMillions(Number(v)) },
    { field: "accounts_payable", headerName: "A/P", minWidth: 120, valueFormatter: (v) => asMillions(Number(v)) },
    { field: "total_debt", headerName: "Total Debt", minWidth: 130, valueFormatter: (v) => asMillions(Number(v)) },
    { field: "shareholder_equity", headerName: "Equity", minWidth: 130, valueFormatter: (v) => asMillions(Number(v)) },
  ];

  const cashColumns: GridColDef[] = [
    { field: "fiscal_year", headerName: "Year", minWidth: 90 },
    { field: "operating_cash_flow", headerName: "OCF", minWidth: 120, valueFormatter: (v) => asMillions(Number(v)) },
    { field: "capex", headerName: "CapEx", minWidth: 120, valueFormatter: (v) => asMillions(Number(v)) },
    { field: "free_cash_flow", headerName: "FCF", minWidth: 120, valueFormatter: (v) => asMillions(Number(v)) },
    { field: "debt_issued", headerName: "Debt Issued", minWidth: 130, valueFormatter: (v) => asMillions(Number(v)) },
    { field: "debt_repaid", headerName: "Debt Repaid", minWidth: 130, valueFormatter: (v) => asMillions(Number(v)) },
    { field: "ending_cash_balance", headerName: "Ending Cash", minWidth: 130, valueFormatter: (v) => asMillions(Number(v)) },
  ];

  return (
    <Card>
      <CardHeader title="3-Statement Forecast Table" subheader="Projected Income Statement, Balance Sheet, and Cash Flow" />
      <CardContent>
        <Stack spacing={2}>
          <Typography variant="subtitle2">Income Statement</Typography>
          <DataGrid autoHeight rows={incomeRows} columns={incomeColumns} disableRowSelectionOnClick pageSizeOptions={[5, 10, 20, 100]} />

          <Divider />

          <Typography variant="subtitle2">Balance Sheet</Typography>
          <DataGrid autoHeight rows={balanceRows} columns={balanceColumns} disableRowSelectionOnClick pageSizeOptions={[5, 10, 20, 100]} />

          <Divider />

          <Typography variant="subtitle2">Cash Flow Statement</Typography>
          <DataGrid autoHeight rows={cashRows} columns={cashColumns} disableRowSelectionOnClick pageSizeOptions={[5, 10, 20, 100]} />
        </Stack>
      </CardContent>
    </Card>
  );
}
