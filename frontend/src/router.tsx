import { createBrowserRouter } from "react-router-dom";
import App from "./App";
import HomePage from "./pages/HomePage";
import CaseDetailPage from "./pages/CaseDetailPage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "cases/", element: <CaseDetailPage /> }
    ]
  }
]);

export default router;