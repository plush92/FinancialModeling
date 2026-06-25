import { Button, Card, CardContent, CardHeader, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { useMemo, useState } from "react";

type Props = {
  assumptionsVersion: string;
  onRun: (params: { assumptionsVersion: string; horizonYears: number; revenueGrowth: number; grossMargin: number }) => void;
  running: boolean;
};

export function AssumptionEditorPanel({ assumptionsVersion, onRun, running }: Props) {
  const [horizonYears, setHorizonYears] = useState(7);
  const [revenueGrowth, setRevenueGrowth] = useState(6);
  const [grossMargin, setGrossMargin] = useState(40);

  const versionLabel = useMemo(() => (assumptionsVersion ? assumptionsVersion : "latest"), [assumptionsVersion]);

  return (
    <Card>
      <CardHeader title="Assumption Editor" subheader="Driver overrides for forecast runs (non-destructive)" />
      <CardContent>
        <Stack spacing={1.5}>
          <Typography variant="body2" color="text.secondary">
            Current assumptions version: {versionLabel}
          </Typography>

          <TextField
            select
            size="small"
            label="Forecast Horizon (Years)"
            value={horizonYears}
            onChange={(event) => setHorizonYears(Number(event.target.value))}
          >
            {[5, 6, 7, 8, 9, 10].map((year) => (
              <MenuItem key={year} value={year}>
                {year}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            size="small"
            label="Revenue Growth Override (%)"
            type="number"
            value={revenueGrowth}
            onChange={(event) => setRevenueGrowth(Number(event.target.value))}
          />

          <TextField
            size="small"
            label="Gross Margin Override (%)"
            type="number"
            value={grossMargin}
            onChange={(event) => setGrossMargin(Number(event.target.value))}
          />

          <Button
            variant="contained"
            onClick={() =>
              onRun({
                assumptionsVersion: "latest",
                horizonYears,
                revenueGrowth,
                grossMargin,
              })
            }
            disabled={running}
          >
            {running ? "Running Forecast..." : "Apply & Recalculate"}
          </Button>
        </Stack>
      </CardContent>
    </Card>
  );
}
