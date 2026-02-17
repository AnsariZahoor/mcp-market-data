/**
 * Centralized environment variables configuration
 * Import this file instead of using process.env directly
 * All variables are required - app will warn if missing
 */

export const env = {
  // Privy Configuration
  PRIVY_APP_ID: process.env.NEXT_PUBLIC_PRIVY_APP_ID,
  
  // MCP Server Configuration  
  MCP_AUTH_URL: process.env.NEXT_PUBLIC_MCP_AUTH_URL,
  
  // App Configuration
  APP_URL: process.env.NEXT_PUBLIC_APP_URL,
} as const;

// All environment variables are required
const REQUIRED_ENV_VARS = [
  "PRIVY_APP_ID",
  "MCP_AUTH_URL", 
  "APP_URL",
] as const;

// Validation helper - call this on app start to catch missing env vars early
export function validateEnv() {
  const missing = REQUIRED_ENV_VARS.filter((key) => !env[key]);
  
  if (missing.length > 0) {
    const message = `Missing required environment variables: ${missing.join(", ")}`;
    console.error(message);
    console.error("Please check your .env.local file");
    throw new Error(message);
  }
  
  return true;
}

// Type-safe access
export type EnvConfig = typeof env;

