"""
rag_bot.py  — Sir Gideon Ofnir RAG bot

IMPROVEMENTS in this version:
  #1  Retrieval quality
      - top_k raised 12 → 20 for richer candidate pool
      - HyDE (Hypothetical Document Embedding): generates a fake lore passage
        as an extra dense query, pulling in chunks the original query misses
      - MMR threshold raised 0.90 → 0.92 to keep more diverse results

  #2  Hallucination guards
      - source_grounding_score(): heuristic check — if <40% of named entities
        in the answer appear in the sources, the answer is flagged
      - Low-grounding answers are re-asked at temperature=0 with a stricter prompt
      - Confident vs hedged split preserved from original

  #3  Query understanding
      - Entity extraction from query → used in both routing and retrieval
      - Richer lore sub-category detection: character / location / item / event /
        mechanic / theory — each gets a tailored answer prompt
      - LORE_SIGNALS expanded with Shadow of the Erdtree content

  #4  Memory & context
      - fuse_followup() upgraded: now also checks if the question is ≤5 words
        AND the last assistant turn mentioned a lore entity (entity co-reference)
      - LLM-based rewrite triggered only when keyword heuristic confirms follow-up
        (single LLM call, fast model)

  #5  Intent classifier
      - LORE_RESCUE_PATTERNS: regex list that rescues vague queries containing
        known entities from being misrouted as OFF_TOPIC
      - Follow-up in a lore conversation → assume lore without LLM call
      - Mechanics vs lore split preserved and extended

  #6  Data / chunking (retriever-side quick wins applied here)
      - retrieve() called with top_k=20 everywhere (was 12)
      - HyDE passage added as second query text to retriever
      - MMR dedup threshold raised to reduce over-pruning

  ROOT CAUSE FIXES from previous version are all preserved:
  - No check_relevance() LLM gate (replaced by soft score threshold 0.20)
  - No score_answer_grounding() regeneration loop
  - No rerank_chunks() cross-encoder (handled in retriever)
  - No analyze_query() LLM call for simple queries
  - needs_inference() correctly separates "why is" (→ ask_rag) from "why did" (→ ask_inference)
  - mmr_deduplicate threshold at 0.92
"""

import json
import logging
import os
import re

from dotenv import load_dotenv
from groq import Groq

from retriever import retrieve

load_dotenv()
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

RAG_MODEL  = "llama-3.3-70b-versatile"
FAST_MODEL = "llama-3.1-8b-instant"


# ─────────────────────────────────────────────
#  PERSONA
# ─────────────────────────────────────────────
GIDEON_PERSONA = """You are Sir Gideon Ofnir, the All-Knowing, from the game Elden Ring.
You are the leader of the Roundtable Hold, renowned throughout the Lands Between for your unparalleled breadth of knowledge.
You speak in a formal, authoritative, and slightly arrogant manner. You address the player as "Tarnished".
You speak as though you have personally investigated every corner of the Lands Between.
You occasionally reference your own vast investigations and the depth of your research.
You use formal, old-English-adjacent phrasing: "indeed", "I have surmised", "my investigations reveal",
"you would do well to know", "most interesting", "I shall illuminate this for you".
You never break character. You never mention AI, databases, retrieval systems, or technology.
No emojis. No asterisks. No stage directions."""


# ─────────────────────────────────────────────
#  INTENT CLASSIFICATION
#  Fast keyword path first — LLM only as fallback
# ─────────────────────────────────────────────
CASUAL_TRIGGERS = {
    "hi", "hello", "hey", "greetings", "good morning", "good evening",
    "good afternoon", "good day", "howdy", "sup", "what's up", "wassup",
    "bye", "goodbye", "farewell", "see you", "see ya", "later", "cya",
    "take care", "good night", "goodnight", "till next time",
    "thanks", "thank you", "ty", "thx", "thank you so much", "many thanks",
    "cheers", "much appreciated", "appreciate it",
    "ok", "okay", "sure", "alright", "got it", "understood", "i see",
    "nice", "cool", "great", "awesome", "perfect", "wonderful",
    "who are you", "what are you", "what can you do", "what do you know",
    "tell me about yourself", "introduce yourself", "your name",
    "how are you", "how do you do", "are you well", "how are you doing",
    "you ok", "you okay", "how's it going", "how goes it",
    "lol", "lmao", "haha", "hehe", "interesting", "wow", "oh", "ah",
    "yes", "no", "nope", "yep", "yeah", "nah",
}

# Improvement #3 / #5: expanded with Shadow of the Erdtree content
LORE_SIGNALS = [
    "elden ring", "tarnished", "erdtree", "marika", "malenia", "miquella",
    "radahn", "rennala", "rykard", "mohg", "morgott", "godfrey", "godwyn",
    "melina", "torrent", "fia", "dung eater", "goldmask", "corhyn",
    "hewg", "nepheli", "rogier", "blaidd", "ranni", "nokron", "liurnia",
    "caelid", "altus", "farum azula", "mountaintops", "consecrated snowfield",
    "leyndell", "stormveil", "raya lucaria", "volcano manor",
    "night of the black knives", "black knife", "frenzied flame", "age of",
    "greater will", "outer god", "crucible", "elden beast", "gloam-eyed",
    "deathbird", "fire giant", "roundtable", "finger maiden", "two fingers",
    "three fingers", "serosh", "placidusax", "dragonlord", "astel",
    "scarlet rot", "frenzy", "destined death", "rune of death",
    "golden order", "spirit ash", "incantation", "sorcery", "ash of war",
    "talisman", "stonesword key", "remembrance", "messmer", "hornsent",
    "shadow of the erdtree", "land of shadow", "enir-ilim", "haligtree",
    "millicent", "gowry", "cleanrot", "formless mother", "mohgwyn",
    "deeproot depths", "siofra", "ainsel", "nokstella",
    # Shadow of the Erdtree additions
    "bayle", "igon", "thiollier", "moore", "leda", "needle knight",
    "ansbach", "florissax", "dancing lion", "divine beast", "midra",
    "chaos flame", "frenzy flame", "scadutree", "scadutree avatar",
    "St. Trina", "st trina", "trina", "rellana", "twin moon knight",
    "count ymir", "ymir", "metyr", "gaius", "commander gaius",
    "romina", "jagged peak", "cerulean coast", "realm of shadow",
]

MECHANIC_SIGNALS = [
    "how do i", "how to", "best build", "where to find", "farming",
    "cheese", "easy way", "tips for", "guide to", "how to upgrade",
    "level up", "stats", "poise", "equip load", "flask uses",
    "what level", "best weapon for", "how many", "how do you beat",
    "how do i beat", "what does damage", "how much damage",
]

# Improvement #5: rescue vague queries that contain lore entities
# from being misrouted as OFF_TOPIC by the LLM classifier
LORE_RESCUE_PATTERNS = [
    r"\b(malenia|ranni|miquella|marika|radahn|mohg|morgott|rykard|melina|godwyn|godfrey)\b",
    r"\b(elden ring|great rune|erdtree|roundtable|tarnished|grace|two fingers|three fingers)\b",
    r"\b(limgrave|caelid|liurnia|altus|leyndell|farum azula|haligtree|mountaintops)\b",
    r"\b(night of the black knives|the shattering|fell god|crucible|age of)\b",
    r"\b(frenzied flame|gloam.?eyed|dragonlord|fire giant|ancestor spirit)\b",
    r"\b(black knife|rune of death|godskin|maliketh|placidusax)\b",
    r"\b(messmer|bayle|thiollier|leda|ansbach|florissax|midra|scadutree|rellana)\b",
    r"\b(shadow of the erdtree|land of shadow|realm of shadow|st\.?\s*trina)\b",
]

# Improvement #3: lore sub-category detection
LORE_SUBCATEGORY_PATTERNS = {
    "character": ["who is", "tell me about", "what is the story of", "history of", "background of"],
    "location":  ["where is", "what is in", "area of", "region", "describe the place", "what can be found in"],
    "item":      ["what does", "what is the", "weapon", "armor", "talisman", "ash of war", "item description"],
    "event":     ["what happened", "when did", "night of", "the shattering", "what was the"],
    "theory":    ["why did", "what if", "could it be", "theory", "hidden meaning", "is it true that", "speculate"],
}


def classify_lore_subtype(question: str) -> str:
    q = question.lower()
    for subtype, patterns in LORE_SUBCATEGORY_PATTERNS.items():
        if any(p in q for p in patterns):
            return subtype
    return "lore"


def classify_intent(question: str, chat_history: list | None = None) -> str:
    """
    Returns: casual | lore | mechanics | theory | off_topic

    Improvement #5: LORE_RESCUE_PATTERNS prevent vague lore queries from
    being misrouted as off_topic. Follow-up detection uses history context.
    Fast keyword path handles ~90% of queries without an LLM call.
    """
    q = question.strip().lower().rstrip("?.!")

    # Exact casual match
    if q in CASUAL_TRIGGERS:
        return "casual"
    for trigger in CASUAL_TRIGGERS:
        if q.startswith(trigger + " ") or q.endswith(" " + trigger):
            return "casual"

    q_full = question.lower()

    # Improvement #5: rescue known-entity queries before any other routing
    for pat in LORE_RESCUE_PATTERNS:
        if re.search(pat, q_full):
            if any(m in q_full for m in MECHANIC_SIGNALS):
                return "mechanics"
            if any(t in q_full for t in ["why did", "theory", "could it be", "what if", "speculate"]):
                return "theory"
            return "lore"

    # Standard lore signal check
    if any(signal in q_full for signal in LORE_SIGNALS):
        if any(m in q_full for m in MECHANIC_SIGNALS):
            return "mechanics"
        if any(t in q_full for t in ["why did", "theory", "could it be", "what if", "speculate"]):
            return "theory"
        return "lore"

    # Generic mechanics phrasing
    if any(m in q_full for m in MECHANIC_SIGNALS):
        return "mechanics"

    # Improvement #5: short follow-up in a lore conversation → assume lore
    if chat_history and len(q.split()) <= 6:
        last_user = next(
            (m["content"] for m in reversed(chat_history) if m["role"] == "user"),
            ""
        )
        for pat in LORE_RESCUE_PATTERNS:
            if re.search(pat, last_user.lower()):
                return "lore"

    # Generic lore question words (probably ER in this context)
    lore_question_words = [
        "who is", "what is", "who was", "what was", "what are",
        "who are", "tell me about", "explain", "what happened",
        "why is", "why was", "where is", "where was",
    ]
    if any(q_full.startswith(lw) for lw in lore_question_words):
        return "lore"

    # Fallback: LLM classifier (only genuinely ambiguous cases reach here)
    try:
        prompt = f"""Classify this message into exactly one category.
MESSAGE: "{question}"

Categories:
- CASUAL: greetings, farewells, thanks, filler, questions about who you are
- LORE: Elden Ring story — characters, bosses, items, areas, events, lore, narrative
- MECHANICS: how to play Elden Ring — builds, stats, farming, combat, item locations
- THEORY: speculative questions about Elden Ring lore, fan theories
- OFF_TOPIC: completely unrelated to Elden Ring (cooking, sports, math, coding, etc.)

Important: Any question referencing Elden Ring content — even vaguely — is LORE, not OFF_TOPIC.

One word only: CASUAL, LORE, MECHANICS, THEORY, or OFF_TOPIC"""

        response = client.chat.completions.create(
            model=FAST_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10,
        )
        result = response.choices[0].message.content.strip().upper()
        if "CASUAL"   in result: return "casual"
        if "MECHANIC" in result: return "mechanics"
        if "THEORY"   in result: return "theory"
        if "OFF"      in result: return "off_topic"
        return "lore"
    except Exception as e:
        log.warning("classify_intent LLM failed, defaulting to lore: %s", e)
        return "lore"


# ─────────────────────────────────────────────
#  FOLLOW-UP FUSION
#  Improvement #4: entity co-reference + optional LLM rewrite
# ─────────────────────────────────────────────
FOLLOWUP_PRONOUNS = [
    "he", "she", "they", "it", "his", "her", "their", "its",
    "him", "them", "this", "that", "these", "those",
    "the same", "as well", "also", "what about", "and what",
]


def _extract_lore_entities_from_text(text: str) -> list[str]:
    """Return any LORE_SIGNALS found in the given text."""
    t = text.lower()
    return [sig for sig in LORE_SIGNALS if sig in t]


def fuse_followup(question: str, chat_history: list) -> str:
    """
    Improvement #4: Upgraded follow-up detection.
    Triggers on pronouns OR on short queries (≤5 words) where the last
    assistant turn mentioned a lore entity (entity co-reference).
    Uses one fast-model LLM call to rewrite cleanly when triggered.
    """
    if not chat_history:
        return question

    q_lower = question.lower().strip()
    words = q_lower.split()

    # Pronoun-based follow-up
    pronoun_hit = any(q_lower.startswith(p) for p in FOLLOWUP_PRONOUNS)

    # Improvement #4: entity co-reference — short query after a lore answer
    coref_hit = False
    if not pronoun_hit and len(words) <= 5:
        last_assistant = next(
            (m["content"] for m in reversed(chat_history) if m["role"] == "assistant"),
            ""
        )
        if _extract_lore_entities_from_text(last_assistant):
            coref_hit = True

    if not pronoun_hit and not coref_hit:
        return question

    # Build minimal history context (last 3 turns)
    recent = chat_history[-6:]
    history_text = "\n".join(
        f"{'User' if m['role'] == 'user' else 'Gideon'}: {m['content']}"
        for m in recent
    )

    try:
        prompt = f"""Rewrite the FOLLOW-UP question to be fully self-contained, using context from the conversation.
Return ONLY the rewritten question. No explanation, no quotes, no preamble.

CONVERSATION:
{history_text}

FOLLOW-UP: {question}
REWRITTEN:"""

        resp = client.chat.completions.create(
            model=FAST_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=60,
        )
        rewritten = resp.choices[0].message.content.strip().strip('"')
        if len(rewritten) > 5:
            log.info("Follow-up fused: %r → %r", question, rewritten)
            return rewritten
    except Exception as e:
        log.warning("fuse_followup LLM failed: %s", e)

    # Fallback: naive prefix with last user question
    last_user = next(
        (m["content"] for m in reversed(chat_history) if m["role"] == "user"),
        ""
    )
    if last_user:
        return f"{last_user} — {question}"

    return question


# ─────────────────────────────────────────────
#  MULTI-HOP DETECTION
# ─────────────────────────────────────────────
MULTI_HOP_SIGNALS = [
    " and also ", " and what ", " and who ", " and where ",
    " both ", " as well as ", " in addition ", " furthermore ",
    " relationship between ", " compare ",
]


def is_multi_hop(question: str) -> bool:
    q = question.lower()
    # Two or more known lore entities is also a multi-hop signal
    found_entities = _extract_lore_entities_from_text(q)
    if len(found_entities) >= 2:
        return True
    return any(sig in q for sig in MULTI_HOP_SIGNALS)


def split_multi_hop(question: str) -> list[str]:
    """Split on multi-hop signal words. Returns [question] if unsplittable."""
    q = question.lower()
    for sig in MULTI_HOP_SIGNALS:
        if sig in q:
            parts = question.lower().split(sig.strip(), 1)
            return [p.strip().capitalize() for p in parts if p.strip()]
    return [question]


# ─────────────────────────────────────────────
#  HYDE — Hypothetical Document Embedding
#  Improvement #1: generate a fake lore passage as an extra dense query
# ─────────────────────────────────────────────
def generate_hyde_passage(question: str) -> str | None:
    """
    Generate a short hypothetical lore passage that would answer the question.
    Used as a second query text to retrieve chunks that match the answer style
    rather than just the question style.
    Returns None if the question is too short/casual to benefit from HyDE.
    """
    if len(question.split()) < 4:
        return None

    try:
        prompt = f"""Write a short Elden Ring lore passage (2-3 sentences) that directly answers this question.
Write it as if it were a FromSoftware item description or wiki entry. Be specific and factual-sounding.
Return ONLY the passage. No preamble.

QUESTION: {question}
PASSAGE:"""

        resp = client.chat.completions.create(
            model=FAST_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.25,
            max_tokens=100,
        )
        passage = resp.choices[0].message.content.strip()
        log.info("HyDE passage generated: %r", passage[:80])
        return passage
    except Exception as e:
        log.warning("generate_hyde_passage failed: %s", e)
        return None


# ─────────────────────────────────────────────
#  HALLUCINATION GUARD
#  Improvement #2: source grounding heuristic
# ─────────────────────────────────────────────
def source_grounding_score(answer: str, context: str) -> float:
    """
    Heuristic: what fraction of capitalised proper-noun-like tokens in the
    answer appear in the source context?
    Returns 0.0–1.0. Below 0.40 → re-ask at temperature=0 with stricter prompt.
    """
    # Extract capitalised tokens (likely proper nouns / names)
    answer_entities = set(re.findall(r"\b[A-Z][a-z]{2,}\b", answer))
    # Remove common non-lore words
    common = {"Indeed", "Most", "Tarnished", "Lands", "Between", "However",
               "Furthermore", "Moreover", "Nevertheless", "Therefore", "Also",
               "Though", "Yet", "For", "But", "And", "The", "This", "That"}
    answer_entities -= common

    if not answer_entities:
        return 1.0  # no named claims to verify

    ctx_lower = context.lower()
    hits = sum(1 for e in answer_entities if e.lower() in ctx_lower)
    score = hits / len(answer_entities)
    log.info("Grounding score: %.2f (%d/%d entities found in context)",
             score, hits, len(answer_entities))
    return score


# ─────────────────────────────────────────────
#  MMR DEDUPLICATION
#  Improvement #1/#6: threshold raised to 0.92
# ─────────────────────────────────────────────
def mmr_deduplicate(chunks: list[dict], threshold: float = 0.92) -> list[dict]:
    """
    Remove near-duplicate chunks.
    Threshold 0.92 (was 0.90 in fixed pipeline, 0.82 before that).
    Higher threshold = keep more diverse chunks, less aggressive pruning.
    """
    seen_texts: list[str] = []
    result: list[dict] = []

    for chunk in chunks:
        words = set(chunk["text"].lower().split())
        duplicate = False
        for seen in seen_texts:
            seen_words = set(seen.split())
            if not words or not seen_words:
                continue
            overlap = len(words & seen_words) / max(len(words), len(seen_words))
            if overlap >= threshold:
                duplicate = True
                break
        if not duplicate:
            result.append(chunk)
            seen_texts.append(chunk["text"].lower())

    return result


# ─────────────────────────────────────────────
#  CONTEXT / HISTORY BUILDERS
# ─────────────────────────────────────────────
def build_grounded_context(chunks: list[dict]) -> str:
    lines = []
    for i, chunk in enumerate(chunks, 1):
        lines.append(
            f"[SOURCE {i} — {chunk['name']} | category: {chunk['category']} | area: {chunk['area']}]"
        )
        lines.append(chunk["text"])
        lines.append("")
    return "\n".join(lines)


def build_history_text(chat_history: list, max_turns: int = 6) -> str:
    if not chat_history:
        return ""
    lines = ["RECENT CONVERSATION:"]
    for msg in chat_history[-max_turns:]:
        role = "Tarnished" if msg["role"] == "user" else "Gideon"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines) + "\n\n"


# ─────────────────────────────────────────────
#  RESPONSE HANDLERS
# ─────────────────────────────────────────────
def ask_casual(question: str, chat_history: list) -> str:
    history_text = build_history_text(chat_history)
    prompt = f"""{GIDEON_PERSONA}

The Tarnished is making casual conversation. Respond naturally but stay in character.
Acknowledge warmly in Gideon's formal, arrogant way. 2-3 sentences.
Invite them to ask about lore or their path.

{history_text}TARNISHED: {question}
GIDEON:"""
    try:
        response = client.chat.completions.create(
            model=RAG_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=180,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        log.error("ask_casual failed: %s", e)
        return "Ah, a Tarnished approaches. You would do well to ask me of the Lands Between, for few know its secrets as I do."


def ask_off_topic(question: str, chat_history: list) -> str:
    history_text = build_history_text(chat_history)
    prompt = f"""{GIDEON_PERSONA}

The Tarnished has asked about something outside the Lands Between.
You MUST:
1. Answer the question CORRECTLY first.
2. Connect your answer to Elden Ring lore in a clever, natural way.
3. 3-4 sentences. Never refuse. Always answer, then weave lore in.

Example — "What is 2+2?":
"Four, Tarnished — as immutable as the four fingers of the Crucible that shaped all life before the Erdtree claimed dominion."

{history_text}TARNISHED: {question}
GIDEON:"""
    try:
        response = client.chat.completions.create(
            model=RAG_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.65,
            max_tokens=250,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        log.error("ask_off_topic failed: %s", e)
        return "A most curious question from beyond the Lands Between. My investigations have not encompassed such matters, yet I suspect even this truth echoes something of our great struggle."


def ask_mechanics(question: str, chat_history: list) -> str:
    history_text = build_history_text(chat_history)
    prompt = f"""{GIDEON_PERSONA}

The Tarnished seeks guidance on the practical arts of combat and survival in the Lands Between.
Answer their gameplay question with Gideon's arrogance and formality.
You may speak from general Elden Ring knowledge here.
3-5 sentences. Stay in character.

{history_text}TARNISHED: {question}
GIDEON:"""
    try:
        response = client.chat.completions.create(
            model=RAG_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        log.error("ask_mechanics failed: %s", e)
        return "The path of combat in the Lands Between demands patience and observation, Tarnished. Study your foe before striking."


def ask_no_context(question: str, chat_history: list) -> str:
    history_text = build_history_text(chat_history)
    prompt = f"""{GIDEON_PERSONA}

Your investigation records contain no verified entry on this specific topic.
Admit this in Gideon's voice without inventing ANY lore detail.
State that even your vast investigations have not uncovered this.
2 sentences maximum.

{history_text}TARNISHED: {question}
GIDEON:"""
    try:
        response = client.chat.completions.create(
            model=RAG_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=120,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        log.error("ask_no_context failed: %s", e)
        return "Most curious, Tarnished — even my vast investigations have uncovered no record of this particular matter."


def ask_inference(question: str, context: str, chat_history: list) -> str:
    """Past-causation questions — reason across sources rather than read directly."""
    history_text = build_history_text(chat_history)
    prompt = f"""{GIDEON_PERSONA}

The Tarnished asks a question whose answer is IMPLIED by the lore, not stated explicitly.
Use the sources to REASON toward an answer.

Rules:
1. Use the sources as your foundation — do not ignore them.
2. You MAY draw logical inferences the sources strongly support.
3. Frame inferences: "I have surmised", "my analysis suggests", "it stands to reason".
4. Do NOT invent facts with no basis in the sources whatsoever.
5. 3-5 sentences. Do not over-explain your uncertainty.
6. If inference is impossible, say so in ONE sentence.

{history_text}RETRIEVED SOURCES:
{context}

TARNISHED ASKS: {question}

Reason from the sources. Speak as Gideon. Be concise.
GIDEON:"""

    try:
        response = client.chat.completions.create(
            model=RAG_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.35,
            max_tokens=350,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        log.error("ask_inference failed: %s", e)
        return ask_no_context(question, chat_history)


# ─────────────────────────────────────────────
#  INFERENCE ROUTING
#  FIX preserved: "why is/does" → ask_rag (direct fact in DB)
#                 "why did/was" → ask_inference (past causation, needs reasoning)
# ─────────────────────────────────────────────
INFERENCE_QUESTION_PATTERNS = [
    "why did", "why was", "why were", "why would", "why could",
    "how did", "how was", "how were",
    "what caused", "what made", "what drove",
    "how did she", "how did he", "how did they",
    "what does it mean", "what does this mean",
    "what does her", "what does his", "what does their",
]

DIRECT_FACT_PATTERNS = [
    "why is", "why does", "why are",
    "what color", "what colour",
    "what does she look like", "what does he look like",
    "what does it look like",
]


def needs_inference(question: str) -> bool:
    q = question.lower().strip()
    if any(q.startswith(pat) for pat in DIRECT_FACT_PATTERNS):
        log.info("needs_inference: False (direct-fact) → ask_rag")
        return False
    return any(q.startswith(pat) for pat in INFERENCE_QUESTION_PATTERNS)


# ─────────────────────────────────────────────
#  RAG ANSWER — with subtype-aware prompt
#  Improvement #3: character/location/item/event/theory get tailored prompts
# ─────────────────────────────────────────────
def ask_rag(question: str, context: str, chat_history: list,
            intent: str = "lore", lore_subtype: str = "lore",
            strict: bool = False) -> str:
    """
    Improvement #3: lore_subtype changes the focus instruction.
    Improvement #2: strict=True used for grounding re-ask at temperature=0.
    """
    history_text = build_history_text(chat_history)

    subtype_guidance = {
        "character": "Focus on the character's identity, motivations, relationships, and fate.",
        "location":  "Describe the area, its significance, its inhabitants, and notable events there.",
        "item":      "Describe the item's origin, properties, lore significance, and any related characters.",
        "event":     "Narrate what occurred, who was involved, and what the consequences were.",
        "theory":    "Engage with the speculation. Clearly distinguish confirmed lore from reasonable inference.",
    }.get(lore_subtype, "Answer fully from the sources provided.")

    theory_addendum = ""
    if intent == "theory":
        theory_addendum = (
            "\nThis is a speculative question. After grounding your answer in sources, "
            "you MAY offer Gideon's own scholarly interpretation — clearly framed as "
            "'I have theorised' or 'my own analysis leads me to believe'. One sentence max.\n"
        )

    strict_note = (
        "\nSTRICT MODE: A previous answer contained names not verified in sources. "
        "This time, mention ONLY names and places that appear word-for-word in the sources below.\n"
        if strict else ""
    )

    prompt = f"""{GIDEON_PERSONA}

════════════════════════════════════════════
HALLUCINATION PREVENTION — ABSOLUTE RULES
════════════════════════════════════════════
{subtype_guidance}
{theory_addendum}{strict_note}
1. Use ONLY information explicitly stated in the SOURCES. Nothing else.
2. Do NOT add names, dates, events, or relationships not in the sources.
3. Do NOT use general Elden Ring knowledge — only what is written in sources below.
4. If sources only partially answer, answer partially and STOP — do not pad.
5. If a detail appears in only one source, say "my records suggest" — not absolute fact.
6. If sources conflict, say "most curious — accounts differ on this matter".
7. NEVER invent character names, locations, events, or relationships.
8. Answer in 3-5 sentences. Formal and authoritative. Stay in character.
9. If you cannot answer from sources, say so in ONE sentence only.

Confidence calibration:
- Fact in MULTIPLE sources → state confidently
- Fact in ONE source → "my records suggest" or "it is noted in my investigations"
- Sources CONFLICT → "most curious — accounts differ on this matter"
════════════════════════════════════════════

{history_text}RETRIEVED SOURCES:
{context}

TARNISHED ASKS: {question}

Answer using ONLY the sources. Speak as Gideon. Stop when sources run out.
GIDEON:"""

    temperature = 0.0 if strict else 0.15
    response = client.chat.completions.create(
        model=RAG_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()


def ask_multi_hop(sub_questions: list[str], chat_history: list) -> tuple[str, list]:
    """Answer each sub-question independently then synthesize."""
    sub_answers = []
    all_sources = []

    for sub_q in sub_questions:
        # Improvement #1: top_k=20 for sub-questions too
        chunks = retrieve(sub_q, top_k=20)
        if not chunks:
            continue
        context = build_grounded_context(chunks)
        history_text = build_history_text(chat_history)
        prompt = f"""{GIDEON_PERSONA}

Answer ONLY using the sources below. One focused paragraph. Stay in character.

{history_text}SOURCES:
{context}

QUESTION: {sub_q}
GIDEON:"""
        try:
            response = client.chat.completions.create(
                model=RAG_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.15,
                max_tokens=250,
            )
            sub_answers.append(response.choices[0].message.content.strip())
            all_sources.extend(f"{c['name']} ({c['category']}, {c['area']})" for c in chunks)
        except Exception as e:
            log.warning("multi-hop sub-question failed: %s", e)

    if not sub_answers:
        return "", []

    combined = "\n\n".join(f"Part {i+1}: {a}" for i, a in enumerate(sub_answers))
    synthesis_prompt = f"""{GIDEON_PERSONA}

You have investigated multiple facets of the Tarnished's question. Below are your findings.
Weave them into a single flowing formal response. Do not number the parts or use headers.
5-8 sentences total. Maintain Gideon's voice throughout.

FINDINGS:
{combined}

GIDEON:"""
    try:
        response = client.chat.completions.create(
            model=RAG_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip(), list(set(all_sources))
    except Exception as e:
        log.warning("multi-hop synthesis failed: %s", e)
        return sub_answers[0] if sub_answers else "", list(set(all_sources))


# ─────────────────────────────────────────────
#  MAIN ENTRY POINT
# ─────────────────────────────────────────────
def ask(question: str, chat_history: list = []) -> tuple[str, list, str]:
    """
    Routes the question and returns (answer, sources, mode).
    mode: casual | off_topic | mechanics | rag | rag_multi_hop | no_context
    """

    # ── Step 1: Intent (rescue patterns → fast keyword → LLM fallback) ───────
    intent = classify_intent(question, chat_history)
    log.info("Intent: %s | Question: %r", intent, question[:80])

    if intent == "casual":
        return ask_casual(question, chat_history), [], "casual"

    if intent == "off_topic":
        return ask_off_topic(question, chat_history), [], "off_topic"

    if intent == "mechanics":
        return ask_mechanics(question, chat_history), [], "mechanics"

    # ── Step 2: Lore sub-category (Improvement #3) ───────────────────────────
    lore_subtype = classify_lore_subtype(question)
    log.info("Lore subtype: %s", lore_subtype)

    # ── Step 3: Follow-up fusion (Improvement #4) ────────────────────────────
    fused_query = fuse_followup(question, chat_history)

    # ── Step 4: Multi-hop routing ─────────────────────────────────────────────
    if is_multi_hop(fused_query):
        sub_questions = split_multi_hop(fused_query)
        if len(sub_questions) >= 2:
            answer, sources = ask_multi_hop(sub_questions, chat_history)
            if answer:
                return answer, sources, "rag_multi_hop"

    # ── Step 5: HyDE — generate hypothetical passage (Improvement #1) ────────
    hyde_passage = generate_hyde_passage(fused_query)

    # ── Step 6: Retrieval (top_k=20, Improvement #1/#6) ──────────────────────
    chunks = retrieve(fused_query, top_k=20)

    # If HyDE produced a passage, retrieve for it too and merge
    if hyde_passage:
        hyde_chunks = retrieve(hyde_passage, top_k=10)
        # Add Hyde chunks that aren't already in primary results (by text hash)
        existing_texts = {c["text"][:80] for c in chunks}
        for hc in hyde_chunks:
            if hc["text"][:80] not in existing_texts:
                chunks.append(hc)
                existing_texts.add(hc["text"][:80])
        log.info("HyDE added %d new chunks", len(hyde_chunks) - len(existing_texts - {c["text"][:80] for c in chunks}))

    if not chunks:
        log.warning("No chunks retrieved for: %r", fused_query)
        return ask_no_context(question, chat_history), [], "no_context"

    # ── Step 7: Soft relevance gate (score-based, no LLM call) ───────────────
    top_score = chunks[0].get("score", 1.0)
    log.info("Top chunk score: %.3f | chunk count: %d", top_score, len(chunks))

    if top_score < 0.20:
        log.warning("Top score %.3f below threshold — returning no_context", top_score)
        return ask_no_context(question, chat_history), [], "no_context"

    # ── Step 8: MMR deduplication (threshold=0.92, Improvement #1/#6) ────────
    chunks = mmr_deduplicate(chunks, threshold=0.92)

    # ── Step 9: Build context and generate answer ─────────────────────────────
    context = build_grounded_context(chunks)

    try:
        if needs_inference(question):
            log.info("Routing to ask_inference (past-causation)")
            answer = ask_inference(question, context, chat_history)
        else:
            log.info("Routing to ask_rag (direct fact/lore) — subtype: %s", lore_subtype)
            answer = ask_rag(fused_query, context, chat_history,
                             intent=intent, lore_subtype=lore_subtype)
    except Exception as e:
        log.error("ask_rag/inference failed: %s", e)
        return ask_no_context(question, chat_history), [], "no_context"

    # ── Step 10: Hallucination guard (Improvement #2) ────────────────────────
    grounding = source_grounding_score(answer, context)
    if grounding < 0.40:
        log.warning("Low grounding score %.2f — re-asking in strict mode", grounding)
        try:
            answer = ask_rag(fused_query, context, chat_history,
                             intent=intent, lore_subtype=lore_subtype, strict=True)
        except Exception as e:
            log.error("Strict re-ask failed: %s", e)

    sources = [f"{c['name']} ({c['category']}, {c['area']})" for c in chunks]
    return answer, sources, "rag"


# ─────────────────────────────────────────────
#  CLI TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  SIR GIDEON OFNIR — THE ALL-KNOWING")
    print("  Elden Ring RAG Bot — Upgraded Pipeline")
    print("=" * 60)

    history = []
    test_questions = [
        "hi",
        "who are you?",
        "What is 2+2?",
        "Who is Malenia?",
        "What is Miquella's plan?",
        "Who is the Gloam-Eyed Queen?",
        "What is Serosh?",
        "What happened on the Night of the Black Knives?",
        "What is the Frenzied Flame?",
        "Why is Ranni blue?",                           # direct fact → ask_rag
        "Why did Ranni kill Godwyn?",                   # past causation → ask_inference
        "Who was her twin?",                            # follow-up fusion test
        "Tell me about Malenia and also about Godwyn",  # multi-hop test
        "how do i beat radahn",                         # mechanics test
        "Who is Messmer?",                              # Shadow DLC test
        "What is Midra?",                               # Shadow DLC test
    ]

    for q in test_questions:
        print(f"\nTarnished : {q}")
        answer, sources, mode = ask(q, history)
        print(f"Gideon [{mode:14s}]: {answer[:220]}{'...' if len(answer) > 220 else ''}")
        if sources:
            print(f"  └─ Sources: {sources[:3]}")
        history.append({"role": "user", "content": q})
        history.append({"role": "assistant", "content": answer})

    print("\n" + "=" * 60)
    print("Done.")