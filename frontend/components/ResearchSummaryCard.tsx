import { Card, CardContent, CardHeader, Grid2 as Grid, Typography } from "@mui/material";

import type { ResearchSummaryCardData } from "../types/financials";

type Props = {
  summary: ResearchSummaryCardData;
};

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <Grid size={{ xs: 6, md: 2.4 }}>
      <Typography variant="h5">{value}</Typography>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
    </Grid>
  );
}

export function ResearchSummaryCard({ summary }: Props) {
  return (
    <Card>
      <CardHeader title="Research Summary" subheader="Structured intelligence coverage snapshot" />
      <CardContent>
        <Grid container spacing={2}>
          <Stat label="Documents" value={summary.total_documents} />
          <Stat label="Risks" value={summary.total_risks} />
          <Stat label="Guidance Updates" value={summary.total_guidance_updates} />
          <Stat label="News Events" value={summary.total_news_events} />
          <Stat label="Negative News" value={summary.negative_news_count} />
        </Grid>
      </CardContent>
    </Card>
  );
}
