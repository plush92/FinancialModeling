import { Alert, Card, CardContent, CardHeader, Chip, Stack, Typography } from "@mui/material";
import { useMemo } from "react";

import type { NewsEvent } from "../types/financials";

type Props = {
  events: NewsEvent[];
};

function sentimentColor(sentiment: string): "success" | "error" | "default" {
  if (sentiment === "Positive") return "success";
  if (sentiment === "Negative") return "error";
  return "default";
}

export function NewsFeed({ events }: Props) {
  const sentimentSummary = useMemo(() => {
    const counts = {
      positive: 0,
      negative: 0,
      neutral: 0,
    };

    for (const event of events) {
      const sentiment = event.sentiment.toLowerCase();
      if (sentiment.includes("positive")) {
        counts.positive += 1;
      } else if (sentiment.includes("negative")) {
        counts.negative += 1;
      } else {
        counts.neutral += 1;
      }
    }

    const total = events.length;
    const score = total === 0 ? 0 : ((counts.positive - counts.negative) / total) * 100;
    return {
      ...counts,
      total,
      score,
    };
  }, [events]);

  return (
    <Card>
      <CardHeader title="News Intelligence" subheader="Classified events with sentiment and importance" />
      <CardContent>
        <Stack spacing={1.2}>
          {events.length === 0 ? (
            <Alert severity="info">
              No news events available yet. This usually means recent articles were not found for the ticker or extraction confidence
              was below threshold. Use Refresh data after new headlines are published.
            </Alert>
          ) : (
            <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
              <Chip size="small" color="success" label={`Positive ${sentimentSummary.positive}`} />
              <Chip size="small" color="default" label={`Neutral ${sentimentSummary.neutral}`} />
              <Chip size="small" color="error" label={`Negative ${sentimentSummary.negative}`} />
              <Chip
                size="small"
                variant="outlined"
                label={`Sentiment score ${sentimentSummary.score >= 0 ? "+" : ""}${sentimentSummary.score.toFixed(0)}`}
              />
            </Stack>
          )}
          {events.slice(0, 12).map((event) => (
            <Stack key={event.id} spacing={0.6} sx={{ borderBottom: "1px solid #e6e8ec", pb: 1 }}>
              <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                <Chip size="small" label={event.event_type} />
                <Chip size="small" label={event.sentiment} color={sentimentColor(event.sentiment)} />
                <Typography variant="caption" color="text.secondary">
                  Importance {event.importance_score}/10 | Confidence {(event.confidence_score * 100).toFixed(0)}%
                </Typography>
              </Stack>
              <Typography variant="subtitle2">{event.headline}</Typography>
              <Typography variant="body2">{event.event_summary}</Typography>
              <Typography variant="caption" color="text.secondary">
                {new Date(event.publication_date).toLocaleDateString()} | {event.source}
              </Typography>
            </Stack>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}
