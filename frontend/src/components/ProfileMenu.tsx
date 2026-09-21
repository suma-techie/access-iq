import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { avatarUrl } from "../api/endpoints";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";

function initials(name: string | undefined): string {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  return parts
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join("");
}

export default function ProfileMenu() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function handleLogout() {
    logout();
    
    setTimeout(() => navigate("/", { replace: true }), 0);
  }

  function goToSettings() {
    setOpen(false);
    navigate("/settings");
  }

  return (
    <div className="profile-menu" ref={ref}>
      <button className="profile-avatar" onClick={() => setOpen((o) => !o)} aria-label="Account menu">
        {user?.avatar_url ? <img src={avatarUrl(user.id)} alt="" /> : initials(user?.display_name)}
      </button>
      {open && (
        <div className="profile-dropdown">
          <div className="profile-dropdown-header">
            <span className="profile-name">{user?.display_name}</span>
            <span className="profile-email">{user?.email}</span>
            <span className="profile-role-tag">{user?.global_role}</span>
          </div>
          <button className="profile-dropdown-item" onClick={goToSettings}>
            Settings
          </button>
          <button className="profile-dropdown-item" onClick={toggleTheme}>
            <span>{theme === "dark" ? "Dark mode" : "Light mode"}</span>
            <span className={`theme-switch ${theme === "light" ? "on" : ""}`}>
              <span className="theme-switch-knob" />
            </span>
          </button>
          <button className="profile-dropdown-item danger" onClick={handleLogout}>
            Log out
          </button>
        </div>
      )}
    </div>
  );
}
