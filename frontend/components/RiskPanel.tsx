import { Alert, Card, CardContent, CardHeader, Chip, Stack, Typography } from "@mui/material";

import type { ResearchRisk } from "../types/financials";

type Props = {
  risks: ResearchRisk[];
};

function severityColor(severity: string): "error" | "warning" | "success" | "default" {
  if (severity === "High") return "error";
  if (severity === "Medium") return "warning";
  if (severity === "Low") return "success";
  return "default";
}

export function RiskPanel({ risks }: Props) {
  return (
    <Card>
      <CardHeader title="Key Risks" subheader="Categorized risk factors from filings and commentary" />
      <CardContent>
        <Stack spacing={1.2}>
          {risks.length === 0 && (
            <Alert severity="info">
              No risks extracted yet. We did not detect explicit risk factors in the latest parsed filings or commentary. This can
              happen when disclosures are limited, extraction confidence is low, or source documents are still being processed.
            </Alert>
          )}
          {risks.slice(0, 12).map((risk) => (
            <Stack key={risk.id} spacing={0.5} sx={{ borderBottom: "1px solid #e6e8ec", pb: 1 }}>
              <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                <Chip size="small" label={risk.risk_category} variant="outlined" />
                <Chip size="small" label={risk.severity} color={severityColor(risk.severity)} />
                <Typography variant="caption" color="text.secondary">
                  Confidence {(risk.confidence * 100).toFixed(0)}%
                </Typography>
              </Stack>
              <Typography variant="body2">{risk.description}</Typography>
              <Typography variant="caption" color="text.secondary">
                Source: {risk.source_document} | {new Date(risk.publication_date).toLocaleDateString()}
              </Typography>
            </Stack>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}
