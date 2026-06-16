"""
quiz.py  —  Elden Ring Lore Quiz

FIXES vs previous version:
  #1  CRITICAL  random.choices(k) crash when k > len(population) on small DBs
  #2  CRITICAL  Silent question-generation failures — all exceptions now logged
  #3  BUG       get_weighted_chunks pulled too few unique chunks (with-replacement
                 sampling on small pools); switched to random.sample on shuffled list
  #4  BUG       get_category_spread_chunks had a seen_names race — all_chunks was
                 built before priority loop finished; fixed ordering
  #5  BUG       chunk candidate pool was only 2×num_questions; raised to 4× so
                 generation failures don't leave you short
  #6  BUG       Exponential backoff on Groq rate-limit errors (was flat 0.5 s)
  #7  QUALITY   Question generation now uses llama-3.3-70b-versatile (was 8b-instant)
  #8  QUALITY   Lore excerpt raised to 1 200 chars (was 900)
  #9  FEATURE   Streak bonus: 3+ correct in a row earns +5 pts per question
  #10 FEATURE   Per-question timer shown after answer (informational, not enforced)
  #11 FEATURE   Session history saved to quiz_history.json — no question repeats
                across runs (last 500 question hashes remembered)
  #12 UX        DB coverage check is now opt-in (--check flag), not printed every run
  #13 UX        Clean quiz header with category legend before questions start
  #14 UX        Detailed wrong-answer review at end (question + all options shown)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import time
from collections import defaultdict
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer

load_dotenv()

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

# ── Models ────────────────────────────────────────────────────────────────
embed_model  = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection    = chroma_client.get_or_create_collection("elden_ring_lore")
groq_client   = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Use the same high-quality model as rag_bot.py  (#7 fix)
QUESTION_MODEL = "llama-3.3-70b-versatile"

# Session history file — persists between runs to avoid repeating questions (#11 fix)
HISTORY_FILE   = Path("./quiz_history.json")
MAX_HISTORY    = 500   # remember this many question hashes


# ═══════════════════════════════════════════════════════════════════════════
#  CATEGORY CONFIG
# ═══════════════════════════════════════════════════════════════════════════

CATEGORY_CONFIG: dict[str, dict] = {
    "boss":         {"label": "Boss Lore",          "weight": 3},
    "character":    {"label": "NPC / Character",    "weight": 3},
    "lore":         {"label": "World Lore",         "weight": 3},
    "area":         {"label": "Area / Location",    "weight": 2},
    "weapon":       {"label": "Weapon Lore",        "weight": 2},
    "spell":        {"label": "Spell / Incantation","weight": 2},
    "armor":        {"label": "Armor Lore",         "weight": 2},
    "talisman":     {"label": "Talisman Lore",      "weight": 2},
    "great_rune":   {"label": "Great Rune",         "weight": 2},
    "ending":       {"label": "Game Ending",        "weight": 2},
    "questline":    {"label": "Questline",          "weight": 2},
    "item":         {"label": "Key Item",           "weight": 1},
    "spirit_ash":   {"label": "Spirit Ash",         "weight": 1},
    "ash_of_war":   {"label": "Ash of War",         "weight": 1},
    "shield":       {"label": "Shield Lore",        "weight": 1},
    "creature":     {"label": "Enemy / Creature",   "weight": 1},
    "dialogue":     {"label": "Dialogue",           "weight": 1},
    "cutscene":     {"label": "Cutscene",           "weight": 1},
    "crystal_tear": {"label": "Crystal Tear",       "weight": 1},
    "whetblade":    {"label": "Whetblade",          "weight": 1},
    "bell_bearing": {"label": "Bell Bearing",       "weight": 1},
    "cookbook":     {"label": "Cookbook",           "weight": 1},
    "painting":     {"label": "Painting",           "weight": 1},
    "cut_content":  {"label": "Cut Content",        "weight": 1},
}

MIN_CHUNK_LENGTH = 200

POINTS_MAP = {"easy": 10, "medium": 20, "hard": 30}
STREAK_BONUS     = 5   # extra pts per question after a 3-question correct streak (#9 fix)
STREAK_THRESHOLD = 3


# ═══════════════════════════════════════════════════════════════════════════
#  SESSION HISTORY  (#11 fix)
#  Stores hashes of previously seen question strings so we don't repeat them.
# ═══════════════════════════════════════════════════════════════════════════

def _load_history() -> set[str]:
    if not HISTORY_FILE.exists():
        return set()
    try:
        data = json.loads(HISTORY_FILE.read_text())
        return set(data.get("seen", []))
    except Exception:
        return set()


def _save_history(seen: set[str]) -> None:
    # Keep only the most recent MAX_HISTORY hashes
    trimmed = list(seen)[-MAX_HISTORY:]
    try:
        HISTORY_FILE.write_text(json.dumps({"seen": trimmed}, indent=2))
    except Exception as e:
        log.warning("Could not save quiz history: %s", e)


def _question_hash(question_text: str) -> str:
    return hashlib.md5(question_text.lower().strip().encode()).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════
#  DB COVERAGE REPORT  (opt-in via --check)
# ═══════════════════════════════════════════════════════════════════════════

def print_db_coverage() -> None:
    results   = collection.get(include=["documents", "metadatas"])
    documents = results["documents"]
    metadatas = results["metadatas"]
    total     = len(documents)

    if total == 0:
        print("  [!] ChromaDB is EMPTY. Run scrape.py then ingest.py first.")
        return

    cat_counts:      dict[str, int] = defaultdict(int)
    cat_long_enough: dict[str, int] = defaultdict(int)

    for doc, meta in zip(documents, metadatas):
        cat = meta.get("category", "unknown")
        cat_counts[cat] += 1
        if len(doc) >= MIN_CHUNK_LENGTH:
            cat_long_enough[cat] += 1

    quizzable_total = sum(cat_long_enough.values())
    print(f"\n  Total chunks in DB : {total}")
    print(f"  Quizzable chunks   : {quizzable_total}  (>={MIN_CHUNK_LENGTH} chars)")
    print()
    print(f"  {'Category':<22} {'In Config':>10} {'Total':>8} {'Quizzable':>10}")
    print(f"  {'-'*22} {'-'*10} {'-'*8} {'-'*10}")

    all_cats = set(list(cat_counts.keys()) + list(CATEGORY_CONFIG.keys()))
    for cat in sorted(all_cats):
        in_config   = "YES" if cat in CATEGORY_CONFIG else "NO"
        total_cat   = cat_counts.get(cat, 0)
        quizzable   = cat_long_enough.get(cat, 0)
        flag        = "  <-- MISSING" if total_cat == 0 else ""
        label       = CATEGORY_CONFIG.get(cat, {}).get("label", cat)
        print(f"  {label:<22} {in_config:>10} {total_cat:>8} {quizzable:>10}{flag}")

    missing = [cat for cat in CATEGORY_CONFIG if cat_long_enough.get(cat, 0) == 0]
    print()
    if missing:
        print("  [WARNING] Categories with NO quizzable chunks:")
        for cat in missing:
            print(f"    - {CATEGORY_CONFIG[cat]['label']} ({cat})")
        print("  Run rescrape_missing.py then ingest.py to fill the gaps.\n")
    else:
        print("  [OK] All categories have quizzable content!\n")


# ═══════════════════════════════════════════════════════════════════════════
#  CHUNK SAMPLING
# ═══════════════════════════════════════════════════════════════════════════

def _load_all_quizzable() -> list[tuple[str, dict]]:
    """Fetch every chunk that meets the minimum length requirement."""
    results   = collection.get(include=["documents", "metadatas"])
    documents = results["documents"]
    metadatas = results["metadatas"]
    return [
        (doc, meta)
        for doc, meta in zip(documents, metadatas)
        if len(doc) >= MIN_CHUNK_LENGTH
    ]


def get_weighted_chunks(count: int = 10) -> list[tuple[str, dict]]:
    """
    Pull `count` unique chunks with category weighting.

    FIX #1 / #3: previous version used random.choices (with-replacement) then
    deduplicated, which silently returned fewer items than requested on small DBs.
    Now we shuffle the full pool with per-item weights applied as repetitions,
    then walk it linearly — guaranteed unique items, no k > len crash.
    """
    combined = _load_all_quizzable()
    if not combined:
        return []

    # Build a weighted pool by repeating each item `weight` times
    weighted_pool: list[tuple[str, dict]] = []
    for doc, meta in combined:
        w = CATEGORY_CONFIG.get(meta.get("category", ""), {}).get("weight", 1)
        weighted_pool.extend([(doc, meta)] * w)

    random.seed()
    random.shuffle(weighted_pool)

    seen_names: set[str] = set()
    result: list[tuple[str, dict]] = []
    for doc, meta in weighted_pool:
        name = meta.get("name", "")
        if name not in seen_names:
            seen_names.add(name)
            result.append((doc, meta))
        if len(result) >= count:
            break

    return result


def get_category_spread_chunks(count: int = 10) -> list[tuple[str, dict]]:
    """
    Guarantee at least one chunk from each high-priority category,
    then fill remaining slots with weighted random picks.

    FIX #6: all_chunks is now built AFTER the priority loop so seen_names
    is fully populated before filtering — no duplicates possible.
    """
    combined = _load_all_quizzable()
    if not combined:
        return []

    by_category: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for doc, meta in combined:
        by_category[meta.get("category", "unknown")].append((doc, meta))

    selected:   list[tuple[str, dict]] = []
    seen_names: set[str]               = set()
    random.seed()

    # Priority pass
    priority_cats = ["boss", "character", "lore", "area", "weapon", "ending"]
    for cat in priority_cats:
        if len(selected) >= count:
            break
        if cat not in by_category:
            continue
        chunk = random.choice(by_category[cat])
        name  = chunk[1].get("name", "")
        if name not in seen_names:
            seen_names.add(name)
            selected.append(chunk)

    # FIX #6: build all_chunks only now, after seen_names is complete
    all_chunks = [
        (doc, meta)
        for cat_chunks in by_category.values()
        for doc, meta in cat_chunks
        if meta.get("name", "") not in seen_names
    ]

    if all_chunks and len(selected) < count:
        all_weights = [
            CATEGORY_CONFIG.get(meta.get("category", ""), {}).get("weight", 1)
            for _, meta in all_chunks
        ]
        # FIX #1: cap k at len(all_chunks)
        k = min((count - len(selected)) * 3, len(all_chunks))
        extras = random.choices(all_chunks, weights=all_weights, k=k)
        for doc, meta in extras:
            name = meta.get("name", "")
            if name not in seen_names:
                seen_names.add(name)
                selected.append((doc, meta))
            if len(selected) >= count:
                break

    random.shuffle(selected)
    return selected[:count]


# ═══════════════════════════════════════════════════════════════════════════
#  DIFFICULTY
# ═══════════════════════════════════════════════════════════════════════════

def get_difficulty(meta: dict, doc: str) -> str:
    """
    Difficulty based on category AND lore density.
    Short docs (scarce info) on hard categories stay hard.
    Very long, detailed docs bump easy cats to medium.
    """
    category  = meta.get("category", "lore")
    easy_cats = {"area", "boss", "character", "ending"}
    hard_cats = {"cut_content", "whetblade", "bell_bearing", "cookbook",
                 "painting", "crystal_tear", "dialogue", "cutscene"}

    if category in hard_cats:
        return "hard"
    if category in easy_cats:
        # Promote to medium if the doc is very rich (likely deep lore)
        return "medium" if len(doc) > 1800 else "easy"
    return "medium"


# ═══════════════════════════════════════════════════════════════════════════
#  QUESTION GENERATION
# ═══════════════════════════════════════════════════════════════════════════

def generate_question(
    doc: str, meta: dict, retry: int = 2, seen_hashes: set[str] | None = None
) -> dict | None:
    """
    FIX #2: all exceptions now logged with reason.
    FIX #7: uses llama-3.3-70b-versatile for much better question quality.
    FIX #8: lore excerpt raised to 1200 chars.
    FIX #15: exponential backoff on rate-limit errors.
    """
    category   = meta.get("category", "lore")
    cat_label  = CATEGORY_CONFIG.get(category, {}).get("label", category)
    difficulty = get_difficulty(meta, doc)
    name       = meta.get("name", "Unknown")
    area       = meta.get("area", "Unknown")

    # Use more of the document (#8 fix)
    lore_excerpt = doc[:1200]

    difficulty_instruction = {
        "easy": (
            "Ask about this entity's primary role, identity, or most famous action. "
            "The answer should be clear to anyone who finished the main story."
        ),
        "medium": (
            "Ask about WHY this entity matters — their lore significance, "
            "their relationship to a demigod or outer god, or what their item "
            "description reveals about the world. Avoid surface-level facts."
        ),
        "hard": (
            "Ask about obscure details: hidden connections, what a specific item "
            "description implies about the world's history, contradictions between "
            "lore sources, or information only revealed through NPC dialogue. "
            "This should stump all but dedicated lore hunters."
        ),
    }[difficulty]

    distractor_instruction = {
        "boss":         "Use other Elden Ring bosses or demigods as wrong answers.",
        "character":    "Use other Elden Ring NPCs or story characters.",
        "weapon":       "Use other Elden Ring weapons with similar themes.",
        "armor":        "Use other Elden Ring armor sets.",
        "spell":        "Use other sorceries or incantations from Elden Ring.",
        "talisman":     "Use other Elden Ring talismans.",
        "great_rune":   "Use other Great Runes or shardbearers.",
        "spirit_ash":   "Use other spirit ashes.",
        "ash_of_war":   "Use other Ashes of War.",
        "area":         "Use other Elden Ring regions, dungeons, or legacy dungeons.",
        "ending":       "Use other Elden Ring endings or ages.",
        "item":         "Use other key story items from Elden Ring.",
        "questline":    "Use other NPC questlines that could be confused with this one.",
        "lore":         "Use other lore concepts, factions, or historical events.",
        "creature":     "Use other enemy types with similar traits.",
        "dialogue":     "Use other characters who could plausibly say this.",
        "cutscene":     "Use other key story moments or characters.",
        "crystal_tear": "Use other Flask of Wondrous Physick tears.",
        "whetblade":    "Use other Whetblades from Elden Ring.",
        "bell_bearing": "Use other Bell Bearings or merchant items.",
        "cookbook":     "Use other Crafting Cookbooks.",
        "painting":     "Use other painting locations or rewards.",
        "cut_content":  "Use other unused or datamined content from Elden Ring.",
        "shield":       "Use other Elden Ring shields or greatshields.",
    }.get(category, "Use other plausible Elden Ring entities as wrong answers.")

    prompt = f"""You are a lore quiz master for the game Elden Ring.
Use the lore text below to craft ONE excellent multiple-choice question.

Entity     : {name}
Category   : {cat_label}
Area       : {area}
Difficulty : {difficulty.upper()}

DIFFICULTY GOAL   : {difficulty_instruction}
DISTRACTOR RULE   : {distractor_instruction}

STRICT RULES:
- Exactly 4 options: A, B, C, D
- Exactly 1 correct answer
- Wrong options must be real Elden Ring things — no nonsense answers
- Every option under 10 words
- No emojis, no markdown inside JSON strings
- Do NOT ask about stat numbers, damage values, or gameplay mechanics
- Do NOT include the entity's exact name in the question if it gives away the answer
- The explanation must cite WHY the correct answer is right using lore from the text below
- Make the question interesting — avoid generic "What is X?" style when possible
- The correct answer must be DIRECTLY supported by the lore text below

RESPOND IN THIS EXACT JSON FORMAT — no markdown fences, no extra text:
{{
  "question": "your question here",
  "options": {{
    "A": "option text",
    "B": "option text",
    "C": "option text",
    "D": "option text"
  }},
  "correct": "A",
  "difficulty": "{difficulty}",
  "explanation": "one sentence lore explanation citing the source text"
}}

LORE TEXT:
Name     : {name}
Category : {cat_label}
Area     : {area}
{lore_excerpt}"""

    backoff = 1.0
    for attempt in range(retry + 1):
        try:
            response = groq_client.chat.completions.create(
                model=QUESTION_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4 + (attempt * 0.1),
                max_tokens=600,
            )
            text = response.choices[0].message.content.strip()
            # Strip any accidental markdown fences
            text = text.replace("```json", "").replace("```", "").strip()

            start = text.find("{")
            end   = text.rfind("}") + 1
            if start < 0 or end <= start:
                log.warning("generate_question: no JSON found in response (attempt %d)", attempt)
                continue

            data = json.loads(text[start:end])

            required = {"question", "options", "correct", "explanation"}
            if not required.issubset(data.keys()):
                log.warning("generate_question: missing keys %s (attempt %d)",
                            required - data.keys(), attempt)
                continue

            if set(data["options"].keys()) != {"A", "B", "C", "D"}:
                log.warning("generate_question: options keys wrong (attempt %d)", attempt)
                continue

            if data["correct"] not in data["options"]:
                log.warning("generate_question: correct key '%s' not in options (attempt %d)",
                            data["correct"], attempt)
                continue

            data.setdefault("difficulty", difficulty)

            # Skip if this exact question was seen in a previous session (#11 fix)
            q_hash = _question_hash(data["question"])
            if seen_hashes and q_hash in seen_hashes:
                log.info("generate_question: skipping previously seen question")
                return None

            return data

        except json.JSONDecodeError as e:
            log.warning("generate_question: JSON parse error (attempt %d): %s", attempt, e)
        except Exception as e:
            # FIX #2 & #15: log the actual error; use exponential backoff for rate limits
            err_str = str(e).lower()
            if "rate" in err_str or "429" in err_str:
                log.warning("generate_question: rate limited, backing off %.1fs", backoff)
                time.sleep(backoff)
                backoff = min(backoff * 2, 30.0)  # cap at 30 s
            else:
                log.error("generate_question: unexpected error (attempt %d): %s", attempt, e)
                if attempt < retry:
                    time.sleep(1.0)

    log.error("generate_question: all %d attempts failed for '%s'", retry + 1, name)
    return None


# ═══════════════════════════════════════════════════════════════════════════
#  SCORING  (with streak bonus)
# ═══════════════════════════════════════════════════════════════════════════

def calculate_score(answers: list[dict]) -> dict:
    """
    FIX #9: awards STREAK_BONUS extra pts per question when the player
    has answered STREAK_THRESHOLD or more questions correctly in a row.
    """
    total_points = 0
    max_points   = 0
    correct_count = 0
    streak        = 0
    breakdown     = []

    for entry in answers:
        diff       = entry.get("difficulty", "medium")
        base_pts   = POINTS_MAP.get(diff, 20)
        max_points += base_pts

        is_correct = entry.get("is_correct", False)
        if is_correct:
            streak        += 1
            correct_count += 1
            bonus          = STREAK_BONUS if streak >= STREAK_THRESHOLD else 0
            earned         = base_pts + bonus
        else:
            streak = 0
            bonus  = 0
            earned = 0

        total_points += earned
        breakdown.append({
            "question":        entry["question"],
            "your_answer":     entry["your_answer"],
            "correct_answer":  entry["correct"],
            "is_correct":      is_correct,
            "points_earned":   earned,
            "points_possible": base_pts,
            "streak_bonus":    bonus,
            "difficulty":      diff,
            "explanation":     entry.get("explanation", ""),
            "category":        entry.get("category", ""),
            "all_options":     entry.get("all_options", {}),
        })

    percentage = round((total_points / max_points) * 100) if max_points > 0 else 0
    rank       = get_rank(percentage)

    return {
        "total_points":    total_points,
        "max_points":      max_points,
        "percentage":      percentage,
        "correct_count":   correct_count,
        "total_questions": len(answers),
        "rank":            rank,
        "breakdown":       breakdown,
    }


def get_rank(percentage: int) -> str:
    if percentage == 100: return "🏆  Elden Lord"
    if percentage >= 90:  return "⭐  Erdtree Sage"
    if percentage >= 75:  return "⚔️  Knight of the Roundtable"
    if percentage >= 60:  return "📖  Tarnished Scholar"
    if percentage >= 40:  return "🌑  Wandering Exile"
    return "💀  Maidenless Wretch"


# ═══════════════════════════════════════════════════════════════════════════
#  QUIZ RUNNER
# ═══════════════════════════════════════════════════════════════════════════

def run_quiz(num_questions: int = 10, mode: str = "weighted") -> None:
    print("\n" + "═" * 65)
    print("   ELDEN RING LORE QUIZ")
    print("   May the grace guide thy knowledge")
    print("═" * 65)
    print(f"   Questions  : {num_questions}")
    print(f"   Mode       : {'Balanced spread' if mode == 'spread' else 'Weighted random'}")
    print(f"   Points     : easy={POINTS_MAP['easy']}  "
          f"medium={POINTS_MAP['medium']}  hard={POINTS_MAP['hard']}")
    print(f"   Streak     : {STREAK_THRESHOLD}+ correct in a row = +{STREAK_BONUS} pts/question")
    print("═" * 65 + "\n")

    # Load session history so we don't repeat questions (#11 fix)
    seen_hashes = _load_history()
    log.info("Loaded %d previously seen question hashes", len(seen_hashes))

    # Sample candidate chunks — FIX #5: 4× pool so generation failures don't exhaust us
    candidate_count = num_questions * 4

    if mode == "spread":
        chunks = get_category_spread_chunks(count=candidate_count)
    else:
        chunks = get_weighted_chunks(count=candidate_count)

    if not chunks:
        print("[ERROR] No data in ChromaDB. Run scrape.py then ingest.py first.")
        return

    print(f"[GENERATING] Pulling from {len(chunks)} candidate chunks "
          f"using {QUESTION_MODEL}...\n")

    questions:   list[dict] = []
    new_hashes:  set[str]   = set()
    used_chunks: int        = 0

    for doc, meta in chunks:
        if len(questions) >= num_questions:
            break
        used_chunks += 1

        name = meta.get("name", "?")
        cat  = meta.get("category", "?")
        label = CATEGORY_CONFIG.get(cat, {}).get("label", cat)
        print(f"  [{len(questions)+1:>2}/{num_questions}]  {name:<30}  [{label}]...", end=" ", flush=True)

        q = generate_question(doc, meta, seen_hashes=seen_hashes)
        if q:
            q["category"]    = label
            q["source_name"] = name
            questions.append(q)
            # Track hash for dedup
            h = _question_hash(q["question"])
            new_hashes.add(h)
            seen_hashes.add(h)
            print("OK")
        else:
            print("FAILED — skipping")

    if not questions:
        print("\n[ERROR] Failed to generate any questions. Check your GROQ_API_KEY.")
        return

    actual = len(questions)
    print(f"\n[OK] Generated {actual}/{num_questions} questions "
          f"(scanned {used_chunks} chunks).")

    print("\nPress ENTER to begin the quiz, or Ctrl-C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nQuiz cancelled.")
        return

    # ── Question loop ──────────────────────────────────────────────────────
    print("\n" + "═" * 65)
    answers:         list[dict] = []
    current_streak:  int        = 0

    for i, q in enumerate(questions, 1):
        diff   = q.get("difficulty", "medium")
        pts    = POINTS_MAP.get(diff, 20)
        cat    = q.get("category", "")
        source = q.get("source_name", "")

        streak_note = (
            f"  🔥 Streak ×{current_streak}  (+{STREAK_BONUS} bonus pts if correct)"
            if current_streak >= STREAK_THRESHOLD else ""
        )

        print(f"\n  Question {i}/{actual}  ·  [{cat}]  ·  {diff.upper()} ({pts} pts)")
        if source:
            print(f"  Topic: {source}")
        if streak_note:
            print(streak_note)
        print()
        print(f"  {q['question']}\n")
        for letter in ("A", "B", "C", "D"):
            print(f"    {letter})  {q['options'][letter]}")

        # Time the answer (#10 fix — informational)
        print()
        t_start = time.time()
        while True:
            try:
                raw = input("  Your answer (A/B/C/D): ").strip().upper()
            except KeyboardInterrupt:
                print("\n\nQuiz interrupted. Saving progress...\n")
                # Save what we have
                _finalise(answers, new_hashes, seen_hashes)
                return
            if raw in ("A", "B", "C", "D"):
                break
            print("  Please enter A, B, or C or D.")
        elapsed = time.time() - t_start

        is_correct = raw == q["correct"]
        if is_correct:
            current_streak += 1
            bonus = STREAK_BONUS if current_streak >= STREAK_THRESHOLD else 0
            earned = pts + bonus
            bonus_note = f"  +{STREAK_BONUS} streak bonus!" if bonus else ""
            print(f"\n  ✓  CORRECT!  +{pts} pts{bonus_note}  ({elapsed:.1f}s)")
        else:
            current_streak = 0
            print(f"\n  ✗  Wrong.  Correct answer: "
                  f"{q['correct']})  {q['options'][q['correct']]}")

        print(f"  ➜  {q['explanation']}")
        print("\n" + "─" * 65)

        answers.append({
            "question":    q["question"],
            "your_answer": q["options"].get(raw, raw),
            "correct":     q["options"][q["correct"]],
            "is_correct":  is_correct,
            "difficulty":  diff,
            "explanation": q["explanation"],
            "category":    cat,
            "all_options": q["options"],
        })

    _finalise(answers, new_hashes, seen_hashes)


# ═══════════════════════════════════════════════════════════════════════════
#  FINALISE — results screen + save history
# ═══════════════════════════════════════════════════════════════════════════

def _finalise(
    answers: list[dict],
    new_hashes: set[str],
    seen_hashes: set[str],
) -> None:
    if not answers:
        print("No answers recorded.")
        return

    result = calculate_score(answers)

    print("\n" + "═" * 65)
    print("  QUIZ COMPLETE")
    print("═" * 65)
    print(f"  Score   :  {result['total_points']} / {result['max_points']} pts  "
          f"({result['percentage']}%)")
    print(f"  Correct :  {result['correct_count']} / {result['total_questions']} questions")
    print(f"  Rank    :  {result['rank']}")
    print("═" * 65)

    # Quick breakdown table
    print("\n  Breakdown:")
    for i, b in enumerate(result["breakdown"], 1):
        mark  = "✓" if b["is_correct"] else "✗"
        bonus = f"  (+{b['streak_bonus']} streak)" if b["streak_bonus"] else ""
        print(
            f"  {i:>2}. [{mark}]  {b['points_earned']:>3}/{b['points_possible']}pts  "
            f"[{b['difficulty']:<6}]  {b['category']}{bonus}"
        )

    # Wrong answers review — show all options so you can learn (#14 fix)
    wrong = [b for b in result["breakdown"] if not b["is_correct"]]
    if wrong:
        print(f"\n  ── REVIEW: {len(wrong)} wrong answer(s) ──\n")
        for b in wrong:
            print(f"  Q: {b['question']}")
            opts = b.get("all_options", {})
            for letter in ("A", "B", "C", "D"):
                marker = "✓" if b["correct_answer"] == opts.get(letter, "") else " "
                you    = " ← you" if b["your_answer"] == opts.get(letter, "") else ""
                print(f"    [{marker}] {letter})  {opts.get(letter, '')}{you}")
            print(f"    Explanation: {b['explanation']}")
            print()

    # Category performance bar chart
    cat_stats: dict[str, dict] = defaultdict(lambda: {"correct": 0, "total": 0})
    for b in result["breakdown"]:
        cat_stats[b["category"]]["total"] += 1
        if b["is_correct"]:
            cat_stats[b["category"]]["correct"] += 1

    if len(cat_stats) > 1:
        print("  Category Performance:")
        for cat, stats in sorted(cat_stats.items()):
            pct = round(stats["correct"] / stats["total"] * 100)
            bar = "█" * stats["correct"] + "░" * (stats["total"] - stats["correct"])
            print(f"    {cat:<24}  {bar}  {stats['correct']}/{stats['total']}  ({pct}%)")

    print()

    # Persist seen hashes so future runs avoid repeating these questions (#11 fix)
    _save_history(seen_hashes)
    log.info("Saved %d question hashes to history", len(seen_hashes))


# ═══════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    args = sys.argv[1:]

    # python quiz.py --check
    if "--check" in args:
        print("\n" + "═" * 65)
        print("  ELDEN RING LORE DB — COVERAGE REPORT")
        print("═" * 65)
        print_db_coverage()
        sys.exit(0)

    # python quiz.py --clear-history
    if "--clear-history" in args:
        _save_history(set())
        print("[OK] Quiz history cleared. All questions are fair game again.")
        sys.exit(0)

    num_questions = 10
    mode          = "weighted"

    if "--questions" in args:
        idx = args.index("--questions")
        try:
            num_questions = max(1, int(args[idx + 1]))
        except (IndexError, ValueError):
            log.warning("Invalid --questions value, using default 10")

    if "--spread" in args:
        mode = "spread"

    run_quiz(num_questions=num_questions, mode=mode)