import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/ResponsiveDashboard";
import { Toaster } from "./components/ui/sonner";
import "./App.css";
import "./styles/responsive.css";

function App() {
  return (
    <div className="App min-h-screen bg-[#0a1628]">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="*" element={<Dashboard />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
