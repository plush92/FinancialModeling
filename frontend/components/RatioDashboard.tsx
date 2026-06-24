import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { Accordion, AccordionDetails, AccordionSummary, Box, Grid2 as Grid, Stack, Typography } from "@mui/material";

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

function dedupeMetrics<T extends { metric_name: string; display_name: string }>(metrics: T[]): T[] {
  const seen = new Set<string>();
  const deduped: T[] = [];
  for (const metric of metrics) {
    const key = `${metric.metric_name}|${metric.display_name.toLowerCase()}`;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    deduped.push(metric);
  }
  return deduped;
}

export function RatioDashboard({ ratios }: Props) {
  const sectionOrder = ["profitability", "liquidity", "leverage", "growth", "efficiency", "cash_flow"];

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h5">Ratio Dashboard</Typography>
      </Box>

      {sectionOrder.map((sectionKey) => {
        const metrics = dedupeMetrics(ratios.sections[sectionKey] ?? []);
        if (metrics.length === 0) {
          return null;
        }
        return (
          <Accordion key={sectionKey} disableGutters defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Stack direction="row" spacing={1} alignItems="center">
                <Typography variant="h6">{SECTION_LABELS[sectionKey] ?? sectionKey}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {metrics.length} metrics
                </Typography>
              </Stack>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={1.5}>
                {metrics.map((metric) => (
                  <Grid key={metric.metric_name} size={{ xs: 12, md: 6, lg: 4 }}>
                    <MetricCard metric={metric} />
                  </Grid>
                ))}
              </Grid>
            </AccordionDetails>
          </Accordion>
        );
      })}
    </Stack>
  );
}
