import { Alert, Card, CardContent, CardHeader, Chip, Grid2 as Grid, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";

import { createForecast } from "../services/api";
import type { ForecastResponse, ForecastScenario } from "../types/financials";
import { AssumptionEditorPanel } from "./AssumptionEditorPanel";
import { ForecastChartView } from "./ForecastChartView";
import { ScenarioSelector } from "./ScenarioSelector";
import { ThreeStatementTable } from "./ThreeStatementTable";

type Props = {
  ticker: string;
};

export function ForecastDashboard({ ticker }: Props) {
  const [scenario, setScenario] = useState<ForecastScenario>("base");
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runForecast = async (
    nextScenario: ForecastScenario,
    options?: { assumptionsVersion?: string; horizonYears?: number; revenueGrowth?: number; grossMargin?: number }
  ) => {
    setLoading(true);
    setError(null);
    try {
      const payload = await createForecast(ticker, {
        scenario: nextScenario,
        assumptions_version: options?.assumptionsVersion ?? "latest",
        horizon_years: options?.horizonYears,
        assumptions_override:
          options?.revenueGrowth != null || options?.grossMargin != null
            ? {
                revenue_drivers:
                  options?.revenueGrowth != null
                    ? { revenue_growth_by_year: Array(10).fill(options.revenueGrowth / 100) }
                    : undefined,
                margin_drivers:
                  options?.grossMargin != null
                    ? { gross_margin_pct: options.grossMargin / 100 }
                    : undefined,
              }
            : undefined,
      });
      setForecast(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run forecast.");
      setForecast(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void runForecast(scenario);
  }, [scenario, ticker]);

  const validation = forecast?.validation;

  return (
    <Stack spacing={2}>
      <Card>
        <CardHeader title="Forecast Dashboard" subheader="Driver-Based Forecast Engine (3-Statement Model)" />
        <CardContent>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 4 }}>
              <ScenarioSelector scenario={scenario} onChange={(next) => setScenario(next)} />
            </Grid>
            <Grid size={{ xs: 12, md: 8 }}>
              <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                <Chip size="small" label={`Ticker: ${ticker}`} />
                {forecast && <Chip size="small" label={`Assumptions: ${forecast.assumptions_version}`} />}
                {forecast && <Chip size="small" label={`Scenario: ${forecast.scenario}`} />}
                {loading && <Chip size="small" color="info" label="Running..." />}
              </Stack>
            </Grid>
          </Grid>

          {error && (
            <Alert sx={{ mt: 2 }} severity="error">
              {error}
            </Alert>
          )}
        </CardContent>
      </Card>

      <AssumptionEditorPanel
        assumptionsVersion={forecast?.assumptions_version ?? "latest"}
        onRun={(params) =>
          void runForecast(scenario, {
            assumptionsVersion: params.assumptionsVersion,
            horizonYears: params.horizonYears,
            revenueGrowth: params.revenueGrowth,
            grossMargin: params.grossMargin,
          })
        }
        running={loading}
      />

      {validation && (
        <Card>
          <CardHeader title="Forecast Validation" subheader="Accounting integrity and sanity checks" />
          <CardContent>
            <Stack spacing={1}>
              <Typography variant="body2">Balance Sheet Balanced: {validation.balance_sheet_balanced ? "Yes" : "No"}</Typography>
              <Typography variant="body2">Cash Rollforward Reconciled: {validation.cash_rollforward_reconciled ? "Yes" : "No"}</Typography>
              {validation.negative_asset_warnings.slice(0, 3).map((warning) => (
                <Alert key={warning} severity="warning">
                  {warning}
                </Alert>
              ))}
              {validation.unreasonable_growth_flags.slice(0, 3).map((flag) => (
                <Alert key={flag} severity="warning">
                  {flag}
                </Alert>
              ))}
              {validation.margin_sanity_flags.slice(0, 3).map((flag) => (
                <Alert key={flag} severity="warning">
                  {flag}
                </Alert>
              ))}
              {validation.notes.slice(0, 3).map((note) => (
                <Alert key={note} severity="info">
                  {note}
                </Alert>
              ))}
            </Stack>
          </CardContent>
        </Card>
      )}

      {forecast && (
        <>
          <ForecastChartView projections={forecast.projections} />
          <ThreeStatementTable projections={forecast.projections} />
        </>
      )}
    </Stack>
  );
}
