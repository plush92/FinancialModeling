import { Container } from "@mui/material";
import { FinancialStatementsPage } from "./pages/FinancialStatementsPage";

export default function App() {
  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <FinancialStatementsPage />
    </Container>
  );
}
