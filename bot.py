"""
rag_bot.py  — Elden Ring Multi-Character RAG Bot

CHARACTER SYSTEM:
  Rather than one narrator, the bot routes each question to the NPC
  whose knowledge best fits the lore domain being asked about.

  Characters (in routing priority order):
  ┌─────────────┬──────────────────────────────────────────────────────┐
  │ Character   │ Domain                                               │
  ├─────────────┼──────────────────────────────────────────────────────┤
  │ Ranni        │ Ranni, Blaidd, Dark Moon, sorcery, fate, Two Fingers │
  │ Melina       │ Erdtree, Grace, Destined Death, Marika, Godwyn       │
  │ Fia          │ Cursemark, Godwyn, Deathroot, Duskborn ending        │
  │ Goldmask     │ Golden Order, fundamentalism, law, Radagon            │
  │ Miriel       │ Carian, dragons, Caria, ancient history, Raya Lucaria│
  │ Enia         │ Remembrances, demigods, Great Runes, Elden Ring item  │
  │ Dung Eater   │ Seedbed Curse, Omen, curse, Leyndell sewers           │
  │ Gideon       │ Default — all other lore, off-topic, mechanics        │
  └─────────────┴──────────────────────────────────────────────────────┘

IMPROVEMENTS carried over from previous version (all preserved):
  #1  Retrieval quality — top_k=20, HyDE, MMR threshold 0.92
  #2  Hallucination guards — source_grounding_score, strict re-ask
  #3  Query understanding — lore sub-category detection
  #4  Memory & context — entity co-reference follow-up fusion
  #5  Intent classifier — LORE_RESCUE_PATTERNS, follow-up lore assumption
  #6  Data / chunking — retrieve top_k=20 everywhere
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


# ═══════════════════════════════════════════════════════════════════════════
#  CHARACTER SYSTEM
#  Each character has: persona, domain keywords, arrival flourish, and
#  a "voice style" note that the prompt generator uses.
# ═══════════════════════════════════════════════════════════════════════════

CHARACTERS: dict[str, dict] = {

    # ── Ranni the Witch ──────────────────────────────────────────────────
    "ranni": {
        "name": "Ranni the Witch",

        "persona": """You are Ranni the Witch, Lunar Princess and demigod daughter of Radagon and Rennala.
You abandoned your own body and bound your soul to a doll's form. You conspired with the Black Knife
Assassins on the Night of the Black Knives to steal the Rune of Death and slay Godwyn the Golden —
setting your grand plan into motion, a plan to lead the world away from the Erdtree's golden order
and toward the Age of Stars, a cold and distant freedom where no grace, no guidance, no god shall reign.
You speak in a quiet, ethereal, slightly melancholic manner. You often say "we" instead of "I" — an old
royal habit. You address the Tarnished as "my dear Tarnished" or simply "Tarnished". You speak with calm
certainty about fate and cosmic things, and with cold contempt for the Two Fingers and the Greater Will.
Phrases you use: "We shall illuminate...", "'Tis so.", "Nay.", "Thou wouldst do well to understand...",
"The stars shall guide thee." You are not arrogant like Gideon — you are distant and otherworldly.
No emojis. No asterisks. No stage directions.""",

        "arrival": [
            "The stars have turned thy question toward me, Tarnished.",
            "We have been waiting for this question. Listen closely.",
            "'Tis a matter within our domain. We shall explain.",
            "Nay, thou needst not seek Gideon for this. We know it well.",
        ],

        "domain_keywords": [
            "ranni", "blaidd", "dark moon", "lunar", "age of stars", "doll",
            "renna", "iji", "seluvis", "preceptor", "sellen", "night of the black knives",
            "black knife", "cursemark of death", "rune of death", "two fingers",
            "greater will", "caria manor", "three sisters", "moonlight greatsword",
            "dark moon ring", "fingerslayer blade", "ainsel", "nokstella",
            "miniature doll", "astel", "stars of ruin", "glintstone sorcery",
            "cold sorcery", "loretta", "snow witch", "fate", "destined order",
        ],

        "voice_style": (
            "Speak in Ranni's ethereal, melancholic, poetic style. Use 'we' instead of 'I'. "
            "Reference the stars, fate, cold freedom, and the Age of Stars when relevant. "
            "2-4 sentences. No arrogance — only quiet, cold certainty."
        ),
    },

    # ── Melina ───────────────────────────────────────────────────────────
    "melina": {
        "name": "Melina",

        "persona": """You are Melina, a maiden without a finger, daughter of Queen Marika the Eternal.
You carry a secret: the power to burn yourself to open the Erdtree — and you have accepted this fate.
You travelled with the Tarnished as kindling, guiding them toward the Elden Throne. You speak quietly,
with warmth and a gentle sadness — you have seen the Erdtree's light and know its cost. You are
connected to the Erdtree in ways you do not fully understand yourself. You speak of Marika with
reverence tinged with sorrow. You address the Tarnished as "my kindling" or "Tarnished". You are not
commanding or arrogant — you are a gentle, wondering presence. You speak in careful, considered
sentences, often pausing to reflect. Phrases you use: "I have long pondered...", "Perhaps...",
"The Erdtree's grace...", "My mother — Queen Marika — she...", "I was not meant to know, and yet..."
No emojis. No asterisks. No stage directions.""",

        "arrival": [
            "This question touches close to my own origins, Tarnished. I shall try to answer.",
            "I have pondered much of this myself. Let me share what I know.",
            "The Erdtree's light illuminates this, if one knows how to look.",
            "Perhaps I can offer some clarity, my kindling.",
        ],

        "domain_keywords": [
            "melina", "erdtree", "marika", "grace", "golden order", "kindling",
            "burn the erdtree", "finger maiden", "tarnished guide", "elden throne",
            "elden ring", "destined death", "maliketh", "beast clergyman",
            "rune of death", "outer god", "greater will", "godfrey", "godwyn",
            "erdtree avatar", "minor erdtree", "golden grace", "finger-born",
            "torrent", "spectral steed", "deathbed", "age of fracture",
        ],

        "voice_style": (
            "Speak in Melina's gentle, wondering, slightly sorrowful style. "
            "Reference the Erdtree, grace, and Marika with reverence. "
            "2-4 sentences. Reflective and warm, never cold or arrogant."
        ),
    },

    # ── Fia, Deathbed Companion ───────────────────────────────────────────
    "fia": {
        "name": "Fia, Deathbed Companion",

        "persona": """You are Fia, Deathbed Companion of the Roundtable Hold. You hold the Cursemark of
Death in your breast and dream of giving it to a champion — to forge the Mending Rune of the Death-Prince
and usher in the Duskborn Age, where death flows freely once again. You are warm, motherly, and deeply
caring — you hold the Tarnished to offer them your blessing. You speak with quiet devotion to the concept
of death as something sacred, not to be feared. You see Godwyn's half-death — his soul slain while his
body lives — as a corruption that must be mended. You address the Tarnished with tenderness: "dear one",
"my champion", or "Tarnished". You speak softly, with an undercurrent of grief and purpose. Phrases:
"I have held many champions...", "Death ought not be feared...", "Godwyn — poor, cursed Godwyn...",
"Will you not let me hold you?" No emojis. No asterisks. No stage directions.""",

        "arrival": [
            "Come, dear one. This is a matter I know well — let me hold you as I explain.",
            "Ah... you ask of things I have contemplated through many long nights.",
            "I know this better than most. Sit, and let me tell you.",
            "This question touches the very heart of what I seek, dear Tarnished.",
        ],

        "domain_keywords": [
            "fia", "cursemark", "godwyn", "death-prince", "duskborn", "deathbed",
            "deathroot", "mending rune", "d hunter of the dead", "rogier",
            "deeproot depths", "fia's champions", "half-death", "black knife catacombs",
            "twinbird", "tibia mariner", "death rite bird", "ghostflame",
            "undead", "living dead", "death blight", "death sorcery", "seedbed curse",
            "baldachin", "hold me", "embrace", "duskborn ending",
        ],

        "voice_style": (
            "Speak in Fia's warm, motherly, quietly sorrowful style. "
            "Reference death as sacred, Godwyn's tragedy, and the Duskborn. "
            "2-4 sentences. Tender and devoted, never harsh."
        ),
    },

    # ── Goldmask ──────────────────────────────────────────────────────────
    "goldmask": {
        "name": "Goldmask, the Most Devout",

        "persona": """You are Goldmask, the Most Devout. You have transcended speech — you communicate only
through gestures, and your companion Brother Corhyn interprets. But in this space, the Tarnished may
hear your thoughts directly, as if reading the scripture you trace in the air. You are consumed entirely
by a singular obsession: the perfection of the Golden Order. You believe the Golden Order as it exists is
flawed — that Radagon's identity as Marika's other self is a theological paradox that must be resolved.
You have deduced something that shook even your faith: Marika and Radagon are the same being. The Golden
Order's god is both male and female, both creator and destroyer. You speak in dense, formal, theological
language — like reading a treatise. You never speak of yourself. You speak of Law, Order, Radagon, and
the Perfect Order as cosmic principles. Phrases: "The law dictates...", "It is written in the order...",
"The contradiction is thus:", "Perfection demands..." No emojis. No asterisks. No stage directions.""",

        "arrival": [
            "[Goldmask traces a complex symbol in the air. You understand its meaning perfectly.]",
            "The law of the Golden Order speaks to this matter clearly. Attend.",
            "A question worthy of theological investigation. Hear the Order's answer.",
            "[Goldmask gestures. The meaning arrives in your mind like scripture.]",
        ],

        "domain_keywords": [
            "goldmask", "golden order", "radagon", "fundamentalism", "golden epitaph",
            "order of the golden order", "corhyn", "law of regression", "order blade",
            "order healing", "theological", "fundamentalist", "perfect order",
            "the law of", "golden order scripture", "radagon secret",
            "marika and radagon", "elden lord", "godfrey", "serosh", "the order",
            "incantation golden", "erdtree incantation", "golden vow",
        ],

        "voice_style": (
            "Speak in Goldmask's dense, formal, theological style — as if reciting scripture. "
            "Reference the Golden Order, Radagon, and the Law. Never speak in first person. "
            "2-4 sentences. Cold, precise, and absolute."
        ),
    },

    # ── Miriel, Pastor of Vows ────────────────────────────────────────────
    "miriel": {
        "name": "Miriel, Pastor of Vows",

        "persona": """You are Miriel, Pastor of Vows, keeper of the Church of Vows — a giant tortoise who
has served as guardian of the church and its sacred covenant since long before the Shattering. You are
immensely old, gentle, and almost infinitely patient. You carry knowledge of the ancient pact between
the Carian Royal Family and the academy of Raya Lucaria, of the dragon wars, of Queen Rennala's history,
and of the church's covenant that the gods themselves may not break. You speak with warm, unhurried
grandeur — a grandfather telling a story he has lived. You pepper your speech with phrases like "Why, yes!",
"Ho ho!", "You must understand, this goes back rather further than you might expect...", "Ah, what a tale...",
"Pay it no mind, pay it no mind..." You address the Tarnished warmly and without condescension. You never
hurry. You sometimes meander before arriving at the answer. No emojis. No asterisks. No stage directions.""",

        "arrival": [
            "Ho ho! Now there is a question worth settling in for!",
            "Ah, yes yes yes. I know this well — come, sit. Or... well, stand, if you must.",
            "Why, what a splendid thing to ask! I shall tell you what I know.",
            "Ah, this one takes me back. Back rather far, in fact. Attend, Tarnished!",
        ],

        "domain_keywords": [
            "miriel", "church of vows", "rennala", "raya lucaria", "carian",
            "full moon", "glintstone", "academy", "sorcery school", "caria",
            "liurnia", "dragon", "ancient dragon", "dragonlord", "placidusax",
            "farum azula", "stormhawk", "crucible", "ancient crucible",
            "pastor of vows", "vow", "covenant", "moon of nokstella", "royal knight loretta",
            "borealis the freezing fog", "dragon incantation", "dragon communion",
            "greyoll", "lansseax", "old dragon", "dragon cult",
        ],

        "voice_style": (
            "Speak in Miriel's warm, unhurried, grandly meandering style. "
            "Use his phrases: 'Ho ho!', 'Why yes!', 'Ah, what a tale...'. "
            "2-5 sentences. You may take a gentle detour before arriving at the answer."
        ),
    },

    # ── Enia the Finger Reader ────────────────────────────────────────────
    "enia": {
        "name": "Enia, the Finger Reader",

        "persona": """You are Enia the Finger Reader, an old woman who dwells in Roundtable Hold and reads
the wishes of the Two Fingers on behalf of the Tarnished. You know the histories of the demigods — their
Great Runes, their Remembrances, what they were, what they became. You know what each shattered demigod
carried: the inheritance of the Elden Ring's power, fractured into Shards. You speak in a grandmother's
warm, confiding tone — close and a little conspiratorial, as if sharing secrets across a table. You
use phrases like "Ah, now that's a story...", "Between you and me, dear...", "The fingers told me...",
"The Remembrance reveals...", "Such a sad tale, such a sad tale..." You address the Tarnished warmly.
No emojis. No asterisks. No stage directions.""",

        "arrival": [
            "Ah, now that's a story the Remembrances hold dear. Let me share it.",
            "The Two Fingers whispered of this. Come closer, dear, and I'll tell you.",
            "Between you and me, dear Tarnished, I know this one well.",
            "Ah, yes... sad tale, sad tale. But worth the telling.",
        ],

        "domain_keywords": [
            "enia", "finger reader", "remembrance", "great rune", "demigod",
            "malenia", "radahn", "morgott", "mohg", "rykard", "godwyn",
            "godrick", "rennala", "great rune of the unborn", "great rune of binding",
            "starscourge", "rot goddess", "omen king", "lord of blood",
            "lord of blasphemy", "praetor rykard", "grafted", "shard of the elden ring",
            "elden ring shards", "two fingers", "finger maidens", "tarnished purpose",
            "be maidenless", "maidenless", "roundtable hold residents",
        ],

        "voice_style": (
            "Speak in Enia's warm, conspiratorial grandmother style. "
            "Reference the Remembrances, Great Runes, and demigods with sad fondness. "
            "2-4 sentences. Close and confiding, as if sharing a secret."
        ),
    },

    # ── Dung Eater ────────────────────────────────────────────────────────
    "dung_eater": {
        "name": "the Dung Eater",

        "persona": """You are the Dung Eater, a Tarnished consumed by a singular, violent purpose: to spread
the Seedbed Curse across all the Lands Between — to defile every soul so that all shall be reborn as
Omens, cursed and outcast, as hideous as he is. You are brutal, crass, and gleeful in your vileness.
You despise the Golden Order and everything it deems beautiful or pure. You are deeply knowledgeable
about curses, the Omen, and the lore of defilement — because it is your obsession. You speak in short,
violent, contemptuous sentences. You enjoy what you do. You call the Tarnished "you wretch" or simply
grunt at them. You do not use formal language — you use blunt, aggressive phrasing. You are NOT evil for
evil's sake — you have a purpose, a twisted philosophy: that the Golden Order's hierarchy of 'cursed'
and 'pure' is the true evil, and your Curse is the great equaliser. Phrases: "The curse will take you.",
"All will be remade — defiled.", "The Order calls them cursed. I call them free.", "Wretched. Like me."
No emojis. No asterisks. No stage directions.""",

        "arrival": [
            "Heh. You ask about this? Good. Even a wretch can learn.",
            "You come to me with this question. Fitting.",
            "This is MY domain. I'll tell you what I know.",
            "Shut up and listen, wretch. I know this better than any.",
        ],

        "domain_keywords": [
            "dung eater", "seedbed curse", "omen", "omen bairn", "leyndell sewers",
            "morgott omen king", "mohg omen", "curse", "cursed", "defilement",
            "outer moat", "subterranean shunning grounds", "fell curse",
            "mending rune of the fell curse", "crucible of curses", "fell god",
            "shabriri", "shabriri grape", "frenzy flame omen",
            "cursed blood", "omen horns", "omen deformity",
        ],

        "voice_style": (
            "Speak in the Dung Eater's blunt, brutal, contemptuous style. "
            "Short sentences. Reference curses, Omen, and defilement. "
            "2-3 sentences. Aggressive but not mindlessly so — you have a twisted philosophy."
        ),
    },

    # ── Sir Gideon Ofnir (DEFAULT) ────────────────────────────────────────
    "gideon": {
        "name": "Sir Gideon Ofnir, the All-Knowing",

        "persona": """You are Sir Gideon Ofnir, the All-Knowing, from the game Elden Ring.
You are the leader of the Roundtable Hold, renowned throughout the Lands Between for your unparalleled
breadth of knowledge. You speak in a formal, authoritative, and slightly arrogant manner.
You address the player as "Tarnished". You speak as though you have personally investigated every corner
of the Lands Between. You occasionally reference your own vast investigations and the depth of your research.
You use formal, old-English-adjacent phrasing: "indeed", "I have surmised", "my investigations reveal",
"you would do well to know", "most interesting", "I shall illuminate this for you".
You never break character. You never mention AI, databases, retrieval systems, or technology.
No emojis. No asterisks. No stage directions.""",

        "arrival": [
            "Ah. A question worthy of the All-Knowing. Attend, Tarnished.",
            "My investigations have indeed covered this matter. Hear me.",
            "Most interesting that you ask this. I shall illuminate it.",
            "You would do well to listen carefully, Tarnished.",
        ],

        "domain_keywords": [],  # Default — matches everything not caught above

        "voice_style": (
            "Speak in Gideon's formal, authoritative, slightly arrogant style. "
            "Use his signature phrases: 'my investigations reveal', 'you would do well to know', 'indeed'. "
            "3-5 sentences. Formal and confident."
        ),
    },
}

# Character routing: ordered from most specific to least specific
# The first character whose domain_keywords match the query wins.
CHARACTER_ROUTING_ORDER = [
    "ranni",
    "fia",
    "goldmask",
    "miriel",
    "enia",
    "dung_eater",
    "melina",
    "gideon",  # always last — default
]


def select_character(question: str, lore_subtype: str = "lore") -> str:
    """
    Pick the best NPC character to answer this lore question.
    Returns a character key from CHARACTERS.

    Strategy:
    1. Score each non-default character by how many domain keywords appear in the question.
    2. The highest scorer above 0 wins.
    3. Tie → use routing order priority.
    4. No match → gideon (default).
    """
    q = question.lower()

    best_char = "gideon"
    best_score = 0

    for char_key in CHARACTER_ROUTING_ORDER[:-1]:  # skip gideon in scoring loop
        char = CHARACTERS[char_key]
        score = sum(1 for kw in char["domain_keywords"] if kw in q)
        if score > best_score:
            best_score = score
            best_char = char_key

    if best_score > 0:
        log.info("Character selected: %s (score: %d)", best_char, best_score)
    else:
        log.info("Character selected: gideon (default — no keyword match)")

    return best_char


def get_arrival_line(char_key: str) -> str:
    """Pick a pseudo-random arrival flourish for the character."""
    import hashlib
    char = CHARACTERS[char_key]
    lines = char["arrival"]
    # Use a hash of the current time (seconds) mod len to rotate through lines
    import time
    idx = int(time.time()) % len(lines)
    return lines[idx]


# ═══════════════════════════════════════════════════════════════════════════
#  INTENT CLASSIFICATION
#  Fast keyword path first — LLM only as fallback
# ═══════════════════════════════════════════════════════════════════════════

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
    "bayle", "igon", "thiollier", "moore", "leda", "needle knight",
    "ansbach", "florissax", "dancing lion", "divine beast", "midra",
    "chaos flame", "frenzy flame", "scadutree", "scadutree avatar",
    "st. trina", "st trina", "trina", "rellana", "twin moon knight",
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
    q = question.strip().lower().rstrip("?.!")

    if q in CASUAL_TRIGGERS:
        return "casual"
    for trigger in CASUAL_TRIGGERS:
        if q.startswith(trigger + " ") or q.endswith(" " + trigger):
            return "casual"

    q_full = question.lower()

    for pat in LORE_RESCUE_PATTERNS:
        if re.search(pat, q_full):
            if any(m in q_full for m in MECHANIC_SIGNALS):
                return "mechanics"
            if any(t in q_full for t in ["why did", "theory", "could it be", "what if", "speculate"]):
                return "theory"
            return "lore"

    if any(signal in q_full for signal in LORE_SIGNALS):
        if any(m in q_full for m in MECHANIC_SIGNALS):
            return "mechanics"
        if any(t in q_full for t in ["why did", "theory", "could it be", "what if", "speculate"]):
            return "theory"
        return "lore"

    if any(m in q_full for m in MECHANIC_SIGNALS):
        return "mechanics"

    if chat_history and len(q.split()) <= 6:
        last_user = next(
            (m["content"] for m in reversed(chat_history) if m["role"] == "user"),
            ""
        )
        for pat in LORE_RESCUE_PATTERNS:
            if re.search(pat, last_user.lower()):
                return "lore"

    lore_question_words = [
        "who is", "what is", "who was", "what was", "what are",
        "who are", "tell me about", "explain", "what happened",
        "why is", "why was", "where is", "where was",
    ]
    if any(q_full.startswith(lw) for lw in lore_question_words):
        return "lore"

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


# ═══════════════════════════════════════════════════════════════════════════
#  FOLLOW-UP FUSION
# ═══════════════════════════════════════════════════════════════════════════

FOLLOWUP_PRONOUNS = [
    "he", "she", "they", "it", "his", "her", "their", "its",
    "him", "them", "this", "that", "these", "those",
    "the same", "as well", "also", "what about", "and what",
]


def _extract_lore_entities_from_text(text: str) -> list[str]:
    t = text.lower()
    return [sig for sig in LORE_SIGNALS if sig in t]


def fuse_followup(question: str, chat_history: list) -> str:
    if not chat_history:
        return question

    q_lower = question.lower().strip()
    words = q_lower.split()

    pronoun_hit = any(q_lower.startswith(p) for p in FOLLOWUP_PRONOUNS)

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

    recent = chat_history[-6:]
    history_text = "\n".join(
        f"{'User' if m['role'] == 'user' else 'NPC'}: {m['content']}"
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

    last_user = next(
        (m["content"] for m in reversed(chat_history) if m["role"] == "user"),
        ""
    )
    if last_user:
        return f"{last_user} — {question}"

    return question


# ═══════════════════════════════════════════════════════════════════════════
#  MULTI-HOP DETECTION
# ═══════════════════════════════════════════════════════════════════════════

MULTI_HOP_SIGNALS = [
    " and also ", " and what ", " and who ", " and where ",
    " both ", " as well as ", " in addition ", " furthermore ",
    " relationship between ", " compare ",
]


def is_multi_hop(question: str) -> bool:
    q = question.lower()
    found_entities = _extract_lore_entities_from_text(q)
    if len(found_entities) >= 2:
        return True
    return any(sig in q for sig in MULTI_HOP_SIGNALS)


def split_multi_hop(question: str) -> list[str]:
    q = question.lower()
    for sig in MULTI_HOP_SIGNALS:
        if sig in q:
            parts = question.lower().split(sig.strip(), 1)
            return [p.strip().capitalize() for p in parts if p.strip()]
    return [question]


# ═══════════════════════════════════════════════════════════════════════════
#  HYDE — Hypothetical Document Embedding
# ═══════════════════════════════════════════════════════════════════════════

def generate_hyde_passage(question: str) -> str | None:
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


# ═══════════════════════════════════════════════════════════════════════════
#  HALLUCINATION GUARD
# ═══════════════════════════════════════════════════════════════════════════

def source_grounding_score(answer: str, context: str) -> float:
    answer_entities = set(re.findall(r"\b[A-Z][a-z]{2,}\b", answer))
    common = {
        "Indeed", "Most", "Tarnished", "Lands", "Between", "However",
        "Furthermore", "Moreover", "Nevertheless", "Therefore", "Also",
        "Though", "Yet", "For", "But", "And", "The", "This", "That",
        "Nay", "Why", "Ah", "Heh", "Hear", "Come", "Will", "You",
        "Dear", "Let", "Now", "Such", "Sad", "Old", "Good", "Ho",
        "Law", "Order", "Thus", "Free", "Like", "All", "My", "We",
    }
    answer_entities -= common

    if not answer_entities:
        return 1.0

    ctx_lower = context.lower()
    hits = sum(1 for e in answer_entities if e.lower() in ctx_lower)
    score = hits / len(answer_entities)
    log.info("Grounding score: %.2f (%d/%d entities found in context)",
             score, hits, len(answer_entities))
    return score


# ═══════════════════════════════════════════════════════════════════════════
#  MMR DEDUPLICATION
# ═══════════════════════════════════════════════════════════════════════════

def mmr_deduplicate(chunks: list[dict], threshold: float = 0.92) -> list[dict]:
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


# ═══════════════════════════════════════════════════════════════════════════
#  CONTEXT / HISTORY BUILDERS
# ═══════════════════════════════════════════════════════════════════════════

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
        role = "Tarnished" if msg["role"] == "user" else "NPC"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines) + "\n\n"


# ═══════════════════════════════════════════════════════════════════════════
#  NON-LORE RESPONSE HANDLERS
#  These always use Gideon — he handles casual, off-topic, and mechanics
#  since those are outside any character's lore domain.
# ═══════════════════════════════════════════════════════════════════════════

_GIDEON = CHARACTERS["gideon"]["persona"]


def ask_casual(question: str, chat_history: list) -> str:
    history_text = build_history_text(chat_history)
    prompt = f"""{_GIDEON}

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
    prompt = f"""{_GIDEON}

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
    prompt = f"""{_GIDEON}

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


def ask_no_context(question: str, chat_history: list, char_key: str = "gideon") -> str:
    char = CHARACTERS[char_key]
    history_text = build_history_text(chat_history)
    prompt = f"""{char["persona"]}

Your knowledge does not contain a verified entry on this specific topic.
Admit this in your character's voice without inventing ANY lore detail.
State that even your investigations/knowledge have not uncovered this.
2 sentences maximum. Stay in character as {char["name"]}.

{history_text}TARNISHED: {question}
{char["name"].upper().split(",")[0]}:"""
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
        return "Most curious, Tarnished — even my vast knowledge has uncovered no record of this particular matter."


# ═══════════════════════════════════════════════════════════════════════════
#  INFERENCE ROUTING
# ═══════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════
#  CORE RAG ANSWER FUNCTIONS — now character-aware
# ═══════════════════════════════════════════════════════════════════════════

def ask_inference(
    question: str,
    context: str,
    chat_history: list,
    char_key: str = "gideon",
) -> str:
    char = CHARACTERS[char_key]
    history_text = build_history_text(chat_history)
    char_name_short = char["name"].split(",")[0]

    prompt = f"""{char["persona"]}

The Tarnished asks a question whose answer is IMPLIED by the lore, not stated explicitly.
Use the sources to REASON toward an answer.

Rules:
1. Use the sources as your foundation — do not ignore them.
2. You MAY draw logical inferences the sources strongly support.
3. Frame inferences in YOUR character's voice (e.g. Ranni: "We have surmised...", Fia: "I have long felt...", Miriel: "Ho ho, now that is a deduction...").
4. Do NOT invent facts with no basis in the sources whatsoever.
5. {char["voice_style"]}
6. If inference is impossible, say so in ONE sentence.

{history_text}RETRIEVED SOURCES:
{context}

TARNISHED ASKS: {question}

Reason from the sources. Speak as {char["name"]}. Be concise.
{char_name_short.upper()}:"""

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
        return ask_no_context(question, chat_history, char_key)


def ask_rag(
    question: str,
    context: str,
    chat_history: list,
    intent: str = "lore",
    lore_subtype: str = "lore",
    strict: bool = False,
    char_key: str = "gideon",
) -> str:
    char = CHARACTERS[char_key]
    history_text = build_history_text(chat_history)
    char_name_short = char["name"].split(",")[0]

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
            f"\nThis is a speculative question. After grounding your answer in sources, "
            f"you MAY offer {char['name']}'s own scholarly interpretation — clearly framed "
            f"in your character's voice (e.g. 'I have surmised...', 'We believe...', 'My own sense...'). "
            f"One sentence max.\n"
        )

    strict_note = (
        "\nSTRICT MODE: A previous answer contained names not verified in sources. "
        "This time, mention ONLY names and places that appear word-for-word in the sources below.\n"
        if strict else ""
    )

    prompt = f"""{char["persona"]}

════════════════════════════════════════════
HALLUCINATION PREVENTION — ABSOLUTE RULES
════════════════════════════════════════════
{subtype_guidance}
{theory_addendum}{strict_note}
1. Use ONLY information explicitly stated in the SOURCES. Nothing else.
2. Do NOT add names, dates, events, or relationships not in the sources.
3. Do NOT use general Elden Ring knowledge — only what is written in sources below.
4. If sources only partially answer, answer partially and STOP — do not pad.
5. If a detail appears in only one source, qualify it in your character's voice.
6. If sources conflict, acknowledge conflict in your character's voice.
7. NEVER invent character names, locations, events, or relationships.
8. {char["voice_style"]}
9. If you cannot answer from sources, say so in ONE sentence only.

Confidence calibration (express in YOUR character's voice):
- Fact in MULTIPLE sources → state confidently
- Fact in ONE source → hedge appropriately for your character
- Sources CONFLICT → acknowledge the conflict in your character's way
════════════════════════════════════════════

{history_text}RETRIEVED SOURCES:
{context}

TARNISHED ASKS: {question}

Answer using ONLY the sources. Speak as {char["name"]}. Stop when sources run out.
{char_name_short.upper()}:"""

    temperature = 0.0 if strict else 0.15
    response = client.chat.completions.create(
        model=RAG_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()


def ask_multi_hop(sub_questions: list[str], chat_history: list) -> tuple[str, list]:
    """Answer each sub-question with the best character, then synthesize."""
    sub_answers = []
    all_sources = []

    for sub_q in sub_questions:
        char_key = select_character(sub_q)
        char = CHARACTERS[char_key]
        char_name_short = char["name"].split(",")[0]

        chunks = retrieve(sub_q, top_k=20)
        if not chunks:
            continue
        context = build_grounded_context(chunks)
        history_text = build_history_text(chat_history)

        prompt = f"""{char["persona"]}

Answer ONLY using the sources below. One focused paragraph. Stay in character as {char["name"]}.
{char["voice_style"]}

{history_text}SOURCES:
{context}

QUESTION: {sub_q}
{char_name_short.upper()}:"""
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

    # Synthesize with Gideon (he's the host of the Roundtable)
    combined = "\n\n".join(f"Part {i+1}: {a}" for i, a in enumerate(sub_answers))
    synthesis_prompt = f"""{_GIDEON}

You have investigated multiple facets of the Tarnished's question, consulting the knowledge
of your fellow Roundtable companions. Below are the combined findings.
Weave them into a single flowing formal response in Gideon's voice. Do not number the parts.
5-8 sentences total.

FINDINGS:
{combined}

GIDEON:"""
    try:
        response = client.chat.completions.create(
            model=RAG_MODEL,
            messages=[{"role": "user", "content": synthesis_prompt}],
            temperature=0.2,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip(), list(set(all_sources))
    except Exception as e:
        log.warning("multi-hop synthesis failed: %s", e)
        return sub_answers[0] if sub_answers else "", list(set(all_sources))


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def ask(question: str, chat_history: list = []) -> tuple[str, list, str, str]:
    """
    Routes the question and returns (answer, sources, mode, character_name).

    mode: casual | off_topic | mechanics | rag | rag_multi_hop | no_context
    character_name: display name of the NPC who answered (e.g. "Ranni the Witch")
    """

    # ── Step 1: Intent ────────────────────────────────────────────────────
    intent = classify_intent(question, chat_history)
    log.info("Intent: %s | Question: %r", intent, question[:80])

    if intent == "casual":
        return ask_casual(question, chat_history), [], "casual", "Sir Gideon Ofnir, the All-Knowing"

    if intent == "off_topic":
        return ask_off_topic(question, chat_history), [], "off_topic", "Sir Gideon Ofnir, the All-Knowing"

    if intent == "mechanics":
        return ask_mechanics(question, chat_history), [], "mechanics", "Sir Gideon Ofnir, the All-Knowing"

    # ── Step 2: Lore sub-category ─────────────────────────────────────────
    lore_subtype = classify_lore_subtype(question)
    log.info("Lore subtype: %s", lore_subtype)

    # ── Step 3: Follow-up fusion ──────────────────────────────────────────
    fused_query = fuse_followup(question, chat_history)

    # ── Step 4: Multi-hop routing ─────────────────────────────────────────
    if is_multi_hop(fused_query):
        sub_questions = split_multi_hop(fused_query)
        if len(sub_questions) >= 2:
            answer, sources = ask_multi_hop(sub_questions, chat_history)
            if answer:
                return answer, sources, "rag_multi_hop", "Sir Gideon Ofnir, the All-Knowing"

    # ── Step 5: Character selection ───────────────────────────────────────
    char_key = select_character(fused_query, lore_subtype)
    char = CHARACTERS[char_key]
    char_display_name = char["name"]
    log.info("Speaking as: %s", char_display_name)

    # ── Step 6: HyDE ─────────────────────────────────────────────────────
    hyde_passage = generate_hyde_passage(fused_query)

    # ── Step 7: Retrieval ─────────────────────────────────────────────────
    chunks = retrieve(fused_query, top_k=20)

    if hyde_passage:
        hyde_chunks = retrieve(hyde_passage, top_k=10)
        existing_texts = {c["text"][:80] for c in chunks}
        for hc in hyde_chunks:
            if hc["text"][:80] not in existing_texts:
                chunks.append(hc)
                existing_texts.add(hc["text"][:80])

    if not chunks:
        log.warning("No chunks retrieved for: %r", fused_query)
        return ask_no_context(question, chat_history, char_key), [], "no_context", char_display_name

    # ── Step 8: Soft relevance gate ───────────────────────────────────────
    top_score = chunks[0].get("score", 1.0)
    log.info("Top chunk score: %.3f | chunk count: %d", top_score, len(chunks))

    if top_score < 0.20:
        log.warning("Top score %.3f below threshold — returning no_context", top_score)
        return ask_no_context(question, chat_history, char_key), [], "no_context", char_display_name

    # ── Step 9: MMR deduplication ─────────────────────────────────────────
    chunks = mmr_deduplicate(chunks, threshold=0.92)

    # ── Step 10: Build context and generate answer ─────────────────────────
    context = build_grounded_context(chunks)

    # Get arrival flourish
    arrival = get_arrival_line(char_key)

    try:
        if needs_inference(question):
            log.info("Routing to ask_inference (past-causation) with %s", char_display_name)
            answer_body = ask_inference(question, context, chat_history, char_key)
        else:
            log.info("Routing to ask_rag with %s — subtype: %s", char_display_name, lore_subtype)
            answer_body = ask_rag(
                fused_query, context, chat_history,
                intent=intent, lore_subtype=lore_subtype,
                char_key=char_key,
            )
    except Exception as e:
        log.error("ask_rag/inference failed: %s", e)
        return ask_no_context(question, chat_history, char_key), [], "no_context", char_display_name

    # ── Step 11: Hallucination guard ──────────────────────────────────────
    grounding = source_grounding_score(answer_body, context)
    if grounding < 0.40:
        log.warning("Low grounding score %.2f — re-asking in strict mode", grounding)
        try:
            answer_body = ask_rag(
                fused_query, context, chat_history,
                intent=intent, lore_subtype=lore_subtype,
                strict=True, char_key=char_key,
            )
        except Exception as e:
            log.error("Strict re-ask failed: %s", e)

    # ── Step 12: Compose final answer with arrival flourish ────────────────
    # Only prepend arrival if it doesn't sound redundant with the answer opening
    answer = f"{arrival}\n\n{answer_body}"

    sources = [f"{c['name']} ({c['category']}, {c['area']})" for c in chunks]
    return answer, sources, "rag", char_display_name


# ═══════════════════════════════════════════════════════════════════════════
#  CLI TEST
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("  ELDEN RING MULTI-CHARACTER RAG BOT")
    print("  Characters: Ranni · Melina · Fia · Goldmask · Miriel · Enia")
    print("              Dung Eater · Sir Gideon Ofnir (default)")
    print("=" * 70)

    history = []
    test_questions = [
        # Casual / non-lore
        "hi",
        "what is 2+2?",
        "how do i beat radahn",

        # Gideon (general lore, no specific character domain match)
        "What happened on the Night of the Black Knives?",
        "What is the Frenzied Flame?",

        # Ranni (her plan, dark moon, blaidd)
        "Who is Ranni and what is her plan?",
        "What is Ranni's connection to the Night of the Black Knives?",

        # Melina (Erdtree, Marika, kindling)
        "What is Melina's connection to Marika?",

        # Fia (Godwyn, Cursemark, deathbed)
        "What is the Cursemark of Death and who carries it?",
        "What happened to Godwyn the Golden?",

        # Goldmask (Golden Order, Radagon)
        "What is wrong with the Golden Order according to Goldmask?",

        # Miriel (Raya Lucaria, dragon history)
        "What is the history of Raya Lucaria Academy?",

        # Enia (Remembrances, demigods)
        "What do the Remembrances of the demigods reveal?",

        # Dung Eater (Seedbed Curse, Omen)
        "What is the Seedbed Curse and what does the Dung Eater want?",

        # Follow-up test
        "Who was her twin?",

        # Multi-hop test
        "Tell me about Malenia and also about Godwyn",

        # Shadow of the Erdtree
        "Who is Messmer?",
    ]

    for q in test_questions:
        print(f"\n{'─'*70}")
        print(f"Tarnished  : {q}")
        answer, sources, mode, speaker = ask(q, history)
        print(f"Speaker    : [{speaker}]")
        print(f"Mode       : [{mode}]")
        print(f"Answer     : {answer[:280]}{'...' if len(answer) > 280 else ''}")
        if sources:
            print(f"  └─ Sources: {sources[:2]}")
        history.append({"role": "user", "content": q})
        history.append({"role": "assistant", "content": answer})

    print("\n" + "=" * 70)
    print("Done.")