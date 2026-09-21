import { createContext, useContext, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { fetchMe, login as loginRequest } from "../api/endpoints";
import { apiClient, getStoredToken, setStoredToken } from "../api/client";
import { APPROVAL_GRANTING_ROLES } from "../types";
import type { ApplicationRoleAssignment, User } from "../types";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  roleApplicationIds: string[];
  hasAnyRole: boolean;
  isManager: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

async function loadRoleApplicationIds(userId: string): Promise<string[]> {
  const { data } = await apiClient.get<ApplicationRoleAssignment[]>(`/users/${userId}/roles`);
  
  return data
    .filter((r) => r.revoked_at === null && APPROVAL_GRANTING_ROLES.includes(r.role_name))
    .map((r) => r.application_id);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [roleApplicationIds, setRoleApplicationIds] = useState<string[]>([]);

  const sessionRequestId = useRef(0);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setIsLoading(false);
      return;
    }
    const requestId = ++sessionRequestId.current;
    fetchMe()
      .then(async (u) => {
        if (sessionRequestId.current !== requestId) return;
        setUser(u);
        setRoleApplicationIds(await loadRoleApplicationIds(u.id));
      })
      .catch(() => {
        if (sessionRequestId.current === requestId) setStoredToken(null);
      })
      .finally(() => {
        if (sessionRequestId.current === requestId) setIsLoading(false);
      });
  }, []);

  async function login(email: string, password: string) {
    const requestId = ++sessionRequestId.current;
    const { access_token, user: loggedInUser } = await loginRequest(email, password);
    if (sessionRequestId.current !== requestId) return;
    setStoredToken(access_token);
    setUser(loggedInUser);
    setRoleApplicationIds(await loadRoleApplicationIds(loggedInUser.id));
    
    setIsLoading(false);
  }

  async function refreshUser() {
    const fresh = await fetchMe();
    setUser(fresh);
  }

  function logout() {
    sessionRequestId.current++;
    setStoredToken(null);
    setUser(null);
    setRoleApplicationIds([]);
  }

  const isManager = user?.global_role === "manager" || user?.global_role === "admin";

  return (
    <AuthContext.Provider
      value={{ user, isLoading, roleApplicationIds, hasAnyRole: roleApplicationIds.length > 0, isManager, login, logout, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
