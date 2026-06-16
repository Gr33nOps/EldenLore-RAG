# EldenLore RAG: The Compendium of Grace

> *"Arise now, ye Tarnished, ye dead who yet live. The call of long-lost lore speaks to us all..."*

EldenLore RAG is a vessel of forbidden knowledge, forged to pierce the fog of the Lands Between. An AI-powered Retrieval-Augmented Generation construct, it summons lost history, broken lineages, and the cryptic truths of the Golden Order through natural language — delivered through legendary character personas and tested by trials of wit.

A custom lore database, bound to the semantic currents of ChromaDB and Sentence Transformers, allows any scholar to interrogate the Lands Between and receive answers untainted by the Shattering.

---

## Manifested Features

- **Sight of Grace** — Semantic search across the full breadth of Elden Ring lore
- **Whispers of the Two Fingers** — Deep, context-aware answers forged by Groq language models
- **The Finger Maiden's Chronicle** — A RAG pipeline that anchors every response in truth
- **Echoes of the Roundtable Hold** — Multiple character personas, each viewing the world through their own fractured lens
- **Trials of the Crucible** — Interactive lore quizzes to test your resolve and knowledge
- **Gleaning the Erdtree** — Web scraping tools to harvest text from the far reaches of the digital ether
- **Memory Stone Ledger** — Coverage analysis to ensure your lore database remains whole and unbroken
- **The Scrying Mirror** — A seamless web interface, powered by Streamlit

---

## The Forge

| Layer | Tool |
|---|---|
| Interface | Streamlit |
| LLM | Groq |
| Vector Database | ChromaDB |
| Embeddings | Sentence Transformers |
| Language | Python |
| Scraping | BeautifulSoup & Requests |

---

## Anatomy of the Compendium

```text
EldenLore-RAG/
│
├── data/
│   └── lore/                 # Sacred texts and historical records
│
├── app.py                    # The Scrying Mirror (Streamlit application)
├── bot.py                    # The Spirit Tuning Core (LLM and persona logic)
├── retriever.py              # Guiding Grace (ChromaDB retrieval pipeline)
├── ingest.py                 # Smelting the Lore (Document ingestion script)
├── scraper.py                # The Remembrance Harvester (Lore scraper)
├── Rescrape_missing.py       # Seeking Lost Runes (Missing data re-scraper)
├── quiz.py                   # Trials of the Crucible (Lore quiz system)
├── coverage_check.py         # The All-Knowing's Gaze (Coverage analysis)
├── requirements.txt          # Necessary incantations (Dependencies)
├── .env.example              # Template for binding runes
└── README.md
```

---

## Awakening the Construct

### 1. Claim the Artifact

```bash
git clone https://github.com/Gr33nOps/EldenLore-RAG.git
cd EldenLore-RAG
```

### 2. Concoct the Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Gather the Materials

```bash
pip install -r requirements.txt
```

### 4. Bind the Runes

The construct requires a Groq API key. Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Or copy the provided template and inscribe your key within:

```bash
cp .env.example .env
```

---

## Igniting the Crucible

Before the application can speak, you must breathe life into the memory banks:

```bash
python ingest.py
```

This forges the local ChromaDB vector database from the raw lore texts. It must be run once before launching the app for the first time, and again whenever you add or alter files in `data/lore/`.

---

## Crossing the Fog

```bash
streamlit run app.py
```

Step through the fog at:

> http://localhost:8501

---

## Rituals of Maintenance

**Recover missing lore fragments:**
```bash
python Rescrape_missing.py
```

**Check database coverage against the full history of the world:**
```bash
python coverage_check.py
```

---

## Mending the Fractured Order

**`ModuleNotFoundError`** — Your environment lacks the proper incantations. Ensure your virtual environment is active, then:
```bash
pip install -r requirements.txt
```

**Streamlit fails after moving the project** — The local environment path is shattered. Purge it and begin anew:
```bash
rm -rf venv
python -m venv venv
pip install -r requirements.txt
```

**The AI speaks nonsense or claims to know nothing** — Your vector database has not been forged. Run:
```bash
python ingest.py
```

---

## Disclaimer

This is a fan-made, educational project with no affiliation to FromSoftware or Bandai Namco Entertainment. All Elden Ring intellectual property, lore, names, and assets belong entirely to their respective owners.

*May grace guide your steps.*