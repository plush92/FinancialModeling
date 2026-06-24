import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Link,
  Stack,
  Typography,
} from "@mui/material";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import { useMemo } from "react";

import type { IssuesResponse } from "../types/financials";

type Props = {
  issues: IssuesResponse;
};

type GroupedValidationIssue = {
  key: string;
  severity: string;
  ruleName: string;
  description: string;
  count: number;
  filingIds: number[];
};

type IssueHelp = {
  meaning: string;
  fix: string;
  learnMoreHref: string;
};

function getIssueHelp(ruleName: string, description: string): IssueHelp {
  const blob = `${ruleName} ${description}`.toLowerCase();

  if (blob.includes("cash rollforward")) {
    return {
      meaning:
        "Cash rollforward failed means the period-to-period change in cash does not reconcile cleanly with reported operating, investing, and financing cash flows.",
      fix: "Verify cash flow sign conventions, period alignment, and missing line mappings (especially capex and financing cash flow tags) for the affected filing periods.",
      learnMoreHref: "https://www.wallstreetprep.com/knowledge/statement-of-cash-flows/",
    };
  }

  if (blob.includes("balance") || blob.includes("reconcile")) {
    return {
      meaning: "A reconciliation rule failed, indicating one or more accounting relationships did not tie out within tolerance.",
      fix: "Check mapped source fields for missing tags, denominator mismatches, and fiscal period alignment between statements.",
      learnMoreHref: "https://www.investopedia.com/terms/f/financial-statements.asp",
    };
  }

  return {
    meaning: "This validation rule flagged data quality risk in the extracted financial statements.",
    fix: "Review the source filing and mapped fields for missing values, wrong tag mappings, or inconsistent period boundaries.",
    learnMoreHref: "https://www.investopedia.com/terms/d/datavalidation.asp",
  };
}

export function ValidationIssuesTable({ issues }: Props) {
  const groupedValidationIssues = useMemo(() => {
    const grouped = new Map<string, GroupedValidationIssue>();
    for (const issue of issues.validation_issues) {
      const key = `${issue.severity}|${issue.rule_name}|${issue.description}`;
      const existing = grouped.get(key);
      if (existing) {
        existing.count += 1;
        if (issue.filing_id !== null && !existing.filingIds.includes(issue.filing_id)) {
          existing.filingIds.push(issue.filing_id);
        }
        continue;
      }

      grouped.set(key, {
        key,
        severity: issue.severity,
        ruleName: issue.rule_name,
        description: issue.description,
        count: 1,
        filingIds: issue.filing_id !== null ? [issue.filing_id] : [],
      });
    }

    const severityRank: Record<string, number> = {
      error: 0,
      warning: 1,
      info: 2,
    };

    return Array.from(grouped.values()).sort((a, b) => {
      const left = severityRank[a.severity] ?? 3;
      const right = severityRank[b.severity] ?? 3;
      if (left !== right) {
        return left - right;
      }
      if (a.count !== b.count) {
        return b.count - a.count;
      }
      return a.ruleName.localeCompare(b.ruleName);
    });
  }, [issues.validation_issues]);

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
          {groupedValidationIssues.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No validation issues.
            </Typography>
          ) : (
            <Stack spacing={1}>
              {groupedValidationIssues.map((group) => {
                const help = getIssueHelp(group.ruleName, group.description);
                return (
                  <Accordion key={group.key} disableGutters>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Stack spacing={0.5} sx={{ width: "100%" }}>
                        <Stack direction="row" alignItems="center" spacing={1}>
                          <Chip
                            size="small"
                            label={group.severity}
                            color={group.severity === "error" ? "error" : "warning"}
                          />
                          <Typography variant="subtitle2">{group.ruleName}</Typography>
                        </Stack>
                        <Typography variant="body2" color="text.secondary">
                          {group.description}
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {group.count} occurrence{group.count === 1 ? "" : "s"}
                        </Typography>
                      </Stack>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Stack spacing={1}>
                        {group.filingIds.length > 0 && (
                          <Typography variant="body2" color="text.secondary">
                            Affected filings: {group.filingIds.join(", ")}
                          </Typography>
                        )}
                        <Typography variant="body2">
                          <strong>What this means:</strong> {help.meaning}
                        </Typography>
                        <Typography variant="body2">
                          <strong>How to fix:</strong> {help.fix}
                        </Typography>
                        <Link href={help.learnMoreHref} target="_blank" rel="noopener noreferrer" underline="hover">
                          Learn more
                        </Link>
                      </Stack>
                    </AccordionDetails>
                  </Accordion>
                );
              })}
            </Stack>
          )}
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
              pageSizeOptions={[5, 10, 20, 100]}
            />
          )}
        </CardContent>
      </Card>
    </Stack>
  );
}
