import {
  Card,
  CardContent,
  CardHeader,
  FormControlLabel,
  Stack,
  Switch,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import { useMemo, useState } from "react";

import type { CashFlowStatement } from "../types/financials";

type Props = {
  rows: CashFlowStatement[];
};

type PeriodMode = "quarterly" | "annual" | "ttm";

type CashFlowRowView = CashFlowStatement & {
  period_label: string;
  deltas: Record<string, number | null>;
};

const QUARTER_ORDER: Record<string, number> = {
  Q1: 1,
  Q2: 2,
  Q3: 3,
  Q4: 4,
  FY: 5,
};

const METRIC_FIELDS: Array<keyof CashFlowStatement> = ["operating_cash_flow", "capex", "free_cash_flow"];

function asMillions(value: number): string {
  return `${(value / 1_000_000).toFixed(1)}M`;
}

function asNumber(value: unknown): number | null {
  if (value === null || value === undefined) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function sortByPeriodDesc(a: CashFlowStatement, b: CashFlowStatement): number {
  if (a.fiscal_year !== b.fiscal_year) {
    return b.fiscal_year - a.fiscal_year;
  }
  return (QUARTER_ORDER[b.fiscal_period] ?? 0) - (QUARTER_ORDER[a.fiscal_period] ?? 0);
}

function trendArrow(rows: CashFlowRowView[], field: keyof CashFlowStatement): string {
  if (rows.length < 2) {
    return "->";
  }
  const current = asNumber(rows[0][field]);
  const previous = asNumber(rows[1][field]);
  if (current === null || previous === null) {
    return "->";
  }
  if (current > previous) {
    return "↑";
  }
  if (current < previous) {
    return "↓";
  }
  return "->";
}

function buildTTMRows(rows: CashFlowStatement[]): CashFlowStatement[] {
  const quarterlyAsc = [...rows]
    .filter((row) => row.fiscal_period.startsWith("Q"))
    .sort((a, b) => {
      if (a.fiscal_year !== b.fiscal_year) {
        return a.fiscal_year - b.fiscal_year;
      }
      return (QUARTER_ORDER[a.fiscal_period] ?? 0) - (QUARTER_ORDER[b.fiscal_period] ?? 0);
    });

  if (quarterlyAsc.length < 4) {
    return [];
  }

  const ttmRows: CashFlowStatement[] = [];
  for (let i = 3; i < quarterlyAsc.length; i += 1) {
    const windowRows = quarterlyAsc.slice(i - 3, i + 1);
    const end = quarterlyAsc[i];
    ttmRows.push({
      id: Number(`${end.fiscal_year}${i}7`),
      company_id: end.company_id,
      fiscal_year: end.fiscal_year,
      fiscal_period: end.fiscal_period,
      operating_cash_flow: windowRows.reduce((sum, row) => sum + Number(row.operating_cash_flow), 0),
      capex: windowRows.reduce((sum, row) => sum + Number(row.capex), 0),
      free_cash_flow: windowRows.reduce((sum, row) => sum + Number(row.free_cash_flow), 0),
    });
  }
  return ttmRows;
}

function withDeltas(rows: CashFlowRowView[]): CashFlowRowView[] {
  return rows.map((row, index) => {
    const previous = rows[index + 1];
    const deltas: Record<string, number | null> = {};
    for (const field of METRIC_FIELDS) {
      const current = asNumber(row[field]);
      const prior = previous ? asNumber(previous[field]) : null;
      if (current === null || prior === null || prior === 0) {
        deltas[field] = null;
      } else {
        deltas[field] = ((current - prior) / Math.abs(prior)) * 100;
      }
    }
    return {
      ...row,
      deltas,
    };
  });
}

function formatDelta(delta: number | null): string {
  if (delta === null) {
    return "n/a";
  }
  const sign = delta > 0 ? "+" : "";
  return `${sign}${delta.toFixed(1)}%`;
}

function deltaColor(delta: number | null): string {
  if (delta === null || delta === 0) {
    return "text.secondary";
  }
  return delta > 0 ? "success.main" : "error.main";
}

export function CashFlowTable({ rows }: Props) {
  const [periodMode, setPeriodMode] = useState<PeriodMode>("quarterly");
  const [compareMode, setCompareMode] = useState(false);

  const viewRows = useMemo(() => {
    let filtered: CashFlowStatement[];
    if (periodMode === "annual") {
      filtered = rows.filter((row) => row.fiscal_period === "FY");
    } else if (periodMode === "ttm") {
      filtered = buildTTMRows(rows);
    } else {
      filtered = rows.filter((row) => row.fiscal_period.startsWith("Q"));
    }

    const sorted = [...filtered].sort(sortByPeriodDesc);
    const labeled: CashFlowRowView[] = sorted.map((row) => ({
      ...row,
      period_label:
        periodMode === "ttm"
          ? `TTM ending ${row.fiscal_year} ${row.fiscal_period}`
          : `${row.fiscal_year} ${row.fiscal_period}`,
      deltas: {},
    }));
    return withDeltas(labeled);
  }, [periodMode, rows]);

  const columns: GridColDef[] = [
    {
      field: "period_label",
      headerName: "Period",
      minWidth: 180,
      flex: 0.9,
      headerClassName: "period-header",
      cellClassName: "period-cell",
      sortable: false,
    },
    {
      field: "operating_cash_flow",
      headerName: `Operating CF ${trendArrow(viewRows, "operating_cash_flow")}`,
      minWidth: 170,
      renderCell: (params) => {
        const delta = params.row.deltas.operating_cash_flow;
        return compareMode ? (
          <Stack spacing={0.25}>
            <Typography variant="body2">{asMillions(Number(params.value))}</Typography>
            <Typography variant="caption" color={deltaColor(delta)}>{formatDelta(delta)}</Typography>
          </Stack>
        ) : asMillions(Number(params.value));
      },
    },
    {
      field: "capex",
      headerName: `CapEx ${trendArrow(viewRows, "capex")}`,
      minWidth: 140,
      renderCell: (params) => {
        const delta = params.row.deltas.capex;
        return compareMode ? (
          <Stack spacing={0.25}>
            <Typography variant="body2">{asMillions(Number(params.value))}</Typography>
            <Typography variant="caption" color={deltaColor(delta)}>{formatDelta(delta)}</Typography>
          </Stack>
        ) : asMillions(Number(params.value));
      },
    },
    {
      field: "free_cash_flow",
      headerName: `Free Cash Flow ${trendArrow(viewRows, "free_cash_flow")}`,
      minWidth: 170,
      renderCell: (params) => {
        const delta = params.row.deltas.free_cash_flow;
        return compareMode ? (
          <Stack spacing={0.25}>
            <Typography variant="body2">{asMillions(Number(params.value))}</Typography>
            <Typography variant="caption" color={deltaColor(delta)}>{formatDelta(delta)}</Typography>
          </Stack>
        ) : asMillions(Number(params.value));
      },
    },
  ];

  return (
    <Card>
      <CardHeader title="Cash Flow Statement" />
      <CardContent>
        <Stack spacing={1.5}>
          <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} justifyContent="space-between">
            <ToggleButtonGroup
              exclusive
              size="small"
              value={periodMode}
              onChange={(_, value: PeriodMode | null) => value && setPeriodMode(value)}
            >
              <ToggleButton value="quarterly">Quarterly</ToggleButton>
              <ToggleButton value="annual">Annual</ToggleButton>
              <ToggleButton value="ttm">TTM</ToggleButton>
            </ToggleButtonGroup>
            <FormControlLabel
              control={<Switch checked={compareMode} onChange={(event) => setCompareMode(event.target.checked)} />}
              label="Compare to previous period"
            />
          </Stack>

          <DataGrid
            autoHeight
            rows={viewRows}
            columns={columns}
            disableRowSelectionOnClick
            pageSizeOptions={[5, 10, 20, 100]}
            sx={{
              "& .period-header": {
                position: "sticky",
                left: 0,
                zIndex: 4,
                backgroundColor: "background.paper",
              },
              "& .period-cell": {
                position: "sticky",
                left: 0,
                zIndex: 3,
                backgroundColor: "background.paper",
                borderRight: "1px solid",
                borderColor: "divider",
              },
            }}
          />
        </Stack>
      </CardContent>
    </Card>
  );
}
