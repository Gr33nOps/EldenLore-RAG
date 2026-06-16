import streamlit as st
from bot import ask
from quiz import get_weighted_chunks, generate_question, calculate_score, get_rank, POINTS_MAP, CATEGORY_CONFIG

st.set_page_config(
    page_title="EldenLore RAG",
    page_icon="⚔",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Character visual config ───────────────────────────────────────────────────
CHARACTER_VISUALS = {
    "Sir Gideon Ofnir, the All-Knowing": {
        "initial": "G",
        "color": "#c9a84c",
        "bg": "#2a1f00",
        "title": "Sir Gideon Ofnir",
        "subtitle": "The All-Knowing",
        "accent": "#c9a84c",
        "rune": "⚔",
    },
    "Ranni the Witch": {
        "initial": "R",
        "color": "#a0b8e0",
        "bg": "#0d1a2e",
        "title": "Ranni the Witch",
        "subtitle": "Lunar Princess",
        "accent": "#a0b8e0",
        "rune": "✦",
    },
    "Melina": {
        "initial": "M",
        "color": "#d4a574",
        "bg": "#2a1500",
        "title": "Melina",
        "subtitle": "Kindling Maiden",
        "accent": "#d4a574",
        "rune": "✦",
    },
    "Fia, Deathbed Companion": {
        "initial": "F",
        "color": "#9b8db0",
        "bg": "#1a0d2e",
        "title": "Fia",
        "subtitle": "Deathbed Companion",
        "accent": "#9b8db0",
        "rune": "✦",
    },
    "Goldmask, the Most Devout": {
        "initial": "G",
        "color": "#e8c870",
        "bg": "#2a2000",
        "title": "Goldmask",
        "subtitle": "The Most Devout",
        "accent": "#e8c870",
        "rune": "◎",
    },
    "Miriel, Pastor of Vows": {
        "initial": "M",
        "color": "#7ab892",
        "bg": "#0a2010",
        "title": "Miriel",
        "subtitle": "Pastor of Vows",
        "accent": "#7ab892",
        "rune": "✦",
    },
    "Enia, the Finger Reader": {
        "initial": "E",
        "color": "#c4a882",
        "bg": "#1a1208",
        "title": "Enia",
        "subtitle": "Finger Reader",
        "accent": "#c4a882",
        "rune": "✦",
    },
    "the Dung Eater": {
        "initial": "D",
        "color": "#8a6060",
        "bg": "#1a0808",
        "title": "Dung Eater",
        "subtitle": "Cursed Revenant",
        "accent": "#8a6060",
        "rune": "✦",
    },
}

DEFAULT_CHAR = CHARACTER_VISUALS["Sir Gideon Ofnir, the All-Knowing"]


def get_char_visual(char_name: str) -> dict:
    for key, val in CHARACTER_VISUALS.items():
        if key in char_name or char_name in key:
            return val
    return DEFAULT_CHAR


# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@400;700&family=Cinzel:wght@400;600;700&family=Crimson+Text:ital,wght@0,400;0,600;1,400;1,600&display=swap');

/* ── Reset & Base ── */
.stApp {
    background-color: #060504;
    background-image:
        radial-gradient(ellipse 80% 40% at 50% 0%, #150f00 0%, transparent 70%),
        radial-gradient(ellipse 60% 30% at 50% 100%, #0a0800 0%, transparent 70%);
    color: #c9a84c;
}
#MainMenu, footer, header { visibility: hidden; }
::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: #060504; }
::-webkit-scrollbar-thumb { background: #c9a84c33; border-radius: 2px; }

/* ── Main title block ── */
.eldenlore-header {
    text-align: center;
    padding: 28px 0 4px 0;
}
.eldenlore-wordmark {
    font-family: 'Cinzel Decorative', serif;
    font-size: 0.8em;
    font-weight: 400;
    letter-spacing: 6px;
    color: #c9a84c55;
    text-transform: uppercase;
    display: block;
    margin-bottom: 2px;
}
.eldenlore-title {
    font-family: 'Cinzel Decorative', serif;
    color: #c9a84c;
    font-size: 2.4em;
    font-weight: 700;
    letter-spacing: 2px;
    text-shadow: 0 0 60px #c9a84c44, 0 2px 4px #000;
    line-height: 1.2;
    display: block;
}
.eldenlore-sub {
    font-family: 'Crimson Text', serif;
    font-style: italic;
    color: #c9a84c66;
    font-size: 1.1em;
    letter-spacing: 1px;
    display: block;
    margin-top: 6px;
}

/* ── Grace divider ── */
.grace-divider {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin: 14px 0;
}
.grace-line {
    flex: 1;
    height: 1px;
    background: linear-gradient(to right, transparent, #c9a84c44, transparent);
}
.grace-diamond {
    width: 7px;
    height: 7px;
    background: #c9a84c;
    transform: rotate(45deg);
    box-shadow: 0 0 10px #c9a84c88;
    flex-shrink: 0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #040302 !important;
    border-right: 1px solid #c9a84c1a !important;
}
[data-testid="stSidebar"] .stMarkdown * {
    font-family: 'Crimson Text', serif;
}
.sidebar-logo {
    font-family: 'Cinzel Decorative', serif;
    font-size: 1.2em;
    font-weight: 700;
    color: #c9a84c;
    text-align: center;
    letter-spacing: 2px;
    padding: 4px 0;
    text-shadow: 0 0 30px #c9a84c55;
}
.sidebar-tagline {
    font-family: 'Crimson Text', serif;
    font-style: italic;
    color: #c9a84c55;
    font-size: 0.95em;
    text-align: center;
    letter-spacing: 0.5px;
}
.rune-sep {
    text-align: center;
    color: #c9a84c33;
    font-size: 1em;
    letter-spacing: 10px;
    margin: 10px 0;
    font-family: serif;
}
.sidebar-section-label {
    font-family: 'Cinzel', serif;
    font-size: 0.72em;
    color: #c9a84c55;
    letter-spacing: 3px;
    text-align: center;
    margin: 12px 0 6px 0;
}
.sidebar-info {
    font-family: 'Crimson Text', serif;
    color: #c9a84c66;
    font-size: 1.0em;
    line-height: 2;
    padding: 0 4px;
}

/* ── Nav radio ── */
div[data-testid="stRadio"] label {
    color: #c9a84c66 !important;
    font-family: 'Cinzel', serif !important;
    font-size: 0.88em !important;
    letter-spacing: 2px;
    transition: color 0.2s;
}
div[data-testid="stRadio"] label:hover,
div[data-testid="stRadio"] label[data-selected="true"] {
    color: #c9a84c !important;
}

/* ── Suggestion buttons — centered single column ── */
.stButton > button {
    background: #0a0800 !important;
    color: #c9a84c77 !important;
    border: 1px solid #c9a84c1a !important;
    border-radius: 2px !important;
    width: 100% !important;
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: center !important;
    font-family: 'Crimson Text', serif !important;
    font-size: 1.05em !important;
    padding: 14px 20px !important;
    transition: all 0.25s !important;
    letter-spacing: 0.3px !important;
    line-height: 1.5 !important;
}
/* Hit every possible child Streamlit might inject */
.stButton > button *,
.stButton > button p,
.stButton > button span,
.stButton > button div {
    text-align: center !important;
    justify-content: center !important;
    width: 100% !important;
    margin: 0 !important;
}
.stButton > button:hover {
    background: #130f00 !important;
    color: #c9a84c !important;
    border-color: #c9a84c55 !important;
    box-shadow: 0 0 14px #c9a84c18 !important;
    transform: translateY(-1px) !important;
}

/* ── Left‑align suggestion buttons (keys starting with sq_) ── */
[data-testid^="stButton-sq_"] button {
    text-align: left !important;
    justify-content: flex-start !important;
}
[data-testid^="stButton-sq_"] button * {
    text-align: left !important;
    justify-content: flex-start !important;
}

/* ── Begin the Trial button — centre using its id ── */
#start_quiz {
    display: flex !important;
    justify-content: center !important;
}
#start_quiz button {
    min-width: 200px !important;
    text-align: center !important;
    padding: 14px 36px !important;
    font-family: 'Cinzel', serif !important;
    font-size: 0.92em !important;
    letter-spacing: 3px !important;
    color: #c9a84c !important;
    border-color: #c9a84c55 !important;
    transform: none !important;
}
#start_quiz button:hover {
    border-color: #c9a84c !important;
    box-shadow: 0 0 20px #c9a84c22 !important;
    transform: none !important;
}

/* ── Chat input — nuke all Streamlit wrapper backgrounds ── */
[data-testid="stBottom"] {
    background: linear-gradient(to top, #060504 80%, transparent) !important;
    border-top: none !important;
    box-shadow: none !important;
    padding-top: 20px !important;
}
[data-testid="stBottom"] > div,
[data-testid="stBottom"] > div > div,
[data-testid="stBottom"] > div > div > div {
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
    border: none !important;
}
/* Nuke grey from every nested layer inside stChatInput */
[data-testid="stChatInput"] *:not(button):not(button *):not(textarea):not(input) {
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
    border: none !important;
}
/* Re-apply the styled outer shell */
[data-testid="stChatInput"] > div > div {
    background: #0d0a00 !important;
    border: 1px solid #c9a84c44 !important;
    border-radius: 2px !important;
    box-shadow: 0 0 20px #c9a84c0a, inset 0 1px 0 #c9a84c11 !important;
    transition: border-color 0.25s, box-shadow 0.25s !important;
}
[data-testid="stChatInput"] > div > div:focus-within {
    border-color: #c9a84c88 !important;
    box-shadow: 0 0 30px #c9a84c18, inset 0 1px 0 #c9a84c22 !important;
}
/* The text input itself */
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] input {
    background: transparent !important;
    background-color: transparent !important;
    color: #e8d5a3 !important;
    font-family: 'Crimson Text', serif !important;
    font-size: 1.12em !important;
    font-style: italic !important;
    caret-color: #c9a84c !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}
[data-testid="stChatInput"] textarea::placeholder,
[data-testid="stChatInput"] input::placeholder {
    color: #c9a84c55 !important;
    font-style: italic !important;
    font-family: 'Crimson Text', serif !important;
}

/* ── Send button — NO inner box, arrow sits inside outer container ── */
[data-testid="stChatInput"] button {
    background: transparent !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    color: #c9a84c !important;
    transition: all 0.25s !important;
    padding: 6px !important;
    margin: 0 !important;
}
[data-testid="stChatInput"] button:hover {
    background: #c9a84c11 !important;
    border: none !important;
    box-shadow: none !important;
}
[data-testid="stChatInput"] button:focus,
[data-testid="stChatInput"] button:active {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}
/* All inner spans/divs inside the send button — no borders */
[data-testid="stChatInput"] button *,
[data-testid="stChatInput"] button span,
[data-testid="stChatInput"] button div {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    background: transparent !important;
}
[data-testid="stChatInput"] button svg {
    fill: #c9a84c !important;
    stroke: #c9a84c !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
}

/* User messages */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
    background: #0d0a00 !important;
    border: 1px solid #c9a84c18 !important;
    border-left: 2px solid #c9a84c33 !important;
    color: #c9a84c88 !important;
    font-family: 'Crimson Text', serif !important;
    font-style: italic;
    font-size: 1.12em !important;
    line-height: 1.8 !important;
    border-radius: 2px !important;
    padding: 14px 18px !important;
}

/* Assistant messages */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] {
    background: linear-gradient(160deg, #0f0c00 0%, #0a0900 100%) !important;
    border: 1px solid #c9a84c28 !important;
    border-left: 2px solid #c9a84c77 !important;
    color: #e8d5a3 !important;
    font-family: 'Crimson Text', serif !important;
    font-size: 1.18em !important;
    line-height: 2.0 !important;
    border-radius: 2px !important;
    padding: 18px 22px !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #080600 !important;
    color: #c9a84c55 !important;
    font-family: 'Cinzel', serif !important;
    font-size: 0.8em !important;
    letter-spacing: 2px;
    border: 1px solid #c9a84c18 !important;
    border-radius: 1px !important;
}
.streamlit-expanderContent {
    background: #060400 !important;
    border: 1px solid #c9a84c18 !important;
    color: #c9a84c66 !important;
    font-family: 'Crimson Text', serif !important;
    font-size: 1.0em !important;
    line-height: 1.9;
}

/* ── Progress ── */
.stProgress > div > div {
    background: linear-gradient(90deg, #c9a84c, #e8c870) !important;
    box-shadow: 0 0 6px #c9a84c44;
}
.stProgress > div {
    background: #1a1200 !important;
    border: 1px solid #c9a84c1a !important;
    border-radius: 1px !important;
}

/* ── Status messages ── */
.stSuccess {
    background: #080e06 !important;
    border: 1px solid #3a6a3c66 !important;
    color: #7aaa7c !important;
    font-family: 'Crimson Text', serif !important;
    font-size: 1.05em !important;
    border-radius: 2px !important;
}
.stWarning {
    background: #100e00 !important;
    border: 1px solid #c9a84c44 !important;
    color: #c9a84c !important;
    font-family: 'Crimson Text', serif !important;
    font-size: 1.05em !important;
    border-radius: 2px !important;
}
.stError {
    background: #100000 !important;
    border: 1px solid #7a2020 !important;
    color: #aa5555 !important;
    font-family: 'Crimson Text', serif !important;
    font-size: 1.05em !important;
    border-radius: 2px !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: #c9a84c !important; }

/* ── Headers ── */
h1, h2, h3 {
    font-family: 'Cinzel', serif !important;
    color: #c9a84c !important;
    letter-spacing: 2px;
}

/* ── Character speaker badge ── */
.char-speaker-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 4px 12px 4px 6px;
    border-radius: 2px;
    margin-bottom: 10px;
    border: 1px solid;
}
.char-avatar-small {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8em;
    font-family: 'Cinzel', serif;
    flex-shrink: 0;
}
.char-name-small {
    font-family: 'Cinzel', serif;
    font-size: 0.78em;
    letter-spacing: 1.5px;
}
.char-subtitle-small {
    font-family: 'Crimson Text', serif;
    font-style: italic;
    font-size: 0.88em;
}

/* ── Mode badge ── */
.mode-badge {
    font-family: 'Cinzel', serif;
    font-size: 0.65em;
    letter-spacing: 2px;
    padding: 2px 8px;
    border: 1px solid #c9a84c22;
    color: #c9a84c44;
    display: inline-block;
    margin-left: 8px;
    vertical-align: middle;
}

/* ── Suggested questions header ── */
.suggest-header {
    font-family: 'Cinzel', serif;
    font-size: 0.75em;
    letter-spacing: 3px;
    color: #c9a84c44;
    text-align: center;
    margin: 16px 0 10px 0;
}

/* ── Quiz ── */
.quiz-q-box {
    font-family: 'Crimson Text', serif;
    color: #e8d5a3;
    font-size: 1.22em;
    line-height: 1.85;
    margin: 16px 0;
    padding: 20px 22px;
    background: #0a0800;
    border: 1px solid #c9a84c28;
    border-left: 2px solid #c9a84c66;
    border-radius: 1px;
}
.quiz-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}
.quiz-counter {
    font-family: 'Cinzel', serif;
    color: #c9a84c55;
    font-size: 0.78em;
    letter-spacing: 2px;
}
.quiz-diff {
    font-family: 'Cinzel', serif;
    font-size: 0.75em;
    letter-spacing: 1.5px;
}
.score-card {
    background: linear-gradient(160deg, #0d0a00 0%, #140f00 100%);
    border: 1px solid #c9a84c44;
    border-left: 3px solid #c9a84c;
    padding: 24px 28px;
    margin: 16px 0;
    border-radius: 2px;
}
.score-big {
    font-family: 'Cinzel Decorative', serif;
    color: #c9a84c;
    font-size: 2.6em;
    font-weight: 700;
    text-align: center;
    text-shadow: 0 0 30px #c9a84c55;
    letter-spacing: 2px;
}
.rank-text {
    font-family: 'Cinzel Decorative', serif;
    color: #c9a84c;
    font-size: 1.2em;
    text-align: center;
    letter-spacing: 3px;
    text-shadow: 0 0 20px #c9a84c66;
    margin: 10px 0 4px 0;
}
.score-subtext {
    font-family: 'Crimson Text', serif;
    font-style: italic;
    color: #c9a84c88;
    text-align: center;
    font-size: 1.05em;
    margin: 4px 0;
}

/* ── Quiz radio ── */
div[data-testid="stRadio"] > div {
    gap: 6px;
}
div[data-testid="stRadio"] > div > label {
    background: #080600 !important;
    border: 1px solid #c9a84c18 !important;
    padding: 11px 16px !important;
    border-radius: 2px !important;
    transition: all 0.2s !important;
    font-family: 'Crimson Text', serif !important;
    font-size: 1.08em !important;
    line-height: 1.6 !important;
}
div[data-testid="stRadio"] > div > label:hover {
    border-color: #c9a84c44 !important;
    background: #100d00 !important;
}

/* ── Character roster pills in sidebar ── */
.char-pill {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    border: 1px solid #c9a84c14;
    border-radius: 2px;
    margin: 4px 0;
    cursor: default;
}
.char-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}
.char-pill-name {
    font-family: 'Cinzel', serif;
    font-size: 0.8em;
    color: #c9a84c77;
    letter-spacing: 0.5px;
}
.char-pill-domain {
    font-family: 'Crimson Text', serif;
    font-size: 0.88em;
    color: #c9a84c44;
    font-style: italic;
    margin-left: auto;
}

/* ── Verdict box in results ── */
.verdict-banner {
    font-family: 'Cinzel', serif;
    font-size: 0.78em;
    letter-spacing: 3px;
    color: #c9a84c55;
    text-align: center;
    margin: 20px 0 12px 0;
}
.review-header {
    font-family: 'Cinzel', serif;
    font-size: 0.78em;
    letter-spacing: 2.5px;
    color: #c9a84c55;
    text-align: center;
    margin: 20px 0 14px 0;
}

/* ── Quiz answer review ── */
.answer-correct { color: #7aaa7c; font-size: 1.08em; }
.answer-wrong   { color: #aa5555; font-size: 1.08em; }
.answer-correct-mark { color: #7aaa7c; font-family: 'Cinzel', serif; font-size: 0.88em; }
.answer-wrong-mark   { color: #aa5555; font-family: 'Cinzel', serif; font-size: 0.88em; }

/* ── Gideon note in expander ── */
.gideon-note {
    font-family: 'Crimson Text', serif;
    color: #c9a84c88;
    font-style: italic;
    margin-top: 12px;
    padding-top: 10px;
    border-top: 1px solid #c9a84c18;
    font-size: 1.05em;
    line-height: 1.85;
}

/* ── Start quiz box ── */
.quiz-intro {
    font-family: 'Crimson Text', serif;
    color: #c9a84c88;
    font-size: 1.12em;
    text-align: center;
    line-height: 2.0;
    margin: 20px 0;
}
.quiz-points-bar {
    font-family: 'Cinzel', serif;
    color: #c9a84c44;
    font-size: 0.75em;
    letter-spacing: 2px;
    text-align: center;
    margin-bottom: 6px;
}

/* ── Speaker header for messages ── */
.speaker-header {
    margin-bottom: 10px;
}
.speaker-name {
    font-family: 'Cinzel', serif;
    font-size: 0.82em;
    letter-spacing: 2px;
    text-transform: uppercase;
}
.speaker-divider {
    height: 1px;
    background: linear-gradient(to right, currentColor, transparent);
    margin-top: 5px;
    opacity: 0.3;
}

/* ── Empty state ── */
.empty-state-rune {
    text-align: center;
    font-size: 2.5em;
    color: #c9a84c22;
    margin: 30px 0 10px 0;
    font-family: serif;
}
.empty-state-text {
    font-family: 'Crimson Text', serif;
    font-style: italic;
    color: #c9a84c44;
    text-align: center;
    font-size: 1.08em;
    margin-bottom: 24px;
    line-height: 1.9;
}
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 10px 0 4px 0;">
        <div class="sidebar-logo">EldenLore</div>
        <div class="sidebar-tagline">Lore of the Lands Between</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="rune-sep">✦ ✦ ✦</div>', unsafe_allow_html=True)

    page = st.radio(
        "",
        ["Seek Knowledge", "Test Your Lore"],
        label_visibility="collapsed",
    )

    st.markdown('<div class="rune-sep">✦ ✦ ✦</div>', unsafe_allow_html=True)

    # Character roster
    st.markdown('<div class="sidebar-section-label">SPEAKING CHARACTERS</div>', unsafe_allow_html=True)

    roster = [
        ("Ranni",      "#a0b8e0", "Sorcery & fate"),
        ("Melina",     "#d4a574", "Erdtree & grace"),
        ("Fia",        "#9b8db0", "Death & cursemark"),
        ("Goldmask",   "#e8c870", "Golden Order"),
        ("Miriel",     "#7ab892", "Ancient history"),
        ("Enia",       "#c4a882", "Demigods & runes"),
        ("Dung Eater", "#8a6060", "Curses & Omen"),
        ("Gideon",     "#c9a84c", "All other lore"),
    ]
    for name, color, domain in roster:
        st.markdown(f"""
        <div class="char-pill">
            <div class="char-dot" style="background:{color};box-shadow:0 0 5px {color}66;"></div>
            <span class="char-pill-name">{name}</span>
            <span class="char-pill-domain">{domain}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="rune-sep">✦ ✦ ✦</div>', unsafe_allow_html=True)

    if st.button("Clear Audience", key="clear_btn"):
        st.session_state.messages = []
        st.session_state.last_character = None
        st.session_state.generating = False
        st.rerun()

    st.markdown('<div class="rune-sep">✦ ✦ ✦</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-info">
        Ask of characters, bosses, items,<br>
        weapons, sorceries, incantations,<br>
        Great Runes, areas, and the lore<br>
        of Shadow of the Erdtree.
    </div>
    """, unsafe_allow_html=True)


# ── Suggested questions ───────────────────────────────────────────────────────
# Replaced with 8 simple, popular, and interesting lore questions
SUGGESTED_QUESTIONS = [
    "Who is Ranni and what is her plan?",
    "What is the Night of the Black Knives?",
    "What happened to Godwyn the Golden?",
    "Why is Malenia cursed with the Scarlet Rot?",
    "What is the Elden Ring and why is it shattered?",
    "Who is Miquella and why is he important?",
    "What is the Erdtree and what does it represent?",
    "What caused the Shattering of the Elden Ring?",
]


# ── Session state ─────────────────────────────────────────────────────────────
defaults = {
    "messages": [],
    "last_character": None,
    "generating": False,
    "quiz_questions": [],
    "quiz_submitted": False,
    "quiz_started": False,
    "current_q": 0,
    "selected_answers": {},
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Helper: render character speaker label ────────────────────────────────────
def render_char_header(char_name: str, mode: str = ""):
    vis = get_char_visual(char_name)
    mode_html = f'<span class="mode-badge">{mode.upper()}</span>' if mode and mode not in ("rag", "casual") else ""
    st.markdown(f"""
    <div class="speaker-header">
        <span class="speaker-name" style="color:{vis['accent']};">
            {vis['title']} · {vis['subtitle']}
        </span>{mode_html}
        <div class="speaker-divider" style="color:{vis['accent']};"></div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE: SEEK KNOWLEDGE
# ═══════════════════════════════════════════════════════════════════════════
if page == "Seek Knowledge":

    # Header
    st.markdown("""
    <div class="eldenlore-header">
        <span class="eldenlore-wordmark">EldenLore RAG</span>
        <span class="eldenlore-title">Seek Knowledge</span>
        <span class="eldenlore-sub">"Eight voices carry the secrets of the Lands Between."</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="grace-divider">
        <div class="grace-line"></div>
        <div class="grace-diamond"></div>
        <div class="grace-line"></div>
    </div>
    """, unsafe_allow_html=True)

    # Empty state + suggestions — hidden while generating
    if not st.session_state.messages and not st.session_state.generating:
        st.markdown("""
        <div class="empty-state-rune">⚔</div>
        <div class="empty-state-text">
            Your question will summon the most fitting voice from the Lands Between.<br>
            Ask of lore, characters, events, or the secrets of the Erdtree.
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="suggest-header">MATTERS OF INQUIRY</div>', unsafe_allow_html=True)

        # ── Two columns with 4 questions each ──────────────────────────────
        col1, col2 = st.columns(2)
        half = len(SUGGESTED_QUESTIONS) // 2

        with col1:
            for i, question in enumerate(SUGGESTED_QUESTIONS[:half]):
                if st.button(question, key=f"sq_{i}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": question})
                    st.session_state.generating = True
                    st.rerun()

        with col2:
            for i, question in enumerate(SUGGESTED_QUESTIONS[half:]):
                if st.button(question, key=f"sq_{i+half}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": question})
                    st.session_state.generating = True
                    st.rerun()

    # Chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant" and msg.get("character"):
                render_char_header(msg["character"], msg.get("mode", ""))
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("✦  SOURCES FROM THE LANDS BETWEEN"):
                    for source in msg["sources"]:
                        st.markdown(f"<span style='color:#c9a84c66;font-family:Crimson Text,serif;font-size:1em;'>— {source}</span>", unsafe_allow_html=True)

    # Generate answer for last user message
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        question = st.session_state.messages[-1]["content"]
        with st.chat_message("assistant"):
            with st.spinner("The Lands Between stir..."):
                result = ask(question, st.session_state.messages[:-1])
                if len(result) == 4:
                    answer, sources, mode, char_name = result
                else:
                    answer, sources, mode = result
                    char_name = "Sir Gideon Ofnir, the All-Knowing"

            render_char_header(char_name, mode)
            st.markdown(answer)
            if sources:
                with st.expander("✦  SOURCES FROM THE LANDS BETWEEN"):
                    for source in sources:
                        st.markdown(f"<span style='color:#c9a84c66;font-family:Crimson Text,serif;font-size:1em;'>— {source}</span>", unsafe_allow_html=True)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "character": char_name,
            "mode": mode,
        })
        st.session_state.last_character = char_name
        st.session_state.generating = False
        st.rerun()

    # Input
    question = st.chat_input("Speak your inquiry, Tarnished…")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        st.session_state.generating = True
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE: TEST YOUR LORE (quiz)
# ═══════════════════════════════════════════════════════════════════════════
elif page == "Test Your Lore":

    st.markdown("""
    <div class="eldenlore-header">
        <span class="eldenlore-wordmark">EldenLore RAG</span>
        <span class="eldenlore-title">Trial of Lore</span>
        <span class="eldenlore-sub">"Let us see if your mind is as sharp as your blade, Tarnished."</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="grace-divider">
        <div class="grace-line"></div>
        <div class="grace-diamond"></div>
        <div class="grace-line"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── START SCREEN ─────────────────────────────────────────────────────
    if not st.session_state.quiz_started:
        st.markdown("""
        <div class="quiz-intro">
            Ten questions drawn from the lore of the Lands Between.<br>
            Each question is scored by difficulty — prove your knowledge.
        </div>
        <div class="quiz-points-bar">
            EASY &nbsp;·&nbsp; 10 PTS &nbsp;&nbsp;✦&nbsp;&nbsp; MEDIUM &nbsp;·&nbsp; 20 PTS &nbsp;&nbsp;✦&nbsp;&nbsp; HARD &nbsp;·&nbsp; 30 PTS
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="rune-sep" style="margin:20px 0 14px 0;">✦ ✦ ✦</div>
        <div style="font-family:Crimson Text,serif;color:#c9a84c55;font-size:1.0em;text-align:center;margin-bottom:18px;">
            Questions are drawn from the full breadth of the Lands Between
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Begin the Trial", key="start_quiz"):
                with st.spinner("The trial is being prepared…"):
                    chunks = get_weighted_chunks(count=20)
                    questions = []
                    for doc, meta in chunks:
                        if len(questions) >= 10:
                            break
                        q = generate_question(doc, meta)
                        if q:
                            q["category_label"] = CATEGORY_CONFIG.get(
                                meta.get("category", ""), {}
                            ).get("label", meta.get("category", ""))
                            questions.append(q)

                st.session_state.quiz_questions = questions
                st.session_state.quiz_started = True
                st.session_state.quiz_submitted = False
                st.session_state.selected_answers = {}
                st.session_state.current_q = 0
                st.rerun()

    # ── QUESTION SCREEN ───────────────────────────────────────────────────
    elif not st.session_state.quiz_submitted:
        questions = st.session_state.quiz_questions
        current = st.session_state.current_q
        total = len(questions)
        q = questions[current]

        diff = q.get("difficulty", "medium")
        pts = POINTS_MAP.get(diff, 20)
        cat_label = q.get("category_label", "")
        diff_color = {"easy": "#7aaa7c", "medium": "#c9a84c", "hard": "#aa5555"}.get(diff, "#c9a84c")

        st.markdown(f"""
        <div class="quiz-meta">
            <span class="quiz-counter">QUESTION {current + 1} OF {total}</span>
            <span class="quiz-diff" style="color:{diff_color};">{diff.upper()} — {pts} PTS</span>
            <span style="font-family:Cinzel,serif;font-size:0.72em;color:#c9a84c44;letter-spacing:1.5px;">{cat_label}</span>
        </div>
        """, unsafe_allow_html=True)

        st.progress(current / total)
        st.markdown('<div class="rune-sep" style="margin:10px 0;">✦</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="quiz-q-box">{q["question"]}</div>', unsafe_allow_html=True)

        options = [f"{k})  {v}" for k, v in q["options"].items()]
        pre_selected = st.session_state.selected_answers.get(current)
        pre_index = None
        if pre_selected:
            for idx, opt in enumerate(options):
                if opt.startswith(pre_selected):
                    pre_index = idx
                    break

        selected = st.radio("", options, key=f"q_{current}", index=pre_index)

        st.markdown("")
        col1, col2, col3 = st.columns([1, 3, 1])

        with col1:
            if current > 0:
                if st.button("Prev", key="prev_btn"):
                    st.session_state.current_q -= 1
                    st.rerun()

        with col3:
            if selected:
                letter = selected[0]
                st.session_state.selected_answers[current] = letter
                if current < total - 1:
                    if st.button("Next", key="next_btn"):
                        st.session_state.current_q += 1
                        st.rerun()
                else:
                    answered = len(st.session_state.selected_answers)
                    if answered >= total:
                        if st.button("Submit ✦", key="submit_btn"):
                            st.session_state.quiz_submitted = True
                            st.rerun()
                    else:
                        st.button("Submit ✦", key="submit_disabled", disabled=True)

        answered = len(st.session_state.selected_answers)
        st.markdown(f"""
        <div style="font-family:Cinzel,serif;color:#c9a84c44;font-size:0.75em;
             letter-spacing:2px;text-align:center;margin-top:14px;">
        {answered} OF {total} ANSWERED
        </div>
        """, unsafe_allow_html=True)

    # ── RESULTS SCREEN ────────────────────────────────────────────────────
    else:
        questions = st.session_state.quiz_questions
        answers_map = st.session_state.selected_answers
        total = len(questions)

        answer_entries = []
        for i, q in enumerate(questions):
            user_letter = answers_map.get(i, "")
            is_correct = user_letter == q.get("correct", "")
            answer_entries.append({
                "question":    q["question"],
                "your_answer": q["options"].get(user_letter, "Not answered"),
                "correct":     q["options"].get(q.get("correct", ""), ""),
                "is_correct":  is_correct,
                "difficulty":  q.get("difficulty", "medium"),
                "explanation": q.get("explanation", ""),
                "category":    q.get("category_label", ""),
            })

        result = calculate_score(answer_entries)
        pct = result["percentage"]

        st.markdown(f"""
        <div class="score-card">
            <div class="score-big">{result['total_points']} <span style="font-size:0.5em;color:#c9a84c66;">/ {result['max_points']}</span></div>
            <div class="score-subtext">{result['correct_count']} correct of {result['total_questions']} questions — {result['percentage']}%</div>
            <div class="rank-text">{result['rank']}</div>
        </div>
        """, unsafe_allow_html=True)

        if pct == 100:
            st.success("Perfect. You rival even my own knowledge, Tarnished.")
        elif pct >= 80:
            st.success("Impressive. You have studied the Lands Between well.")
        elif pct >= 60:
            st.warning("Adequate, but there is much yet to learn.")
        elif pct >= 40:
            st.warning("You would do well to consult the lore more often, Tarnished.")
        else:
            st.error("Disgraceful. Return when you have studied the Lands Between.")

        st.markdown('<div class="rune-sep" style="margin:20px 0;">✦ ✦ ✦</div>', unsafe_allow_html=True)
        st.markdown('<div class="review-header">REVIEW OF YOUR TRIAL</div>', unsafe_allow_html=True)

        for i, (q, entry) in enumerate(zip(questions, result["breakdown"])):
            user_letter = answers_map.get(i, "")
            correct_letter = q.get("correct", "")
            is_correct = entry["is_correct"]
            diff = q.get("difficulty", "medium")
            pts_earned = entry["points_earned"]
            pts_possible = entry["points_possible"]
            diff_color = {"easy": "#7aaa7c", "medium": "#c9a84c", "hard": "#aa5555"}.get(diff, "#c9a84c")
            label = "✓" if is_correct else "✗"

            with st.expander(
                f"Q{i+1}  {label}  +{pts_earned}/{pts_possible} pts  ·  {q['question'][:60]}{'…' if len(q['question']) > 60 else ''}"
            ):
                st.markdown(f"""
                <div style="font-family:Cinzel,serif;color:{diff_color};font-size:0.78em;letter-spacing:1.5px;margin-bottom:12px;">
                    {diff.upper()} — {pts_possible} PTS &nbsp;·&nbsp; {q.get('category_label', '')}
                </div>
                """, unsafe_allow_html=True)

                for key, val in q["options"].items():
                    if key == correct_letter and key == user_letter:
                        st.markdown(f"<span class='answer-correct'>**{key})  {val}** — ✓ Your answer · Correct</span>", unsafe_allow_html=True)
                    elif key == correct_letter:
                        st.markdown(f"<span class='answer-correct'>**{key})  {val}** — ✓ Correct answer</span>", unsafe_allow_html=True)
                    elif key == user_letter:
                        st.markdown(f"<span class='answer-wrong'>{key})  {val} — ✗ Your answer</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span style='color:#c9a84c44;font-size:1.05em;'>{key})  {val}</span>", unsafe_allow_html=True)

                if q.get("explanation"):
                    st.markdown(f"""
                    <div class="gideon-note">
                    Gideon notes: {q['explanation']}
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown('<div class="rune-sep" style="margin:20px 0;">✦ ✦ ✦</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Face the Trial Again", key="retry"):
                st.session_state.quiz_started = False
                st.session_state.quiz_questions = []
                st.session_state.selected_answers = {}
                st.session_state.quiz_submitted = False
                st.session_state.current_q = 0
                st.rerun()
        with col2:
            if st.button("Return to Gideon", key="return"):
                st.session_state.quiz_started = False
                st.session_state.quiz_questions = []
                st.session_state.selected_answers = {}
                st.session_state.quiz_submitted = False
                st.rerun()