# EldenLore RAG: The Compendium of Grace

> "Arise now, ye Tarnished, ye dead who yet live. The call of long-lost lore speaks to us all..."

EldenLore RAG is a vessel of forbidden knowledge, forged to peer through the fog of the Lands Between. It is an AI-powered Retrieval-Augmented Generation (RAG) construct designed to summon the lost history, broken lineages, and cryptic truths of the Golden Order through natural language conversations, legendary character personas, and trials of wit.

By binding a custom lore database to the semantic currents of ChromaDB and Sentence Transformers, this artifact allows any scholar to interrogate the history of the Lands Between and receive context-aware answers untainted by the Shattering.

## Manifested Features

* **Sight of Grace (Semantic Lore Retrieval):** Traverse the vast expanse of Elden Ring documentation with precise semantic searches.
* **Whispers of the Two Fingers (Groq-Powered LLM):** Receive deep, context-aware answers forged by high-performance Groq language models.
* **The Finger Maiden's Chronicle:** A robust Retrieval-Augmented Generation (RAG) pipeline that anchors AI responses in absolute truth.
* **Echoes of the Roundtable Hold:** Engage with multiple lore-focused character personas, each viewing the world through their own fractured lens.
* **Trials of the Crucible:** Test your resolve and knowledge with interactive lore quizzes.
* **Gleaning the Erdtree:** Automated web scraping and ingestion tools to harvest text from the far reaches of the digital ether.
* **Memory Stone Ledger:** Coverage analysis scripts to ensure your lore database is whole and unbroken.
* **The Scrying Mirror:** A beautiful, seamless web interface powered by Streamlit.

## The Forge (Tech Stack)

* **Front-of-House:** Streamlit
* **The Greater Will (LLM):** Groq
* **The Subterranean Shunning-Grounds (Vector DB):** ChromaDB
* **The Golden Order (Embeddings):** Sentence Transformers
* **The Script:** Python
* **The Harvester:** BeautifulSoup and Requests

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
├── Rescrape_missing.py       # Seeking Lost Runes (Missing data scraper)
├── quiz.py                   # Trials of the Crucible (Lore quiz system)
├── coverage_check.py         # The All-Knowing's Gaze (Coverage analysis)
├── requirements.txt          # Necessary incantations (Dependencies)
├── .env.example              # Template for binding runes
├── .gitignore
└── README.md

```

## Awakening the Construct (Installation)

Before you can query the Erdtree, you must prepare your environment.

### 1. Claim the Artifact

```bash
git clone https://github.com/Gr33nOps/EldenLore-RAG.git
cd EldenLore-RAG

```

### 2. Concoct the Environment

Summon a virtual space to isolate your incantations:

* **Windows:**
```cmd
python -m venv venv
venv\Scripts\activate

```



```
* **macOS/Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate

```

### 3. Gather the Materials

Install the required dependencies into your environment:

```bash
pip install -r requirements.txt

```

### 4. Binding the Runes (.env)

The construct requires a key to access the power of Groq. Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here

```

Alternatively, copy the provided template:

```bash
cp .env.example .env

```

Open the file and scribe your actual API key within.

## Igniting the Crucible (Database Build)

Before launching the application for the first time, you must breathe life into the memory banks by ingesting the lore documents:

```bash
python ingest.py

```

*This ritual manifests the local ChromaDB vector database from the raw texts.*

## Crossing the Fog (Run the Application)

Once the database is forged, ignite the Streamlit interface:

```bash
streamlit run app.py

```

Step through the fog by navigating your browser to:

> http://localhost:8501

## Rituals of Maintenance

### Recovering Lost Fragments

If some lore fragments failed to harvest, run the re-scraper to seek out missing entries:

```bash
python Rescrape_missing.py

```

### Gaze of the All-Knowing

To check how complete your database is compared to the grand history of the world:

```bash
python coverage_check.py

```

### Reinforcing the Erdtree

If you manually alter or add text files to `data/lore/`, you must mend the vector database:

```bash
python ingest.py

```

## Mending the Fractured Order (Troubleshooting)

### ModuleNotFoundError

Your environment lacks the proper incantations. Ensure your virtual environment is active and cast:

```bash
pip install -r requirements.txt

```

### Streamlit Launcher Broken (After Moving the Project)

If you have moved the directory across your file system, the local environment path is shattered. Purge it and cast the ritual anew:

```bash
rm -rf venv
python -m venv venv

```

*Re-install your dependencies after doing this.*

### The Great Emptiness (Missing Vector Database)

If the AI speaks nonsense or claims to know nothing, your database hasn't been forged yet. Run:

```bash
python ingest.py

```

## Disclaimer

This project is a fan-made, educational tool and is completely unaffiliated with FromSoftware or Bandai Namco Entertainment. All Elden Ring intellectual property, lore, names, and assets belong entirely to their respective owners. May grace guide your steps.