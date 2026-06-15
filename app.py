import streamlit as st
from bot import ask
from quiz import get_weighted_chunks, generate_question, calculate_score, get_rank, POINTS_MAP, CATEGORY_CONFIG

st.set_page_config(
    page_title="Sir Gideon Ofnir - The All-Knowing",
    page_icon="⚔",
    layout="centered"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@400;700&family=Cinzel:wght@400;600;700&family=Crimson+Text:ital,wght@0,400;0,600;1,400;1,600&display=swap');

/* Base */
.stApp {
    background-color: #080600;
    background-image:
        radial-gradient(ellipse at 50% 0%, #1a1200 0%, transparent 60%),
        radial-gradient(ellipse at 50% 100%, #0d0a00 0%, transparent 60%);
    color: #c9a84c;
}

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #080600; }
::-webkit-scrollbar-thumb { background: #c9a84c44; border-radius: 2px; }

/* Main title */
.gideon-title {
    text-align: center;
    font-family: 'Cinzel Decorative', serif;
    color: #c9a84c;
    font-size: 1.9em;
    font-weight: 700;
    letter-spacing: 3px;
    text-shadow:
        0 0 40px #c9a84c88,
        0 0 80px #c9a84c33,
        0 2px 4px #000;
    padding: 20px 0 8px 0;
    line-height: 1.4;
}

/* Grace site glow divider */
.grace-divider {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    margin: 8px 0 16px 0;
}
.grace-line {
    flex: 1;
    height: 1px;
    background: linear-gradient(to right, transparent, #c9a84c66, transparent);
}
.grace-diamond {
    width: 8px;
    height: 8px;
    background: #c9a84c;
    transform: rotate(45deg);
    box-shadow: 0 0 12px #c9a84c, 0 0 24px #c9a84c88;
}

/* Quote */
.gideon-quote {
    text-align: center;
    font-family: 'Crimson Text', serif;
    font-style: italic;
    color: #c9a84c99;
    font-size: 1.05em;
    margin-bottom: 24px;
    letter-spacing: 0.5px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #060500 !important;
    border-right: 1px solid #c9a84c22 !important;
}
[data-testid="stSidebar"] * {
    font-family: 'Crimson Text', serif !important;
}

.sidebar-title {
    font-family: 'Cinzel', serif !important;
    color: #c9a84c;
    font-size: 1.2em;
    letter-spacing: 2px;
    text-align: center;
    text-shadow: 0 0 20px #c9a84c66;
    padding: 8px 0;
}

/* Nav radio */
div[data-testid="stRadio"] {
    background: transparent;
}
div[data-testid="stRadio"] label {
    color: #c9a84c99 !important;
    font-family: 'Cinzel', serif !important;
    font-size: 0.85em !important;
    letter-spacing: 1px;
    padding: 4px 0;
    transition: color 0.2s;
}
div[data-testid="stRadio"] label:hover {
    color: #c9a84c !important;
}

/* Suggested question buttons */
.stButton button {
    background: linear-gradient(135deg, #0d0a00 0%, #1a1400 100%) !important;
    color: #c9a84c99 !important;
    border: 1px solid #c9a84c33 !important;
    border-radius: 1px !important;
    width: 100% !important;
    text-align: left !important;
    margin-bottom: 6px !important;
    font-family: 'Crimson Text', serif !important;
    font-size: 0.92em !important;
    padding: 8px 12px !important;
    transition: all 0.2s !important;
    letter-spacing: 0.3px;
}
.stButton button:hover {
    background: linear-gradient(135deg, #1a1400 0%, #2a2000 100%) !important;
    color: #c9a84c !important;
    border-color: #c9a84c77 !important;
    box-shadow: 0 0 12px #c9a84c22 !important;
}

/* Chat input */
.stChatInput {
    border-top: 1px solid #c9a84c22 !important;
    padding-top: 12px !important;
}
.stChatInput input {
    background: #0d0a00 !important;
    color: #c9a84c !important;
    border: 1px solid #c9a84c44 !important;
    border-radius: 1px !important;
    font-family: 'Crimson Text', serif !important;
    font-size: 1em !important;
    caret-color: #c9a84c;
}
.stChatInput input::placeholder {
    color: #c9a84c44 !important;
    font-style: italic;
}
.stChatInput input:focus {
    border-color: #c9a84c99 !important;
    box-shadow: 0 0 16px #c9a84c22 !important;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
}
[data-testid="stChatMessageContent"] {
    background: linear-gradient(135deg, #0d0a00 0%, #110e00 100%) !important;
    border: 1px solid #c9a84c33 !important;
    border-left: 2px solid #c9a84c66 !important;
    color: #e8d5a3 !important;
    font-family: 'Crimson Text', serif !important;
    font-size: 1.05em !important;
    line-height: 1.85 !important;
    border-radius: 1px !important;
    padding: 14px 18px !important;
}

/* User message different style */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
    background: #0a0800 !important;
    border-left: 2px solid #c9a84c33 !important;
    color: #c9a84c88 !important;
    font-style: italic;
}

/* Expander */
.streamlit-expanderHeader {
    background: #0d0a00 !important;
    color: #c9a84c77 !important;
    font-family: 'Cinzel', serif !important;
    font-size: 0.8em !important;
    letter-spacing: 1px;
    border: 1px solid #c9a84c22 !important;
}
.streamlit-expanderContent {
    background: #0a0800 !important;
    border: 1px solid #c9a84c22 !important;
    color: #c9a84c77 !important;
    font-family: 'Crimson Text', serif !important;
    font-size: 0.9em !important;
}

/* Progress bar */
.stProgress > div > div {
    background: linear-gradient(90deg, #c9a84c, #f0d080) !important;
    box-shadow: 0 0 8px #c9a84c66;
}
.stProgress > div {
    background: #1a1400 !important;
    border: 1px solid #c9a84c22 !important;
}

/* Quiz radio options */
div[data-testid="stRadio"] > div {
    gap: 8px;
}

/* Success/Warning/Error */
.stSuccess {
    background: #0a1200 !important;
    border: 1px solid #4a8a4c !important;
    color: #8aaa8c !important;
    font-family: 'Crimson Text', serif !important;
}
.stWarning {
    background: #1a1200 !important;
    border: 1px solid #c9a84c44 !important;
    color: #c9a84c !important;
    font-family: 'Crimson Text', serif !important;
}
.stError {
    background: #1a0000 !important;
    border: 1px solid #8a2020 !important;
    color: #aa6060 !important;
    font-family: 'Crimson Text', serif !important;
}

/* Spinner */
.stSpinner > div {
    border-top-color: #c9a84c !important;
}

/* Section headers */
h1, h2, h3 {
    font-family: 'Cinzel', serif !important;
    color: #c9a84c !important;
    letter-spacing: 2px;
}

/* Sidebar info text */
.sidebar-info {
    font-family: 'Crimson Text', serif;
    color: #c9a84c66;
    font-size: 0.88em;
    line-height: 1.8;
}

/* Rune separator */
.rune-sep {
    text-align: center;
    color: #c9a84c33;
    font-size: 1.2em;
    letter-spacing: 8px;
    margin: 12px 0;
}

/* Score card */
.score-card {
    background: linear-gradient(135deg, #0d0a00 0%, #1a1400 100%);
    border: 1px solid #c9a84c44;
    border-left: 3px solid #c9a84c;
    padding: 16px 20px;
    margin: 12px 0;
    font-family: 'Crimson Text', serif;
}
.score-big {
    font-family: 'Cinzel', serif;
    color: #c9a84c;
    font-size: 2em;
    font-weight: 700;
    text-align: center;
    text-shadow: 0 0 20px #c9a84c66;
}
.rank-text {
    font-family: 'Cinzel Decorative', serif;
    color: #c9a84c;
    font-size: 1.2em;
    text-align: center;
    letter-spacing: 2px;
    text-shadow: 0 0 16px #c9a84c88;
    margin: 8px 0;
}
.diff-badge-easy   { color: #8aaa8c; font-size: 0.78em; font-family: 'Cinzel', serif; letter-spacing: 1px; }
.diff-badge-medium { color: #c9a84c; font-size: 0.78em; font-family: 'Cinzel', serif; letter-spacing: 1px; }
.diff-badge-hard   { color: #aa6060; font-size: 0.78em; font-family: 'Cinzel', serif; letter-spacing: 1px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.markdown('<p class="sidebar-title">⚔ GIDEON OFNIR ⚔</p>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="rune-sep">✦ ✦ ✦</div>', unsafe_allow_html=True)

page = st.sidebar.radio("", ["Seek Knowledge", "Test Your Lore"])

st.sidebar.markdown('<div class="rune-sep">✦ ✦ ✦</div>', unsafe_allow_html=True)

if st.sidebar.button("Clear Audience"):
    st.session_state.messages = []
    st.rerun()

st.sidebar.markdown('<div class="rune-sep">✦ ✦ ✦</div>', unsafe_allow_html=True)

st.sidebar.markdown("""
<div class="sidebar-info">
Gideon's knowledge spans:<br><br>
Characters &amp; NPCs<br>
Bosses &amp; Demigods<br>
Areas &amp; Locations<br>
Weapons &amp; their Lore<br>
Spells &amp; Incantations<br>
Armor, Talismans &amp; Items<br>
Great Runes &amp; Spirit Ashes<br>
The Greater Will &amp; Outer Gods<br>
Shadow of the Erdtree DLC
</div>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
defaults = {
    "messages": [],
    "quiz_questions": [],
    "quiz_submitted": False,
    "quiz_started": False,
    "current_q": 0,
    "selected_answers": {},
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Suggested questions ───────────────────────────────────────────────────────
SUGGESTED_QUESTIONS = [
    "Why is Ranni blue?",
    "Who is Malenia and what is her curse?",
    "What happened on the Night of the Black Knives?",
    "Who is Messmer the Impaler?",
    "What is the Scarlet Rot?",
    "Tell me about Mohg Lord of Blood",
    "What is Miquella's plan?",
    "Who are the Two Fingers?",
    "What is the Frenzied Flame?",
    "Tell me about Godwyn the Golden",
]

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: SEEK KNOWLEDGE (chat)
# ─────────────────────────────────────────────────────────────────────────────
if page == "Seek Knowledge":
    st.markdown('<div class="gideon-title">Sir Gideon Ofnir<br>The All-Knowing</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="grace-divider">
        <div class="grace-line"></div>
        <div class="grace-diamond"></div>
        <div class="grace-line"></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="gideon-quote">"I know all that transpires in the Lands Between. Ask, Tarnished."</div>', unsafe_allow_html=True)

    if not st.session_state.messages:
        st.markdown("""
        <div class="rune-sep">✦ ✦ ✦</div>
        <div style="font-family: Cinzel, serif; color: #c9a84c66; font-size: 0.75em; letter-spacing: 2px; text-align: center; margin-bottom: 12px;">MATTERS OF INQUIRY</div>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        for i, question in enumerate(SUGGESTED_QUESTIONS):
            with (col1 if i % 2 == 0 else col2):
                if st.button(question, key=f"sq_{i}"):
                    st.session_state.messages.append({"role": "user", "content": question})
                    st.rerun()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "sources" in msg and msg["sources"]:
                with st.expander("SOURCES FROM THE LANDS BETWEEN"):
                    for source in msg["sources"]:
                        st.markdown(f"— {source}")

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        question = st.session_state.messages[-1]["content"]
        with st.chat_message("assistant"):
            with st.spinner("Gideon consults his vast knowledge..."):
                answer, sources, mode = ask(question, st.session_state.messages[:-1])
            st.markdown(answer)
            if sources:
                with st.expander("SOURCES FROM THE LANDS BETWEEN"):
                    for source in sources:
                        st.markdown(f"— {source}")
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
        })
        st.rerun()

    question = st.chat_input("Speak your inquiry, Tarnished...")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: TEST YOUR LORE (quiz)
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Test Your Lore":
    st.markdown('<div class="gideon-title">Prove Your Knowledge</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="grace-divider">
        <div class="grace-line"></div>
        <div class="grace-diamond"></div>
        <div class="grace-line"></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="gideon-quote">"Let us see if your mind is as sharp as your blade, Tarnished."</div>', unsafe_allow_html=True)

    # ── START SCREEN ─────────────────────────────────────────────────────────
    if not st.session_state.quiz_started:
        st.markdown("""
        <div style="font-family: Crimson Text, serif; color: #c9a84c88; font-size: 1em; text-align: center; line-height: 1.8; margin: 20px 0;">
        Ten questions drawn from the lore of the Lands Between.<br>
        Points scale by difficulty — easy, medium, or hard.<br>
        The same trial for all who seek to prove themselves worthy.
        </div>
        <div style="font-family: Cinzel, serif; color: #c9a84c44; font-size: 0.72em; letter-spacing: 2px; text-align: center; margin-bottom: 4px;">
        EASY 10 pts &nbsp;·&nbsp; MEDIUM 20 pts &nbsp;·&nbsp; HARD 30 pts
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Begin the Trial", key="start_quiz"):
                with st.spinner("Gideon prepares your trial..."):
                    chunks = get_weighted_chunks(count=20)  # oversample, take first 10 that generate
                    questions = []
                    for doc, meta in chunks:
                        if len(questions) >= 10:
                            break
                        q = generate_question(doc, meta)
                        if q:
                            # attach human-readable category label
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

    # ── QUESTION SCREEN ───────────────────────────────────────────────────────
    elif not st.session_state.quiz_submitted:
        questions = st.session_state.quiz_questions
        current = st.session_state.current_q
        total = len(questions)

        q = questions[current]
        diff = q.get("difficulty", "medium")
        pts = POINTS_MAP.get(diff, 20)
        cat_label = q.get("category_label", "")

        diff_color = {"easy": "#8aaa8c", "medium": "#c9a84c", "hard": "#aa6060"}.get(diff, "#c9a84c")

        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-family:Cinzel,serif; color:#c9a84c66; font-size:0.75em; letter-spacing:2px;">
                QUESTION {current + 1} OF {total}
            </span>
            <span style="font-family:Cinzel,serif; color:{diff_color}; font-size:0.72em; letter-spacing:1px;">
                {diff.upper()} — {pts} PTS &nbsp;|&nbsp; {cat_label}
            </span>
        </div>
        """, unsafe_allow_html=True)

        st.progress((current) / total)
        st.markdown('<div class="rune-sep">✦</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div style="font-family: Crimson Text, serif; color: #e8d5a3; font-size: 1.15em; line-height: 1.7;
             margin: 16px 0; padding: 16px; background: #0d0a00;
             border: 1px solid #c9a84c33; border-left: 2px solid #c9a84c66;">
        {q['question']}
        </div>
        """, unsafe_allow_html=True)

        options = [f"{k})  {v}" for k, v in q["options"].items()]
        selected = st.radio("", options, key=f"q_{current}", index=None)

        st.markdown("")
        col1, col2 = st.columns(2)

        with col1:
            if current > 0:
                if st.button("← Previous"):
                    st.session_state.current_q -= 1
                    st.rerun()

        with col2:
            if selected:
                letter = selected[0]
                st.session_state.selected_answers[current] = letter
                if current < total - 1:
                    if st.button("Next →"):
                        st.session_state.current_q += 1
                        st.rerun()
                else:
                    if st.button("Submit to Gideon"):
                        st.session_state.quiz_submitted = True
                        st.rerun()

        answered = len(st.session_state.selected_answers)
        st.markdown(f"""
        <div style="font-family: Cinzel, serif; color: #c9a84c44; font-size: 0.7em;
             letter-spacing: 1px; text-align: center; margin-top: 16px;">
        {answered} OF {total} ANSWERED
        </div>
        """, unsafe_allow_html=True)

    # ── RESULTS SCREEN ────────────────────────────────────────────────────────
    else:
        questions = st.session_state.quiz_questions
        answers_map = st.session_state.selected_answers
        total = len(questions)

        # Build answer dicts for calculate_score
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

        st.markdown("""
        <div class="grace-divider">
            <div class="grace-line"></div>
            <div class="grace-diamond"></div>
            <div class="grace-line"></div>
        </div>
        <div style="font-family: Cinzel, serif; color: #c9a84c66; font-size: 0.75em;
             letter-spacing: 3px; text-align: center; margin-bottom: 16px;">THE VERDICT</div>
        """, unsafe_allow_html=True)

        # Score card
        st.markdown(f"""
        <div class="score-card">
            <div class="score-big">{result['total_points']} / {result['max_points']}</div>
            <div style="text-align:center; font-family:Crimson Text,serif; color:#c9a84c88; margin:4px 0;">
                {result['correct_count']} correct of {result['total_questions']} &nbsp;·&nbsp; {result['percentage']}%
            </div>
            <div class="rank-text">{result['rank']}</div>
        </div>
        """, unsafe_allow_html=True)

        # Gideon verdict line
        pct = result["percentage"]
        if pct == 100:
            st.success("Perfect. You rival even my own knowledge, Tarnished.")
        elif pct >= 80:
            st.success("Impressive. You have studied the Lands Between well.")
        elif pct >= 60:
            st.warning("Adequate, but there is much yet to learn.")
        elif pct >= 40:
            st.warning("You would do well to consult me more often, Tarnished.")
        else:
            st.error("Disgraceful. Return when you have studied the Lands Between.")

        st.markdown('<div class="rune-sep">✦ ✦ ✦</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-family: Cinzel, serif; color: #c9a84c66; font-size: 0.75em;
             letter-spacing: 2px; text-align: center; margin-bottom: 12px;">REVIEW OF YOUR TRIAL</div>
        """, unsafe_allow_html=True)

        for i, (q, entry) in enumerate(zip(questions, result["breakdown"])):
            user_letter = answers_map.get(i, "")
            correct_letter = q.get("correct", "")
            is_correct = entry["is_correct"]
            diff = q.get("difficulty", "medium")
            pts_earned = entry["points_earned"]
            pts_possible = entry["points_possible"]
            diff_color = {"easy": "#8aaa8c", "medium": "#c9a84c", "hard": "#aa6060"}.get(diff, "#c9a84c")
            label = "✓ CORRECT" if is_correct else "✗ WRONG"

            with st.expander(f"Q{i+1} [{label}]  +{pts_earned}/{pts_possible} pts  —  {q['question']}"):
                st.markdown(f"""
                <div style="font-family:Cinzel,serif; color:{diff_color}; font-size:0.72em; letter-spacing:1px; margin-bottom:10px;">
                    {diff.upper()} — {pts_possible} PTS &nbsp;|&nbsp; {q.get('category_label', '')}
                </div>
                """, unsafe_allow_html=True)

                for key, val in q["options"].items():
                    if key == correct_letter and key == user_letter:
                        st.markdown(f"**{key})  {val}** — ✓ Your answer (Correct)")
                    elif key == correct_letter:
                        st.markdown(f"**{key})  {val}** — ✓ Correct answer")
                    elif key == user_letter:
                        st.markdown(f"{key})  {val} — ✗ Your answer (Wrong)")
                    else:
                        st.markdown(f"{key})  {val}")

                st.markdown(f"""
                <div style="font-family: Crimson Text, serif; color: #c9a84c88; font-style: italic;
                     margin-top: 10px; padding-top: 8px; border-top: 1px solid #c9a84c22;">
                Gideon notes: {q.get('explanation', '')}
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<div class="rune-sep">✦ ✦ ✦</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Face the Trial Again"):
                st.session_state.quiz_started = False
                st.session_state.quiz_questions = []
                st.session_state.selected_answers = {}
                st.session_state.quiz_submitted = False
                st.session_state.current_q = 0
                st.rerun()
        with col2:
            if st.button("Return to Gideon"):
                st.session_state.quiz_started = False
                st.session_state.quiz_questions = []
                st.session_state.selected_answers = {}
                st.session_state.quiz_submitted = False
                page = "Seek Knowledge"
                st.rerun()