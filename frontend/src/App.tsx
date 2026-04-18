import { Outlet } from "react-router-dom";
import { CasesProvider } from "./CasesContext";

export default function App() {
  return (
    <CasesProvider>
      <Outlet />
    </CasesProvider>
  )
}