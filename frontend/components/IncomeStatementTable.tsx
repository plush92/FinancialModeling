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

import type { IncomeStatement } from "../types/financials";

type Props = {
  rows: IncomeStatement[];
};

type PeriodMode = "quarterly" | "annual" | "ttm";

type IncomeRowView = IncomeStatement & {
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

const METRIC_FIELDS: Array<keyof IncomeStatement> = ["revenue", "gross_profit", "operating_income", "net_income", "eps"];

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

function sortByPeriodDesc(a: IncomeStatement, b: IncomeStatement): number {
  if (a.fiscal_year !== b.fiscal_year) {
    return b.fiscal_year - a.fiscal_year;
  }
  return (QUARTER_ORDER[b.fiscal_period] ?? 0) - (QUARTER_ORDER[a.fiscal_period] ?? 0);
}

function trendArrow(rows: IncomeRowView[], field: keyof IncomeStatement): string {
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

function buildTTMRows(rows: IncomeStatement[]): IncomeStatement[] {
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

  const ttmRows: IncomeStatement[] = [];
  for (let i = 3; i < quarterlyAsc.length; i += 1) {
    const windowRows = quarterlyAsc.slice(i - 3, i + 1);
    const end = quarterlyAsc[i];
    ttmRows.push({
      id: Number(`${end.fiscal_year}${i}9`),
      company_id: end.company_id,
      fiscal_year: end.fiscal_year,
      fiscal_period: end.fiscal_period,
      revenue: windowRows.reduce((sum, row) => sum + Number(row.revenue), 0),
      gross_profit: windowRows.reduce((sum, row) => sum + Number(row.gross_profit), 0),
      operating_income: windowRows.reduce((sum, row) => sum + Number(row.operating_income), 0),
      net_income: windowRows.reduce((sum, row) => sum + Number(row.net_income), 0),
      eps: windowRows.reduce((sum, row) => sum + Number(row.eps), 0),
    });
  }
  return ttmRows;
}

function withDeltas(rows: IncomeRowView[]): IncomeRowView[] {
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

export function IncomeStatementTable({ rows }: Props) {
  const [periodMode, setPeriodMode] = useState<PeriodMode>("quarterly");
  const [compareMode, setCompareMode] = useState(false);

  const viewRows = useMemo(() => {
    let filtered: IncomeStatement[];
    if (periodMode === "annual") {
      filtered = rows.filter((row) => row.fiscal_period === "FY");
    } else if (periodMode === "ttm") {
      filtered = buildTTMRows(rows);
    } else {
      filtered = rows.filter((row) => row.fiscal_period.startsWith("Q"));
    }

    const sorted = [...filtered].sort(sortByPeriodDesc);
    const labeled: IncomeRowView[] = sorted.map((row) => ({
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
      field: "revenue",
      headerName: `Revenue ${trendArrow(viewRows, "revenue")}`,
      minWidth: 150,
      renderCell: (params) => {
        const delta = params.row.deltas.revenue;
        return compareMode ? (
          <Stack spacing={0.25}>
            <Typography variant="body2">{asMillions(Number(params.value))}</Typography>
            <Typography variant="caption" color={deltaColor(delta)}>
              {formatDelta(delta)}
            </Typography>
          </Stack>
        ) : (
          asMillions(Number(params.value))
        );
      },
    },
    {
      field: "gross_profit",
      headerName: `Gross Profit ${trendArrow(viewRows, "gross_profit")}`,
      minWidth: 150,
      renderCell: (params) => {
        const delta = params.row.deltas.gross_profit;
        return compareMode ? (
          <Stack spacing={0.25}>
            <Typography variant="body2">{asMillions(Number(params.value))}</Typography>
            <Typography variant="caption" color={deltaColor(delta)}>
              {formatDelta(delta)}
            </Typography>
          </Stack>
        ) : (
          asMillions(Number(params.value))
        );
      },
    },
    {
      field: "operating_income",
      headerName: `Operating Income ${trendArrow(viewRows, "operating_income")}`,
      minWidth: 170,
      renderCell: (params) => {
        const delta = params.row.deltas.operating_income;
        return compareMode ? (
          <Stack spacing={0.25}>
            <Typography variant="body2">{asMillions(Number(params.value))}</Typography>
            <Typography variant="caption" color={deltaColor(delta)}>
              {formatDelta(delta)}
            </Typography>
          </Stack>
        ) : (
          asMillions(Number(params.value))
        );
      },
    },
    {
      field: "net_income",
      headerName: `Net Income ${trendArrow(viewRows, "net_income")}`,
      minWidth: 140,
      renderCell: (params) => {
        const delta = params.row.deltas.net_income;
        return compareMode ? (
          <Stack spacing={0.25}>
            <Typography variant="body2">{asMillions(Number(params.value))}</Typography>
            <Typography variant="caption" color={deltaColor(delta)}>
              {formatDelta(delta)}
            </Typography>
          </Stack>
        ) : (
          asMillions(Number(params.value))
        );
      },
    },
    {
      field: "eps",
      headerName: `EPS ${trendArrow(viewRows, "eps")}`,
      minWidth: 120,
      renderCell: (params) => {
        const value = Number(params.value);
        const delta = params.row.deltas.eps;
        return compareMode ? (
          <Stack spacing={0.25}>
            <Typography variant="body2">{value.toFixed(2)}</Typography>
            <Typography variant="caption" color={deltaColor(delta)}>
              {formatDelta(delta)}
            </Typography>
          </Stack>
        ) : (
          value.toFixed(2)
        );
      },
    },
  ];

  return (
    <Card>
      <CardHeader title="Income Statement" />
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
