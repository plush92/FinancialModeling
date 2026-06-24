import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import TrendingFlatIcon from "@mui/icons-material/TrendingFlat";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import {
  Card,
  CardContent,
  Chip,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import { useMemo, useState } from "react";

import type { RatioMetricSeries } from "../types/financials";
import { HistoricalRatioChart } from "./HistoricalRatioChart";

type Props = {
  metric: RatioMetricSeries;
};

type MetricContext = {
  why: string;
  good: string;
};

const METRIC_CONTEXT: Record<string, MetricContext> = {
  gross_margin: {
    why: "Shows how much revenue remains after direct product/service costs. Higher gross margin means stronger pricing power and cost control.",
    good: "Software and platform businesses often target 60%+, while retail/hardware businesses usually run materially lower.",
  },
  operating_margin: {
    why: "Measures operating profitability before financing and taxes. Indicates whether the core business model scales efficiently.",
    good: "Mature leaders often sustain double-digit margins; consistent expansion over time is a strong signal.",
  },
  net_margin: {
    why: "Captures bottom-line profit after all expenses. It summarizes overall earnings efficiency.",
    good: "Higher and stable net margins versus peers are generally positive; sudden compression is a warning sign.",
  },
  ebitda_margin: {
    why: "Approximates operating cash earnings before non-cash and financing effects. Useful for comparing operating performance.",
    good: "Higher than peer median and stable across cycles is generally favorable.",
  },
  roa: {
    why: "Shows how effectively assets generate profit. Useful for asset-heavy industries.",
    good: "Improving ROA and performance above close peers is usually a positive indicator.",
  },
  roe: {
    why: "Measures return generated on shareholder equity. Reflects management effectiveness at creating owner value.",
    good: "Sustained mid-to-high teens ROE can be strong, but confirm it is not driven only by excessive leverage.",
  },
  roic: {
    why: "Measures how efficiently the company turns invested capital into operating returns. High ROIC suggests strong capital allocation.",
    good: "ROIC above estimated cost of capital is essential; sustained double-digit ROIC is often strong for quality businesses.",
  },
  current_ratio: {
    why: "Assesses ability to cover short-term obligations with short-term assets.",
    good: "Around 1.2x to 2.0x is common in many sectors; too high can also indicate idle working capital.",
  },
  quick_ratio: {
    why: "Stricter liquidity measure that excludes inventory and focuses on more liquid assets.",
    good: "Around 1.0x or above is often viewed as healthy, depending on working-capital model.",
  },
  cash_ratio: {
    why: "Most conservative liquidity metric, comparing cash to current liabilities.",
    good: "Higher improves resilience, but very high levels can imply underutilized capital.",
  },
  debt_to_equity: {
    why: "Shows capital structure risk by comparing debt load to equity base.",
    good: "Lower is generally safer; acceptable ranges vary by industry and stability of cash flows.",
  },
  debt_to_assets: {
    why: "Indicates what share of assets is financed with debt, a direct leverage gauge.",
    good: "Lower is typically better for downside resilience, especially in cyclical industries.",
  },
  interest_coverage_ratio: {
    why: "Measures ability to service interest expense from operating income.",
    good: "Higher is better; values comfortably above 3x are often viewed as safer.",
  },
  net_debt_to_ebitda: {
    why: "Approximates years of EBITDA needed to repay net debt.",
    good: "Lower is better; below ~3x is often acceptable, while below ~2x is generally conservative.",
  },
  asset_turnover: {
    why: "Shows how efficiently assets generate revenue.",
    good: "Higher is better for most sectors; compare only against similar asset-intensity peers.",
  },
  inventory_turnover: {
    why: "Measures how quickly inventory is sold and replaced.",
    good: "Higher turnover usually indicates stronger demand and inventory discipline.",
  },
  receivables_turnover: {
    why: "Tracks how quickly the company collects cash from customers.",
    good: "Higher is better; declining turnover can signal collection or customer quality risk.",
  },
  dso: {
    why: "Days Sales Outstanding estimates average collection time for receivables. Lower DSO means faster cash collection.",
    good: "Lower and stable versus peers is preferred; persistent increases may indicate weakening collections.",
  },
  dio: {
    why: "Days Inventory Outstanding tracks how long inventory sits before being sold.",
    good: "Lower is generally better unless strategic stocking is deliberate and profitable.",
  },
  ccc: {
    why: "Cash Conversion Cycle measures time between cash outflows and cash inflows from operations. Lower CCC improves cash efficiency.",
    good: "Lower or negative CCC is often strong, especially in businesses with fast inventory turns and supplier financing power.",
  },
  free_cash_flow: {
    why: "Shows cash left after core operations and capital investment. It is key for buybacks, debt reduction, and reinvestment.",
    good: "Consistently positive and growing free cash flow is a hallmark of financial flexibility.",
  },
  free_cash_flow_margin: {
    why: "Measures how much revenue converts into free cash flow.",
    good: "Higher and improving margins are generally favorable, especially through economic cycles.",
  },
  cash_conversion_ratio: {
    why: "Compares operating cash flow to net income to test earnings quality.",
    good: "At or above 1.0x over time often suggests earnings are backed by cash generation.",
  },
  capex_as_pct_revenue: {
    why: "Shows capital intensity required to support revenue.",
    good: "Lower can indicate an asset-light model, but context matters if spending drives growth.",
  },
  revenue_growth_yoy: {
    why: "Measures top-line expansion versus prior year.",
    good: "Sustained positive growth above peer median, with stable margins, is typically strong.",
  },
  gross_profit_growth_yoy: {
    why: "Tracks growth in gross profit, capturing both growth and gross margin quality.",
    good: "Healthy gross profit growth alongside stable gross margins is generally favorable.",
  },
  operating_income_growth_yoy: {
    why: "Shows expansion of operating earnings from core operations.",
    good: "Higher and durable operating income growth indicates improving operating leverage.",
  },
  net_income_growth_yoy: {
    why: "Measures growth in bottom-line earnings.",
    good: "Consistent positive growth with good cash conversion is generally more durable.",
  },
  eps_growth_yoy: {
    why: "Tracks per-share earnings growth relevant to shareholder returns.",
    good: "Sustained EPS growth with stable dilution profile is typically a positive signal.",
  },
  free_cash_flow_growth_yoy: {
    why: "Measures year-over-year growth in free cash flow capacity.",
    good: "Consistent growth in free cash flow tends to support valuation and strategic flexibility.",
  },
};

function getMetricContext(metric: RatioMetricSeries): MetricContext {
  return (
    METRIC_CONTEXT[metric.metric_name] ?? {
      why: "Shows a key dimension of operating performance, balance-sheet quality, or cash efficiency.",
      good: "A favorable level is one that is improving over time and outperforming comparable peers.",
    }
  );
}

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

function MiniSparkline({ values }: { values: Array<number | string | null> }) {
  const numericValues = values.map((value) => toFiniteNumber(value)).filter((value): value is number => value !== null);
  if (numericValues.length < 2) {
    return (
      <Typography variant="caption" color="text.secondary">
        --
      </Typography>
    );
  }

  const min = Math.min(...numericValues);
  const max = Math.max(...numericValues);
  const width = 110;
  const height = 34;
  const step = width / (numericValues.length - 1);

  const points = numericValues
    .map((value, index) => {
      const x = index * step;
      const y = max === min ? height / 2 : height - ((value - min) / (max - min)) * height;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg width={width} height={height} role="img" aria-label="Metric trend sparkline">
      <polyline fill="none" stroke="#2a9d8f" strokeWidth={2} points={points} />
    </svg>
  );
}

function trendVisual(direction: RatioMetricSeries["trend_direction"]) {
  if (direction === "Improving") {
    return <Chip size="small" icon={<TrendingUpIcon />} color="success" label="Improving" />;
  }
  if (direction === "Deteriorating") {
    return <Chip size="small" icon={<TrendingDownIcon />} color="error" label="Deteriorating" />;
  }
  if (direction === "Stable" || direction === null) {
    return <Chip size="small" icon={<TrendingFlatIcon />} color="default" label="Stable" />;
  }
  return <Chip size="small" variant="outlined" label="Insufficient history" />;
}

export function MetricCard({ metric }: Props) {
  const [detailView, setDetailView] = useState<"latest" | "history">("latest");
  const uniqueInputPairs = Array.from(new Map(Object.entries(metric.latest_inputs_used)).entries());
  const context = getMetricContext(metric);
  const historyValues = useMemo(
    () => metric.history.map((point) => point.value),
    [metric.history]
  );

  const handleDetailViewChange = (event: SelectChangeEvent) => {
    setDetailView(event.target.value as "latest" | "history");
  };

  return (
    <Card variant="outlined" sx={{ height: "100%" }}>
      <CardContent>
        <Stack spacing={1.5}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
            <Tooltip
              title={
                <Stack spacing={0.75} sx={{ maxWidth: 420 }}>
                  <Typography variant="subtitle2">Formula</Typography>
                  <Typography variant="body2">{metric.formula}</Typography>
                  <Typography variant="subtitle2">Why It Matters</Typography>
                  <Typography variant="body2">{context.why}</Typography>
                  <Typography variant="subtitle2">What Good Looks Like</Typography>
                  <Typography variant="body2">{context.good}</Typography>
                </Stack>
              }
              arrow
              placement="top"
            >
              <Typography variant="subtitle1" sx={{ cursor: "help" }}>
                {metric.display_name}
              </Typography>
            </Tooltip>
            {trendVisual(metric.trend_direction)}
          </Stack>

          <Stack direction="row" alignItems="center" justifyContent="space-between" spacing={1}>
            <Typography variant="h4">{formatMetric(metric.latest_value, metric.unit)}</Typography>
            <MiniSparkline values={historyValues} />
          </Stack>

          <FormControl size="small" sx={{ maxWidth: 220 }}>
            <InputLabel id={`metric-view-${metric.metric_name}`}>Metric View</InputLabel>
            <Select
              labelId={`metric-view-${metric.metric_name}`}
              value={detailView}
              label="Metric View"
              onChange={handleDetailViewChange}
            >
              <MenuItem value="latest">Latest only</MenuItem>
              <MenuItem value="history">Show history and inputs</MenuItem>
            </Select>
          </FormControl>

          {detailView === "history" && (
            <>
              <HistoricalRatioChart points={metric.history} unit={metric.unit} />

              <Typography variant="caption" color="text.secondary">
                Inputs used: {uniqueInputPairs
                  .map(([key, value]) => `${key}=${value ?? "N/A"}`)
                  .join(", ")}
              </Typography>
            </>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
