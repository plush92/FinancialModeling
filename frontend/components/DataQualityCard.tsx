import { Alert, Card, CardContent, CardHeader, Stack, Typography } from "@mui/material";

import type { QualityResponse } from "../types/financials";
import { CompletenessScoreDisplay } from "./CompletenessScoreDisplay";

type Props = {
  quality: QualityResponse;
};

export function DataQualityCard({ quality }: Props) {
  return (
    <Card>
      <CardHeader title="Data Quality" subheader="Reconciliation and completeness checks" />
      <CardContent>
        <Stack spacing={2}>
          <CompletenessScoreDisplay score={quality.quality_score} />
          <Typography variant="body2">Warnings: {quality.warnings.length}</Typography>
          <Typography variant="body2">Errors: {quality.errors.length}</Typography>
          {quality.warnings.slice(0, 3).map((warning, idx) => (
            <Alert key={`warning-${idx}`} severity="warning">
              {warning}
            </Alert>
          ))}
          {quality.errors.slice(0, 3).map((error, idx) => (
            <Alert key={`error-${idx}`} severity="error">
              {error}
            </Alert>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}
