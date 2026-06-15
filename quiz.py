import os
import random
import time
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv
import json
from collections import defaultdict

load_dotenv()

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("elden_ring_lore")
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ---------------------------------------------------------------------------
# CATEGORY CONFIG
# ---------------------------------------------------------------------------
CATEGORY_CONFIG = {
    "boss":         {"label": "Boss Lore",         "weight": 3},
    "character":    {"label": "NPC / Character",   "weight": 3},
    "lore":         {"label": "World Lore",        "weight": 3},
    "area":         {"label": "Area / Location",   "weight": 2},
    "weapon":       {"label": "Weapon Lore",       "weight": 2},
    "spell":        {"label": "Spell / Incantation","weight": 2},
    "armor":        {"label": "Armor Lore",        "weight": 2},
    "talisman":     {"label": "Talisman Lore",     "weight": 2},
    "great_rune":   {"label": "Great Rune",        "weight": 2},
    "ending":       {"label": "Game Ending",       "weight": 2},
    "questline":    {"label": "Questline",         "weight": 2},
    "item":         {"label": "Key Item",          "weight": 1},
    "spirit_ash":   {"label": "Spirit Ash",        "weight": 1},
    "ash_of_war":   {"label": "Ash of War",        "weight": 1},
    "shield":       {"label": "Shield Lore",       "weight": 1},
    "creature":     {"label": "Enemy / Creature",  "weight": 1},
    "dialogue":     {"label": "Dialogue",          "weight": 1},
    "cutscene":     {"label": "Cutscene",          "weight": 1},
    "crystal_tear": {"label": "Crystal Tear",      "weight": 1},
    "whetblade":    {"label": "Whetblade",         "weight": 1},
    "bell_bearing": {"label": "Bell Bearing",      "weight": 1},
    "cookbook":     {"label": "Cookbook",          "weight": 1},
    "painting":     {"label": "Painting",          "weight": 1},
    "cut_content":  {"label": "Cut Content",       "weight": 1},
}

MIN_CHUNK_LENGTH = 200

POINTS_MAP = {
    "easy":   10,
    "medium": 20,
    "hard":   30,
}

# ---------------------------------------------------------------------------
# DB COVERAGE REPORT
# Shows you exactly what's in your ChromaDB before the quiz starts
# ---------------------------------------------------------------------------

def print_db_coverage():
    results = collection.get(include=["documents", "metadatas"])
    documents = results["documents"]
    metadatas = results["metadatas"]

    total = len(documents)
    if total == 0:
        print("  [!] ChromaDB is EMPTY. Run scrape.py and ingest.py first.")
        return

    # Count by category
    cat_counts = defaultdict(int)
    cat_long_enough = defaultdict(int)
    for doc, meta in zip(documents, metadatas):
        cat = meta.get("category", "unknown")
        cat_counts[cat] += 1
        if len(doc) >= MIN_CHUNK_LENGTH:
            cat_long_enough[cat] += 1

    print(f"\n  Total chunks in DB: {total}")
    print(f"  Chunks long enough to quiz (>={MIN_CHUNK_LENGTH} chars): "
          f"{sum(cat_long_enough.values())}")
    print()
    print(f"  {'Category':<20} {'In Config':>10} {'Total':>8} {'Quizzable':>10}")
    print(f"  {'-'*20} {'-'*10} {'-'*8} {'-'*10}")

    all_cats = set(list(cat_counts.keys()) + list(CATEGORY_CONFIG.keys()))
    for cat in sorted(all_cats):
        in_config = "YES" if cat in CATEGORY_CONFIG else "NO"
        total_cat = cat_counts.get(cat, 0)
        quizzable = cat_long_enough.get(cat, 0)
        flag = "  <-- MISSING" if total_cat == 0 else ""
        label = CATEGORY_CONFIG.get(cat, {}).get("label", cat)
        print(f"  {label:<20} {in_config:>10} {total_cat:>8} {quizzable:>10}{flag}")

    print()

    # Warn about any category with zero quizzable chunks
    missing = [cat for cat in CATEGORY_CONFIG if cat_long_enough.get(cat, 0) == 0]
    if missing:
        print(f"  [WARNING] These categories have NO quizzable chunks:")
        for cat in missing:
            print(f"    - {CATEGORY_CONFIG[cat]['label']} ({cat})")
        print("  Run rescrape_missing.py then ingest.py to fill the gaps.\n")
    else:
        print("  [OK] All 24 categories have quizzable content!\n")


# ---------------------------------------------------------------------------
# CHUNK SAMPLING — truly random seed each run, balanced by category
# ---------------------------------------------------------------------------

def get_weighted_chunks(count: int = 10) -> list[tuple[str, dict]]:
    """Pull chunks from ChromaDB with category weighting. 
    Uses a fresh random seed each call so you never get the same quiz twice."""
    results = collection.get(include=["documents", "metadatas"])
    documents = results["documents"]
    metadatas = results["metadatas"]

    combined = [
        (doc, meta)
        for doc, meta in zip(documents, metadatas)
        if len(doc) >= MIN_CHUNK_LENGTH
    ]

    if not combined:
        return []

    weights = [
        CATEGORY_CONFIG.get(meta.get("category", ""), {}).get("weight", 1)
        for _, meta in combined
    ]

    # Fresh seed every run = different quiz every time
    random.seed()
    selected = random.choices(combined, weights=weights, k=min(count * 5, len(combined)))

    # Deduplicate by name, keep first occurrence
    seen_names = set()
    deduped = []
    for doc, meta in selected:
        name = meta.get("name", "")
        if name not in seen_names:
            seen_names.add(name)
            deduped.append((doc, meta))
        if len(deduped) >= count:
            break

    return deduped


def get_category_spread_chunks(count: int = 10) -> list[tuple[str, dict]]:
    """Alternative sampler: guarantees at least one chunk from each high-weight 
    category, then fills remaining slots with weighted random picks.
    Great for a 'well-rounded' quiz."""
    results = collection.get(include=["documents", "metadatas"])
    documents = results["documents"]
    metadatas = results["metadatas"]

    # Group by category
    by_category: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for doc, meta in zip(documents, metadatas):
        if len(doc) >= MIN_CHUNK_LENGTH:
            cat = meta.get("category", "unknown")
            by_category[cat].append((doc, meta))

    selected = []
    seen_names = set()
    random.seed()

    # Priority categories that must appear if possible
    priority_cats = ["boss", "character", "lore", "area", "weapon", "ending"]
    for cat in priority_cats:
        if cat in by_category and len(selected) < count:
            chunk = random.choice(by_category[cat])
            name = chunk[1].get("name", "")
            if name not in seen_names:
                seen_names.add(name)
                selected.append(chunk)

    # Fill remaining slots with weighted random
    all_chunks = [
        (doc, meta)
        for cat_chunks in by_category.values()
        for doc, meta in cat_chunks
        if meta.get("name", "") not in seen_names
    ]

    all_weights = [
        CATEGORY_CONFIG.get(meta.get("category", ""), {}).get("weight", 1)
        for _, meta in all_chunks
    ]

    if all_chunks and len(selected) < count:
        extras = random.choices(
            all_chunks, weights=all_weights,
            k=min((count - len(selected)) * 3, len(all_chunks))
        )
        for doc, meta in extras:
            name = meta.get("name", "")
            if name not in seen_names:
                seen_names.add(name)
                selected.append((doc, meta))
            if len(selected) >= count:
                break

    random.shuffle(selected)
    return selected[:count]


# ---------------------------------------------------------------------------
# DIFFICULTY DETECTION
# ---------------------------------------------------------------------------

def get_difficulty(meta: dict) -> str:
    category = meta.get("category", "lore")
    easy_cats = {"area", "boss", "character", "ending"}
    hard_cats = {"cut_content", "whetblade", "bell_bearing", "cookbook",
                 "painting", "crystal_tear", "dialogue", "cutscene"}
    if category in easy_cats:
        return "easy"
    if category in hard_cats:
        return "hard"
    return "medium"


# ---------------------------------------------------------------------------
# QUESTION GENERATION — richer prompts, uses more lore context
# ---------------------------------------------------------------------------

def generate_question(doc: str, meta: dict, retry: int = 2) -> dict | None:
    category = meta.get("category", "lore")
    cat_label = CATEGORY_CONFIG.get(category, {}).get("label", category)
    difficulty = get_difficulty(meta)
    name = meta.get("name", "Unknown")
    area = meta.get("area", "Unknown")

    difficulty_instruction = {
        "easy": (
            "Ask about this entity's primary role, identity, or most famous action. "
            "The answer should be obvious to anyone who finished the main story."
        ),
        "medium": (
            "Ask about WHY this entity matters — their lore significance, "
            "their relationship to a demigod or outer god, or what their item description reveals. "
            "Avoid surface-level facts."
        ),
        "hard": (
            "Ask about obscure details: hidden connections to cut content, "
            "what a specific item description implies about the world's history, "
            "contradictions between sources, or lore only revealed through NPC dialogue. "
            "This should stump all but dedicated lore hunters."
        ),
    }[difficulty]

    distractor_instruction = {
        "boss":         "Use other Elden Ring bosses or demigods as wrong answers.",
        "character":    "Use other Elden Ring NPCs or story characters as wrong answers.",
        "weapon":       "Use other Elden Ring weapons with similar themes as wrong answers.",
        "armor":        "Use other Elden Ring armor sets as wrong answers.",
        "spell":        "Use other sorceries or incantations from Elden Ring as wrong answers.",
        "talisman":     "Use other Elden Ring talismans as wrong answers.",
        "great_rune":   "Use other Great Runes or shardbearers as wrong answers.",
        "spirit_ash":   "Use other spirit ashes as wrong answers.",
        "ash_of_war":   "Use other Ashes of War as wrong answers.",
        "area":         "Use other Elden Ring regions, dungeons, or legacy dungeons as wrong answers.",
        "ending":       "Use other Elden Ring endings or ages as wrong answers.",
        "item":         "Use other key story items from Elden Ring as wrong answers.",
        "questline":    "Use other NPC questlines that could be confused with this one as wrong answers.",
        "lore":         "Use other lore concepts, factions, or historical events from Elden Ring as wrong answers.",
        "creature":     "Use other enemy types with similar traits as wrong answers.",
        "dialogue":     "Use other characters who could plausibly say this as wrong answers.",
        "cutscene":     "Use other key story moments or characters as wrong answers.",
        "crystal_tear": "Use other Flask of Wondrous Physick tears as wrong answers.",
        "whetblade":    "Use other Whetblades from Elden Ring as wrong answers.",
        "bell_bearing": "Use other Bell Bearings or merchant items as wrong answers.",
        "cookbook":     "Use other Crafting Cookbooks as wrong answers.",
        "painting":     "Use other painting locations or rewards as wrong answers.",
        "cut_content":  "Use other unused or datamined content from Elden Ring as wrong answers.",
        "shield":       "Use other Elden Ring shields or greatshields as wrong answers.",
    }.get(category, "Use other plausible Elden Ring entities as wrong answers.")

    # Give the model more context — use up to 900 chars of the actual lore
    lore_excerpt = doc[:900]

    prompt = f"""You are a lore quiz master for the game Elden Ring.
Use the lore below to craft ONE excellent multiple-choice question.

Entity: {name}
Category: {cat_label}
Area: {area}
Difficulty: {difficulty.upper()}

DIFFICULTY GOAL: {difficulty_instruction}
DISTRACTOR RULE: {distractor_instruction}

STRICT RULES:
- Exactly 4 options: A, B, C, D
- Exactly 1 correct answer
- Wrong options must be real Elden Ring things — no nonsense answers
- Every option under 10 words
- No emojis
- Do NOT ask about stat numbers, damage values, or gameplay mechanics
- Do NOT include the entity's exact name in the question if it gives away the answer
- The explanation must cite WHY the correct answer is right using lore from the text below
- Make the question interesting — avoid "What is X?" style questions when possible

RESPOND IN THIS EXACT JSON FORMAT ONLY — no markdown, no extra text:
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
Name: {name}
Category: {cat_label}
Area: {area}
{lore_excerpt}"""

    for attempt in range(retry + 1):
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4 + (attempt * 0.1),  # slight temp bump on retry
                max_tokens=500,
            )
            text = response.choices[0].message.content.strip()
            text = text.replace("```json", "").replace("```", "").strip()

            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])

                required = {"question", "options", "correct", "explanation"}
                if required.issubset(data.keys()):
                    if set(data["options"].keys()) == {"A", "B", "C", "D"}:
                        if data["correct"] in data["options"]:
                            data.setdefault("difficulty", difficulty)
                            return data

        except json.JSONDecodeError:
            if attempt < retry:
                time.sleep(0.5)
            continue
        except Exception as e:
            if attempt < retry:
                time.sleep(1.0)
            continue

    return None


# ---------------------------------------------------------------------------
# SCORING
# ---------------------------------------------------------------------------

def calculate_score(answers: list[dict]) -> dict:
    total_points = 0
    max_points = 0
    correct_count = 0
    breakdown = []

    for entry in answers:
        diff = entry.get("difficulty", "medium")
        pts = POINTS_MAP.get(diff, 20)
        max_points += pts

        is_correct = entry.get("is_correct", False)
        earned = pts if is_correct else 0
        total_points += earned
        if is_correct:
            correct_count += 1

        breakdown.append({
            "question":       entry["question"],
            "your_answer":    entry["your_answer"],
            "correct_answer": entry["correct"],
            "is_correct":     is_correct,
            "points_earned":  earned,
            "points_possible": pts,
            "difficulty":     diff,
            "explanation":    entry.get("explanation", ""),
            "category":       entry.get("category", ""),
        })

    percentage = round((total_points / max_points) * 100) if max_points > 0 else 0
    rank = get_rank(percentage)

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
    if percentage == 100: return "Elden Lord"
    if percentage >= 90:  return "Erdtree Sage"
    if percentage >= 75:  return "Knight of the Roundtable"
    if percentage >= 60:  return "Tarnished Scholar"
    if percentage >= 40:  return "Wandering Exile"
    return "Maidenless Wretch"


# ---------------------------------------------------------------------------
# QUIZ RUNNER
# ---------------------------------------------------------------------------

def run_quiz(num_questions: int = 10, mode: str = "weighted") -> None:
    print("\n" + "=" * 65)
    print("   ELDEN RING LORE QUIZ  —  May the grace guide thy sword")
    print("=" * 65)

    # Show DB coverage so the user knows what's available
    print("\n[DB COVERAGE CHECK]")
    print_db_coverage()

    # Choose sampling mode
    if mode == "spread":
        print(f"[MODE] Balanced spread — guaranteed coverage across major categories")
        chunks = get_category_spread_chunks(count=num_questions * 2)
    else:
        print(f"[MODE] Weighted random — every quiz is different")
        chunks = get_weighted_chunks(count=num_questions * 2)

    if not chunks:
        print("\n[ERROR] No data in ChromaDB. Run scrape.py then ingest.py first.")
        return

    print(f"\n[GENERATING QUESTIONS] Pulling from {len(chunks)} candidate chunks...\n")

    questions = []
    used_chunks = 0

    for doc, meta in chunks:
        if len(questions) >= num_questions:
            break
        used_chunks += 1

        name = meta.get("name", "?")
        cat  = meta.get("category", "?")
        print(f"  Generating [{len(questions)+1}/{num_questions}] "
              f"{name} [{CATEGORY_CONFIG.get(cat, {}).get('label', cat)}]...", end=" ")

        q = generate_question(doc, meta)
        if q:
            q["category"] = CATEGORY_CONFIG.get(
                meta.get("category", ""), {}
            ).get("label", meta.get("category", ""))
            q["source_name"] = name
            questions.append(q)
            print("OK")
        else:
            print("FAILED — skipping")

    if not questions:
        print("\n[ERROR] Failed to generate any questions. Check your GROQ_API_KEY.")
        return

    actual = len(questions)
    print(f"\n[OK] Generated {actual} questions from {used_chunks} chunks scanned.")
    print("\nPress ENTER to begin the quiz...")
    input()

    print("\n" + "=" * 65)
    print(f"  {actual} QUESTIONS  |  Points scale by difficulty")
    print(f"  easy = {POINTS_MAP['easy']}pts  |  medium = {POINTS_MAP['medium']}pts  |  hard = {POINTS_MAP['hard']}pts")
    print("=" * 65 + "\n")

    answers = []
    for i, q in enumerate(questions, 1):
        diff   = q.get("difficulty", "medium")
        pts    = POINTS_MAP.get(diff, 20)
        cat    = q.get("category", "")
        source = q.get("source_name", "")

        print(f"  Question {i}/{actual}  [{cat}]  ({diff.upper()} — {pts} pts)")
        if source:
            print(f"  Topic: {source}")
        print()
        print(f"  {q['question']}\n")
        for letter, option in q["options"].items():
            print(f"    {letter}) {option}")

        print()
        while True:
            user_input = input("  Your answer (A/B/C/D): ").strip().upper()
            if user_input in ("A", "B", "C", "D"):
                break
            print("  Please enter A, B, C, or D.")

        is_correct = user_input == q["correct"]
        print()
        if is_correct:
            print(f"  ✓ CORRECT!  +{pts} points")
        else:
            print(f"  ✗ Wrong.  Correct answer: "
                  f"{q['correct']}) {q['options'][q['correct']]}")
        print(f"  → {q['explanation']}")
        print("\n" + "-" * 65 + "\n")

        answers.append({
            "question":    q["question"],
            "your_answer": q["options"].get(user_input, ""),
            "correct":     q["options"][q["correct"]],
            "is_correct":  is_correct,
            "difficulty":  diff,
            "explanation": q["explanation"],
            "category":    cat,
        })

    result = calculate_score(answers)

    print("=" * 65)
    print("  QUIZ COMPLETE")
    print("=" * 65)
    print(f"  Score:    {result['total_points']} / {result['max_points']} pts  "
          f"({result['percentage']}%)")
    print(f"  Correct:  {result['correct_count']} / {result['total_questions']} questions")
    print(f"  Rank:     {result['rank']}")
    print("=" * 65)

    print("\n  Breakdown:")
    for i, b in enumerate(result["breakdown"], 1):
        mark = "✓" if b["is_correct"] else "✗"
        print(f"  {i:>2}. [{mark}] {b['points_earned']:>2}/{b['points_possible']}pts  "
              f"[{b['difficulty']:<6}]  {b['category']}")

    # Category performance summary
    cat_stats: dict[str, dict] = defaultdict(lambda: {"correct": 0, "total": 0})
    for b in result["breakdown"]:
        cat_stats[b["category"]]["total"] += 1
        if b["is_correct"]:
            cat_stats[b["category"]]["correct"] += 1

    if len(cat_stats) > 1:
        print("\n  By Category:")
        for cat, stats in sorted(cat_stats.items()):
            pct = round(stats["correct"] / stats["total"] * 100)
            bar = "█" * stats["correct"] + "░" * (stats["total"] - stats["correct"])
            print(f"    {cat:<22}  {bar}  {stats['correct']}/{stats['total']}  ({pct}%)")

    print()


# ---------------------------------------------------------------------------
# STANDALONE DB CHECK — run as: python quiz.py --check
# ---------------------------------------------------------------------------

def check_db_only():
    print("\n" + "=" * 65)
    print("  ELDEN RING LORE DB — COVERAGE REPORT")
    print("=" * 65)
    print_db_coverage()


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    args = sys.argv[1:]

    if "--check" in args:
        # Just print DB coverage and exit
        check_db_only()
        sys.exit(0)

    # Parse optional flags:
    #   --questions N    number of questions (default 10)
    #   --spread         use balanced category spread instead of weighted random
    num_questions = 10
    mode = "weighted"

    if "--questions" in args:
        idx = args.index("--questions")
        try:
            num_questions = int(args[idx + 1])
        except (IndexError, ValueError):
            print("[WARN] Invalid --questions value, using default 10")

    if "--spread" in args:
        mode = "spread"

    run_quiz(num_questions=num_questions, mode=mode)