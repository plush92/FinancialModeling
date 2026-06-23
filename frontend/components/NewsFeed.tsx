import { Alert, Card, CardContent, CardHeader, Chip, Stack, Typography } from "@mui/material";

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
  return (
    <Card>
      <CardHeader title="News Intelligence" subheader="Classified events with sentiment and importance" />
      <CardContent>
        <Stack spacing={1.2}>
          {events.length === 0 && <Alert severity="info">No news events available.</Alert>}
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
