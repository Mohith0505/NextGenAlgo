import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import MainLayout from "./components/MainLayout";
import Landing from "./pages/Landing";
import AuthSubscription from "./pages/AuthSubscription";
import Dashboard from "./pages/Dashboard";
import BrokerManagement from "./pages/BrokerManagement";
import QuickTradePanel from "./pages/QuickTradePanel";
import ExecutionGroups from "./pages/ExecutionGroups";
import OptionChain from "./pages/OptionChain";
import Strategies from "./pages/Strategies";
import RiskManagement from "./pages/RiskManagement";
import AnalyticsInsights from "./pages/AnalyticsInsights";
import AdminPanel from "./pages/AdminPanel";
import NotFound from "./pages/NotFound";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/auth" element={<AuthSubscription />} />
        <Route element={<MainLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/brokers" element={<BrokerManagement />} />
          <Route path="/quick-trade" element={<QuickTradePanel />} />
          <Route path="/execution-groups" element={<ExecutionGroups />} />
          <Route path="/option-chain" element={<OptionChain />} />
          <Route path="/strategies" element={<Strategies />} />
          <Route path="/risk" element={<RiskManagement />} />
          <Route path="/analytics" element={<AnalyticsInsights />} />
          <Route path="/admin" element={<AdminPanel />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
