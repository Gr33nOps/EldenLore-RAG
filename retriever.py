"""
retriever.py  — robust retrieval for Elden Ring RAG bot

ROOT CAUSE FIXES vs retrieve_fixed.py:
  1. expand_query and rerank are OPTIONAL — failures return empty/original,
     never blocking retrieval. Previously any Groq error = 0 results.
  2. Groq rate-limit defence: expand_query returns [] on any exception,
     letting Pass 1 (raw query) still work alone.
  3. rerank() gracefully falls back to score-sorted order on any error.
  4. Added get_collection_size() for diagnostics.
  5. Added diagnose() to print DB health — run directly to debug.
  6. Score formula: 1/(1+dist) — safe for L2 distances (never negative).
  7. n_results capped at actual collection size to prevent ChromaDB crash.
  8. Every retrieval pass is independently try/caught — one pass failing
     never kills the others.
"""

import json
import logging
import os

import chromadb
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ── Models ────────────────────────────────────────────────────────────────────
model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("elden_ring_lore")
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Use 8b for helper calls — 70b burns rate limits fast
HELPER_MODEL = "llama-3.1-8b-instant"


# ── Distance → similarity ─────────────────────────────────────────────────────
def _score(dist: float) -> float:
    """
    Cosine distance → similarity in [0, 1].
    Collection now uses hnsw:space='cosine' (set in ingest.py).
    For normalised sentence-transformer vectors, cosine dist is in [0,1]
    so 1-dist is always non-negative.
    If you haven't re-ingested yet, temporarily use: 1.0 / (1.0 + dist)
    """
    return round(max(0.0, 1.0 - dist), 3)


def _safe_n(requested: int) -> int:
    """Cap n_results at actual DB size — ChromaDB crashes if you ask for more."""
    db_size = collection.count()
    return min(requested, max(1, db_size))


def get_collection_size() -> int:
    return collection.count()


# ── Entity relations map ──────────────────────────────────────────────────────
ENTITY_RELATIONS: dict[str, list[str]] = {
    "miquella": [
        "st trina", "promised consort radahn", "miquella's needle",
        "enir-ilim", "haligtree", "unalloyed gold", "needle knight leda",
        "remembrance of a god and a lord", "mohg lord of blood",
        "miquella's haligtree", "shadow of the erdtree",
    ],
    "ranni": [
        "blaidd", "iji", "night of black knives", "age of stars",
        "dark moon", "rune of death", "darkmoon greatsword",
        "fingerslayer blade", "snow witch", "preceptor seluvis",
        "ranni's dark moon", "remembrance of the full moon queen",
    ],
    "malenia": [
        "scarlet rot", "millicent", "elphael", "haligtree",
        "cleanrot knights", "rot goddess", "blade of miquella",
        "remembrance of the rot goddess", "hand of malenia",
        "gowry", "unalloyed gold needle",
    ],
    "mohg": [
        "formless mother", "mohgwyn palace", "white mask varre",
        "dynasty", "blood lord", "remembrance of the blood lord",
        "mohg the omen", "mohgwyn's sacred spear",
    ],
    "marika": [
        "radagon", "erdtree", "elden ring", "greater will", "godfrey",
        "tarnished", "golden order", "shattering", "empyrean",
        "two fingers", "messmer", "godwyn",
    ],
    "radagon": [
        "marika", "golden order", "rennala", "elden ring",
        "radagon icon", "remembrance of the full moon queen",
    ],
    "messmer": [
        "land of shadow", "shadow keep", "hornsent", "marika",
        "remembrance of the impaler", "messmer's spear",
        "fire knight", "scadu altus",
    ],
    "godwyn": [
        "night of black knives", "ranni", "deathroot", "death",
        "prince of death", "black knife", "cursemark of death",
        "rune of death", "deeproot depths", "fia",
    ],
    "godfrey": [
        "hoarah loux", "serosh", "tarnished", "elden lord",
        "remembrance of hoarah loux", "crucible", "radagon",
    ],
    "morgott": [
        "omen", "fell omen", "leyndell", "remembrance of the omen king",
        "morgott's cursed sword", "erdtree", "marika",
    ],
    "radahn": [
        "starscourge", "caelid", "scarlet rot", "malenia",
        "remembrance of the starscourge", "festival", "promised consort",
        "miquella", "starscourge greatsword",
    ],
    "rykard": [
        "volcano manor", "blasphemous blade", "serpent",
        "remembrance of the blasphemous", "tanith", "gelmir",
    ],
    "malekith": [
        "black blade", "maliketh", "rune of death", "destined death",
        "remembrance of the black blade", "gurranq", "beast clergyman",
    ],
    "maliketh": [
        "black blade", "rune of death", "destined death",
        "remembrance of the black blade", "gurranq", "beast clergyman",
    ],
    "fia": [
        "deathbed companion", "deeproot depths", "godwyn",
        "cursemark of death", "age of the duskborn", "d hunter",
        "remembrance of the lichdragon",
    ],
    "gloam-eyed queen": [
        "godskin apostle", "godskin noble", "destined death",
        "black flame", "maliketh", "rune of death",
    ],
    "gloam eyed queen": [
        "godskin apostle", "godskin noble", "destined death",
        "black flame", "maliketh", "rune of death",
    ],
    "serosh": [
        "godfrey", "crucible", "hoarah loux", "beast",
        "elden lord", "tarnished",
    ],
    "placidusax": [
        "dragonlord", "farum azula", "elden beast",
        "remembrance of the dragonlord", "ancient dragon",
    ],
    "fortissax": [
        "lichdragon", "godwyn", "deeproot depths",
        "remembrance of the lichdragon", "death lightning",
    ],
    "frenzied flame": [
        "three fingers", "hyetta", "shabriri", "lord of frenzied flame",
        "age of fracture", "frenzied flame proscription",
        "midra", "abyssal woods",
    ],
    "erdtree": [
        "golden order", "greater will", "marika", "outer god",
        "crucible", "two fingers", "grace",
    ],
    "greater will": [
        "two fingers", "erdtree", "outer gods", "elden ring",
        "marika", "empyrean", "fingers",
    ],
    "night of black knives": [
        "ranni", "godwyn", "black knife assassins", "rune of death",
        "maliketh", "cursemark of death", "death",
    ],
    "scarlet rot": [
        "malenia", "rot goddess", "caelid", "kindred of rot",
        "lake of rot", "radahn", "millicent",
    ],
    "twinbird": [
        "marika", "death", "deathbird", "outer god", "destined death",
    ],
    "nox": [
        "nokron", "nokstella", "fingerslayer blade", "silver tears",
        "mimic tear", "siofra river", "eternal city",
    ],
    "crucible": [
        "erdtree", "ancient", "godfrey", "crucible knight",
        "aspects of the crucible", "primordial",
    ],
}

# ── Category intent map ───────────────────────────────────────────────────────
CATEGORY_INTENT_MAP: dict[str, list[str]] = {
    "armor": [
        "armor", "armour", "helm", "helmet", "gauntlets", "greaves",
        "chest piece", "outfit", "wearing", "clothing", "set pieces",
    ],
    "weapon": [
        "weapon", "sword", "blade", "greatsword", "katana", "halberd",
        "spear", "axe", "hammer", "staff", "seal", "bow", "crossbow",
        "twinblade", "dagger", "scythe", "whip", "fist", "claw", "flail",
    ],
    "shield": ["shield", "greatshield", "buckler"],
    "great_rune": ["great rune", "shardbearers"],
    "spirit_ash": ["spirit ash", "spirit ashes", "summon spirit"],
    "ash_of_war": ["ash of war", "weapon skill"],
    "spell": ["sorcery", "incantation", "spell", "glintstone", "magic"],
    "talisman": ["talisman", "charm", "medallion", "soreseal"],
    "crystal_tear": ["crystal tear", "physick", "wondrous physick"],
    "ending": [
        "ending", "age of ", "finale", "age of fracture",
        "age of stars", "frenzied flame ending", "age of order",
    ],
    "questline": ["quest", "questline", "how to complete", "walkthrough"],
    "dialogue": ["say", "says", "said", "quote", "dialogue", "exact words"],
    "lore": [
        "who is", "what is", "why is", "lore", "history", "backstory",
        "what happened", "explain", "origin of",
    ],
    "boss": ["boss", "fight", "how to beat"],
    "area": ["area", "region", "location", "where", "map", "zone"],
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def detect_categories(query: str) -> list[str]:
    q = query.lower()
    return list({cat for cat, kws in CATEGORY_INTENT_MAP.items() if any(kw in q for kw in kws)})


def get_relation_queries(query: str) -> list[str]:
    q = query.lower()
    seen: set[str] = set()
    result: list[str] = []
    for entity, relations in ENTITY_RELATIONS.items():
        if entity in q:
            for r in relations:
                if r not in seen:
                    seen.add(r)
                    result.append(r)
                    if len(result) >= 8:
                        return result
    return result


def boost_remembrances(chunks: list[dict]) -> list[dict]:
    remembrance = [c for c in chunks if "remembrance" in c["name"].lower()]
    others = [c for c in chunks if "remembrance" not in c["name"].lower()]
    return remembrance + others


# ── Query expansion (OPTIONAL — failure = empty list, never crashes) ──────────
def expand_query(query: str) -> list[str]:
    """
    Returns up to 6 expanded queries, or [] on any failure.
    NEVER raises — a failed expansion just means we use the raw query alone.
    """
    prompt = f"""You are a search query expander for an Elden Ring lore database.

The database contains: boss lore, character lore, area descriptions, weapon/armor/item descriptions,
spell descriptions, remembrances, NPC dialogue, and cutscene text.

Given this question: "{query}"

Generate 6 alternative search queries. Rules:
- Use EXACT Elden Ring character/item/place names
- Short, dense keyword phrases — not full sentences
- Include the Remembrance name if a boss is involved
- Cover different angles of the same question

Return ONLY a JSON array of 6 strings. No markdown, no explanation.
Example: ["query one", "query two", "query three", "query four", "query five", "query six"]"""

    try:
        response = groq_client.chat.completions.create(
            model=HELPER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=350,
        )
        text = response.choices[0].message.content.strip()
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            queries = json.loads(text[start:end])
            if isinstance(queries, list):
                return [str(q) for q in queries[:6]]
    except Exception as e:
        log.warning("expand_query failed (retrieval continues without expansion): %s", e)
    return []


# ── Reranker (OPTIONAL — failure = score-sorted order) ───────────────────────
def rerank(query: str, chunks: list[dict]) -> list[dict]:
    """
    LLM rerank. On any failure, returns chunks sorted by embedding score.
    Never crashes the pipeline.
    """
    if not chunks:
        return chunks

    chunk_list = ""
    for i, chunk in enumerate(chunks):
        preview = chunk["text"][:400].replace("\n", " ")
        chunk_list += f"[{i}] {chunk['name']} (category={chunk['category']}): {preview}\n\n"

    prompt = f"""Rerank these Elden Ring lore chunks to best answer the question.
Put the most directly relevant chunks first.

QUESTION: {query}

CHUNKS:
{chunk_list}

Return ONLY comma-separated indices, most relevant first.
Example: 3,0,7,2,1,5,4,6
Only numbers and commas."""

    try:
        response = groq_client.chat.completions.create(
            model=HELPER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=120,
        )
        order_text = response.choices[0].message.content.strip()
        indices = [int(x.strip()) for x in order_text.split(",") if x.strip().isdigit()]
        reranked: list[dict] = []
        seen: set[int] = set()
        for i in indices:
            if 0 <= i < len(chunks) and i not in seen:
                reranked.append(chunks[i])
                seen.add(i)
        # Append anything the LLM missed
        for i, chunk in enumerate(chunks):
            if i not in seen:
                reranked.append(chunk)
        log.info("rerank: reordered %d chunks", len(reranked))
        return reranked
    except Exception as e:
        log.warning("rerank failed (using score order): %s", e)
        return sorted(chunks, key=lambda x: x["score"], reverse=True)


# ── Main retrieval ────────────────────────────────────────────────────────────
def retrieve(query: str, top_k: int = 12) -> list[dict]:
    """
    Multi-pass retrieval. Each pass is independently try/caught.
    Returns top_k chunks sorted by score. Never raises.

    Passes:
      1. Raw query + expanded queries (unfiltered)
      2. Entity relation queries
      3. Category-filtered query with score boost
    """
    db_size = collection.count()
    if db_size == 0:
        log.error("ChromaDB collection is EMPTY — run your ingest script first!")
        return []

    log.info("retrieve(%r) — DB has %d documents", query[:80], db_size)

    expanded = expand_query(query)
    relation_queries = get_relation_queries(query)
    detected_cats = detect_categories(query)

    log.info("  expanded queries: %d | relation queries: %d | categories: %s",
             len(expanded), len(relation_queries), detected_cats or "(none)")

    all_queries = [query] + expanded
    seen_ids: set[str] = set()
    all_chunks: list[dict] = []

    # ── Pass 1: General unfiltered search ────────────────────────────────────
    for q in all_queries:
        try:
            embedding = model.encode(q).tolist()
            n = _safe_n(10)
            results = collection.query(query_embeddings=[embedding], n_results=n)
            for doc_id, doc, meta, dist in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_chunks.append({
                        "text":     doc,
                        "name":     meta.get("name", ""),
                        "area":     meta.get("area", ""),
                        "category": meta.get("category", ""),
                        "score":    _score(dist),
                    })
        except Exception as e:
            log.warning("Pass 1 query failed for %r: %s", q[:60], e)

    log.info("  Pass 1: %d unique chunks", len(all_chunks))

    # ── Pass 2: Entity relation queries ──────────────────────────────────────
    for rq in relation_queries:
        try:
            embedding = model.encode(rq).tolist()
            n = _safe_n(5)
            results = collection.query(query_embeddings=[embedding], n_results=n)
            for doc_id, doc, meta, dist in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_chunks.append({
                        "text":     doc,
                        "name":     meta.get("name", ""),
                        "area":     meta.get("area", ""),
                        "category": meta.get("category", ""),
                        "score":    _score(dist),
                    })
        except Exception as e:
            log.warning("Pass 2 query failed for %r: %s", rq[:60], e)

    log.info("  After Pass 2: %d unique chunks", len(all_chunks))

    # ── Pass 3: Category-filtered search with score boost ────────────────────
    if detected_cats:
        try:
            embedding = model.encode(query).tolist()
            where_filter = (
                {"category": {"$in": detected_cats}}
                if len(detected_cats) > 1
                else {"category": detected_cats[0]}
            )
            n = _safe_n(15)
            results = collection.query(
                query_embeddings=[embedding],
                n_results=n,
                where=where_filter,
            )
            for doc_id, doc, meta, dist in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_chunks.append({
                        "text":     doc,
                        "name":     meta.get("name", ""),
                        "area":     meta.get("area", ""),
                        "category": meta.get("category", ""),
                        "score":    round(_score(dist) * 1.15, 3),
                    })
        except Exception as e:
            log.warning("Pass 3 failed: %s", e)

    log.info("  After Pass 3: %d unique chunks", len(all_chunks))

    if not all_chunks:
        log.warning("retrieve() returned 0 chunks for: %r", query)
        return []

    all_chunks.sort(key=lambda x: x["score"], reverse=True)
    candidates = boost_remembrances(all_chunks[:30])

    reranked = rerank(query, candidates)
    final = reranked[:top_k]
    log.info("  Final: returning %d chunks (top score=%.3f)", len(final), final[0]["score"] if final else 0)
    return final


# ── Diagnostics ───────────────────────────────────────────────────────────────
def diagnose():
    """Run this directly to check DB health and retrieval quality."""
    print("\n" + "=" * 60)
    print("  RETRIEVER DIAGNOSTICS")
    print("=" * 60)

    size = collection.count()
    print(f"\nDB size: {size} documents")

    if size == 0:
        print("❌ COLLECTION IS EMPTY — run ingest.py first!")
        return

    # Sample some documents
    sample = collection.peek(10)
    print(f"\nSample document names:")
    for meta in sample.get("metadatas", []):
        print(f"  [{meta.get('category', '?')}] {meta.get('name', '?')} | {meta.get('area', '?')}")

    # Check unique categories
    # (ChromaDB doesn't support distinct queries, so we peek more)
    large_sample = collection.peek(200)
    cats = {m.get("category", "?") for m in large_sample.get("metadatas", [])}
    print(f"\nCategories in first 200 docs: {sorted(cats)}")

    # Test retrieval
    test_queries = [
        "Who is Malenia?",
        "What is Miquella's plan?",
        "Who killed Godwyn?",
        "What is the Frenzied Flame?",
    ]
    print("\nRetrieval test:")
    for q in test_queries:
        results = retrieve(q, top_k=3)
        print(f"\n  Q: {q}")
        if not results:
            print("  ❌ NO RESULTS")
        for r in results:
            print(f"  [{r['score']:.3f}] {r['name']} ({r['category']})")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    diagnose()