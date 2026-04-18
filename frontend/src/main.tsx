import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import router from "./router";
import { theme } from "./theme";
import { CasesProvider } from "./CasesContext";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <ThemeProvider theme={theme}>
    <CssBaseline />
    <CasesProvider>
      <RouterProvider router={router} />
    </CasesProvider>
  </ThemeProvider>
);