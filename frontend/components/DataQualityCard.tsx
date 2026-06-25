import { Alert, Card, CardContent, CardHeader, Stack, Typography } from "@mui/material";
import { useMemo } from "react";

import type { QualityResponse } from "../types/financials";
import { CompletenessScoreDisplay } from "./CompletenessScoreDisplay";

type Props = {
  quality: QualityResponse;
};

export function DataQualityCard({ quality }: Props) {
  const groupedWarnings = useMemo(() => {
    const grouped = new Map<string, number>();
    for (const warning of quality.warnings) {
      grouped.set(warning, (grouped.get(warning) ?? 0) + 1);
    }
    return Array.from(grouped.entries())
      .map(([message, count]) => ({ message, count }))
      .sort((a, b) => b.count - a.count);
  }, [quality.warnings]);

  const groupedErrors = useMemo(() => {
    const grouped = new Map<string, number>();
    for (const error of quality.errors) {
      grouped.set(error, (grouped.get(error) ?? 0) + 1);
    }
    return Array.from(grouped.entries())
      .map(([message, count]) => ({ message, count }))
      .sort((a, b) => b.count - a.count);
  }, [quality.errors]);

  return (
    <Card>
      <CardHeader title="Data Quality" subheader="Reconciliation and completeness checks" />
      <CardContent>
        <Stack spacing={2}>
          <CompletenessScoreDisplay score={quality.quality_score} />
          <Typography variant="body2">Warnings: {quality.warnings.length} ({groupedWarnings.length} unique)</Typography>
          <Typography variant="body2">Errors: {quality.errors.length} ({groupedErrors.length} unique)</Typography>
          {groupedWarnings.slice(0, 3).map((warning) => (
            <Alert key={`warning-${warning.message}`} severity="warning">
              {warning.message}
              {warning.count > 1 ? ` (${warning.count} occurrences)` : ""}
            </Alert>
          ))}
          {groupedErrors.slice(0, 3).map((error) => (
            <Alert key={`error-${error.message}`} severity="error">
              {error.message}
              {error.count > 1 ? ` (${error.count} occurrences)` : ""}
            </Alert>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}
