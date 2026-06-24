import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import { Alert, Button, Card, CardContent, CardHeader, Chip, Divider, Stack, Typography } from "@mui/material";
import { useMemo } from "react";

import type { TimelineItem } from "../types/financials";

type Props = {
  items: TimelineItem[];
};

type FilingCard = {
  key: string;
  filingType: string;
  date: string;
  sourceName: string;
  sourceUrl: string | null;
  keyChanges: string[];
};

const FILING_TYPE_PATTERN = /(10-Q|10-K|8-K|20-F|6-K|S-1|DEF 14A)/i;

function inferFilingType(item: TimelineItem): string {
  if (item.filing_type) {
    return item.filing_type;
  }
  const probe = `${item.source_document ?? ""} ${item.title}`;
  const match = probe.match(FILING_TYPE_PATTERN);
  return match ? match[1].toUpperCase() : "Filing";
}

function buildFilingCards(items: TimelineItem[]): FilingCard[] {
  const groups = new Map<string, FilingCard>();

  for (const item of items) {
    const sourceName = item.source_document ?? item.title;
    const filingType = inferFilingType(item);
    const groupKey = `${sourceName}::${item.date}`;
    const existing = groups.get(groupKey);

    const changeText = item.item_type === "Document" ? item.summary : `${item.item_type}: ${item.summary}`;

    if (existing) {
      if (!existing.keyChanges.includes(changeText)) {
        existing.keyChanges.push(changeText);
      }
      if (!existing.sourceUrl && item.source_document_url) {
        existing.sourceUrl = item.source_document_url;
      }
      continue;
    }

    groups.set(groupKey, {
      key: groupKey,
      filingType,
      date: item.date,
      sourceName,
      sourceUrl: item.source_document_url ?? null,
      keyChanges: [changeText],
    });
  }

  return Array.from(groups.values())
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 20);
}

export function EventTimeline({ items }: Props) {
  const filingCards = useMemo(() => buildFilingCards(items), [items]);

  return (
    <Card>
      <CardHeader title="Event Timeline" subheader="Deduplicated filing timeline with key changes and source links" />
      <CardContent>
        <Stack spacing={1.1}>
          {filingCards.length === 0 && (
            <Alert severity="info">
              Timeline is empty because we have not yet extracted dated research, risks, guidance, or news items for this ticker. Try
              Refresh data after syncing newer filings and news sources.
            </Alert>
          )}
          {filingCards.map((filing) => (
            <Stack key={filing.key} spacing={1} sx={{ border: "1px solid", borderColor: "divider", borderRadius: 1, p: 1.25 }}>
              <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                <Chip size="small" label={filing.filingType} variant="outlined" />
                <Typography variant="caption" color="text.secondary">
                  {new Date(filing.date).toLocaleDateString()}
                </Typography>
              </Stack>

              <Typography variant="subtitle2">{filing.sourceName}</Typography>

              <Divider />

              <Stack spacing={0.35}>
                <Typography variant="caption" color="text.secondary">
                  Key changes
                </Typography>
                {filing.keyChanges.slice(0, 4).map((change) => (
                  <Typography key={change} variant="body2">
                    - {change}
                  </Typography>
                ))}
              </Stack>

              {filing.sourceUrl ? (
                <Stack direction="row" justifyContent="flex-end">
                  <Button
                    size="small"
                    variant="text"
                    href={filing.sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    endIcon={<OpenInNewIcon />}
                  >
                    View full document
                  </Button>
                </Stack>
              ) : (
                <Typography variant="caption" color="text.secondary">
                  Full document link unavailable for this entry.
                </Typography>
              )}
            </Stack>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}
