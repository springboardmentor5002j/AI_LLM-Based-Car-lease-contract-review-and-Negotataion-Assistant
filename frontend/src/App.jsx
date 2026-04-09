import { Routes, Route } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import Dashboard from "./pages/Dashboard";
import Reports from "./pages/Reports";

function App() {

  return (
    <Routes>

      {/* Upload Screen */}
      <Route path="/" element={<UploadPage />} />

      {/* Dashboard Screen */}
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/reports" element={<Reports />} />

    </Routes>
  );

}

export default App;