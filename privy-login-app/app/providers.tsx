"use client";

import { PrivyProvider } from "@privy-io/react-auth";
import { MCPAuthProvider } from "@/lib/mcp-auth";
import { env, validateEnv } from "@/lib/env";

// Validate environment variables on client-side initialization
if (typeof window !== "undefined") {
  try {
    validateEnv();
  } catch (error) {
    console.error("Environment validation failed:", error);
  }
}

// Validate Privy App ID before rendering
if (!env.PRIVY_APP_ID) {
  throw new Error(
    "NEXT_PUBLIC_PRIVY_APP_ID is required. Please set it in your .env.local file.\n" +
    "Example: NEXT_PUBLIC_PRIVY_APP_ID=your-privy-app-id"
  );
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <PrivyProvider
      appId={env.PRIVY_APP_ID!}
      config={{
        loginMethods: ["email"],
        appearance: {
          theme: "dark",
          accentColor: "#6366f1",
          showWalletLoginFirst: false,
        },
        embeddedWallets: {
          ethereum: {
            createOnLogin: "off",
          },
          solana: {
            createOnLogin: "off",
          },
          showWalletUIs: false,
        },
      }}
    >
      <MCPAuthProvider>
        {children}
      </MCPAuthProvider>
    </PrivyProvider>
  );
}

