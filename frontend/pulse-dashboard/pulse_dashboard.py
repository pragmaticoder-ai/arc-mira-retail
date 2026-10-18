"""PULSE: evidence, manager decisions, and observed demand outcomes."""

from __future__ import annotations

import hmac
import os

import data_provider as data
import streamlit as st
import ui

from tools.shared.clock import now

st.set_page_config(page_title="PULSE — Unmet Demand", page_icon="📊", layout="wide")
STORES = {
    "dubai_marina_01": "MIRA Dubai Marina",
    "jbr_01": "MIRA JBR",
    "al_barsha_01": "MIRA Al Barsha",
}
requires_login = bool(os.getenv("K_SERVICE") or os.getenv("DEMO_PASSWORD"))
if requires_login and not st.session_state.get("manager_authenticated"):
    ui.theme(login=True)
    expected_user = os.getenv("DEMO_USERNAME", "")
    expected_password = os.getenv("DEMO_PASSWORD", "")
    if not expected_user or not expected_password:
        st.error("Manager access is not configured.")
        st.stop()
    with st.container(key="manager_access"):
        st.markdown(
            '<div class="login-brand">' + ui.logo() + "</div>", unsafe_allow_html=True
        )
        st.markdown(
            '<div class="login-intro"><span class="pulse-pill">✦ PULSE store intelligence</span><h1>Manager access</h1><p>Sign in to view store intelligence</p></div>',
            unsafe_allow_html=True,
        )
        with st.form("manager_login"):
            username = st.text_input("Manager ID", placeholder="Your manager username")
            password = st.text_input(
                "Password", type="password", placeholder="Enter your password"
            )
            login_store = st.selectbox(
                "Store", list(STORES), format_func=lambda sid: STORES[sid]
            )
            submit = st.form_submit_button(
                "Access dashboard", type="primary", use_container_width=True
            )
        if submit:
            if hmac.compare_digest(
                username.strip().encode(), expected_user.encode()
            ) and hmac.compare_digest(password.encode(), expected_password.encode()):
                st.session_state["manager_authenticated"] = True
                st.session_state["active_store"] = login_store
                st.rerun()
            else:
                st.error("Incorrect username or password.")
        st.markdown(
            '<p class="login-note">MIRA Retail · Operations access</p>',
            unsafe_allow_html=True,
        )
    st.stop()
ui.theme()
REFRESH_SECONDS = int(os.getenv("PULSE_REFRESH_SECONDS", "10"))


def perform(fn, *args) -> None:
    try:
        with st.spinner("Saving manager decision…"):
            fn(*args)
    except (ValueError, RuntimeError) as exc:
        st.error(str(exc))
    else:
        messages = {"approve_discount": "Discount approved and applied to the shared catalog.",
                    "reject_discount": "Discount rejected. Prices remain unchanged.",
                    "approve_po": "Purchase order approved; demo delivery received into shared stock.",
                    "reject_po": "Purchase order rejected. Stock remains unchanged.",
                    "decide_demand": "Manager decision saved. See Action history for the result."}
        st.session_state["action_notice"] = messages.get(fn.__name__, "Decision saved.")
        st.rerun()


def unmet_demand(store: str, hours: int) -> None:
    st.subheader("The demand a completed sale can hide")
    insights = data.demand_insights(store, hours)
    if not insights:
        st.info(
            "No customer intent recorded in this period. Ask ARIA for a product to start the loop."
        )
    for insight in insights:
        with st.container(border=True):
            st.markdown(f"### {insight['product_name']}")
            st.write(insight["summary"])
            counts = insight["counts"]
            cols = st.columns(4)
            for col, label, value in zip(
                cols,
                [
                    "Temporary compromises",
                    "Rejected / abandoned",
                    "Satisfied alternatives",
                    "Original need fulfilled",
                ],
                [
                    counts["compromise"],
                    counts["rejected"] + counts["abandoned"],
                    counts["satisfied"],
                    counts["fulfilled"],
                ],
            ):
                col.metric(label, value)
            st.caption(
                f"{insight['synthetic_sessions']} synthetic seed sessions; other evidence comes from shopper sessions. Unknown outcomes are excluded from explicit unmet-demand totals."
            )
            with st.expander("Customer evidence"):
                for event in insight["evidence"]:
                    st.write(
                        f"**{event['outcome']}** · {event['evidence'] or 'No explicit statement'}"
                    )
                    st.caption(
                        f"Session {event['session_id']} · {event['timestamp']} · {event['data_origin']}"
                    )
            decision = insight["decision"]
            if decision:
                st.success(
                    f"Manager decision: {decision['action']} · {decision['execution']}"
                )
                monitor = insight["outcome_monitor"]
                st.write(
                    f"After decision: {monitor['after_sessions']} new product-request sessions; "
                    f"{monitor['after']['fulfilled']} fulfilled; {monitor['after']['unresolved']} explicit unmet needs."
                )
                st.caption(monitor["note"])
                if decision.get("po_id"):
                    st.caption(
                        f"Purchase order: {decision['po_id']}. Demo delivery is simulated; supplier integration is outside this prototype."
                    )
            else:
                st.write(f"**Recommended:** {insight['recommended_action']}")
                st.dataframe(
                    [
                        {k: v for k, v in option.items() if k != "available"}
                        for option in insight["action_options"]
                    ],
                    hide_index=True,
                    use_container_width=True,
                )
                choices = [
                    o["action"] for o in insight["action_options"] if o["available"]
                ]
                selected = st.selectbox(
                    "Choose an action",
                    choices,
                    index=choices.index(insight["recommended_action"]),
                    key=f"choice_{insight['proposal_key']}",
                )
                if st.button(
                    "Approve selected action",
                    key=f"approve_{insight['proposal_key']}",
                    type="primary",
                ):
                    perform(
                        data.decide_demand, insight["proposal_key"], store, selected
                    )


def stockouts(store: str, hours: int, *, preview=False) -> None:
    patterns = data.stockout_patterns(store, hours)
    selected = st.session_state.get("alert_detail")
    if selected and not preview:
        match = next((p for p in patterns if p["product_id"] == selected), None)
        if st.button("← Back to stockout alerts"):
            st.session_state.pop("alert_detail", None)
            st.rerun()
        if match:
            st.subheader("Alert detail")
            patterns = [match]
        else:
            st.session_state.pop("alert_detail", None)
            st.info("This alert is no longer active for the selected store and period.")
    else:
        st.subheader("Stockout alerts")
    if not patterns:
        st.info("No stockout patterns meet the selected period's incident threshold.")
    for pattern in patterns:
        po = pattern["po"]
        with st.container(border=True):
            ui.alert_heading(
                pattern["product_name"],
                f"{STORES[store]} · {pattern['incident_count']} stockout sessions",
                amount=pattern.get("revenue_at_risk_aed"),
            )
            st.write(f"**Operational hypothesis** · {pattern['root_cause']}")
            st.caption(
                f"{pattern['confidence_level']} heuristic confidence. Timing correlation does not establish causation."
            )
            if preview or not selected:
                if st.button(
                    "View alert details",
                    key=f"detail_{pattern['product_id']}_{preview}",
                ):
                    st.session_state["alert_detail"] = pattern["product_id"]
                    st.session_state["pulse_page_next"] = "Stockout alerts"
                    st.rerun()
                continue
            with st.expander("Evidence and calculation", expanded=True):
                st.write(pattern.get("root_cause_evidence", {}))
                st.write(pattern["calculation_basis"])
                st.caption(
                    f"Modeled recoverable revenue: AED {pattern['revenue_recoverable_aed']:.2f}. Scenario estimate, not measured sales recovery."
                )
            st.markdown("#### Recommended purchase order")
            cols = st.columns(3)
            cols[0].metric("Quantity", str(po["quantity"]) + " units")
            cols[1].metric("Status", po["status"].capitalize())
            cols[2].metric("Priority", po.get("urgency", "Review").capitalize())
            st.caption(
                "Approval simulates delivery and adds these units to shared stock once. No supplier is contacted."
            )
            if po["status"] == "pending":
                approve, reject = st.columns(2)
                if approve.button(
                    "Approve & restock (demo)",
                    key=f"ap_{po['po_id']}",
                    type="primary",
                    use_container_width=True,
                ):
                    perform(data.approve_po, po["po_id"])
                if reject.button(
                    "Reject PO", key=f"rj_{po['po_id']}", use_container_width=True
                ):
                    perform(data.reject_po, po["po_id"])
            else:
                if po["status"] == "rejected":
                    st.warning("Purchase order rejected. Inventory unchanged. See Action history.")
                elif not po.get("inventory_received_at"):
                    st.info("Approved earlier; awaiting stock receipt.")
                    if st.button("Receive approved PO (demo)", key=f"receive_{po['po_id']}"):
                        perform(data.approve_po, po["po_id"])
                else:
                    st.success(f"Completed: {po['quantity']} units received into shared inventory (demo). See Action history.")


def perishables(store: str, *, preview=False) -> None:
    st.subheader("Perishable alerts")
    alerts = data.perishable_alerts(store)
    if not alerts:
        st.info("No perishables require a discount review.")
    for item in alerts:
        with st.container(border=True):
            ui.alert_heading(
                item["product_name"],
                f"{STORES[store]} · {item['days_to_expiry']} days to expiry",
                kind="perishable",
                amount=item["revenue_at_risk_aed"],
            )
            if preview:
                if item["status"] == "approved":
                    st.success(f"Applied: {item['discount_pct']:.0f}% off · AED {item['discounted_price_aed']:.2f}")
                elif item["status"] == "rejected":
                    st.warning("Discount rejected · prices unchanged")
                else:
                    st.write(f"Proposed {item['discount_pct']:.0f}% discount · approval required")
                if st.button("Review perishable", key=f"review_{item['product_id']}"):
                    st.session_state["pulse_page_next"] = "Perishables"
                    st.rerun()
                continue
            metrics = st.columns(3)
            for col, label, value in zip(
                metrics,
                ["In stock", "Days left", "Units at risk"],
                [item["stock_quantity"], item["days_to_expiry"], item["units_at_risk"]],
            ):
                col.metric(label, value)
            st.write(
                f"{item['stock_quantity']} units; {item['units_at_risk']} projected unsold at the available sales rate."
            )
            st.write(
                f"Proposed {item['discount_pct']:.0f}% discount → AED {item['discounted_price_aed']:.2f}"
            )
            with st.expander("Evidence and projection"):
                st.write(item.get("evidence", {}))
                st.caption(
                    "Sell-through and financial values are scenario estimates. They do not establish measured waste recovery."
                )
            if item["status"] == "pending":
                a, b = st.columns(2)
                if a.button("Approve discount", key=f"discount_{item['product_id']}"):
                    perform(data.approve_discount, item["product_id"], store)
                if b.button(
                    "Reject discount", key=f"reject_discount_{item['product_id']}"
                ):
                    perform(data.reject_discount, item["product_id"], store)
            else:
                if item["status"] == "approved":
                    st.success(f"Discount approved and applied: AED {item['discounted_price_aed']:.2f}. Visible to ARIA and shopper checkout.")
                else:
                    st.warning("Discount rejected. Shopper prices unchanged.")


def history(store: str) -> None:
    rows = data.action_history(store)
    st.caption("Persistent decisions for this store, including products whose alerts have cleared. Times include their UTC offset.")
    status = st.selectbox("Action status", ["All", "Completed", "Approved", "Rejected", "Monitoring"])
    filtered = [r for r in rows if status == "All" or r["Status"] == status]
    if not filtered:
        st.info("No decisions match this status yet.")
    else:
        st.dataframe(filtered, hide_index=True, use_container_width=True)


def activity(store: str, hours: int) -> None:
    rows = data.customer_activity(store, hours)
    st.caption("Separate customer profiles, conversations, baskets and orders. Legacy sessions without timestamps are labeled explicitly.")
    customer = st.selectbox("Customer", ["All customers"] + sorted({r["Customer"] for r in rows}))
    filtered = [r for r in rows if customer == "All customers" or r["Customer"] == customer]
    if filtered:
        st.dataframe(filtered, hide_index=True, use_container_width=True)
    else:
        st.info("No customer activity yet. Sign into ARIA as a demo customer and start a conversation.")


def main() -> None:
    stamp = now().strftime("%H:%M:%S %Z")
    ui.topbar(stamp)
    with st.container(key="manager_account"):
        with st.popover("PM", help="Manager account"):
            st.markdown("**Manager account**")
            st.caption(os.getenv("DEMO_USERNAME", "Local manager"))
            if requires_login and st.button("Sign out", key="avatar_sign_out"):
                st.session_state.clear()
                st.rerun()
    if not data.is_live():
        st.warning(
            "Cross-app persistence is not configured. Start both apps with scripts/run_local.py for the complete loop."
        )
    if "pulse_page_next" in st.session_state:
        st.session_state["pulse_page"] = st.session_state.pop("pulse_page_next")
    with st.sidebar:
        st.caption("Store workspace")
        store = st.selectbox(
            "Store",
            list(STORES),
            format_func=lambda sid: STORES[sid],
            key="active_store",
        )
        hours = st.selectbox(
            "Period", [48, 168], format_func=lambda h: f"Last {h} hours"
        )
        st.divider()
        st.radio(
            "Operations",
            ["Overview", "Unmet demand", "Stockout alerts", "Perishables", "Customer activity", "Action history"],
            key="pulse_page",
        )
        if st.button("Refresh now", type="primary", use_container_width=True):
            st.rerun()
        st.caption(f"Updated {stamp}")
        st.caption(
            "Offline fixtures" if data.settings.use_mock else "Google-backed store data"
        )
        if requires_login and st.button("Sign out", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    page = st.session_state.get("pulse_page", "Overview")
    st.title("Store intelligence" if page == "Overview" else page)
    st.caption(f"{STORES[store]} · Last {hours} hours · Human-approved operations")
    if st.session_state.get("action_notice"):
        st.success(st.session_state.pop("action_notice"))
    if not data.settings.use_mock:
        if st.button("Generate Google analysis"):
            with st.spinner("Analyzing store evidence..."):
                try:
                    st.session_state[f"summary_{store}_{hours}"] = data.google_summary(
                        store, hours
                    )
                except Exception:
                    st.error("Google analysis is unavailable. Please retry.")
        if st.session_state.get(f"summary_{store}_{hours}"):
            with st.container(border=True):
                st.markdown("#### PULSE briefing")
                st.write(st.session_state[f"summary_{store}_{hours}"])

    @st.fragment(run_every=REFRESH_SECONDS if REFRESH_SECONDS > 0 else None)
    def live_view():
        board = data.board_data(store, hours) if page == "Overview" else None
        metrics = ({"incidents_48h": sum(p["incident_count"] for p in board["patterns"]),
                    "unresolved": sum(i["counts"]["unresolved"] for i in board["insights"]),
                    "compromises": sum(i["counts"]["compromise"] for i in board["insights"]),
                    "pos_pending": sum(p["po"]["status"] == "pending" for p in board["patterns"])}
                   if board else data.summary_metrics(store, hours))
        completed = sum(r["Status"] == "Completed" for r in (board["history"] if board else data.action_history(store)))
        if board:
            ui.board_hero(STORES[store], metrics["pos_pending"], completed)
        cols = st.columns(4)
        for col, label, key in zip(
            cols,
            ["Stockout sessions", "Explicit unmet needs", "POs pending", "Actions completed"],
            ["incidents_48h", "unresolved", "pos_pending", "completed"],
        ):
            col.metric(label, completed if key == "completed" else metrics[key])
        st.caption(
            f"{metrics['compromises']} temporary compromises · Updated {now():%H:%M:%S %Z}"
        )
        st.markdown(" ")
        if page == "Overview":
            ui.overview_charts(board)
            recent = board["history"][:3]
            if recent:
                with st.container(border=True):
                    st.markdown("#### Recent decisions")
                    st.dataframe(recent, hide_index=True, use_container_width=True)
            left, right = st.columns([1.25, 1])
            with left:
                stockouts(store, hours, preview=True)
            with right:
                perishables(store, preview=True)
        elif page == "Unmet demand":
            unmet_demand(store, hours)
        elif page == "Stockout alerts":
            stockouts(store, hours)
        elif page == "Customer activity":
            activity(store, hours)
        elif page == "Action history":
            history(store)
        else:
            perishables(store)

    live_view()


if __name__ == "__main__":
    main()
