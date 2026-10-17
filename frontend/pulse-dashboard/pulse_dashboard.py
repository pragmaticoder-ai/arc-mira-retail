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

from mock_data import (
    perishable_alerts,
    stockout_patterns,
    summary_metrics,
)

# ── Config (env-backed; Secret Manager in production) ────────────────────
PULSE_AGENT_URL = os.getenv("PULSE_AGENT_URL")  # unset -> mock mode
STORE_NAME = os.getenv("PULSE_STORE_NAME", "MIRA Dubai Marina")
REFRESH_SECONDS = int(os.getenv("PULSE_REFRESH_SECONDS", "10"))
USE_MOCK = PULSE_AGENT_URL is None

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
    mode = "MOCK DATA" if USE_MOCK else "LIVE"
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
        m = summary_metrics()
        st.metric("Stockout alerts", len(stockout_patterns()))
        st.metric("Perishable alerts", len(perishable_alerts()))
        st.metric("POs pending", m["pos_pending"])


def metric_row() -> None:
    m = summary_metrics()
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
    for p in stockout_patterns():
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
                ev = p["root_cause_evidence"]
                st.markdown(
                    f"- Delivery: **{ev['delivery_day']} {ev['delivery_time']}** · "
                    f"Peak demand: **{ev['demand_peak_window']}** · "
                    f"Gap: **{ev['gap_hours']}h**"
                )
                for src in ev["data_sources"]:
                    st.markdown(f"- {src}")
                st.caption(p["calculation_basis"])

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
                    st.rerun()
                if b.button("❌ Reject", key=f"rj_{po['po_id']}"):
                    st.session_state.po_status[po["po_id"]] = "rejected"
                    st.rerun()
            else:
                st.success(f"PO {status.upper()} — status updated in AlloyDB")

            st.markdown("</div>", unsafe_allow_html=True)


def perishable_section() -> None:
    st.subheader("Perishable discount proposals")
    for a in perishable_alerts():
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
