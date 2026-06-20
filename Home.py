import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Financial Modeling Lab", page_icon="📊", layout="wide")

st.title("Financial Modeling Lab")
st.caption("Build your intuition while you model: adjust assumptions and learn what changes downstream.")

st.markdown(
    """
This starter app balances **modeling** and **education**:
- Use the controls to build a 5-year projection
- Hover over input help icons for tooltips
- Open the **Formulas & Definitions** page in the sidebar to learn concepts
"""
)

with st.expander("How this model works", expanded=True):
    st.write(
        "We project revenue, estimate operating performance, convert to free cash flow, "
        "and apply a simple DCF multiple using your discount rate and terminal growth assumptions."
    )

c1, c2, c3 = st.columns(3)

with c1:
    revenue_0 = st.number_input(
        "Base Revenue (Year 0)",
        min_value=0.0,
        value=100_000_000.0,
        step=1_000_000.0,
        help="Starting annual revenue before projections begin.",
    )
    growth_rate = st.slider(
        "Annual Revenue Growth (%)",
        min_value=-20.0,
        max_value=50.0,
        value=8.0,
        step=0.5,
        help="Assumed year-over-year percentage increase in revenue.",
    )

with c2:
    gross_margin = st.slider(
        "Gross Margin (%)",
        min_value=0.0,
        max_value=95.0,
        value=60.0,
        step=0.5,
        help="Gross Profit / Revenue. Higher means better unit economics.",
    )
    opex_ratio = st.slider(
        "Operating Expense Ratio (%)",
        min_value=0.0,
        max_value=90.0,
        value=30.0,
        step=0.5,
        help="Operating expenses as a percent of revenue (SG&A, R&D, etc.).",
    )

with c3:
    tax_rate = st.slider(
        "Tax Rate (%)",
        min_value=0.0,
        max_value=50.0,
        value=21.0,
        step=0.5,
        help="Effective tax rate applied to operating profit in this simplified model.",
    )
    capex_ratio = st.slider(
        "CapEx Ratio (% of Revenue)",
        min_value=0.0,
        max_value=30.0,
        value=5.0,
        step=0.5,
        help="Capital expenditures as a percent of revenue.",
    )

st.subheader("Valuation Assumptions")
v1, v2, v3 = st.columns(3)

with v1:
    discount_rate = st.slider(
        "Discount Rate / WACC (%)",
        min_value=1.0,
        max_value=30.0,
        value=10.0,
        step=0.5,
        help="Required return used to discount future free cash flows to present value.",
    )

with v2:
    terminal_growth = st.slider(
        "Terminal Growth (%)",
        min_value=0.0,
        max_value=8.0,
        value=2.5,
        step=0.1,
        help="Perpetual growth assumption after the explicit forecast period.",
    )

with v3:
    years = st.slider(
        "Projection Years",
        min_value=3,
        max_value=10,
        value=5,
        step=1,
        help="Number of years in explicit forecast horizon.",
    )

if discount_rate <= terminal_growth:
    st.error("Discount rate must be greater than terminal growth for a valid Gordon Growth terminal value.")
    st.stop()

years_index = np.arange(1, years + 1)

g = growth_rate / 100
ngm = gross_margin / 100
opex = opex_ratio / 100
tax = tax_rate / 100
capex = capex_ratio / 100
r = discount_rate / 100
tg = terminal_growth / 100

revenues = [revenue_0 * ((1 + g) ** y) for y in years_index]
gross_profit = [rev * ngm for rev in revenues]
operating_expense = [rev * opex for rev in revenues]
ebitda = [gp - oe for gp, oe in zip(gross_profit, operating_expense)]
taxes = [max(e, 0) * tax for e in ebitda]
capex_values = [rev * capex for rev in revenues]
fcf = [e - t - c for e, t, c in zip(ebitda, taxes, capex_values)]

discount_factors = [(1 / ((1 + r) ** y)) for y in years_index]
pv_fcf = [cf * df for cf, df in zip(fcf, discount_factors)]

terminal_value = (fcf[-1] * (1 + tg)) / (r - tg)
pv_terminal_value = terminal_value * discount_factors[-1]
enterprise_value = sum(pv_fcf) + pv_terminal_value

model_df = pd.DataFrame(
    {
        "Year": years_index,
        "Revenue": revenues,
        "Gross Profit": gross_profit,
        "Operating Expense": operating_expense,
        "EBITDA": ebitda,
        "Taxes": taxes,
        "CapEx": capex_values,
        "Free Cash Flow": fcf,
        "PV of FCF": pv_fcf,
    }
)

st.subheader("Projection Table")
st.dataframe(
    model_df.style.format(
        {
            "Revenue": "${:,.0f}",
            "Gross Profit": "${:,.0f}",
            "Operating Expense": "${:,.0f}",
            "EBITDA": "${:,.0f}",
            "Taxes": "${:,.0f}",
            "CapEx": "${:,.0f}",
            "Free Cash Flow": "${:,.0f}",
            "PV of FCF": "${:,.0f}",
        }
    ),
    use_container_width=True,
)

m1, m2, m3 = st.columns(3)
m1.metric("Sum of PV(FCF)", f"${sum(pv_fcf):,.0f}")
m2.metric("PV of Terminal Value", f"${pv_terminal_value:,.0f}")
m3.metric("Estimated Enterprise Value", f"${enterprise_value:,.0f}")

st.subheader("Free Cash Flow Trend")
st.line_chart(model_df.set_index("Year")[["Free Cash Flow", "PV of FCF"]])

st.info(
    "Tip: Try changing one input at a time (for example growth rate or discount rate) to build intuition "
    "about sensitivity and model behavior."
)
