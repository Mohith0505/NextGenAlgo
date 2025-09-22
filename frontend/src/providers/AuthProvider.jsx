import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, getAuthToken, setAuthToken } from "../api";

const AuthContext = createContext(undefined);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => getAuthToken());
  const [user, setUser] = useState(null);
  const [initialising, setInitialising] = useState(!!token);

  useEffect(() => {
    let mounted = true;
    setAuthToken(token);
    if (!token) {
      setUser(null);
      setInitialising(false);
      return;
    }

    async function loadProfile() {
      try {
        const profile = await api.getCurrentUser();
        if (mounted) setUser(profile);
      } catch (err) {
        console.error("Failed to load user profile", err);
        if (mounted) {
          setToken(null);
          setAuthToken(null);
          setUser(null);
        }
      } finally {
        if (mounted) setInitialising(false);
      }
    }

    loadProfile();
    return () => {
      mounted = false;
    };
  }, [token]);

  const login = useCallback(async ({ email, password }) => {
    const response = await api.login({ email, password });
    setToken(response.access_token);
    setAuthToken(response.access_token);
    const profile = await api.getCurrentUser();
    setUser(profile);
    return profile;
  }, []);

  const register = useCallback(async ({ name, email, password, phone }) => {
    await api.register({ name, email, password, phone });
    return login({ email, password });
  }, [login]);

  const logout = useCallback(() => {
    setToken(null);
    setAuthToken(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ token, user, initialising, login, register, logout }),
    [token, user, initialising, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuthContext must be used within AuthProvider");
  }
  return context;
}
