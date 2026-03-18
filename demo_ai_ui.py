import streamlit as st
import time
import html
import re
from datetime import datetime
from src.rag_agent import RAGVisaAssistant
from src.build_knowledge_base import ensure_kb_exists

# GSU Brand Colors
GSU_BLUE = "#0039A6"
GSU_DARK = "#1A1A2E"
GSU_GRAY_100 = "#F5F5F5"
GSU_GRAY_200 = "#E8E8E8"
GSU_GRAY_500 = "#6B7280"
GSU_GRAY_700 = "#374151"
GSU_ACCENT = "#55C1E5"

st.set_page_config(
    page_title="Immi - GSU Visa Assistant",
    page_icon="assets/immi_icon.png" if False else None,
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400&display=swap');

    html, body, [class*="css"] {{
        font-family: 'IBM Plex Sans', sans-serif;
    }}

    .stApp {{
        background-color: #FAFAFA;
    }}

    /* ---- SIDEBAR ---- */
    [data-testid="stSidebar"] {{
        background-color: #FFFFFF;
        border-right: 1px solid {GSU_GRAY_200};
    }}

    [data-testid="stSidebar"] .block-container {{
        padding-top: 2rem;
    }}

    /* ---- HEADER ---- */
    .immi-header {{
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 1.5rem 0 1.25rem 0;
        border-bottom: 1px solid {GSU_GRAY_200};
        margin-bottom: 1.5rem;
    }}

    .immi-logo {{
        width: 36px;
        height: 36px;
        background: {GSU_BLUE};
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 18px;
        font-weight: 600;
        flex-shrink: 0;
    }}

    .immi-brand {{
        display: flex;
        flex-direction: column;
        gap: 1px;
    }}

    .immi-name {{
        font-size: 1.1rem;
        font-weight: 600;
        color: {GSU_DARK};
        letter-spacing: -0.2px;
        margin: 0;
        line-height: 1.2;
    }}

    .immi-tagline {{
        font-size: 0.78rem;
        color: {GSU_GRAY_500};
        margin: 0;
        font-weight: 400;
    }}

    /* ---- SIDEBAR NAV ---- */
    .sidebar-section-label {{
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: {GSU_GRAY_500};
        padding: 0 0 0.5rem 0;
        margin: 1.25rem 0 0.5rem 0;
        border-bottom: 1px solid {GSU_GRAY_200};
    }}

    /* ---- SUGGESTION & FEEDBACK BUTTONS ---- */
    .stButton > button {{
        background: #FFFFFF !important;
        color: {GSU_GRAY_700} !important;
        border: 1px solid {GSU_GRAY_200} !important;
        border-radius: 6px !important;
        padding: 0.5rem 0.75rem !important;
        font-size: 0.82rem !important;
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-weight: 400 !important;
        text-align: center !important;
        transition: all 0.15s ease !important;
        width: 100% !important;
        justify-content: center !important;
        letter-spacing: 0 !important;
    }}

    .stButton > button:hover {{
        background: {GSU_BLUE}1A !important; /* light variant of GSU blue */
        border-color: {GSU_BLUE} !important;
        color: {GSU_BLUE} !important;
        transform: none !important;
        box-shadow: none !important;
    }}

    /* Feedback Yes/No buttons inline, similar to IBM style */
    [data-testid="stHorizontalBlock"] .stButton > button {{
        width: auto !important;
        min-width: 90px !important;
        padding: 0.35rem 1.3rem !important;
        border-radius: 999px !important;
        font-weight: 500 !important;
    }}

    /* ---- MAIN CONTENT ---- */
    .main-content {{
        max-width: 760px;
        margin: 0 auto;
        padding: 0 1rem;
    }}

    .chat-header {{
        padding: 1.75rem 0 1.25rem 0;
        border-bottom: 1px solid {GSU_GRAY_200};
        margin-bottom: 1.75rem;
    }}

    .chat-title {{
        font-size: 1.05rem;
        font-weight: 500;
        color: {GSU_DARK};
        margin: 0;
    }}

    /* ---- MESSAGES ---- */
    .msg-wrapper {{
        display: flex;
        gap: 12px;
        margin-bottom: 1.5rem;
        align-items: flex-start;
    }}

    .msg-wrapper.user {{
        flex-direction: row-reverse;
    }}

    .msg-avatar {{
        width: 28px;
        height: 28px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: 600;
        flex-shrink: 0;
        margin-top: 2px;
    }}

    .msg-avatar.bot {{
        background: {GSU_BLUE};
        color: white;
    }}

    .msg-avatar.user {{
        background: {GSU_GRAY_200};
        color: {GSU_GRAY_700};
    }}

    .msg-content {{
        flex: 1;
        max-width: 88%;
    }}

    .msg-sender {{
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: {GSU_GRAY_500};
        margin-bottom: 4px;
    }}

    .msg-bubble {{
        padding: 0.9rem 1.1rem;
        border-radius: 8px;
        font-size: 0.92rem;
        line-height: 1.65;
        color: {GSU_GRAY_700};
    }}

    .msg-bubble.bot {{
        background: #FFFFFF !important;
        border: 1px solid {GSU_GRAY_200} !important;
        color: {GSU_GRAY_700} !important;
    }}

    .msg-bubble.user {{
        background: {GSU_BLUE} !important;
        color: #FFFFFF !important;
        border: none !important;
    }}

    /* ---- REFERENCES ---- */
    .references {{
        margin-top: 10px;
        padding: 0;
    }}

    .references-label {{
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: {GSU_GRAY_500};
        margin-bottom: 6px;
    }}

    .ref-item {{
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 7px 10px;
        background: {GSU_GRAY_100};
        border: 1px solid {GSU_GRAY_200};
        border-radius: 5px;
        margin-bottom: 4px;
        text-decoration: none;
    }}

    .ref-item-dot {{
        width: 6px;
        height: 6px;
        background: {GSU_ACCENT};
        border-radius: 50%;
        flex-shrink: 0;
    }}

    .ref-item-url {{
        font-size: 0.78rem;
        color: {GSU_BLUE};
        font-family: 'IBM Plex Mono', monospace;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    /* ---- WELCOME ---- */
    .welcome-block {{
        padding: 2rem;
        background: #FFFFFF;
        border: 1px solid {GSU_GRAY_200};
        border-radius: 10px;
        margin-bottom: 2rem;
    }}

    .welcome-title {{
        font-size: 1rem;
        font-weight: 600;
        color: {GSU_DARK};
        margin: 0 0 0.5rem 0;
    }}

    .welcome-body {{
        font-size: 0.88rem;
        color: {GSU_GRAY_500};
        line-height: 1.65;
        margin: 0 0 1rem 0;
    }}

    .disclaimer-bar {{
        display: flex;
        align-items: flex-start;
        gap: 8px;
        padding: 0.75rem 1rem;
        background: #EEF4FF;
        border-left: 3px solid {GSU_BLUE};
        border-radius: 4px;
        font-size: 0.82rem;
        color: #1A3A80;
        line-height: 1.55;
    }}

    /* ---- SESSION STATUS ---- */
    .session-pill {{
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 500;
    }}

    .session-pill.active {{
        background: #E8F5E9;
        color: #2E7D32;
    }}

    .session-pill.idle {{
        background: #FFF3E0;
        color: #E65100;
    }}

    .session-pill.expired {{
        background: #FFEBEE;
        color: #C62828;
    }}

    .session-dot {{
        width: 6px;
        height: 6px;
        border-radius: 50%;
    }}

    .session-dot.active {{ background: #4CAF50; }}
    .session-dot.idle {{ background: #FF9800; }}
    .session-dot.expired {{ background: #F44336; }}

    /* ---- CHAT INPUT ---- */
    /* Remove outer wrapper styling entirely (no "outlier" bar) */
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] > div > div {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
        border-radius: 0 !important;
    }}

    .stChatInput textarea {{
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 0.9rem !important;
        border: 1px solid {GSU_BLUE} !important;
        border-radius: 10px !important;
        background: #FFFFFF !important;
        padding: 0.72rem 0.9rem !important;
        transition: border-color 140ms ease, box-shadow 140ms ease !important;
    }}

    [data-testid="stChatInput"] textarea:focus {{
        border-color: {GSU_BLUE} !important;
        box-shadow: 0 0 0 3px rgba(0, 57, 166, 0.16) !important;
        background: #FFFFFF !important;
    }}

    /* ---- SIDEBAR INFO ---- */
    .info-panel {{
        background: {GSU_GRAY_100};
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1rem;
    }}

    .info-panel-title {{
        font-size: 0.78rem;
        font-weight: 600;
        color: {GSU_DARK};
        margin: 0 0 0.6rem 0;
        letter-spacing: 0.02em;
    }}

    .info-panel-row {{
        display: flex;
        gap: 8px;
        margin-bottom: 0.45rem;
        align-items: flex-start;
    }}

    .info-panel-label {{
        font-size: 0.78rem;
        color: {GSU_GRAY_500};
        flex-shrink: 0;
        min-width: 60px;
    }}

    .info-panel-value {{
        font-size: 0.78rem;
        color: {GSU_GRAY_700};
        font-weight: 500;
    }}

    /* Streamlit internal overrides */
    .block-container {{
        padding-top: 1rem !important;
    }}

    div[data-testid="stChatMessage"] {{
        background: transparent !important;
    }}

    .stSpinner > div {{
        border-top-color: {GSU_BLUE} !important;
    }}

    /* ---- CHAT INPUT TEXT FIX ---- */
    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInput"] input,
    .stChatInput textarea,
    .stChatInput input {{
        color: #1A1A2E !important;
        background: #FFFFFF !important;
        caret-color: #1A1A2E !important;
        -webkit-text-fill-color: #1A1A2E !important;
    }}
    [data-testid="stChatInput"] textarea::placeholder,
    .stChatInput textarea::placeholder {{
        color: #6B7280 !important;
        opacity: 1 !important;
        -webkit-text-fill-color: #6B7280 !important;
    }}

    .feedback-prompt {{
        text-align: center;
        font-size: 0.9rem;
        font-weight: 600;
        color: {GSU_DARK};
        margin: 0.25rem 0 0.75rem 0;
    }}

    /* Hide streamlit default elements */
    #MainMenu, footer, header {{
        visibility: hidden;
    }}
    </style>
""", unsafe_allow_html=True)


# ---- SESSION STATE ----
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'last_activity' not in st.session_state:
    st.session_state.last_activity = time.time()

if 'session_expired' not in st.session_state:
    st.session_state.session_expired = False

if 'pending_question' not in st.session_state:
    st.session_state.pending_question = None

# Feedback state
if 'awaiting_feedback' not in st.session_state:
    st.session_state.awaiting_feedback = False

if 'show_feedback_form' not in st.session_state:
    st.session_state.show_feedback_form = False

if 'greeting_shown' not in st.session_state:
    st.session_state.greeting_shown = False

if 'assistant' not in st.session_state:
    with st.spinner("Loading Immi..."):
        ensure_kb_exists(
            json_file="data/raw_docs/isss_content.json",
            persist_directory="data/visa_kb",
        )
        st.session_state.assistant = RAGVisaAssistant()

# ---- TIMEOUT LOGIC ----
SESSION_TIMEOUT = 600  # 10 minutes

def check_session():
    elapsed = time.time() - st.session_state.last_activity
    if elapsed >= SESSION_TIMEOUT and len(st.session_state.messages) > 0:
        st.session_state.session_expired = True
    return elapsed

elapsed = check_session()

def get_session_status():
    if st.session_state.session_expired:
        return "expired", "Session ended"
    elif elapsed > 300:
        return "idle", "Idle"
    else:
        return "active", "Active"


# ---- SIDEBAR ----
with st.sidebar:
    # Immi branding in sidebar
    st.markdown(f"""
        <div class="immi-header">
            <div class="immi-logo">I</div>
            <div class="immi-brand">
                <p class="immi-name">Immi</p>
                <p class="immi-tagline">ISSS Assistant</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    status_key, status_label = get_session_status()
    st.markdown(f"""
        <div class="session-pill {status_key}">
            <div class="session-dot {status_key}"></div>
            {status_label}
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-label">Suggested Questions</div>', unsafe_allow_html=True)

    example_questions = [
        "Can I work off-campus on F-1?",
        "What is CPT and how do I apply?",
        "How do I apply for OPT?",
        "What documents do I need to travel?",
        "Can I drop below full-time enrollment?",
        "How long does OPT last?",
    ]

    for question in example_questions:
        if st.button(question, key=f"q_{question}", use_container_width=True):
            if not st.session_state.session_expired:
                st.session_state.pending_question = question
                st.session_state.last_activity = time.time()
                st.rerun()

    st.markdown('<div class="sidebar-section-label">ISSS Contact</div>', unsafe_allow_html=True)

    st.markdown(f"""
        <div class="info-panel">
            <div class="info-panel-row">
                <span class="info-panel-label">Email</span>
                <span class="info-panel-value">isss@gsu.edu</span>
            </div>
            <div class="info-panel-row">
                <span class="info-panel-label">Phone</span>
                <span class="info-panel-value">(404) 413-2070</span>
            </div>
            <div class="info-panel-row">
                <span class="info-panel-label">Hours</span>
                <span class="info-panel-value">Mon–Fri, 8:30 AM–5:15 PM</span>
            </div>
            <div class="info-panel-row">
                <span class="info-panel-label">Location</span>
                <span class="info-panel-value">
Student Success Center,
Suite 100,
25-27 Auburn Ave NE,
Atlanta, GA 30303</span>
            </div>
        </div>
    """, unsafe_allow_html=True)


# ---- MAIN AREA ----
col_main = st.columns([1])[0]

with col_main:
    st.markdown('<div class="main-content">', unsafe_allow_html=True)

    st.markdown(f"""
        <div class="chat-header">
            <p class="chat-title">Immi — ISSS Assistant</p>
        </div>
    """, unsafe_allow_html=True)

    # ---- WELCOME STATE ----
    if len(st.session_state.messages) == 0 and not st.session_state.session_expired:
        st.markdown(f"""
            <div class="welcome-block">
                <p class="welcome-title">Welcome to Immi</p>
                <p class="welcome-body">
                    Ask any question about your F-1 visa status, CPT, OPT, travel, or enrollment requirements.
                    Every answer is sourced from official ISSS and USCIS documentation.
                </p>
                <div class="disclaimer-bar">
                    Immi provides informational guidance only. For official immigration advice,
                    always consult an ISSS advisor.
                </div>
            </div>
        """, unsafe_allow_html=True)

    # ---- SESSION EXPIRED ----
    if st.session_state.session_expired:
        st.markdown(f"""
            <div style="padding: 1.5rem; background: #FFF8F0; border: 1px solid #FFE0B2;
                        border-radius: 8px; margin-bottom: 1.5rem;">
                <p style="font-weight: 600; color: #E65100; margin: 0 0 0.3rem 0; font-size: 0.9rem;">
                    Session ended
                </p>
                <p style="color: #BF360C; font-size: 0.85rem; margin: 0;">
                    Your session has been closed after 10 minutes of inactivity.
                    Refresh the page to start a new conversation.
                </p>
            </div>
        """, unsafe_allow_html=True)

    # ---- PROCESS PENDING QUESTION FROM SIDEBAR ----
    if st.session_state.pending_question and not st.session_state.session_expired:
        pending = st.session_state.pending_question
        st.session_state.pending_question = None
        st.session_state.messages.append({
            "role": "user",
            "content": pending,
            "timestamp": time.time(),
        })
        with st.spinner("Searching official sources..."):
            result = st.session_state.assistant.answer_question(pending)
        st.session_state.messages.append({
            "role": "assistant",
            "content": result["answer"],
            "sources": result.get("sources", []),
            "timestamp": time.time(),
        })
        st.session_state.awaiting_feedback = True
        st.session_state.show_feedback_form = False
        st.rerun()

    # ---- CHAT HISTORY ----
    for message in st.session_state.messages:
        ts = message.get("timestamp")
        time_label = ""
        if ts:
            time_dt = datetime.fromtimestamp(ts)
            time_label = time_dt.strftime("%I:%M %p").lstrip("0")

        if message["role"] == "user":
            safe_user = html.escape(message["content"]).replace("\n", "<br>")
            st.markdown(f"""
                <div class="msg-wrapper user">
                    <div class="msg-avatar user">You</div>
                    <div class="msg-content" style="text-align: right;">
                        <div class="msg-sender" style="text-align: right;">You{f" · {time_label}" if time_label else ""}</div>
                        <div class="msg-bubble user">{safe_user}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            raw_bot = message["content"]
            if not isinstance(raw_bot, str):
                continue

            # Remove stray HTML-only lines like bare </div> that can appear as black code blocks.
            lines = raw_bot.splitlines()
            filtered_lines = [
                ln for ln in lines
                if ln.strip().lower() not in {"</div>", "<div>", "<div/>", "</p>", "<p>"}
            ]
            cleaned_bot = "\n".join(filtered_lines).strip()
            if not cleaned_bot:
                continue

            safe_bot = html.escape(cleaned_bot).replace("\n", "<br>")

            st.markdown(f"""
                <div class="msg-wrapper">
                    <div class="msg-avatar bot">IM</div>
                    <div class="msg-content">
                        <div class="msg-sender">Immi{f" · {time_label}" if time_label else ""}</div>
                        <div class="msg-bubble bot">{safe_bot}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # References rendered in a simple, clean box below the message (no nested HTML classes to avoid wrappers).
            if message.get("sources"):
                links_html = "".join(
                    f"<li><a href='{src}' target='_blank'>{html.escape(src)}</a></li>"
                    for src in message["sources"]
                )
                refs_html = f"""
                    <div style="
                        margin-top: 0.6rem;
                        padding: 0.75rem 0.9rem;
                        border: 1px solid #E5E7EB;
                        border-radius: 6px;
                        background: #F9FAFB;
                    ">
                        <div style="
                            font-size: 0.72rem;
                            font-weight: 600;
                            letter-spacing: 0.06em;
                            text-transform: uppercase;
                            color: #6B7280;
                            margin-bottom: 0.35rem;
                        ">
                            References
                        </div>
                        <ul style="margin: 0; padding-left: 1.1rem; font-size: 0.82rem;">
                            {links_html}
                        </ul>
                    </div>
                """
                st.markdown(refs_html, unsafe_allow_html=True)

    # ---- FEEDBACK ON LAST ANSWER ----
    if not st.session_state.session_expired and st.session_state.messages:
        last_msg = st.session_state.messages[-1]
        if last_msg["role"] == "assistant" and st.session_state.awaiting_feedback:
            st.markdown("<hr style='margin: 1.5rem 0 0.75rem 0;' />", unsafe_allow_html=True)
            st.markdown('<div class="feedback-prompt">Did I answer your question?</div>', unsafe_allow_html=True)
            fb_col0, fb_col1, fb_col_gap, fb_col2, fb_col3 = st.columns([5, 1.2, 0.6, 1.2, 5])
            with fb_col1:
                if st.button("Yes", key="fb_yes", type="primary"):
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "Thank you for confirming. You can ask another question at any time.",
                        "sources": [],
                        "timestamp": time.time(),
                    })
                    st.session_state.awaiting_feedback = False
                    st.session_state.show_feedback_form = False
                    st.rerun()
            with fb_col2:
                if st.button("No", key="fb_no", type="secondary"):
                    st.session_state.awaiting_feedback = False
                    st.session_state.show_feedback_form = True
                    st.rerun()
            with fb_col0:
                st.write("")
            with fb_col3:
                st.write("")

    # ---- DETAILED FEEDBACK FORM (when answer was not helpful) ----
    if not st.session_state.session_expired and st.session_state.show_feedback_form:
        st.markdown("---")
        st.markdown("#### Help us improve this answer")
        with st.form(key="feedback_form"):
            issue_type = st.selectbox(
                "What was the main issue?",
                [
                    "Incorrect response",
                    "Partial answer",
                    "Wrong or unclear source",
                    "Formatting or clarity issue",
                    "Other",
                ],
            )
            details = st.text_area(
                "Please describe what was wrong or missing.",
                height=120,
                placeholder="For example: The guidance about CPT hours per week does not match the current ISSS policy...",
            )
            submitted = st.form_submit_button("Submit feedback")

            if submitted:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": (
                        "Sorry that did not fully answer your question. "
                        "Please clarify or restate your question below so I can try again. "
                        "For case-specific guidance, you should also contact an ISSS advisor."
                    ),
                    "sources": [],
                    "timestamp": time.time(),
                })
                st.session_state.show_feedback_form = False
                st.rerun()

    def _looks_like_greeting(text: str) -> bool:
        t = text.strip().lower()
        if not t:
            return False
        if len(t) <= 40 and re.fullmatch(r"(hi|hello|hey|good morning|good afternoon|good evening|hiya|howdy)[!. ]*", t):
            return True
        if len(t) <= 60 and re.match(r"^(hi|hello|hey)\b", t):
            return True
        return False

    def _looks_like_thanks(text: str) -> bool:
        t = text.strip().lower()
        if not t:
            return False
        return any(
            phrase in t
            for phrase in [
                "thank you",
                "thanks",
                "thanks!",
                "thank u",
                "appreciate it",
            ]
        )

    # ---- CHAT INPUT ----
    if not st.session_state.session_expired:
        if prompt := st.chat_input("Ask a question...", key="chat_input"):
            st.session_state.last_activity = time.time()
            before_count = len(st.session_state.messages)

            # Special handling for greetings so Immi does not keep re-introducing itself.
            is_greeting = _looks_like_greeting(prompt)
            is_thanks = _looks_like_thanks(prompt)

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": prompt,
                    "timestamp": time.time(),
                }
            )

            # Short, polite acknowledgement for pure "thanks" messages without triggering feedback.
            if is_thanks and not is_greeting:
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": (
                            "You’re welcome. If you have another ISSS-related question, "
                            "you can type it below."
                        ),
                        "sources": [],
                        "timestamp": time.time(),
                    }
                )
                st.session_state.awaiting_feedback = False
                st.session_state.show_feedback_form = False
                st.rerun()

            if is_greeting and st.session_state.greeting_shown:
                # Short, non-repetitive acknowledgement without another long introduction.
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": (
                            "You can ask me any ISSS-related question whenever you are ready."
                        ),
                        "sources": [],
                        "timestamp": time.time(),
                    }
                )
                st.session_state.awaiting_feedback = False
                st.session_state.show_feedback_form = False
                st.rerun()

            with st.spinner("Searching official sources..."):
                result = st.session_state.assistant.answer_question(prompt)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": result["answer"],
                    "sources": result.get("sources", []),
                    "timestamp": time.time(),
                }
            )

            if is_greeting:
                st.session_state.greeting_shown = True

            # Only ask Yes/No feedback for substantive answers, not for the very first greeting.
            st.session_state.awaiting_feedback = before_count > 0
            st.session_state.show_feedback_form = False
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)