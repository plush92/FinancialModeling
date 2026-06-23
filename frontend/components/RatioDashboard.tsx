import { Box, Grid2 as Grid, Stack, Typography } from "@mui/material";

import type { RatiosResponse } from "../types/financials";
import { MetricCard } from "./MetricCard";

type Props = {
  ratios: RatiosResponse;
};

const SECTION_LABELS: Record<string, string> = {
  profitability: "Profitability",
  liquidity: "Liquidity",
  leverage: "Leverage",
  growth: "Growth",
  efficiency: "Efficiency",
  cash_flow: "Cash Flow",
};

export function RatioDashboard({ ratios }: Props) {
  const sectionOrder = ["profitability", "liquidity", "leverage", "growth", "efficiency", "cash_flow"];

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h5">Ratio Dashboard</Typography>
        <Typography color="text.secondary">Version {ratios.calculation_version} | Generated {new Date(ratios.generated_at).toLocaleString()}</Typography>
      </Box>

      {sectionOrder.map((sectionKey) => {
        const metrics = ratios.sections[sectionKey] ?? [];
        if (metrics.length === 0) {
          return null;
        }
        return (
          <Stack key={sectionKey} spacing={1}>
            <Typography variant="h6">{SECTION_LABELS[sectionKey] ?? sectionKey}</Typography>
            <Grid container spacing={1.5}>
              {metrics.map((metric) => (
                <Grid key={metric.metric_name} size={{ xs: 12, md: 6, lg: 4 }}>
                  <MetricCard metric={metric} />
                </Grid>
              ))}
            </Grid>
          </Stack>
        );
      })}
    </Stack>
  );
}
