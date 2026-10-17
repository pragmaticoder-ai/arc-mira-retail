// app/api/aria/chat/route.ts
// ARIA chat endpoint implementing the Agent API contract (POST /aria/chat).
//
// Behaviour is env-driven (see lib/config.ts):
//   - ARIA_AGENT_URL unset  → serve the scripted mock (local dev, offline demo)
//   - ARIA_AGENT_URL set     → proxy to the real ADK agent, forwarding the
//                              ARIA_AGENT_TOKEN as a Bearer token if present
//
// No endpoint or credential is hardcoded; all come from the environment so
// they can be sourced from Secret Manager in Cloud Run without code changes.

import { NextResponse } from 'next/server'
import { getAriaConfig } from '@/lib/config'
import { mockAriaResponse } from '@/lib/mockAria'
import type { AriaChatRequest, AriaChatResponse } from '@/lib/types'

export const dynamic = 'force-dynamic'

function badRequest(message: string) {
  return NextResponse.json({ error: true, error_message: message }, { status: 400 })
}

export async function POST(request: Request) {
  const cfg = getAriaConfig()

  let body: Partial<AriaChatRequest>
  try {
    body = await request.json()
  } catch {
    return badRequest('Invalid JSON body')
  }

  if (!body.message || typeof body.message !== 'string') {
    return badRequest('message is required')
  }

  // Fill contract-required fields from env-backed defaults when omitted.
  const req: AriaChatRequest = {
    session_id: body.session_id ?? crypto.randomUUID(),
    customer_id: body.customer_id ?? cfg.defaultCustomerId,
    store_id: body.store_id ?? cfg.defaultStoreId,
    message: body.message,
  }

  // ── Mock mode ──────────────────────────────────────────────────────
  if (cfg.useMock) {
    const res: AriaChatResponse = mockAriaResponse(req)
    return NextResponse.json(res)
  }

  // ── Proxy to the real ADK agent ────────────────────────────────────
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), cfg.requestTimeoutMs)
  try {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (cfg.ariaAgentToken) headers['Authorization'] = `Bearer ${cfg.ariaAgentToken}`

    const upstream = await fetch(`${cfg.ariaAgentUrl}/aria/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify(req),
      signal: controller.signal,
    })

    if (!upstream.ok) {
      return NextResponse.json(
        { error: true, error_message: `Agent returned ${upstream.status}` },
        { status: 502 },
      )
    }
    const data = (await upstream.json()) as AriaChatResponse
    return NextResponse.json(data)
  } catch (err) {
    const aborted = err instanceof Error && err.name === 'AbortError'
    return NextResponse.json(
      { error: true, error_message: aborted ? 'Agent request timed out' : 'Agent request failed' },
      { status: 504 },
    )
  } finally {
    clearTimeout(timeout)
  }
}
