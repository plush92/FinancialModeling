import { Stack, ToggleButton, ToggleButtonGroup, Typography } from "@mui/material";

import type { ForecastScenario } from "../types/financials";

type Props = {
  scenario: ForecastScenario;
  onChange: (scenario: ForecastScenario) => void;
};

export function ScenarioSelector({ scenario, onChange }: Props) {
  return (
    <Stack spacing={0.5}>
      <Typography variant="subtitle2">Scenario</Typography>
      <ToggleButtonGroup
        size="small"
        exclusive
        value={scenario}
        onChange={(_, value: ForecastScenario | null) => {
          if (value) {
            onChange(value);
          }
        }}
      >
        <ToggleButton value="base">Base</ToggleButton>
        <ToggleButton value="bull">Bull</ToggleButton>
        <ToggleButton value="bear">Bear</ToggleButton>
      </ToggleButtonGroup>
    </Stack>
  );
}
