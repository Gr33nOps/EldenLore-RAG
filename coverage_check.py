"""
coverage_check.py
Scans the entire ChromaDB and finds:
1. Entries with wiki-title names (e.g. "Twinbird | Elden Ring Wiki" instead of "Twinbird")
2. Entries with very thin content (under 200 chars — likely scraped navigation text not lore)
3. Known important lore entities that have zero chunks at all
4. Entries with broken HTML (no spaces between words)

Run: python coverage_check.py
Outputs a report + a ready-to-use rescrape list you can feed into rescrape_missing.py
"""

import chromadb
from sentence_transformers import SentenceTransformer
import re
import json

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("elden_ring_lore")

total = collection.count()
print(f"Total chunks in DB: {total}")
print("Loading in batches (this takes ~60 seconds)...\n")

# ── Batch load everything ────────────────────────────────────────────────────
BATCH = 2000
all_docs   = []
all_metas  = []

for offset in range(0, total, BATCH):
    res = collection.get(
        include=["metadatas", "documents"],
        limit=BATCH,
        offset=offset,
    )
    all_docs.extend(res["documents"])
    all_metas.extend(res["metadatas"])
    print(f"  {min(offset + BATCH, total)}/{total}", end="\r")

print(f"Loaded {len(all_docs)} chunks.\n")

# ── Group chunks by name ─────────────────────────────────────────────────────
from collections import defaultdict
name_to_chunks = defaultdict(list)
for doc, meta in zip(all_docs, all_metas):
    name = meta.get("name", "UNKNOWN")
    name_to_chunks[name].append({
        "doc": doc,
        "category": meta.get("category", ""),
        "area": meta.get("area", ""),
    })

all_entry_names = set(name_to_chunks.keys())
print(f"Unique named entries in DB: {len(all_entry_names)}\n")

# ─────────────────────────────────────────────────────────────────────────────
# PROBLEM 1: Wiki-title names (contain " | " or " Wiki" or "| Elden Ring")
# These got saved with the full page title instead of the clean entity name
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 70)
print("PROBLEM 1: Entries with messy wiki-title names")
print("=" * 70)

wiki_title_entries = []
for name in all_entry_names:
    if " | " in name or "Wiki" in name or "Elden Ring" in name and len(name) > 30:
        wiki_title_entries.append(name)

wiki_title_entries.sort()
print(f"Found {len(wiki_title_entries)} entries with wiki-title names:\n")
for name in wiki_title_entries[:50]:
    chunk_count = len(name_to_chunks[name])
    sample = name_to_chunks[name][0]["doc"][:80].replace("\n", " ")
    print(f"  [{chunk_count} chunks] {name}")
    print(f"    → {sample}")

if len(wiki_title_entries) > 50:
    print(f"  ... and {len(wiki_title_entries) - 50} more")

# ─────────────────────────────────────────────────────────────────────────────
# PROBLEM 2: Thin entries (all chunks under 200 chars — almost no lore content)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("PROBLEM 2: Entries with very thin content (all chunks < 200 chars)")
print("=" * 70)

thin_entries = []
for name, chunks in name_to_chunks.items():
    max_len = max(len(c["doc"]) for c in chunks)
    if max_len < 200:
        thin_entries.append((name, max_len, chunks[0]["category"]))

thin_entries.sort(key=lambda x: x[1])
print(f"Found {len(thin_entries)} thin entries:\n")
for name, max_len, cat in thin_entries[:40]:
    sample = name_to_chunks[name][0]["doc"][:80].replace("\n", " ")
    print(f"  [{max_len} chars | {cat}] {name}")
    print(f"    → {sample}")

if len(thin_entries) > 40:
    print(f"  ... and {len(thin_entries) - 40} more")

# ─────────────────────────────────────────────────────────────────────────────
# PROBLEM 3: Broken HTML (run-together words — no spaces between words)
# Detected by high ratio of CamelCase transitions
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("PROBLEM 3: Entries with broken HTML (missing spaces between words)")
print("=" * 70)

def broken_html_score(text: str) -> float:
    """Returns ratio of CamelCase transitions to total chars. High = broken."""
    transitions = len(re.findall(r'[a-z][A-Z]', text))
    return transitions / max(len(text), 1)

broken_entries = []
for name, chunks in name_to_chunks.items():
    scores = [broken_html_score(c["doc"]) for c in chunks]
    avg_score = sum(scores) / len(scores)
    if avg_score > 0.015:  # more than 1.5% of chars are CamelCase transitions
        broken_entries.append((name, avg_score, chunks[0]["category"]))

broken_entries.sort(key=lambda x: -x[1])
print(f"Found {len(broken_entries)} entries with broken HTML:\n")
for name, score, cat in broken_entries[:30]:
    sample = name_to_chunks[name][0]["doc"][:100].replace("\n", " ")
    print(f"  [score={score:.3f} | {cat}] {name}")
    print(f"    → {sample}")

if len(broken_entries) > 30:
    print(f"  ... and {len(broken_entries) - 30} more")

# ─────────────────────────────────────────────────────────────────────────────
# PROBLEM 4: Known important lore entities with zero chunks
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("PROBLEM 4: Known important entities with ZERO chunks in DB")
print("=" * 70)

IMPORTANT_ENTITIES = [
    # Core lore
    "Elden Ring", "Golden Order", "Erdtree", "Shattering", "Greater Will",
    "Outer Gods", "Crucible", "Tarnished", "Grace", "Death",
    # Characters
    "Marika", "Radagon", "Godfrey", "Miquella", "Malenia", "Ranni",
    "Godwyn", "Morgott", "Mohg", "Rykard", "Maliketh", "Radahn",
    "Melina", "Blaidd", "Fia", "Patches", "Gideon", "Hewg",
    "Millicent", "Roderika", "Nepheli", "Gurranq", "Hyetta",
    "Tanith", "Sellen", "D Hunter", "Seluvis", "Rogier",
    "St. Trina", "Torrent", "Leda", "Ansbach", "Messmer",
    # Indirect entities
    "Gloam-Eyed Queen", "Serosh", "Twinbird", "Fell God",
    "Formless Mother", "Two Fingers", "Three Fingers",
    "Black Knife Assassins", "Night of the Black Knives",
    "Nox", "Albinauric", "Omen", "Empyrean", "Numen",
    # Key items
    "Cursemark of Death", "Fingerslayer Blade", "Coded Sword",
    "Miquella's Needle", "Deathroot", "Rune of Death",
    "Fingerslayer Blade", "Dark Moon Ring", "Haligtree Medallion",
    # Endings
    "Age of Fracture", "Age of Stars", "Age of Order",
    "Age of the Duskborn", "Blessing of Despair",
    "Lord of the Frenzied Flame",
    # Areas
    "Limgrave", "Leyndell", "Caelid", "Liurnia", "Altus Plateau",
    "Mountaintops of the Giants", "Crumbling Farum Azula",
    "Nokron", "Mohgwyn Palace", "Haligtree", "Elphael",
    "Land of Shadow", "Shadow Keep", "Enir-Ilim",
    # DLC
    "Promised Consort Radahn", "Bayle", "Midra", "Romina",
    "Rellana", "Metyr", "Scadutree Avatar", "Dancing Lion",
]

all_names_lower = {n.lower(): n for n in all_entry_names}
missing_important = []

for entity in IMPORTANT_ENTITIES:
    # Check exact match
    if entity.lower() not in all_names_lower:
        # Check partial match
        partial = [n for n in all_entry_names if entity.lower() in n.lower()]
        if partial:
            print(f"  [PARTIAL] '{entity}' → found as: {partial[0]}")
        else:
            missing_important.append(entity)
            print(f"  [MISSING] {entity}")

print(f"\n{len(missing_important)} important entities completely absent from DB")

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY REPORT
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Total chunks:          {total}")
print(f"Unique entries:        {len(all_entry_names)}")
print(f"Wiki-title names:      {len(wiki_title_entries)}")
print(f"Thin entries (<200c):  {len(thin_entries)}")
print(f"Broken HTML entries:   {len(broken_entries)}")
print(f"Missing important:     {len(missing_important)}")

total_problems = (
    len(wiki_title_entries) +
    len(thin_entries) +
    len(broken_entries) +
    len(missing_important)
)
print(f"\nTotal problem entries: {total_problems}")

# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT: Save full report to file
# ─────────────────────────────────────────────────────────────────────────────
report = {
    "total_chunks": total,
    "unique_entries": len(all_entry_names),
    "wiki_title_names": wiki_title_entries,
    "thin_entries": [(n, l, c) for n, l, c in thin_entries],
    "broken_html_entries": [(n, round(s, 4), c) for n, s, c in broken_entries],
    "missing_important": missing_important,
}

with open("coverage_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print("\nFull report saved to: coverage_report.json")
print("\nNext steps:")
print("  1. Review the output above")
print("  2. Run: python rescrape_missing.py   (fixes the 23 known missing entries)")
print("  3. For wiki-title and broken HTML entries, the scraper needs a fix")
print("     to use get_text(separator=' ') instead of get_text(strip=True)")
print("  4. For truly missing entries, add them to rescrape_missing.py")