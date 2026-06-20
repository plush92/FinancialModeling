CANONICAL_TAG_MAPPINGS = {
    "income_statement": {
        "revenue": [
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "SalesRevenueNet",
            "Revenues",
            "Revenue",
        ],
        "gross_profit": ["GrossProfit"],
        "operating_income": ["OperatingIncomeLoss"],
        "net_income": ["NetIncomeLoss", "ProfitLoss"],
        "eps": ["EarningsPerShareDiluted", "EarningsPerShareBasic"],
    },
    "balance_sheet": {
        "cash": ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"],
        "total_assets": ["Assets"],
        "total_liabilities": ["Liabilities"],
        "shareholder_equity": [
            "StockholdersEquity",
            "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        ],
        "total_debt": [
            "LongTermDebtAndFinanceLeaseObligations",
            "LongTermDebtCurrent",
            "ShortTermBorrowings",
        ],
    },
    "cash_flow_statement": {
        "operating_cash_flow": ["NetCashProvidedByUsedInOperatingActivities"],
        "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
        "free_cash_flow": [],
    },
}

# Metrics that are typically monetary values in companyfacts.
USD_UNIT_METRICS = {
    "revenue",
    "gross_profit",
    "operating_income",
    "net_income",
    "cash",
    "total_assets",
    "total_liabilities",
    "shareholder_equity",
    "total_debt",
    "operating_cash_flow",
    "capex",
    "free_cash_flow",
}
