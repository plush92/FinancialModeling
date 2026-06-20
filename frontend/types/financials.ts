export type Company = {
  id: number;
  ticker: string;
  company_name: string;
  cik: number | null;
};

export type IncomeStatement = {
  id: number;
  company_id: number;
  fiscal_year: number;
  fiscal_period: string;
  revenue: number;
  gross_profit: number;
  operating_income: number;
  net_income: number;
  eps: number;
};

export type BalanceSheet = {
  id: number;
  company_id: number;
  fiscal_year: number;
  fiscal_period: string;
  cash: number;
  total_assets: number;
  total_liabilities: number;
  shareholder_equity: number;
  total_debt: number;
};

export type CashFlowStatement = {
  id: number;
  company_id: number;
  fiscal_year: number;
  fiscal_period: string;
  operating_cash_flow: number;
  capex: number;
  free_cash_flow: number;
};

export type FinancialsResponse = {
  company: Company;
  income_statements: IncomeStatement[];
  balance_sheets: BalanceSheet[];
  cash_flow_statements: CashFlowStatement[];
};
