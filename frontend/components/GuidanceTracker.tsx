import { Alert, Card, CardContent, CardHeader } from "@mui/material";
import { DataGrid, type GridColDef } from "@mui/x-data-grid";

import type { GuidanceRecord } from "../types/financials";

type Props = {
  guidance: GuidanceRecord[];
};

export function GuidanceTracker({ guidance }: Props) {
  const columns: GridColDef[] = [
    { field: "publication_date", headerName: "Date", minWidth: 110 },
    { field: "guidance_type", headerName: "Guidance Type", minWidth: 180, flex: 1 },
    { field: "guidance_value", headerName: "Guidance", minWidth: 160, flex: 1 },
    {
      field: "confidence",
      headerName: "Confidence",
      minWidth: 130,
      valueFormatter: (value) => `${(Number(value) * 100).toFixed(0)}%`,
    },
    { field: "source_document", headerName: "Source", minWidth: 220, flex: 1 },
  ];

  const rows = guidance;

  return (
    <Card>
      <CardHeader title="Guidance Tracker" subheader="Management guidance history and confidence" />
      <CardContent>
        {rows.length === 0 ? (
          <Alert severity="info">
            No guidance extracted yet. We did not find explicit forward-looking guidance language in the latest processed documents.
            Try refreshing data after new filings, earnings calls, or press releases are available.
          </Alert>
        ) : (
          <DataGrid autoHeight rows={rows} columns={columns} disableRowSelectionOnClick pageSizeOptions={[5, 10, 20, 100]} />
        )}
      </CardContent>
    </Card>
  );
}
