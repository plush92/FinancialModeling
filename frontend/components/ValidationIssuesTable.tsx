import { Card, CardContent, CardHeader, Chip, Stack, Typography } from "@mui/material";
import { DataGrid, GridColDef } from "@mui/x-data-grid";

import type { IssuesResponse } from "../types/financials";

type Props = {
  issues: IssuesResponse;
};

export function ValidationIssuesTable({ issues }: Props) {
  const validationColumns: GridColDef[] = [
    {
      field: "severity",
      headerName: "Severity",
      minWidth: 110,
      renderCell: (params) => <Chip size="small" label={params.value} color={params.value === "error" ? "error" : "warning"} />,
    },
    { field: "rule_name", headerName: "Rule", minWidth: 180 },
    { field: "description", headerName: "Description", minWidth: 340, flex: 1 },
    { field: "filing_id", headerName: "Filing ID", minWidth: 100 },
  ];

  const mappingColumns: GridColDef[] = [
    { field: "attempted_field", headerName: "Field", minWidth: 150 },
    { field: "xbrl_tag", headerName: "XBRL Tag", minWidth: 230 },
    { field: "confidence", headerName: "Confidence", minWidth: 110 },
    { field: "notes", headerName: "Notes", minWidth: 320, flex: 1 },
  ];

  return (
    <Stack spacing={2}>
      <Card>
        <CardHeader title="Validation Issues" />
        <CardContent>
          <DataGrid
            autoHeight
            rows={issues.validation_issues}
            columns={validationColumns}
            disableRowSelectionOnClick
            pageSizeOptions={[5, 10, 20]}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader title="Mapping Exceptions" />
        <CardContent>
          {issues.mapping_exceptions.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No mapping exceptions.
            </Typography>
          ) : (
            <DataGrid
              autoHeight
              rows={issues.mapping_exceptions}
              columns={mappingColumns}
              disableRowSelectionOnClick
              pageSizeOptions={[5, 10, 20]}
            />
          )}
        </CardContent>
      </Card>
    </Stack>
  );
}
