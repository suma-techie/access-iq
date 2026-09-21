import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { fetchRequests } from "../api/endpoints";
import { useAuth } from "../context/AuthContext";
import Logo from "./Logo";
import ProfileMenu from "./ProfileMenu";

const POLL_INTERVAL_MS = 30_000;

function NavSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="nav-section">
      <span className="nav-section-title">{title}</span>
      {children}
    </div>
  );
}

const MOBILE_QUERY = "(max-width: 880px)";

function isMobileViewport(): boolean {
  try {
    return window.matchMedia(MOBILE_QUERY).matches;
  } catch {
    return false;
  }
}

function getInitialSidebarOpen(): boolean {
  try {
    
    if (isMobileViewport()) return false;
    return localStorage.getItem("accessiq_sidebar_open") !== "false";
  } catch {
    return true;
  }
}

export default function Layout() {
  const { isManager, hasAnyRole, user } = useAuth();
  const location = useLocation();
  const [pendingCount, setPendingCount] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(getInitialSidebarOpen);

  function toggleSidebar() {
    setSidebarOpen((prev) => {
      const next = !prev;
      if (!isMobileViewport()) {
        try {
          localStorage.setItem("accessiq_sidebar_open", String(next));
        } catch {
          
        }
      }
      return next;
    });
  }

  useEffect(() => {
    if (isMobileViewport()) setSidebarOpen(false);
  }, [location.pathname]);

  const canSeeApprovals = isManager || hasAnyRole;
  
  const canRequestAccess = !isManager;

  useEffect(() => {
    if (!canSeeApprovals) return;
    let cancelled = false;
    function poll() {
      fetchRequests("approvals").then((reqs) => {
        if (!cancelled) setPendingCount(reqs.length);
      });
    }
    poll();
    const interval = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [canSeeApprovals]);

  return (
    <div className="app-shell-sidebar">
      {sidebarOpen && <div className="sidebar-backdrop" onClick={() => setSidebarOpen(false)} />}
      <aside className={`sidebar ${sidebarOpen ? "" : "collapsed"}`}>
        <div className="brand">
          <Logo size={22} />
          <span>AccessIQ</span>
        </div>

        <NavSection title="Overview">
          <NavLink to="/dashboard">Dashboard</NavLink>
          {canRequestAccess && <NavLink to="/chat">New request</NavLink>}
          {canRequestAccess && <NavLink to="/my-requests">My Requests</NavLink>}
        </NavSection>

        {canSeeApprovals && (
          <NavSection title="Approvals">
            <NavLink to="/approvals">
              Pending Approvals {pendingCount > 0 && <span className="nav-badge">{pendingCount}</span>}
            </NavLink>
            <NavLink to="/client-approvals">Client-Controlled</NavLink>
            <NavLink to="/revocation">Revocation</NavLink>
          </NavSection>
        )}

        <NavSection title="Manage">
          <NavLink to="/projects">Projects</NavLink>
          <NavLink to="/applications">Applications</NavLink>
          {isManager && <NavLink to="/delegations">Delegations</NavLink>}
          {user?.global_role === "admin" && <NavLink to="/users">Users</NavLink>}
        </NavSection>
      </aside>
      <div className="main-area">
        <header className="topbar">
          <button className="sidebar-toggle" onClick={toggleSidebar} aria-label="Toggle menu">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M2 5h14M2 9h14M2 13h14" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            </svg>
          </button>
          <ProfileMenu />
        </header>
        <main className="app-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
