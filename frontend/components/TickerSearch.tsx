import SearchIcon from "@mui/icons-material/Search";
import { LoadingButton } from "@mui/lab";
import { Stack, TextField } from "@mui/material";
import { useState } from "react";

type TickerSearchProps = {
  isLoading: boolean;
  onSearch: (ticker: string) => Promise<void>;
};

export function TickerSearch({ isLoading, onSearch }: TickerSearchProps) {
  const [ticker, setTicker] = useState("AAPL");

  return (
    <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
      <TextField
        label="Ticker"
        value={ticker}
        onChange={(event) => setTicker(event.target.value.toUpperCase())}
        sx={{ maxWidth: 220 }}
      />
      <LoadingButton
        variant="contained"
        loading={isLoading}
        loadingPosition="start"
        startIcon={<SearchIcon />}
        onClick={() => onSearch(ticker)}
      >
        Load Historical Financials
      </LoadingButton>
    </Stack>
  );
}
