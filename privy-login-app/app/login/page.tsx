"use client";

import { Suspense } from "react";
import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { usePrivy } from "@privy-io/react-auth";
import { Loader2, AlertCircle, Shield, CheckCircle2 } from "lucide-react";

const OAUTH_PARAMS_KEY = "mcp_oauth_params";

interface OAuthParams {
  redirect_uri: string | null;
  state: string | null;
  client_id: string | null;
  client_name: string | null;
  scope: string | null;
}

function LoadingFallback() {
  return (
    <div className="welcome-container">
      <div className="welcome-card">
        <Loader2 className="mcp-spinner" size={40} />
        <p style={{ marginTop: "16px", color: "#888" }}>Loading...</p>
      </div>
    </div>
  );
}

function MCPLoginContent() {
  const searchParams = useSearchParams();
  const { ready, authenticated, login, logout, getAccessToken } = usePrivy();
  
  const [oauthParams, setOauthParams] = useState<OAuthParams>({
    redirect_uri: null,
    state: null,
    client_id: null,
    client_name: null,
    scope: null,
  });
  const [error, setError] = useState<string | null>(null);
  const [isRedirecting, setIsRedirecting] = useState(false);
  const [redirectComplete, setRedirectComplete] = useState(false);
  const [paramsLoaded, setParamsLoaded] = useState(false);

  // Read OAuth parameters from URL or sessionStorage
  useEffect(() => {
    // First try to get from URL
    let redirect_uri = searchParams.get("redirect_uri");
    let state = searchParams.get("state");
    let client_id = searchParams.get("client_id");
    let client_name = searchParams.get("client_name");
    let scope = searchParams.get("scope");

    // If URL has params, save to sessionStorage
    if (redirect_uri && state) {
      const params = { redirect_uri, state, client_id, client_name, scope };
      sessionStorage.setItem(OAUTH_PARAMS_KEY, JSON.stringify(params));
      console.log("OAuth params saved to sessionStorage:", params);
      setOauthParams(params);
    } else {
      // Try to restore from sessionStorage (after Privy redirect)
      const savedParams = sessionStorage.getItem(OAUTH_PARAMS_KEY);
      if (savedParams) {
        try {
          const params = JSON.parse(savedParams) as OAuthParams;
          console.log("OAuth params restored from sessionStorage:", params);
          redirect_uri = params.redirect_uri;
          state = params.state;
          client_id = params.client_id;
          client_name = params.client_name;
          scope = params.scope;
          setOauthParams(params);
        } catch (e) {
          console.error("Failed to parse saved OAuth params:", e);
        }
      }
    }

    // Validate required params
    if (!redirect_uri) {
      setError("Missing redirect_uri parameter. This page must be accessed via OAuth flow.");
    } else if (!state) {
      setError("Missing state parameter. Invalid OAuth request.");
    } else {
      setError(null);
    }

    setParamsLoaded(true);
  }, [searchParams]);

  // Handle redirect after Privy authentication
  const handleOAuthRedirect = useCallback(async () => {
    if (!oauthParams.redirect_uri || !oauthParams.state) {
      setError("Missing OAuth parameters. Cannot complete authorization.");
      return;
    }

    setIsRedirecting(true);
    setError(null);

    try {
      console.log("Getting Privy access token...");
      const privyToken = await getAccessToken();
      
      if (!privyToken) {
        throw new Error("Failed to obtain authentication token");
      }
      console.log("Got Privy token, length:", privyToken.length);

      // Build callback URL with code and state
      const callbackUrl = new URL(oauthParams.redirect_uri);
      callbackUrl.searchParams.set("code", privyToken);
      callbackUrl.searchParams.set("state", oauthParams.state);

      const redirectUrl = callbackUrl.toString();
      console.log("Redirecting to:", redirectUrl);
      
      // Clear saved params before redirect
      sessionStorage.removeItem(OAUTH_PARAMS_KEY);

      // IMPORTANT:
      // - For localhost callbacks (Cursor/Claude), navigating can leave the tab "stuck" or show a 400 on refresh.
      //   We trigger via hidden iframe and keep the UX clean.
      // - For remote callbacks (e.g. ChatGPT redirect_uri=https://chatgpt.com/...), iframe navigation is usually
      //   blocked by X-Frame-Options/CSP, so we MUST do a top-level redirect.
      const isLocalhostCallback = (() => {
        try {
          const u = new URL(oauthParams.redirect_uri);
          return (
            u.protocol === "http:" &&
            (u.hostname === "localhost" || u.hostname === "127.0.0.1" || u.hostname === "[::1]")
          );
        } catch {
          return false;
        }
      })();

      // Show success immediately (in case something external intercepts the callback)
      setRedirectComplete(true);
      setIsRedirecting(false);

      if (isLocalhostCallback) {
        const iframe = document.createElement("iframe");
        iframe.style.display = "none";
        iframe.src = redirectUrl;
        document.body.appendChild(iframe);

        setTimeout(() => {
          iframe.remove();
        }, 5000);
      } else {
        // Give React a moment to paint the success state, then navigate top-level.
        await new Promise((resolve) => setTimeout(resolve, 100));
        window.location.assign(redirectUrl);
      }
    } catch (err) {
      console.error("OAuth redirect failed:", err);
      setError(err instanceof Error ? err.message : "Authorization failed");
      setIsRedirecting(false);
    }
  }, [oauthParams, getAccessToken]);

  // Auto-redirect when Privy authenticates
  useEffect(() => {
    if (!paramsLoaded) return;
    
    console.log("Auth state check:", { 
      authenticated, 
      ready, 
      redirect_uri: oauthParams.redirect_uri, 
      state: oauthParams.state,
      isRedirecting 
    });
    
    if (authenticated && ready && oauthParams.redirect_uri && oauthParams.state && !isRedirecting) {
      console.log("All conditions met, calling handleOAuthRedirect...");
      handleOAuthRedirect();
    }
  }, [authenticated, ready, oauthParams, isRedirecting, handleOAuthRedirect, paramsLoaded]);

  const handleLogout = () => {
    logout();
    setError(null);
    setIsRedirecting(false);
  };

  // Loading state
  if (!ready || !paramsLoaded) {
    return (
      <div className="welcome-container">
        <div className="welcome-card">
          <Loader2 className="mcp-spinner" size={40} />
          <p style={{ marginTop: "16px", color: "#888" }}>Initializing...</p>
        </div>
      </div>
    );
  }

  // Error state - missing OAuth params
  if (!oauthParams.redirect_uri || !oauthParams.state) {
    return (
      <div className="welcome-container">
        <div className="welcome-card">
          <div className="welcome-badge">ERROR</div>
          
          <div className="welcome-brand">
            <img 
              src="https://www.app.pandaterminal.com/logo.svg" 
              alt="PANDA" 
              className="welcome-logo" 
            />
            <span className="welcome-name">PANDA MCP</span>
          </div>

          <h1 className="welcome-title" style={{ fontSize: "36px" }}>
            Invalid OAuth Request
          </h1>

          <div className="welcome-error">
            <AlertCircle size={18} />
            <span>{error || "This page must be accessed via the MCP OAuth flow."}</span>
          </div>

          <p className="welcome-description">
            Please initiate authentication from your MCP client application.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="welcome-container">
      <div className="welcome-card">
        <div className="welcome-badge">MCP SERVER</div>
        
        <div className="welcome-brand">
          <img 
            src="https://www.app.pandaterminal.com/logo.svg" 
            alt="PANDA" 
            className="welcome-logo" 
          />
          <span className="welcome-name">PANDA MCP</span>
        </div>

        <h1 className="welcome-title">
          Authorize Access
        </h1>

        <p className="welcome-description">
          {oauthParams.client_name 
            ? `${oauthParams.client_name} is requesting access to your PANDA MCP account.`
            : "An application is requesting access to your PANDA MCP account."
          }
        </p>

        {oauthParams.scope && (
          <div className="oauth-scope-info">
            <Shield size={16} />
            <span>Requested permissions: {oauthParams.scope}</span>
          </div>
        )}

        {error && (
          <div className="welcome-error">
            <AlertCircle size={18} />
            <span>{error}</span>
            {authenticated && (
              <button onClick={handleLogout} className="error-retry-link">
                Try again
              </button>
            )}
          </div>
        )}

        {redirectComplete ? (
          <div className="welcome-success">
            <CheckCircle2 size={48} color="#22c55e" />
            <h2 style={{ marginTop: "16px", color: "#22c55e", fontSize: "24px" }}>
              Authorization Complete
            </h2>
            <p style={{ marginTop: "8px", color: "#888" }}>
              You can close this tab and return to your application.
            </p>
          </div>
        ) : authenticated && !error ? (
          <div className="welcome-connecting">
            <Loader2 className="mcp-spinner" size={24} />
            <p>{isRedirecting ? "Redirecting to application..." : "Completing authorization..."}</p>
          </div>
        ) : !authenticated ? (
          <button 
            onClick={login}
            className="welcome-button"
          >
            Authorize with Privy
          </button>
        ) : null}

        {!redirectComplete && (
          <div className="welcome-footer">
            <p>
              You will be redirected back to the requesting application.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function MCPLoginPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <MCPLoginContent />
    </Suspense>
  );
}
