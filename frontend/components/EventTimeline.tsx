import { Alert, Card, CardContent, CardHeader, Chip, Stack, Typography } from "@mui/material";

import type { TimelineItem } from "../types/financials";

type Props = {
  items: TimelineItem[];
};

export function EventTimeline({ items }: Props) {
  return (
    <Card>
      <CardHeader title="Event Timeline" subheader="Chronological filings, risks, guidance, and news" />
      <CardContent>
        <Stack spacing={1.1}>
          {items.length === 0 && <Alert severity="info">Timeline is empty.</Alert>}
          {items.slice(0, 20).map((item, index) => (
            <Stack key={`${item.item_type}-${item.title}-${index}`} spacing={0.4} sx={{ borderBottom: "1px solid #e6e8ec", pb: 1 }}>
              <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                <Chip size="small" label={item.item_type} variant="outlined" />
                <Typography variant="caption" color="text.secondary">
                  {new Date(item.date).toLocaleDateString()}
                </Typography>
                {item.sentiment && <Chip size="small" label={item.sentiment} />}
                {item.importance_score != null && (
                  <Typography variant="caption" color="text.secondary">
                    Importance {item.importance_score}/10
                  </Typography>
                )}
              </Stack>
              <Typography variant="subtitle2">{item.title}</Typography>
              <Typography variant="body2">{item.summary}</Typography>
              {item.source_document && (
                <Typography variant="caption" color="text.secondary">
                  Source: {item.source_document}
                </Typography>
              )}
            </Stack>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}
