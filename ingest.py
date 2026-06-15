"""
ingest.py  — Elden Ring lore ingest (fixed)

ROOT CAUSE FIXES:

  BUG 1 — Prefix was embedded WITH the text (shifts vectors, hurts retrieval).
    Fix: embed_text = clean prose only. display_text = prefixed for prompts.

  BUG 2 — Collection used L2 distance (ChromaDB default).
    Fix: metadata={"hnsw:space": "cosine"} on collection creation.
         Requires --reset once to rebuild.

  BUG 3 — RESET_COLLECTION=True by default wiped DB every run.
    Fix: Default False. Use --reset CLI flag or RESET_DB=1 env var.

  BUG 4 — split_text() had infinite loop risk when overlap >= chunk_size/4.
    Fix: Enforce start always advances by at least CHUNK_SIZE // 4.

  BUG 5 — CHUNK_OVERLAP=300 of CHUNK_SIZE=800 (37.5%) caused duplicate chunk spam.
    Fix: CHUNK_OVERLAP reduced to 120 (15%).

  BUG 6 — visual_lore mapped to generic "lore" category.
    Fix: visual_lore gets its own "visual_lore" category for targeted retrieval.

  BUG 7 — make_chunk_id() hash collisions caused DuplicateIDError.
    Original attempt: hashed body[:200] — but overlapping chunks SHARE their
    first 200 chars, so adjacent chunks from the same long entry collided.
    Fix: hash the FULL body text + chunk_index together. The full text is unique
    per chunk even with overlap. chunk_index in the hash (not just the suffix)
    adds a second layer of uniqueness. Global dedup in batch_upsert as a
    final safety net.
"""

import argparse
import hashlib
import os
import re
import sys

import chromadb
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
LORE_DIR        = "data/lore"
CHROMA_PATH     = "./chroma_db"
COLLECTION_NAME = "elden_ring_lore"

CHUNK_SIZE    = 800   # Max characters per chunk before splitting
CHUNK_OVERLAP = 120   # 15% overlap — enough for sentence continuity, not spammy
BATCH_SIZE    = 64

RESET_COLLECTION = os.environ.get("RESET_DB", "0") == "1"

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Ingest Elden Ring lore into ChromaDB")
parser.add_argument("--reset",    action="store_true", help="Wipe collection and rebuild")
parser.add_argument("--file",     type=str, default=None, help="Only ingest a specific file stem")
parser.add_argument("--validate", action="store_true", help="Run retrieval validation after ingest")
args, _ = parser.parse_known_args()
if args.reset:
    RESET_COLLECTION = True

# ---------------------------------------------------------------------------
# CATEGORY MAP
# ---------------------------------------------------------------------------
FILE_TO_CATEGORY: dict[str, str] = {
    "bosses":         "boss",
    "characters":     "character",
    "areas":          "area",
    "lore":           "lore",
    "weapons":        "weapon",
    "spells":         "spell",
    "creatures":      "creature",
    "items":          "item",
    "talismans":      "talisman",
    "armor":          "armor",
    "great_runes":    "great_rune",
    "spirit_ashes":   "spirit_ash",
    "ashes_of_war":   "ash_of_war",
    "shields":        "shield",
    "whetblades":     "whetblade",
    "bell_bearings":  "bell_bearing",
    "crystal_tears":  "crystal_tear",
    "cookbooks":      "cookbook",
    "paintings":      "painting",
    "endings":        "ending",
    "questlines":     "questline",
    "dialogue":       "dialogue",
    "cutscenes":      "cutscene",
    "cut_content":    "cut_content",
    "visual_lore":    "visual_lore",   # own category for appearance/design facts
    "manual_patches": "character",
    "missing_lore":   "lore",
}

PROCESS_ORDER: list[str] = (
    [k for k in FILE_TO_CATEGORY if k not in ("manual_patches", "visual_lore")]
    + ["visual_lore", "manual_patches"]
)

# ---------------------------------------------------------------------------
# INIT
# ---------------------------------------------------------------------------
model  = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path=CHROMA_PATH)

if RESET_COLLECTION:
    try:
        client.delete_collection(COLLECTION_NAME)
        print("⚠  Collection wiped. Rebuilding with cosine distance.\n")
    except Exception:
        pass

collection = client.get_or_create_collection(
    COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)

# ---------------------------------------------------------------------------
# DATA CLEANING
# ---------------------------------------------------------------------------
def clean_name(name: str) -> str:
    if " | " in name:
        name = name.split(" | ")[0].strip()
    name = re.sub(r'\s*\|\s*Elden Ring\s*Wiki.*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\|\s*Wiki.*$',              '', name, flags=re.IGNORECASE)
    if len(name) > 25 and "Location and How to Get" in name:
        name = re.sub(r'\s+Location and How to Get.*$', '', name, flags=re.IGNORECASE)
    return name.strip()


def fix_spaces(text: str) -> str:
    keywords = ["in", "is", "the", "and", "of", "with", "for", "to", "by", "at", "from"]
    for kw in keywords:
        text = re.sub(r'\b' + kw + r'([A-Z])', kw + r' \1', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


# ---------------------------------------------------------------------------
# RAG HELPERS
# ---------------------------------------------------------------------------
def make_chunk_id(file_stem: str, raw_name: str, chunk_index: int, body: str) -> str:
    """
    Generate a collision-proof ID for a chunk.

    Key insight: overlapping chunks from the same entry SHARE their opening
    characters. Using body[:200] as the hash input meant chunk 0 and chunk 1
    of a long boss entry could have identical fingerprints → DuplicateIDError.

    Fix: hash the FULL body text. Every overlapping chunk has slightly different
    content (shifted window), so the full text is unique per chunk.
    chunk_index is also included in both the hash AND the suffix for two
    independent layers of uniqueness.
    """
    fingerprint = f"{file_stem}:{raw_name}:{chunk_index}:{body}"
    content_hash = hashlib.md5(fingerprint.encode()).hexdigest()
    return f"{file_stem}__{content_hash}__{chunk_index}"


def split_text(text: str) -> list[str]:
    """Split text into overlapping chunks with guaranteed forward progress."""
    if len(text) <= CHUNK_SIZE:
        return [text]

    min_advance = max(CHUNK_SIZE // 4, 1)
    segments: list[str] = []
    start = 0

    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        segment = text[start:end]

        if end < len(text):
            for sep in (". ", ".\n", "\n\n", "\n"):
                pos = segment.rfind(sep)
                if pos > CHUNK_SIZE // 2:
                    end     = start + pos + len(sep)
                    segment = text[start:end]
                    break

        cleaned = segment.strip()
        if cleaned:
            segments.append(cleaned)

        next_start = end - CHUNK_OVERLAP
        start = max(next_start, start + min_advance)

    return segments


def parse_lore_file(filepath: str, category: str) -> list[dict]:
    with open(filepath, "r", encoding="utf-8") as fh:
        raw = fh.read()

    file_stem = os.path.splitext(os.path.basename(filepath))[0]
    chunks: list[dict] = []
    seen_ids: set[str] = set()   # per-file dedup as a safety net

    for entry in raw.split("---"):
        entry = entry.strip()
        if not entry:
            continue

        area        = ""
        chapter     = 1
        name        = ""
        body_lines: list[str] = []

        for line in entry.splitlines():
            if   line.startswith("area:"):
                area = line[5:].strip()
            elif line.startswith("chapter:"):
                try:    chapter = int(line[8:].strip())
                except: chapter = 1
            elif line.startswith("name:"):
                name = line[5:].strip()
            else:
                body_lines.append(line)

        body = "\n".join(body_lines).strip()
        if not body or not name:
            continue

        clean_entry_name = clean_name(name)
        clean_body       = fix_spaces(body)
        sub_chunks       = split_text(clean_body)
        n                = len(sub_chunks)

        for idx, sub in enumerate(sub_chunks):
            chunk_id = make_chunk_id(file_stem, name, idx, sub)

            if chunk_id in seen_ids:
                # Should never happen with the full-body hash, but log if it does
                print(f"\n  ⚠ Skipping duplicate chunk ID: {chunk_id} (entry: {name})")
                continue
            seen_ids.add(chunk_id)

            embed_text   = sub
            display_text = f"[{category.upper()} - {clean_entry_name}] {sub}"

            chunks.append({
                "id":           chunk_id,
                "embed_text":   embed_text,
                "display_text": display_text,
                "name":         clean_entry_name,
                "area":         area,
                "chapter":      chapter,
                "category":     category,
                "chunk_index":  idx,
                "total_chunks": n,
            })

    return chunks


def batch_upsert(chunks: list[dict]) -> None:
    # Global dedup across all chunks before sending to ChromaDB
    seen: set[str] = set()
    deduped: list[dict] = []
    for c in chunks:
        if c["id"] not in seen:
            seen.add(c["id"])
            deduped.append(c)

    if len(deduped) < len(chunks):
        print(f"\n  ⚠ Dropped {len(chunks) - len(deduped)} duplicate IDs before upsert")

    for i in range(0, len(deduped), BATCH_SIZE):
        batch = deduped[i : i + BATCH_SIZE]

        embed_texts   = [c["embed_text"]   for c in batch]
        display_texts = [c["display_text"] for c in batch]
        embeddings    = model.encode(embed_texts, show_progress_bar=False).tolist()

        collection.upsert(
            documents=display_texts,
            embeddings=embeddings,
            metadatas=[
                {
                    "name":         c["name"],
                    "area":         c["area"],
                    "chapter":      c["chapter"],
                    "category":     c["category"],
                    "chunk_index":  c["chunk_index"],
                    "total_chunks": c["total_chunks"],
                }
                for c in batch
            ],
            ids=[c["id"] for c in batch],
        )


# ---------------------------------------------------------------------------
# POST-INGEST VALIDATION
# ---------------------------------------------------------------------------
def validate_ingest() -> None:
    val_model = SentenceTransformer("all-MiniLM-L6-v2")

    test_cases = [
        ("Why is Ranni blue",          ["ranni", "blue", "colour", "color", "pale"]),
        ("Who is Malenia",             ["malenia", "blade", "miquella", "rot"]),
        ("What is the Frenzied Flame", ["frenzied", "flame", "three fingers"]),
        ("Who killed Godwyn",          ["godwyn", "black knife", "ranni", "night"]),
        ("What is Serosh",             ["serosh", "godfrey", "beast", "crucible"]),
    ]

    width = 64
    print(f"\n{'═' * width}")
    print("  POST-INGEST VALIDATION")
    print(f"{'═' * width}")
    print(f"  DB size: {collection.count()} documents\n")

    all_passed = True
    for query, expected_keywords in test_cases:
        embedding = val_model.encode(query).tolist()
        n = min(5, collection.count())
        results = collection.query(query_embeddings=[embedding], n_results=n)

        top_score   = 0.0
        top_name    = "(none)"
        keyword_hit = False

        if results["ids"][0]:
            dist        = results["distances"][0][0]
            top_score   = round(max(0.0, 1.0 - dist), 3)
            top_name    = results["metadatas"][0][0].get("name", "?")
            all_docs    = " ".join(results["documents"][0]).lower()
            keyword_hit = any(kw in all_docs for kw in expected_keywords)

        status = "✓" if top_score >= 0.30 and keyword_hit else "✗ LOW"
        if "✗" in status:
            all_passed = False

        print(f"  {status}  [{top_score:.3f}]  Q: {query[:38]:<38}")
        print(f"           Top result: {top_name}")
        if not keyword_hit:
            print(f"           ⚠ Expected keywords not found: {expected_keywords}")
        print()

    if all_passed:
        print("  All checks passed — your data is retrievable.\n")
    else:
        print("  ⚠ Some checks failed.")
        print("    • Check that the relevant .txt files exist in data/lore/")
        print("    • Run with --reset if you switched to cosine distance recently")
        print("    • Check that entries have correct name:/--- format\n")

    print(f"{'═' * width}\n")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def ingest_all() -> None:
    print(f"Elden Ring Lore Ingest  —  source: {LORE_DIR}/")
    print(f"Reset : {'YES — wiping first' if RESET_COLLECTION else 'NO — upsert only (safe)'}")
    print(f"Chunks: max {CHUNK_SIZE} chars, overlap {CHUNK_OVERLAP} chars\n")

    category_stats: dict[str, int] = {}
    total_chunks  = 0
    total_entries = 0

    files_to_process = [args.file] if args.file else PROCESS_ORDER

    for file_stem in files_to_process:
        if file_stem not in FILE_TO_CATEGORY:
            print(f"  [unknown] '{file_stem}' not in FILE_TO_CATEGORY — skipping")
            continue

        category = FILE_TO_CATEGORY[file_stem]
        filepath = os.path.join(LORE_DIR, f"{file_stem}.txt")

        if not os.path.exists(filepath):
            if args.file:
                print(f"  [ERROR] {filepath} not found!")
                sys.exit(1)
            print(f"  [skip]   {file_stem}.txt  (file not found)")
            continue

        chunks = parse_lore_file(filepath, category)
        if not chunks:
            print(f"  [empty]  {file_stem}.txt — no parseable entries (check name:/--- format)")
            continue

        unique_names = len({c["name"] for c in chunks})
        print(
            f"  [{category:<14s}] {file_stem}.txt"
            f"  {unique_names:>4} entries → {len(chunks):>5} chunks ...",
            end="", flush=True,
        )

        batch_upsert(chunks)

        category_stats[category] = category_stats.get(category, 0) + len(chunks)
        total_chunks  += len(chunks)
        total_entries += unique_names
        print("  ✓")

    width = 60
    print(f"\n{'═' * width}")
    print(f"  Ingest complete")
    print(f"{'═' * width}")
    print(f"  {'Category':<18}  {'Chunks':>7}")
    print(f"  {'─' * 30}")
    for cat, count in sorted(category_stats.items(), key=lambda x: -x[1]):
        print(f"  {cat:<18}  {count:>7}")
    print(f"  {'─' * 30}")
    print(f"  {'TOTAL':<18}  {total_chunks:>7}")
    print(f"{'═' * width}")
    print(f"\n  DB path    : {CHROMA_PATH}")
    print(f"  Distance   : cosine")
    print(f"  Total docs : {collection.count()}")

    if args.validate or RESET_COLLECTION:
        validate_ingest()
    else:
        print(f"\n  Tip: run with --validate to confirm retrieval quality\n")


if __name__ == "__main__":
    ingest_all()