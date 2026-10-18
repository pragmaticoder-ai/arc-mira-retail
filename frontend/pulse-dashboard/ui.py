"""MIRA visual components; operational data and decisions remain in the provider."""

from __future__ import annotations

import html

import streamlit as st

MARK = """<svg width="36" height="36" viewBox="0 0 38 38" fill="none" aria-hidden="true"><line x1="19" y1="34" x2="19" y2="17" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><path d="M19 21 C19 21 10 19 8 12 C12 9 19 14 19 21Z" fill="currentColor"/><path d="M19 21 C19 21 28 19 30 12 C26 9 19 14 19 21Z" fill="currentColor" opacity=".55"/><path d="M5 27 L8 27 L10 23 L12 31 L14.5 25 L17 27 L19 27 L21 27 L23.5 23 L26 31 L28 25 L30 27 L33 27" stroke="#c8891a" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>"""


def logo(tagline="OPERATIONS DASHBOARD"):
    return f'<div class="mira-logo">{MARK}<div><span class="mira-word">MIRA<span>Retail</span></span><small>{html.escape(tagline)}</small></div></div>'


def theme(*, login=False):
    st.markdown(
        """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
html,body,[class*="css"],.stApp {font-family:Inter,system-ui,sans-serif;color:#1e293b}
[data-testid="stAppViewContainer"]{background:#f1f5f9}
[data-testid="stHeader"]{background:transparent;height:0}
[data-testid="stToolbar"],#MainMenu,footer{display:none}
[data-testid="stMainBlockContainer"]{max-width:1440px;padding:84px 32px 40px}
[data-testid="stSidebar"]{background:#f1f5f9;border-right:1px solid #e2e8f0;min-width:240px;max-width:260px}
[data-testid="stSidebarUserContent"]{padding-top:76px}
[data-testid="stSidebarCollapsedControl"]{top:64px}
h1{font-size:26px!important;font-weight:600!important;letter-spacing:-.025em}
h2{font-size:20px!important;font-weight:600!important}h3{font-size:17px!important;font-weight:500!important}
p,label,[data-testid="stMarkdownContainer"]{font-size:14px;line-height:1.6}
[data-testid="stTextInput"] [data-baseweb="input"],[data-testid="stSelectbox"] [data-baseweb="select"]>div{background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px}
[data-testid="stTextInput"] input{background:transparent}
[data-testid="stCaptionContainer"] p{font-size:12px;color:#64748b}
[data-testid="stMetric"]{background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:18px 20px}
[data-testid="stMetricLabel"]{color:#64748b;font-size:12px}
[data-testid="stMetricValue"]{font-size:30px;font-weight:600;letter-spacing:-.025em}
[data-testid="stVerticalBlockBorderWrapper"]{background:white;border-radius:8px}
[data-testid="stExpander"]{background:#f8fafc;border:1px solid #e2e8f0}
[data-testid="stButton"] button,[data-testid="stFormSubmitButton"] button{border-radius:6px;font-size:13px;font-weight:500;min-height:38px}
[data-testid="stBaseButton-primary"],[data-testid="stBaseButton-primaryFormSubmit"]{background:#0a5c44;border-color:#0a5c44;color:white}
button:focus-visible,input:focus-visible{outline:3px solid #a3d9c6!important;outline-offset:2px}
[data-testid="stRadio"] label:has(input:checked){background:#edf7f3;color:#073d2e;border-radius:6px}
.mira-logo{display:flex;align-items:center;gap:8px;color:#0a5c44}
.mira-word{font-size:23px;font-weight:600;letter-spacing:-.025em;line-height:1.2}
.mira-word span{color:#c8891a}.mira-logo small{display:block;font-size:9px;letter-spacing:.1em;color:#94a3b8}
.pulse-topbar{position:fixed;left:0;right:0;top:0;height:56px;background:#0f172a;z-index:999;display:flex;align-items:center;justify-content:space-between;padding:0 24px;border-bottom:1px solid #1e293b}
.pulse-topbar .mira-logo{color:white}.pulse-topbar .mira-word{font-size:17px}.pulse-topbar svg{width:26px;height:26px}.pulse-topbar .mira-logo small{display:none}
.pulse-topbar-left{display:flex;align-items:center;gap:18px}.pulse-topbar-title{font-size:13px;color:#94a3b8}.pulse-topbar-right{display:flex;align-items:center;gap:12px;font-size:12px;color:#cbd5e1}
.pulse-pill{display:inline-flex;align-items:center;gap:5px;background:#fef9ec;border:1px solid #fde68a;border-radius:999px;padding:3px 10px;color:#92400e;font-size:11px;font-weight:500}
.st-key-manager_account{position:fixed;top:9px;right:24px;z-index:1001;width:40px}.st-key-manager_account button{border-radius:50%;background:#0a5c44;color:white;border:0;min-height:30px;padding:2px 5px}.pulse-topbar-right{padding-right:48px}
.pulse-avatar{width:30px;height:30px;background:#0a5c44;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-size:11px}
.alert-heading{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;border-bottom:1px solid #e2e8f0;padding:0 0 12px 12px;border-left:3px solid #dc2626;margin-bottom:10px}
.alert-heading.perishable{border-left-color:#c8891a}.alert-heading h3{margin:0;font-size:16px!important}.alert-heading p{margin:3px 0 0;font-size:12px;color:#64748b}
.alert-heading .impact{text-align:right;font-weight:600;color:#991b1b;white-space:nowrap}.alert-heading.perishable .impact{color:#92400e}.impact small{display:block;font-size:10px;font-weight:400;color:#64748b}
.login-brand{text-align:center;margin-bottom:16px}.login-brand .mira-logo{justify-content:center}
.login-intro{text-align:center;margin:16px 0 22px}.login-intro h1{font-size:22px!important;margin:12px 0 2px;padding:0}.login-intro p{font-size:13px;color:#64748b;margin:0}
.login-note{font-size:11px!important;color:#94a3b8;text-align:center;margin:12px 0 0}
.board-hero{background:linear-gradient(115deg,#073d2e,#0a5c44 65%,#14725b);padding:24px 28px;border-radius:16px;color:white;margin:4px 0 24px;box-shadow:0 8px 24px #0a5c4414;position:relative;overflow:hidden}
.board-hero:after{content:"";position:absolute;right:-30px;top:-100px;width:260px;height:260px;border:35px solid #ffffff0d;border-radius:50%;pointer-events:none}
.board-hero small{color:#bce6d6;letter-spacing:.14em;font-size:10px;font-weight:600}.board-hero h2{color:white;font-size:25px!important;margin:6px 0;padding:0}.board-hero p{color:#d1eadf;margin:0;max-width:650px}
[data-testid="stMetric"]{border-radius:12px;box-shadow:0 3px 12px #0f172a05;border-top:3px solid #0a5c44}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:12px}
.section-kicker{font-size:10px;color:#0a5c44;letter-spacing:.13em;font-weight:600;margin-bottom:4px}
.status-chip{display:inline-block;border-radius:99px;padding:4px 10px;background:#edf7f3;color:#0a5c44;font-size:11px;font-weight:600}
@media(max-width:720px){[data-testid="stMainBlockContainer"]{padding:78px 16px 24px}.pulse-topbar{padding:0 16px}.pulse-topbar-title,.refresh-stamp{display:none}.alert-heading{flex-wrap:wrap}}
</style>""",
        unsafe_allow_html=True,
    )
    if login:
        st.markdown(
            """<style>
[data-testid="stAppViewContainer"]{background:#0f172a}
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"]{display:none}
[data-testid="stMainBlockContainer"]{max-width:440px;padding:0 24px;margin:clamp(40px,10vh,120px) auto 48px}
.st-key-manager_access{background:white;border:1px solid #e2e8f0;border-radius:14px;padding:32px 28px}
[data-testid="stForm"]{border:0;padding:0;background:transparent}
[data-testid="stFormSubmitButton"] button{width:100%}
</style>""",
            unsafe_allow_html=True,
        )


def topbar(stamp):
    st.markdown(
        f'<header class="pulse-topbar"><div class="pulse-topbar-left">{logo()}<span class="pulse-topbar-title">/ PULSE Operations</span></div><div class="pulse-topbar-right"><span class="pulse-pill">✦ PULSE</span><span class="refresh-stamp">Updated {html.escape(stamp)}</span></div></header>',
        unsafe_allow_html=True,
    )


def alert_heading(name, subtitle, *, kind="stockout", amount=None):
    impact = (
        f'<div class="impact">AED {amount:,.2f}<small>Modeled exposure</small></div>'
        if amount is not None
        else ""
    )
    st.markdown(
        f'<div class="alert-heading {kind}"><div><h3>{html.escape(name)}</h3><p>{html.escape(subtitle)}</p></div>{impact}</div>',
        unsafe_allow_html=True,
    )


def board_hero(store, pending, completed):
    st.markdown(f'<div class="board-hero"><small>OPERATIONS / LIVE WORKSPACE</small><h2>{html.escape(store)}</h2><p>{pending} purchase orders awaiting review · {completed} completed actions. Turn shopper demand into the next customer’s better experience.</p></div>', unsafe_allow_html=True)


def overview_charts(board):
    import altair as alt

    synthetic=sum(i["synthetic_sessions"] for i in board["insights"])
    st.caption(f"Evidence includes {synthetic} synthetic seed product/session signals; other signals come from recorded shopper sessions. Completed-action totals cover store history.")
    left, right = st.columns([1.3, 1])
    with left, st.container(border=True):
        st.markdown("#### Shopper activity")
        st.caption("Recorded product-request sessions by hour · selected period")
        if board["timeline"]:
            chart = alt.Chart(alt.Data(values=board["timeline"])).mark_area(
                line={"color": "#0a5c44", "strokeWidth": 2.5}, color=alt.Gradient(
                    gradient="linear", stops=[alt.GradientStop(color="#77c9ac", offset=0),
                    alt.GradientStop(color="#f0faf6", offset=1)], x1=0, x2=0, y1=0, y2=1)
            ).encode(x=alt.X("Hour:T", title=None), y=alt.Y("Sessions:Q", title="Sessions", axis=alt.Axis(tickMinStep=1)),
                     tooltip=[alt.Tooltip("Hour:T"), alt.Tooltip("Sessions:Q")]).properties(height=210)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Shopper sessions will appear here as customers use ARIA.")
    with right, st.container(border=True):
        st.markdown("#### What shoppers experienced")
        st.caption("Explicit intent outcomes · each product / session counted once")
        labels = {"fulfilled": "Original fulfilled", "satisfied": "Alternative accepted", "compromise": "Temporary compromise", "rejected": "Alternative rejected", "abandoned": "Abandoned", "unknown": "Needs clarification"}
        rows = [{"Outcome": label, "Sessions": sum(i["counts"][key] for i in board["insights"])} for key, label in labels.items()]
        if any(r["Sessions"] for r in rows):
            chart = alt.Chart(alt.Data(values=rows)).mark_bar(cornerRadiusEnd=5, size=18).encode(
                y=alt.Y("Outcome:N", title=None, sort=list(labels.values())),
                x=alt.X("Sessions:Q", title=None, axis=alt.Axis(tickMinStep=1)),
                color=alt.Color("Outcome:N", scale=alt.Scale(domain=list(labels.values()), range=["#0a5c44", "#49a78a", "#c8891a", "#e07666", "#b45349", "#94a3b8"]), legend=None),
                tooltip=["Outcome:N", "Sessions:Q"]).properties(height=210)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No product intent outcomes recorded in this period.")
    with st.container(border=True):
        st.markdown("#### Where attention matters")
        st.caption("Modeled AED exposure, not measured loss or recovered revenue. Stockout and perishable estimates are separate scenarios.")
        rows = [{"Product": p["product_name"], "AED exposure": p["revenue_at_risk_aed"], "Type": kind}
                for kind, products in [("Stockout", board["patterns"]), ("Perishable", board["alerts"])] for p in products]
        if rows:
            chart = alt.Chart(alt.Data(values=rows)).mark_bar(cornerRadiusEnd=4).encode(
                y=alt.Y("Product:N", sort="-x", title=None, axis=alt.Axis(labelLimit=250)),
                x=alt.X("AED exposure:Q", title="Modeled exposure (AED)"),
                color=alt.Color("Type:N", scale=alt.Scale(domain=["Stockout", "Perishable"], range=["#d46a5f", "#c8891a"]), legend=alt.Legend(orient="top")),
                tooltip=["Product:N", "Type:N", alt.Tooltip("AED exposure:Q", format=",.2f")]).properties(height=max(110, min(360, len(rows)*34)))
            st.altair_chart(chart, use_container_width=True)
        else:
            st.success("No active stockout or perishable exposure to review.")
