"use client";

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";

interface MCPAuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  token: string | null;
  error: string | null;
  logout: () => void;
  getToken: () => string | null;
}

const MCPAuthContext = createContext<MCPAuthContextType | null>(null);

const MCP_TOKEN_KEY = "mcp_jwt_token";

export function MCPAuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error] = useState<string | null>(null);

  // Load token from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem(MCP_TOKEN_KEY);
    if (savedToken) {
      setToken(savedToken);
    }
    setIsLoading(false);
  }, []);

  // NOTE: Auto-login removed - OAuth flow now uses browser redirects, not API calls

  const logout = useCallback(() => {
    localStorage.removeItem(MCP_TOKEN_KEY);
    setToken(null);
  }, []);

  const getToken = useCallback(() => token, [token]);

  return (
    <MCPAuthContext.Provider
      value={{
        isAuthenticated: !!token,
        isLoading,
        token,
        error,
        logout,
        getToken,
      }}
    >
      {children}
    </MCPAuthContext.Provider>
  );
}

export function useMCPAuth() {
  const context = useContext(MCPAuthContext);
  if (!context) {
    throw new Error("useMCPAuth must be used within MCPAuthProvider");
  }
  return context;
}

