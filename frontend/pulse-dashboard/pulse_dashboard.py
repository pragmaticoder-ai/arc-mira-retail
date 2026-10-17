"""PULSE — Operations Intelligence Dashboard (Streamlit).

DEMO STAND-IN built by the frontend engineer so the operations half of the
demo runs offline. The backend engineer owns the production version wired to
the real PULSE agent + AlloyDB/BigQuery. Data shapes follow AGENT_CONTRACTS.md.

Demo moment (ARCHITECTURE.md §10.4): the dashboard auto-refreshes every 10s.
When ARIA logs a session to the bridge, the stockout alert appears within one
refresh cycle, and approving a PO flips its status live on screen.

Config comes from env (PULSE_AGENT_URL, etc.) so it maps to Secret Manager in
Cloud Run — no hardcoded endpoints. When PULSE_AGENT_URL is unset, mock data
is used.
"""

from __future__ import annotations

import os
import time

import streamlit as st

# data_provider serves LIVE data from the real PULSE tools (reading the shared
# ARIA→PULSE bridge) when the backend is importable, else static mock_data.
import data_provider as data

# ── Config (env-backed; Secret Manager in production) ────────────────────
STORE_NAME = os.getenv("PULSE_STORE_NAME", "MIRA Dubai Marina")
REFRESH_SECONDS = int(os.getenv("PULSE_REFRESH_SECONDS", "10"))

# ── Brand tokens (from BRAND.md / lib/brand.ts) ──────────────────────────
MIRA_600 = "#0a5c44"
PULSE_500 = "#c8891a"
DANGER = "#dc2626"
SUCCESS = "#16a34a"
SLATE_900 = "#0f172a"

st.set_page_config(
    page_title="PULSE — MIRA Retail Operations",
    page_icon="📊",
    layout="wide",
)

# ── Minimal brand CSS on top of the Streamlit theme ──────────────────────
st.markdown(
    """
    <style>
      .block-container { padding-top: 2rem; }
      .pulse-nav {
        background: #0f172a; color: #fff; padding: 10px 16px;
        border-radius: 8px; display: flex; justify-content: space-between;
        align-items: center; margin-bottom: 16px;
      }
      .alert-card {
        background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
        padding: 16px; margin-bottom: 12px;
      }
      .alert-stockout { border-left: 4px solid #dc2626; }
      .alert-perishable { border-left: 4px solid #c8891a; }
      .alert-approved { border-left: 4px solid #16a34a; }
      .conf-high { color: #16a34a; font-weight: 600; }
      .evidence { background: #f8fafc; border-radius: 6px; padding: 8px 12px;
                  font-size: 12px; color: #64748b; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session state for PO / discount approvals ────────────────────────────
if "po_status" not in st.session_state:
    st.session_state.po_status = {}  # po_id -> approved/rejected
if "discount_status" not in st.session_state:
    st.session_state.discount_status = {}  # product_id -> approved/rejected


def nav_bar() -> None:
    mode = data.source_label()
    st.markdown(
        f"""
        <div class="pulse-nav">
          <div><strong>MIRA</strong><span style="color:{PULSE_500}">Retail</span>
               &nbsp;/ PULSE Operations</div>
          <div style="font-size:12px;">
            <span style="color:{SUCCESS}">● {mode}</span> &nbsp;
            Last refresh {time.strftime('%H:%M:%S')}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar() -> None:
    with st.sidebar:
        st.selectbox("Store", [STORE_NAME], index=0)
        st.selectbox("Period", ["Last 48 hours", "Last 7 days"], index=0)
        if st.button("↻ Refresh now", use_container_width=True):
            st.rerun()
        st.caption(f"Auto-refresh every {REFRESH_SECONDS}s")
        st.divider()
        m = data.summary_metrics()
        st.metric("Stockout alerts", len(data.stockout_patterns()))
        st.metric("Perishable alerts", len(data.perishable_alerts()))
        st.metric("POs pending", m["pos_pending"])


def metric_row() -> None:
    m = data.summary_metrics()
    c1, c2, c3 = st.columns(3)
    c1.metric("Incidents (48h)", m["incidents_48h"], delta=m["incidents_delta"])
    c2.metric(
        "Revenue at risk",
        f"AED {m['revenue_at_risk_aed']:,.0f}",
        delta="exposure",
        delta_color="inverse",
    )
    c3.metric("POs pending", m["pos_pending"])


def stockout_section() -> None:
    st.subheader("Stockout patterns")
    patterns = data.stockout_patterns()
    if not patterns:
        st.info("No stockout patterns in the current window. "
                "When ARIA logs an unavailable-item session, it appears here.")
        return
    for p in patterns:
        po = p["po"]
        status = st.session_state.po_status.get(po["po_id"], po["status"])
        css = "alert-approved" if status == "approved" else "alert-stockout"

        with st.container():
            st.markdown(f'<div class="alert-card {css}">', unsafe_allow_html=True)
            st.markdown(
                f"**⚠ {p['product_name']} · {STORE_NAME} · "
                f"{p['incident_count']} incidents**"
            )
            # WHAT / IMPACT / WHY per PULSE report structure
            st.markdown(
                f"**Impact:** AED {p['revenue_lost_aed']:,.0f} lost · "
                f"AED {p['revenue_at_risk_aed']:,.0f} at risk · "
                f"AED {p['revenue_recoverable_aed']:,.0f} recoverable if approved today"
            )
            st.markdown(
                f"**Why:** {p['root_cause']} "
                f'<span class="conf-high">[{p["confidence_level"]} confidence]</span>',
                unsafe_allow_html=True,
            )

            with st.expander("Evidence"):
                ev = p.get("root_cause_evidence", {})
                if ev:
                    st.markdown(
                        f"- Delivery: **{ev.get('delivery_day', '—')} "
                        f"{ev.get('delivery_time', '')}** · "
                        f"Peak demand: **{ev.get('demand_peak_window', '—')}** · "
                        f"Gap: **{ev.get('gap_hours', 0)}h**"
                    )
                    for src in ev.get("data_sources", []):
                        st.markdown(f"- {src}")
                st.caption(p.get("calculation_basis", ""))

            st.markdown(
                f"**Draft PO:** {po['quantity']} units · urgency **{po['urgency']}** · "
                f"{po['supplier']}"
            )
            st.caption(po["justification"])
            st.caption("This PO requires your approval before proceeding.")

            if status == "pending":
                a, b = st.columns(2)
                if a.button("✅ Approve PO", key=f"ap_{po['po_id']}", type="primary"):
                    st.session_state.po_status[po["po_id"]] = "approved"
                    data.approve_po(po["po_id"])
                    st.rerun()
                if b.button("❌ Reject", key=f"rj_{po['po_id']}"):
                    st.session_state.po_status[po["po_id"]] = "rejected"
                    data.reject_po(po["po_id"])
                    st.rerun()
            else:
                st.success(f"PO {status.upper()} — status updated in AlloyDB")

            st.markdown("</div>", unsafe_allow_html=True)


def perishable_section() -> None:
    st.subheader("Perishable discount proposals")
    alerts = data.perishable_alerts()
    if not alerts:
        st.info("No perishable items at risk right now.")
        return
    for a in alerts:
        status = st.session_state.discount_status.get(a["product_id"], a["status"])
        css = "alert-approved" if status == "approved" else "alert-perishable"

        with st.container():
            st.markdown(f'<div class="alert-card {css}">', unsafe_allow_html=True)
            st.markdown(
                f"**🕒 {a['product_name']} · {STORE_NAME} · "
                f"expiring in {a['days_to_expiry']} days**"
            )
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("In stock", a["stock_quantity"])
            m2.metric("Days left", a["days_to_expiry"])
            m3.metric("Will expire", a["units_at_risk"])
            m4.metric("Recoverable", f"AED {a['revenue_recoverable_aed']:,.0f}")
            st.markdown(
                f"Current sell rate **{a['daily_sales_rate']}/day** · at this rate "
                f"**{a['units_at_risk']} units** expire → **AED {a['revenue_at_risk_aed']:,.0f}** wasted"
            )
            st.markdown(
                f"**Recommended:** {a['discount_pct']:.0f}% discount → "
                f"AED {a['discounted_price_aed']:.2f}"
            )
            with st.expander("Evidence"):
                for k, v in a["evidence"].items():
                    st.markdown(f"- **{k}:** {v}")

            if status == "pending":
                a1, a2 = st.columns(2)
                if a1.button(
                    "✅ Approve discount", key=f"apd_{a['product_id']}", type="primary"
                ):
                    st.session_state.discount_status[a["product_id"]] = "approved"
                    # Closed loop: flip discount_active=True so ARIA surfaces it.
                    data.approve_discount(a["product_id"])
                    st.rerun()
                if a2.button("❌ Reject", key=f"rjd_{a['product_id']}"):
                    st.session_state.discount_status[a["product_id"]] = "rejected"
                    st.rerun()
                st.caption("Once approved, ARIA surfaces this discount to customers.")
            else:
                st.success(
                    f"Discount {status.upper()} — discount_active=True set in inventory"
                    if status == "approved"
                    else f"Discount {status.upper()}"
                )

            st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    nav_bar()
    sidebar()
    metric_row()
    st.divider()
    left, right = st.columns(2)
    with left:
        stockout_section()
    with right:
        perishable_section()

    # Live auto-refresh — the before/after demo moment.
    time.sleep(REFRESH_SECONDS)
    st.rerun()


if __name__ == "__main__":
    main()
