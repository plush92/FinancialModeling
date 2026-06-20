import { Box, Chip, Typography } from "@mui/material";

type Props = {
  score: number;
};

function qualityColor(score: number): "success" | "warning" | "error" {
  if (score >= 85) {
    return "success";
  }
  if (score >= 60) {
    return "warning";
  }
  return "error";
}

export function CompletenessScoreDisplay({ score }: Props) {
  return (
    <Box>
      <Typography variant="body2" color="text.secondary">
        Completeness & Reconciliation Score
      </Typography>
      <Chip label={`${score}/100`} color={qualityColor(score)} />
    </Box>
  );
}
