// Server-side configuration. The storefront always uses the shared backend.
export function getAriaConfig() {
  return {
    ariaAgentUrl: process.env.ARIA_AGENT_URL || 'http://127.0.0.1:8001',
    ariaAgentToken: process.env.ARIA_AGENT_TOKEN || null,
    defaultStoreId: process.env.DEFAULT_STORE_ID || 'dubai_marina_01',
    defaultCustomerId: process.env.DEFAULT_CUSTOMER_ID || 'sarah_123',
    requestTimeoutMs: Number(process.env.ARIA_REQUEST_TIMEOUT_MS || '15000'),
  }
}
