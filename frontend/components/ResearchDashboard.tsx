import RefreshIcon from "@mui/icons-material/Refresh";
import { Button, Grid2 as Grid, Stack, Typography } from "@mui/material";

import type { GuidanceResponse, NewsResponse, ResearchResponse, RisksResponse, TimelineResponse } from "../types/financials";
import { EventTimeline } from "./EventTimeline";
import { GuidanceTracker } from "./GuidanceTracker";
import { NewsFeed } from "./NewsFeed";
import { ResearchSummaryCard } from "./ResearchSummaryCard";
import { RiskPanel } from "./RiskPanel";

type Props = {
  research: ResearchResponse;
  risks: RisksResponse;
  guidance: GuidanceResponse;
  news: NewsResponse;
  timeline: TimelineResponse;
  onRefresh: () => void;
  isRefreshing: boolean;
};

export function ResearchDashboard({ research, risks, guidance, news, timeline, onRefresh, isRefreshing }: Props) {
  return (
    <Stack spacing={2}>
      <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" alignItems={{ xs: "flex-start", md: "center" }} spacing={1}>
        <Typography variant="h5">Research & News Intelligence</Typography>
        <Button
          variant="outlined"
          size="small"
          startIcon={<RefreshIcon />}
          onClick={onRefresh}
          disabled={isRefreshing}
        >
          {isRefreshing ? "Refreshing..." : "Refresh data"}
        </Button>
      </Stack>
      <ResearchSummaryCard summary={research.summary_card} />

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 6 }}>
          <RiskPanel risks={risks.risks} />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <NewsFeed events={news.news_events} />
        </Grid>
        <Grid size={{ xs: 12 }}>
          <GuidanceTracker guidance={guidance.guidance} />
        </Grid>
        <Grid size={{ xs: 12 }}>
          <EventTimeline items={timeline.timeline} />
        </Grid>
      </Grid>
    </Stack>
  );
}
