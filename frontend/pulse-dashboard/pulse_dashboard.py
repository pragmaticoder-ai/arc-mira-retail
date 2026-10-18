"""PULSE: evidence, manager decisions, and observed demand outcomes."""
from __future__ import annotations

import os

import data_provider as data
import streamlit as st

from tools.shared.clock import now

st.set_page_config(page_title="PULSE — Unmet Demand", page_icon="📊", layout="wide")
STORES = {"dubai_marina_01": "MIRA Dubai Marina", "jbr_01": "MIRA JBR", "al_barsha_01": "MIRA Al Barsha"}
REFRESH_SECONDS = int(os.getenv("PULSE_REFRESH_SECONDS", "10"))


def perform(fn, *args) -> None:
    try:
        fn(*args)
    except (ValueError, RuntimeError) as exc:
        st.error(str(exc))
    else:
        st.rerun()


def unmet_demand(store: str, hours: int) -> None:
    st.subheader("The demand a completed sale can hide")
    insights = data.demand_insights(store, hours)
    if not insights:
        st.info("No customer intent recorded in this period. Ask ARIA for a product to start the loop.")
    for insight in insights:
        with st.container(border=True):
            st.markdown(f"### {insight['product_name']}")
            st.write(insight["summary"])
            counts = insight["counts"]
            cols = st.columns(4)
            for col, label, value in zip(cols, ["Temporary compromises", "Rejected / abandoned", "Satisfied alternatives", "Original need fulfilled"],
                                         [counts["compromise"], counts["rejected"] + counts["abandoned"], counts["satisfied"], counts["fulfilled"]]):
                col.metric(label, value)
            st.caption(f"{insight['synthetic_sessions']} synthetic seed sessions; other evidence comes from local shopper sessions. Unknown outcomes are excluded from explicit unmet-demand totals.")
            with st.expander("Customer evidence"):
                for event in insight["evidence"]:
                    st.write(f"**{event['outcome']}** · {event['evidence'] or 'No explicit statement'}")
                    st.caption(f"Session {event['session_id']} · {event['timestamp']} · {event['data_origin']}")
            decision = insight["decision"]
            if decision:
                st.success(f"Manager decision: {decision['action']} · {decision['execution']}")
                monitor = insight["outcome_monitor"]
                st.write(f"After decision: {monitor['after_sessions']} new product-request sessions; "
                         f"{monitor['after']['fulfilled']} fulfilled; {monitor['after']['unresolved']} explicit unmet needs.")
                st.caption(monitor["note"])
                if decision.get("po_id"):
                    st.caption(f"Purchase-order draft: {decision['po_id']}; supplier delivery remains outside this prototype.")
            else:
                st.write(f"**Recommended:** {insight['recommended_action']}")
                st.dataframe([{k: v for k, v in option.items() if k != "available"} for option in insight["action_options"]], hide_index=True, use_container_width=True)
                choices = [o["action"] for o in insight["action_options"] if o["available"]]
                selected = st.selectbox("Choose an action", choices,
                    index=choices.index(insight["recommended_action"]), key=f"choice_{insight['proposal_key']}")
                if st.button("Approve selected action", key=f"approve_{insight['proposal_key']}", type="primary"):
                    perform(data.decide_demand, insight["proposal_key"], store, selected)


def stockouts(store: str, hours: int) -> None:
    st.subheader("Stockout patterns and purchase orders")
    for pattern in data.stockout_patterns(store, hours):
        po = pattern["po"]
        with st.container(border=True):
            st.write(f"**{pattern['product_name']} · {pattern['incident_count']} stockout sessions**")
            st.write(f"Operational hypothesis: {pattern['root_cause']}")
            st.caption(f"{pattern['confidence_level']} heuristic confidence. Timing correlation does not establish causation.")
            with st.expander("Illustrative impact assumptions"):
                st.write(pattern["calculation_basis"])
                st.write(f"Modeled exposure: AED {pattern['revenue_at_risk_aed']:.2f}; modeled recoverable: AED {pattern['revenue_recoverable_aed']:.2f}.")
                st.caption("Scenario estimates, not measured lost sales or realized recovery.")
            st.write(f"PO {po['po_id']} · {po['quantity']} units · {po['status']}")
            if po["status"] == "pending":
                a, b = st.columns(2)
                if a.button("Approve PO", key=f"ap_{po['po_id']}"):
                    perform(data.approve_po, po["po_id"])
                if b.button("Reject PO", key=f"rj_{po['po_id']}"):
                    perform(data.reject_po, po["po_id"])
            else:
                st.caption("Decision persisted. Refreshing does not create a replacement within this 24-hour cycle.")


def perishables(store: str) -> None:
    st.subheader("Perishable discount proposals")
    alerts = data.perishable_alerts(store)
    if not alerts:
        st.info("No perishables require a discount review.")
    for item in alerts:
        with st.container(border=True):
            st.write(f"**{item['product_name']}** · {item['days_to_expiry']} days to expiry")
            st.write(f"{item['stock_quantity']} units; {item['units_at_risk']} projected unsold at the seeded sales rate.")
            st.write(f"Proposed {item['discount_pct']:.0f}% discount → AED {item['discounted_price_aed']:.2f}")
            st.caption("Sell-through and financial estimates use synthetic local velocity data.")
            if item["status"] == "pending":
                a, b = st.columns(2)
                if a.button("Approve discount", key=f"discount_{item['product_id']}"):
                    perform(data.approve_discount, item["product_id"], store)
                if b.button("Reject discount", key=f"reject_discount_{item['product_id']}"):
                    perform(data.reject_discount, item["product_id"], store)
            else:
                st.success(f"Discount {item['status']}; decision stored for this expiry batch.")


def main() -> None:
    st.title("PULSE · Unmet Demand")
    st.caption(f"{data.source_label()} · Refreshed {now():%H:%M:%S %Z}")
    if not data.is_live():
        st.warning("Cross-app persistence is not configured. Start both apps with scripts/run_local.py for the complete loop.")
    st.caption("Local deterministic prototype. Google model and cloud SDK execution are not integrated.")
    with st.sidebar:
        store = st.selectbox("Store", list(STORES), format_func=lambda sid: STORES[sid])
        hours = st.selectbox("Period (hours)", [48, 168])
        if st.button("Refresh now"):
            st.rerun()
    @st.fragment(run_every=REFRESH_SECONDS if REFRESH_SECONDS > 0 else None)
    def live_view():
        metrics = data.summary_metrics(store, hours)
        columns = st.columns(4)
        for col, label, value in zip(columns, ["Stockout sessions", "Explicit unmet needs", "Temporary compromises", "POs pending"], metrics.values()):
            col.metric(label, value)
        unmet_demand(store, hours)
        st.divider()
        left, right = st.columns(2)
        with left:
            stockouts(store, hours)
        with right:
            perishables(store)
    live_view()


if __name__ == "__main__":
    main()
