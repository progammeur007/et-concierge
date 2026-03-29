import streamlit as st
import os
from dotenv import load_dotenv
from controller import ETVoiceController
from stt_layer import listen_to_user
from tts_layer import speak_to_user

# ─────────────────────────────────────────────
# Config & Load
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Priya — ET AI Concierge",
    layout="wide",
    initial_sidebar_state="collapsed",
)
load_dotenv()

# ─────────────────────────────────────────────
# Pre-defined Opening Greeting (same every time)
# ─────────────────────────────────────────────
PRIYA_GREETING = (
    "Namaste! I'm Priya, your personal Economic Times concierge. "
    "ET offers a lot more than just news — from ET Prime's 4,000-plus stock research reports "
    "and the ET Markets live trading app, to fixed-income investments via ET Money Earn, "
    "leadership masterclasses, and live business summits. "
    "I'm here to help you find exactly what fits your goals. "
    "So tell me — are you an investor, a trader, a business leader, or something else entirely?"
)

# ─────────────────────────────────────────────
# Global CSS — editorial dark-gold theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: #0b0c0e !important;
    color: #e8e0d0 !important;
    font-family: 'DM Sans', sans-serif;
}

#MainMenu, footer, header, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"],
[data-testid="stSidebar"] { display: none !important; }

[data-testid="stAppViewContainer"] > .main > .block-container {
    max-width: 1280px;
    padding: 0 2rem 2rem;
    margin: 0 auto;
}

/* ── Header ── */
.et-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.4rem 0 1rem;
    border-bottom: 1px solid rgba(200,160,60,0.2);
    margin-bottom: 1.8rem;
}
.et-logo {
    font-family: 'DM Serif Display', serif;
    font-size: 1.05rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #c8a03c;
}
.et-logo span { color: #e8e0d0; }
.et-badge {
    background: rgba(200,160,60,0.12);
    border: 1px solid rgba(200,160,60,0.35);
    border-radius: 20px;
    padding: 0.25rem 0.9rem;
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #c8a03c;
}

/* ── Section labels ── */
.section-label {
    font-size: 0.68rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: rgba(200,160,60,0.65);
    margin-bottom: 0.8rem;
    font-weight: 500;
}

/* ── Priya card ── */
.priya-card {
    display: flex;
    align-items: center;
    gap: 1rem;
    background: linear-gradient(135deg, rgba(200,160,60,0.08) 0%, rgba(11,12,14,0) 60%);
    border: 1px solid rgba(200,160,60,0.18);
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1.2rem;
}
.avatar-ring {
    width: 54px; height: 54px;
    border-radius: 50%;
    background: linear-gradient(135deg, #c8a03c, #7a5c10);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.45rem;
    flex-shrink: 0;
    box-shadow: 0 0 0 3px rgba(200,160,60,0.18);
}
.priya-name {
    font-family: 'DM Serif Display', serif;
    font-size: 1.2rem;
    color: #e8e0d0;
    line-height: 1;
    margin-bottom: 0.25rem;
}
.priya-sub { font-size: 0.75rem; color: rgba(232,224,208,0.45); letter-spacing: 0.04em; }

/* ── Status pills ── */
.status-row { display: flex; gap: 0.45rem; margin-bottom: 1.1rem; flex-wrap: wrap; }
.pill { border-radius: 20px; padding: 0.2rem 0.7rem; font-size: 0.68rem; letter-spacing: 0.05em; font-weight: 500; }
.pill-green  { background: rgba(56,180,100,0.12); border: 1px solid rgba(56,180,100,0.3); color: #56c97a; }
.pill-blue   { background: rgba(80,140,240,0.12); border: 1px solid rgba(80,140,240,0.3); color: #7aadf5; }
.pill-gold   { background: rgba(200,160,60,0.12); border: 1px solid rgba(200,160,60,0.3); color: #c8a03c; }

/* ── Buttons ── */
.stButton > button {
    width: 100% !important;
    background: linear-gradient(135deg, #c8a03c 0%, #a07828 100%) !important;
    color: #0b0c0e !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.85rem 1rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    box-shadow: 0 4px 18px rgba(200,160,60,0.22) !important;
    transition: opacity 0.2s, transform 0.15s !important;
}
.stButton > button:hover { opacity: 0.87 !important; transform: translateY(-1px) !important; }
.stButton > button:active { transform: translateY(0) !important; }

.reset-btn > div > button {
    background: transparent !important;
    border: 1px solid rgba(200,160,60,0.25) !important;
    color: rgba(200,160,60,0.6) !important;
    box-shadow: none !important;
    font-size: 0.73rem !important;
    padding: 0.45rem 0.8rem !important;
}

/* ── Text input ── */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(200,160,60,0.2) !important;
    border-radius: 10px !important;
    color: #e8e0d0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.87rem !important;
    padding: 0.65rem 1rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(200,160,60,0.5) !important;
    box-shadow: 0 0 0 3px rgba(200,160,60,0.07) !important;
}
.stTextInput > label {
    color: rgba(232,224,208,0.45) !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}

/* ── Divider ── */
hr { border: none; border-top: 1px solid rgba(255,255,255,0.07) !important; margin: 1rem 0 !important; }

/* ── Chat bubbles ── */
.chat-scroll {
    max-height: 480px;
    overflow-y: auto;
    padding-right: 0.3rem;
    scrollbar-width: thin;
    scrollbar-color: rgba(200,160,60,0.18) transparent;
}
.chat-wrapper { display: flex; flex-direction: column; gap: 1rem; }

.bubble-label { font-size: 0.63rem; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.3rem; font-weight: 500; }
.bubble-label-user { color: rgba(200,160,60,0.55); text-align: right; }
.bubble-label-bot  { color: rgba(255,255,255,0.28); }

.bubble-user {
    align-self: flex-end;
    background: rgba(200,160,60,0.1);
    border: 1px solid rgba(200,160,60,0.22);
    border-radius: 16px 16px 4px 16px;
    padding: 0.8rem 1.05rem;
    max-width: 82%;
    font-size: 0.88rem;
    color: #e8e0d0;
    line-height: 1.55;
}
.bubble-bot {
    align-self: flex-start;
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px 16px 16px 4px;
    padding: 0.8rem 1.05rem;
    max-width: 88%;
    font-size: 0.88rem;
    color: #d8d0c0;
    line-height: 1.6;
}
.bubble-greeting {
    align-self: flex-start;
    background: rgba(200,160,60,0.07);
    border: 1px solid rgba(200,160,60,0.18);
    border-left: 3px solid #c8a03c;
    border-radius: 0 16px 16px 4px;
    padding: 1rem 1.15rem;
    max-width: 95%;
    font-size: 0.88rem;
    color: #e0d4b4;
    line-height: 1.65;
    font-style: italic;
}

/* ── Trace panel ── */
.trace-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.65rem;
    font-size: 0.78rem;
    color: rgba(232,224,208,0.55);
    line-height: 1.6;
}
.trace-card strong { color: #c8a03c; font-weight: 500; }
.trace-step { display: flex; align-items: flex-start; gap: 0.55rem; padding: 0.35rem 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
.trace-step:last-child { border-bottom: none; }
.trace-dot { width: 6px; height: 6px; border-radius: 50%; background: #c8a03c; margin-top: 6px; flex-shrink: 0; opacity: 0.65; }

/* ── Services grid ── */
.services-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.45rem; margin-bottom: 1rem; }
.svc-chip {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px;
    padding: 0.5rem 0.75rem;
    font-size: 0.72rem;
    color: rgba(232,224,208,0.5);
    line-height: 1.4;
}
.svc-chip strong { color: rgba(200,160,60,0.82); display: block; font-size: 0.74rem; margin-bottom: 0.08rem; }

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 2.5rem 1rem;
    color: rgba(232,224,208,0.2);
    font-size: 0.83rem;
    letter-spacing: 0.04em;
    line-height: 1.8;
}
.empty-icon { font-size: 1.8rem; margin-bottom: 0.6rem; opacity: 0.35; display: block; }

.stSpinner > div { color: #c8a03c !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Session State Init
# ─────────────────────────────────────────────
if "agent" not in st.session_state:
    st.session_state.agent = ETVoiceController("data.json")
    st.session_state.chat_history = []
    st.session_state.greeted = False
    st.session_state.last_trace = []


def do_greeting():
    speak_to_user(PRIYA_GREETING)
    st.session_state.chat_history.append({"role": "greeting", "text": PRIYA_GREETING})
    st.session_state.greeted = True
    st.session_state.last_trace = [
        "Session initialized",
        "Knowledge graph loaded from data.json",
        "Pre-defined greeting delivered via TTS",
        "Awaiting user voice input...",
    ]


def handle_user_input(user_text: str):
    st.session_state.last_trace = [
        f'STT captured: "{user_text[:55]}{"..." if len(user_text)>55 else ""}"',
        "Local keyword persona matching...",
        "Graph 2-hop traversal: products + cross-sells + FAQs",
        "LLM response generated",
        "TTS sanitization applied",
        "Response delivered via speaker",
    ]
    response = st.session_state.agent.process_request(user_text)
    st.session_state.chat_history.append({"role": "user", "text": user_text})
    st.session_state.chat_history.append({"role": "bot", "text": response})
    speak_to_user(response)


# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.markdown("""
<div class="et-header">
    <div class="et-logo">Economic <span>Times</span></div>
    <div style="display:flex;align-items:center;gap:0.55rem;">
        <div class="et-badge">AI Concierge</div>
        <div class="et-badge" style="color:rgba(232,224,208,0.35);border-color:rgba(255,255,255,0.09);">v2.0</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Layout
# ─────────────────────────────────────────────
left, right = st.columns([1, 1.6], gap="large")

# ══════════════════════════════
# LEFT — Controls
# ══════════════════════════════
with left:
    st.markdown("""
    <div class="priya-card">
        <div class="avatar-ring">🎙️</div>
        <div>
            <div class="priya-name">Priya</div>
            <div class="priya-sub">ET Voice Concierge · GraphRAG · Gemini Flash</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="status-row">
        <span class="pill pill-green">● Online</span>
        <span class="pill pill-blue">2-Hop Graph</span>
        <span class="pill pill-gold">Gemini Flash</span>
    </div>
    """, unsafe_allow_html=True)

    # Primary CTA — changes after greeting
    if not st.session_state.greeted:
        if st.button("▶  Start Conversation"):
            with st.spinner("Priya is greeting you..."):
                do_greeting()
            st.rerun()
    else:
        if st.button("🎤  Speak to Priya"):
            with st.spinner("Listening..."):
                user_text = listen_to_user()
            if user_text:
                with st.spinner("Thinking..."):
                    handle_user_input(user_text)
                st.rerun()
            else:
                st.error("Mic not detected. Use text fallback below.")

    st.markdown("<hr/>", unsafe_allow_html=True)

    st.markdown('<div class="section-label">Text Fallback</div>', unsafe_allow_html=True)
    t_input = st.text_input("", placeholder="Type your question...", label_visibility="collapsed")
    if st.button("Send →"):
        if t_input.strip():
            if not st.session_state.greeted:
                do_greeting()
            with st.spinner("Thinking..."):
                handle_user_input(t_input.strip())
            st.rerun()

    st.markdown("<hr/>", unsafe_allow_html=True)

    st.markdown('<div class="section-label">ET Services</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="services-grid">
        <div class="svc-chip"><strong>ET Prime Gold</strong>4,000+ reports · ₹999/yr</div>
        <div class="svc-chip"><strong>ET Markets App</strong>Live NSE/BSE · AI charts</div>
        <div class="svc-chip"><strong>ET Money Earn</strong>Fixed income · 9% p.a.</div>
        <div class="svc-chip"><strong>GrandMasters</strong>120+ lessons · ₹4,999/yr</div>
        <div class="svc-chip"><strong>Masterclasses</strong>Leadership · AI · HR · Sales</div>
        <div class="svc-chip"><strong>Axis Bank Card</strong>Lounge + ET Prime offer</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Session</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
        if st.button("↺  Reset Conversation"):
            st.session_state.agent.reset_session()
            st.session_state.chat_history = []
            st.session_state.greeted = False
            st.session_state.last_trace = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════
# RIGHT — Chat + Trace
# ══════════════════════════════
with right:
    chat_col, trace_col = st.columns([1.65, 1], gap="medium")

    # ── Chat history ──
    with chat_col:
        st.markdown('<div class="section-label">Conversation</div>', unsafe_allow_html=True)

        if not st.session_state.chat_history:
            st.markdown("""
            <div class="empty-state">
                <span class="empty-icon">🎙️</span>
                Press <strong style="color:rgba(200,160,60,0.65)">Start Conversation</strong>
                to let Priya introduce herself and<br/>explain all that ET has to offer.
            </div>
            """, unsafe_allow_html=True)
        else:
            html = '<div class="chat-scroll"><div class="chat-wrapper">'
            for msg in st.session_state.chat_history:
                if msg["role"] == "greeting":
                    html += f"""
                    <div>
                        <div class="bubble-label bubble-label-bot">Priya · Opening</div>
                        <div class="bubble-greeting">{msg['text']}</div>
                    </div>"""
                elif msg["role"] == "user":
                    html += f"""
                    <div style="display:flex;flex-direction:column;align-items:flex-end;">
                        <div class="bubble-label bubble-label-user">You</div>
                        <div class="bubble-user">{msg['text']}</div>
                    </div>"""
                else:
                    html += f"""
                    <div>
                        <div class="bubble-label bubble-label-bot">Priya</div>
                        <div class="bubble-bot">{msg['text']}</div>
                    </div>"""
            html += '</div></div>'
            st.markdown(html, unsafe_allow_html=True)

    # ── Agent trace ──
    with trace_col:
        st.markdown('<div class="section-label">Agent Trace</div>', unsafe_allow_html=True)

        if not st.session_state.last_trace:
            st.markdown("""
            <div class="trace-card" style="color:rgba(232,224,208,0.18);font-style:italic;font-size:0.76rem;">
                Graph traversal steps will appear here after each turn.
            </div>
            """, unsafe_allow_html=True)
        else:
            steps = '<div class="trace-card">'
            for step in st.session_state.last_trace:
                steps += f'<div class="trace-step"><div class="trace-dot"></div><div>{step}</div></div>'
            steps += '</div>'
            st.markdown(steps, unsafe_allow_html=True)

        if st.session_state.chat_history:
            user_turns = sum(1 for m in st.session_state.chat_history if m["role"] == "user")
            st.markdown(f"""
            <div class="trace-card">
                <strong>Session</strong><br/>
                Turns: {user_turns} &nbsp;·&nbsp; Messages: {len(st.session_state.chat_history)}
            </div>
            """, unsafe_allow_html=True)