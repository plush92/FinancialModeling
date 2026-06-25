import { Card, CardContent, CardHeader, Stack, Typography } from "@mui/material";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid, Legend } from "recharts";

import type { ForecastPeriod } from "../types/financials";

type Props = {
  projections: ForecastPeriod[];
};

export function ForecastChartView({ projections }: Props) {
  const rows = projections.map((period) => ({
    fiscal_year: String(period.fiscal_year),
    revenue: period.income_statement.revenue,
    net_income: period.income_statement.net_income,
    free_cash_flow: period.cash_flow_statement.free_cash_flow,
  }));

  return (
    <Card>
      <CardHeader title="Forecast Chart View" subheader="Revenue, Net Income, and Free Cash Flow" />
      <CardContent>
        {rows.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            No forecast rows available.
          </Typography>
        ) : (
          <Stack spacing={1}>
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={rows} margin={{ top: 8, right: 20, left: 10, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="fiscal_year" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="revenue" name="Revenue" stroke="#1d4ed8" strokeWidth={2} dot={{ r: 2 }} />
                <Line type="monotone" dataKey="net_income" name="Net Income" stroke="#16a34a" strokeWidth={2} dot={{ r: 2 }} />
                <Line type="monotone" dataKey="free_cash_flow" name="Free Cash Flow" stroke="#ef4444" strokeWidth={2} dot={{ r: 2 }} />
              </LineChart>
            </ResponsiveContainer>
          </Stack>
        )}
      </CardContent>
    </Card>
  );
}
