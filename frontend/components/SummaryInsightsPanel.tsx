import { Alert, Card, CardContent, CardHeader, Chip, Divider, List, ListItem, Stack, Typography } from "@mui/material";

import type { IssuesResponse, QualityResponse, RatiosResponse, TrendsResponse } from "../types/financials";

type Props = {
  ratios: RatiosResponse | null;
  trends: TrendsResponse | null;
  issues: IssuesResponse | null;
  quality: QualityResponse | null;
};

type CategoryTone = "improving" | "deteriorating" | "mixed" | "insufficient";

type Numeric = number | string | null;

const CATEGORY_LABELS: Record<string, string> = {
  profitability: "Profitability",
  growth: "Growth",
  liquidity: "Liquidity",
  leverage: "Leverage",
  efficiency: "Efficiency",
  cash_flow: "Cash Flow",
};

function asNumber(value: Numeric): number | null {
  if (value === null || value === undefined) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function categoryTone(ratios: RatiosResponse | null, key: string): CategoryTone {
  if (!ratios) {
    return "insufficient";
  }

  const metrics = ratios.sections[key] ?? [];
  const directions = metrics
    .map((metric) => metric.trend_direction)
    .filter((direction): direction is "Improving" | "Stable" | "Deteriorating" => direction !== null);

  if (directions.length === 0) {
    return "insufficient";
  }

  const score =
    directions.reduce((sum, direction) => {
      if (direction === "Improving") {
        return sum + 1;
      }
      if (direction === "Deteriorating") {
        return sum - 1;
      }
      return sum;
    }, 0) / directions.length;

  if (score > 0.25) {
    return "improving";
  }
  if (score < -0.25) {
    return "deteriorating";
  }
  return "mixed";
}

function describeTone(tone: CategoryTone): string {
  if (tone === "improving") {
    return "improving";
  }
  if (tone === "deteriorating") {
    return "deteriorating";
  }
  if (tone === "mixed") {
    return "mixed";
  }
  return "insufficient data";
}

function buildOverallSummary(ratios: RatiosResponse | null): string {
  const keys = ["profitability", "growth", "liquidity"];
  return keys
    .map((key) => `${CATEGORY_LABELS[key]} ${describeTone(categoryTone(ratios, key))}`)
    .join("; ");
}

function findBiggestMove(trends: TrendsResponse | null, direction: "up" | "down") {
  if (!trends) {
    return null;
  }

  const candidates = trends.trends
    .map((trend) => {
      const latest = asNumber(trend.latest_value);
      const previous = asNumber(trend.previous_value);
      if (latest === null || previous === null || previous === 0) {
        return null;
      }
      const changePct = ((latest - previous) / Math.abs(previous)) * 100;
      return {
        name: trend.display_name,
        changePct,
      };
    })
    .filter((item): item is { name: string; changePct: number } => item !== null);

  if (candidates.length === 0) {
    return null;
  }

  if (direction === "up") {
    return candidates.sort((a, b) => b.changePct - a.changePct)[0];
  }
  return candidates.sort((a, b) => a.changePct - b.changePct)[0];
}

function summarizeCashPosition(ratios: RatiosResponse | null): string | null {
  if (!ratios) {
    return null;
  }

  const fcf = ratios.sections.cash_flow?.find((metric) => metric.metric_name === "free_cash_flow");
  const fcfMargin = ratios.sections.cash_flow?.find((metric) => metric.metric_name === "free_cash_flow_margin");

  const fcfValue = asNumber(fcf?.latest_value ?? null);
  const marginValue = asNumber(fcfMargin?.latest_value ?? null);

  if (fcfValue === null && marginValue === null) {
    return null;
  }

  const fcfText =
    fcfValue === null
      ? "free cash flow data is limited"
      : fcfValue >= 0
        ? `free cash flow is positive at ${(fcfValue / 1_000_000).toFixed(1)}M`
        : `free cash flow is negative at ${(fcfValue / 1_000_000).toFixed(1)}M`;

  const marginText = marginValue === null ? "" : ` with margin ${(marginValue * 100).toFixed(1)}%`;
  return `${fcfText}${marginText}.`;
}

function getMetric(ratios: RatiosResponse | null, metricName: string) {
  if (!ratios) {
    return null;
  }
  for (const section of Object.values(ratios.sections)) {
    const metric = section.find((item) => item.metric_name === metricName);
    if (metric) {
      return metric;
    }
  }
  return null;
}

function crossMetricInsights(ratios: RatiosResponse | null): string[] {
  if (!ratios) {
    return [];
  }

  const insights: string[] = [];

  const grossMargin = getMetric(ratios, "gross_margin");
  const operatingMargin = getMetric(ratios, "operating_margin");
  if (grossMargin?.trend_direction === "Improving" && operatingMargin?.trend_direction === "Deteriorating") {
    insights.push(
      "Gross margin is improving while operating margin is deteriorating, which can indicate operating expenses are rising faster than revenue."
    );
  }

  const roe = getMetric(ratios, "roe");
  const debtToEquity = getMetric(ratios, "debt_to_equity");
  const roeValue = asNumber(roe?.latest_value ?? null);
  const debtToEquityValue = asNumber(debtToEquity?.latest_value ?? null);
  if (roeValue !== null && debtToEquityValue !== null && roeValue > 0.25 && debtToEquityValue > 2) {
    insights.push(
      "ROE is elevated while debt-to-equity is also high, suggesting returns may be amplified by leverage rather than pure operating strength."
    );
  }

  const revenueGrowth = getMetric(ratios, "revenue_growth_yoy");
  const fcfGrowth = getMetric(ratios, "free_cash_flow_growth_yoy");
  if (revenueGrowth && fcfGrowth) {
    const revGrowthValue = asNumber(revenueGrowth.latest_value);
    const fcfGrowthValue = asNumber(fcfGrowth.latest_value);
    if (revGrowthValue !== null && fcfGrowthValue !== null) {
      if (revGrowthValue > 0 && fcfGrowthValue < 0) {
        insights.push(
          "Revenue is growing while free cash flow is contracting, which may indicate working-capital pressure or heavier reinvestment intensity."
        );
      }
      if (revGrowthValue < 0 && fcfGrowthValue > 0) {
        insights.push(
          "Revenue is slowing but free cash flow is improving, suggesting tighter cost control or improved cash conversion."
        );
      }
    }
  }

  const currentRatio = getMetric(ratios, "current_ratio");
  const quickRatio = getMetric(ratios, "quick_ratio");
  const currentRatioValue = asNumber(currentRatio?.latest_value ?? null);
  const quickRatioValue = asNumber(quickRatio?.latest_value ?? null);
  if (currentRatioValue !== null && quickRatioValue !== null && currentRatioValue > 1.4 && quickRatioValue < 1) {
    insights.push(
      "Current ratio appears healthy, but quick ratio is weak, implying liquidity depends heavily on inventory rather than cash-like assets."
    );
  }

  const roic = getMetric(ratios, "roic");
  const netDebtToEbitda = getMetric(ratios, "net_debt_to_ebitda");
  const roicValue = asNumber(roic?.latest_value ?? null);
  const netDebtToEbitdaValue = asNumber(netDebtToEbitda?.latest_value ?? null);
  if (roicValue !== null && netDebtToEbitdaValue !== null && roicValue > 0.12 && netDebtToEbitdaValue > 3) {
    insights.push(
      "ROIC is solid, but leverage is elevated, so balance-sheet risk should be monitored to ensure returns remain durable through cycles."
    );
  }

  return insights.slice(0, 5);
}

function keyInsights(
  ratios: RatiosResponse | null,
  trends: TrendsResponse | null,
  quality: QualityResponse | null,
): string[] {
  const insights: string[] = [];

  const biggestImprovement = findBiggestMove(trends, "up");
  if (biggestImprovement && biggestImprovement.changePct > 0) {
    insights.push(
      `${biggestImprovement.name} shows the strongest recent improvement (${biggestImprovement.changePct.toFixed(1)}% vs prior period).`
    );
  }

  const biggestDeterioration = findBiggestMove(trends, "down");
  if (biggestDeterioration && biggestDeterioration.changePct < 0) {
    insights.push(
      `${biggestDeterioration.name} has the sharpest recent decline (${biggestDeterioration.changePct.toFixed(1)}% vs prior period).`
    );
  }

  if (quality) {
    insights.push(
      `Data quality score is ${quality.quality_score.toFixed(1)}/100 with ${quality.warnings.length} warning(s) and ${quality.errors.length} error(s).`
    );
  }

  const liquidityStatus = describeTone(categoryTone(ratios, "liquidity"));
  insights.push(`Liquidity profile is ${liquidityStatus}.`);

  const cashSummary = summarizeCashPosition(ratios);
  if (cashSummary) {
    insights.push(cashSummary);
  }

  return insights.slice(0, 5);
}

function redFlags(issues: IssuesResponse | null, quality: QualityResponse | null): string[] {
  const flags: string[] = [];

  if (issues) {
    const grouped = new Map<string, number>();
    for (const issue of issues.validation_issues) {
      const key = `${issue.rule_name}::${issue.description}`;
      grouped.set(key, (grouped.get(key) ?? 0) + 1);
    }

    for (const [key, count] of grouped.entries()) {
      const [ruleName, description] = key.split("::");
      const blob = `${ruleName} ${description}`.toLowerCase();
      if (blob.includes("cash rollforward") && count > 1) {
        flags.push(`${ruleName}: ${count} occurrences detected. Check cash flow mapping and period alignment.`);
      }
      if (count >= 5) {
        flags.push(`${ruleName}: repeated ${count} times, indicating a systemic data quality issue.`);
      }
    }
  }

  if (quality && quality.errors.length > 0) {
    flags.push(`Quality engine reported ${quality.errors.length} error(s); prioritize reconciliation before decisions.`);
  }

  return Array.from(new Set(flags)).slice(0, 5);
}

function toneChipColor(tone: CategoryTone): "success" | "error" | "warning" | "default" {
  if (tone === "improving") {
    return "success";
  }
  if (tone === "deteriorating") {
    return "error";
  }
  if (tone === "mixed") {
    return "warning";
  }
  return "default";
}

export function SummaryInsightsPanel({ ratios, trends, issues, quality }: Props) {
  const summary = buildOverallSummary(ratios);
  const insights = keyInsights(ratios, trends, quality);
  const crossInsights = crossMetricInsights(ratios);
  const flags = redFlags(issues, quality);

  const categoryKeys = ["profitability", "growth", "liquidity", "leverage", "efficiency", "cash_flow"];

  return (
    <Card>
      <CardHeader title="Summary Insights" subheader="Top-level narrative generated from ratios, trends, and data quality signals" />
      <CardContent>
        <Stack spacing={2}>
          <Alert severity="info">
            <strong>Overall trend summary:</strong> {summary}
          </Alert>

          <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
            {categoryKeys.map((key) => {
              const tone = categoryTone(ratios, key);
              return (
                <Chip
                  key={key}
                  size="small"
                  color={toneChipColor(tone)}
                  label={`${CATEGORY_LABELS[key]}: ${describeTone(tone)}`}
                />
              );
            })}
          </Stack>

          <Divider />

          <Stack spacing={0.5}>
            <Typography variant="subtitle1">Key Insights</Typography>
            {insights.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                Not enough data to generate insights yet.
              </Typography>
            ) : (
              <List dense disablePadding>
                {insights.map((insight) => (
                  <ListItem key={insight} sx={{ display: "list-item", py: 0.35 }}>
                    <Typography variant="body2">{insight}</Typography>
                  </ListItem>
                ))}
              </List>
            )}
          </Stack>

          <Stack spacing={0.5}>
            <Typography variant="subtitle1">Cross-Metric Insights</Typography>
            {crossInsights.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                Not enough aligned signals yet to infer cross-metric relationships.
              </Typography>
            ) : (
              <List dense disablePadding>
                {crossInsights.map((insight) => (
                  <ListItem key={insight} sx={{ display: "list-item", py: 0.35 }}>
                    <Typography variant="body2">{insight}</Typography>
                  </ListItem>
                ))}
              </List>
            )}
          </Stack>

          <Stack spacing={0.5}>
            <Typography variant="subtitle1">Potential Red Flags</Typography>
            {flags.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No major red flags detected from current validation outputs.
              </Typography>
            ) : (
              <List dense disablePadding>
                {flags.map((flag) => (
                  <ListItem key={flag} sx={{ display: "list-item", py: 0.35 }}>
                    <Typography variant="body2" color="error.main">
                      {flag}
                    </Typography>
                  </ListItem>
                ))}
              </List>
            )}
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
}
