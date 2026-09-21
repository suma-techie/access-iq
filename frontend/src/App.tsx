import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import MyRequests from "./pages/MyRequests";
import Approvals from "./pages/Approvals";
import ClientApprovals from "./pages/ClientApprovals";
import Revocation from "./pages/Revocation";
import Delegations from "./pages/Delegations";
import Projects from "./pages/Projects";
import Applications from "./pages/Applications";
import ApplicationDetail from "./pages/ApplicationDetail";
import Users from "./pages/Users";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/chat" element={<Chat />} />
              <Route path="/my-requests" element={<MyRequests />} />
              <Route path="/approvals" element={<Approvals />} />
              <Route path="/client-approvals" element={<ClientApprovals />} />
              <Route path="/revocation" element={<Revocation />} />
              <Route path="/delegations" element={<Delegations />} />
              <Route path="/projects" element={<Projects />} />
              <Route path="/applications" element={<Applications />} />
              <Route path="/applications/:applicationId" element={<ApplicationDetail />} />
              <Route path="/users" element={<Users />} />
              <Route path="/settings" element={<Settings />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </ThemeProvider>
  );
}
