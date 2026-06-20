import streamlit as st

st.set_page_config(page_title="Formulas & Definitions", page_icon="📘", layout="wide")

st.title("Formulas & Definitions")
st.caption("A quick reference for the concepts used in the model.")

st.header("Core Projection Formulas")

st.markdown(
    r"""
- **Revenue projection**
  - $\text{Revenue}_t = \text{Revenue}_0 \times (1 + g)^t$

- **Gross Profit**
  - $\text{Gross Profit}_t = \text{Revenue}_t \times \text{Gross Margin}$

- **Operating Expense**
  - $\text{OpEx}_t = \text{Revenue}_t \times \text{OpEx Ratio}$

- **EBITDA (simplified)**
  - $\text{EBITDA}_t = \text{Gross Profit}_t - \text{OpEx}_t$

- **Taxes (simplified)**
  - $\text{Taxes}_t = \max(\text{EBITDA}_t, 0) \times \text{Tax Rate}$

- **Capital Expenditures**
  - $\text{CapEx}_t = \text{Revenue}_t \times \text{CapEx Ratio}$

- **Free Cash Flow (FCF)**
  - $\text{FCF}_t = \text{EBITDA}_t - \text{Taxes}_t - \text{CapEx}_t$
"""
)

st.header("Valuation Formulas")

st.markdown(
    r"""
- **Discount factor**
  - $\text{DF}_t = \frac{1}{(1+r)^t}$

- **Present value of yearly FCF**
  - $\text{PV(FCF)}_t = \text{FCF}_t \times \text{DF}_t$

- **Terminal value (Gordon Growth)**
  - $\text{TV}_n = \frac{\text{FCF}_n \times (1+g_{term})}{r - g_{term}}$

- **Present value of terminal value**
  - $\text{PV(TV)} = \text{TV}_n \times \text{DF}_n$

- **Enterprise value (simplified)**
  - $\text{EV} = \sum_{t=1}^{n} \text{PV(FCF)}_t + \text{PV(TV)}$
"""
)

st.header("Definitions")

definitions = {
    "Revenue": "Total sales generated in a period.",
    "Gross Margin": "Gross profit as a percentage of revenue.",
    "OpEx (Operating Expense)": "Costs required to run operations (e.g., SG&A, R&D).",
    "EBITDA": "Earnings before interest, taxes, depreciation, and amortization. Here it is approximated.",
    "CapEx": "Capital expenditures; long-term investments in assets.",
    "FCF": "Cash generated after operating costs, taxes, and reinvestment needs.",
    "WACC / Discount Rate": "Required return used to discount future cash flows.",
    "Terminal Growth": "Long-run perpetual growth assumption after forecast years.",
    "Enterprise Value": "Value of operating assets before adjusting for cash/debt.",
}

for term, definition in definitions.items():
    st.markdown(f"- **{term}**: {definition}")

st.success(
    "As the model expands, this page can become a full learning center with examples, mini quizzes, and deeper accounting links."
)
