// lib/config.ts
// Single source of truth for runtime configuration.
// Every value comes from an environment variable so nothing is hardcoded.
// Locally these are read from .env.local; in Cloud Run they are injected
// from Secret Manager (via --set-secrets) or --set-env-vars. Code never
// changes between environments — only the env source does.
//
// This module is server-only (API routes / server components). Do not import
// it into client components; values here may hold sensitive endpoints.

export interface AriaConfig {
  /** Base URL of the deployed ARIA ADK agent. Unset → use built-in mock. */
  ariaAgentUrl: string | null
  /** Optional IAM identity/bearer token for authenticated agent calls. */
  ariaAgentToken: string | null
  /** Default store for the demo session. */
  defaultStoreId: string
  /** Default customer persona for the demo session. */
  defaultCustomerId: string
  /** Upstream request timeout (ms) when proxying to the real agent. */
  requestTimeoutMs: number
  /** True when no real agent is configured — serve scripted mock data. */
  useMock: boolean
}

function readEnv(key: string, fallback?: string): string | null {
  const v = process.env[key]
  if (v === undefined || v === '') return fallback ?? null
  return v
}

export function getAriaConfig(): AriaConfig {
  const ariaAgentUrl = readEnv('ARIA_AGENT_URL')
  return {
    ariaAgentUrl,
    ariaAgentToken: readEnv('ARIA_AGENT_TOKEN'),
    defaultStoreId: readEnv('DEFAULT_STORE_ID', 'dubai_marina_01')!,
    defaultCustomerId: readEnv('DEFAULT_CUSTOMER_ID', 'sarah_123')!,
    requestTimeoutMs: Number(readEnv('ARIA_REQUEST_TIMEOUT_MS', '15000')),
    useMock: ariaAgentUrl === null,
  }
}
