"""
rescrape_missing.py  — COMPREHENSIVE EDITION
Scrapes ONLY the entries that are missing or broken in the DB.
This version covers:
  - Everything flagged by db_check.py + coverage_check.py
  - All base-game + Shadow of the Erdtree characters (named NPCs, enemies, bosses)
  - All Outer Gods, demigods, and major lore concepts
  - Key items with lore significance
  - All endings / ages
  - DLC characters and lore

Run this, then run: python ingest.py
"""
import requests
from bs4 import BeautifulSoup
import time
import os
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

FEXTRALIFE_BASE = "https://eldenring.wiki.fextralife.com"
WIKIGG_BASE     = "https://eldenring.wiki.gg"
FANDOM_BASE     = "https://eldenring.fandom.com/wiki"


def clean_text(text: str) -> str:
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if len(line) >= 20:
            lines.append(line)
    seen = set()
    unique = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            unique.append(line)
    return "\n".join(unique)


def scrape_fextralife(path: str):
    url = FEXTRALIFE_BASE + path
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            return None, None
        soup = BeautifulSoup(res.text, "html.parser")
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else path.replace("/", "").replace("+", " ")
        content_div = soup.find("div", {"id": "wiki-content-block"})
        if not content_div:
            return title, ""
        for tag in content_div.find_all(["script", "style", "table", "nav", "footer"]):
            tag.decompose()
        paragraphs = []
        for tag in content_div.find_all(["p", "li"]):
            text = tag.get_text(separator=" ", strip=True)
            if len(text) >= 20:
                paragraphs.append(text)
        return title, clean_text("\n".join(paragraphs[:120]))
    except Exception as e:
        print(f"    Fextralife error: {e}")
        return None, None


def scrape_wikigg(path: str):
    url = WIKIGG_BASE + path
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            return None, None
        soup = BeautifulSoup(res.text, "html.parser")
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else ""
        content = soup.find("div", {"class": "mw-parser-output"})
        if not content:
            return title, ""
        for tag in content.find_all(["script", "style", "table", "nav"]):
            tag.decompose()
        paragraphs = []
        for tag in content.find_all(["p", "li"]):
            text = tag.get_text(separator=" ", strip=True)
            if len(text) >= 20:
                paragraphs.append(text)
        return title, clean_text("\n".join(paragraphs[:120]))[:6000]
    except Exception as e:
        print(f"    Wikigg error: {e}")
        return None, None


def scrape_fandom(path: str):
    url = FANDOM_BASE + "/" + path
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            return None, None
        soup = BeautifulSoup(res.text, "html.parser")
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else ""
        content = soup.find("div", {"class": "mw-parser-output"})
        if not content:
            return title, ""
        for tag in content.find_all(["script", "style", "table", "nav", "figure"]):
            tag.decompose()
        paragraphs = []
        for tag in content.find_all(["p", "li"]):
            text = tag.get_text(separator=" ", strip=True)
            if len(text) >= 20:
                paragraphs.append(text)
        return title, clean_text("\n".join(paragraphs[:120]))
    except Exception as e:
        print(f"    Fandom error: {e}")
        return None, None


def combine_sources(texts: list[str]) -> str:
    seen = set()
    combined = []
    for text in texts:
        if not text:
            continue
        for line in text.splitlines():
            line = line.strip()
            if len(line) >= 20 and line not in seen:
                seen.add(line)
                combined.append(line)
    return "\n".join(combined[:200])


def save_lore(name: str, category: str, area: str, chapter: int,
              text: str, filepath: str):
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"area: {area}\n")
        f.write(f"chapter: {chapter}\n")
        f.write(f"name: {name}\n")
        f.write(text + "\n")
        f.write("\n---\n\n")


# =============================================================================
# MISSING ENTRIES — COMPREHENSIVE LIST
# Organized by category. All entries that db_check + coverage_check flagged,
# PLUS every named character, concept, and lore item in the game.
# =============================================================================
MISSING_ENTRIES = [

    # =========================================================================
    # SECTION 1 — Previously flagged by db_check.py (MISSING in Test 1)
    # =========================================================================
    {
        "name": "Hewg",
        "override_name": "Hewg",
        "category": "character",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Smithing+Master+Hewg",
        "wikigg": "/Hewg",
        "fandom": "Hewg",
    },
    {
        "name": "D's Brother",
        "override_name": "D's Brother",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/D+Brother",
        "wikigg": "/D%27s_Brother",
        "fandom": "D%27s_Brother",
    },
    {
        "name": "Cursemark of Death",
        "override_name": "Cursemark of Death",
        "category": "item",
        "area": "Liurnia of the Lakes",
        "chapter": 4,
        "fex":    "/Cursemark+of+Death",
        "wikigg": "/Cursemark_of_Death",
        "fandom": "Cursemark_of_Death",
    },
    {
        "name": "Fingerslayer Blade",
        "override_name": "Fingerslayer Blade",
        "category": "item",
        "area": "Nokron Eternal City",
        "chapter": 8,
        "fex":    "/Fingerslayer+Blade",
        "wikigg": "/Fingerslayer_Blade",
        "fandom": "Fingerslayer_Blade",
    },
    {
        "name": "Coded Sword",
        "override_name": "Coded Sword",
        "category": "weapon",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Coded+Sword",
        "wikigg": "/Coded_Sword",
        "fandom": "Coded_Sword",
    },
    {
        "name": "St. Trina",
        "override_name": "St. Trina",
        "category": "character",
        "area": "Liurnia of the Lakes",
        "chapter": 4,
        "fex":    "/St+Trina",
        "wikigg": "/St._Trina",
        "fandom": "St._Trina",
    },
    {
        "name": "Crucible",
        "override_name": "Crucible",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Crucible",
        "wikigg": "/Crucible",
        "fandom": "Crucible",
    },
    {
        "name": "Greater Will",
        "override_name": "Greater Will",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Greater+Will",
        "wikigg": "/Greater_Will",
        "fandom": "Greater_Will",
    },
    {
        "name": "Outer Gods",
        "override_name": "Outer Gods",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Outer+Gods",
        "wikigg": "/Outer_Gods",
        "fandom": "Outer_Gods",
    },
    {
        "name": "Black Knife Assassins",
        "override_name": "Black Knife Assassins",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Black+Knife+Assassins",
        "wikigg": "/Black_Knife_Assassins",
        "fandom": "Black_Knife_Assassins",
    },

    # =========================================================================
    # SECTION 2 — Flagged by coverage_check.py (completely missing from DB)
    # =========================================================================
    {
        "name": "Haligtree Medallion",
        "override_name": "Haligtree Medallion",
        "category": "item",
        "area": "Mountaintops of the Giants",
        "chapter": 21,
        "fex":    "/Haligtree+Secret+Medallion",
        "wikigg": "/Haligtree_Secret_Medallion",
        "fandom": "Haligtree_Secret_Medallion",
    },
    {
        "name": "Age of Fracture",
        "override_name": "Age of Fracture",
        "category": "lore",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Elden+Ring+Endings",
        "wikigg": "/Endings",
        "fandom": "Elden_Ring_Endings",
    },
    {
        "name": "Age of the Duskborn",
        "override_name": "Age of the Duskborn",
        "category": "lore",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Age+of+the+Duskborn",
        "wikigg": "/Age_of_the_Duskborn",
        "fandom": "Elden_Ring_Endings",
    },
    {
        "name": "Blessing of Despair",
        "override_name": "Blessing of Despair",
        "category": "lore",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Elden+Ring+Endings",
        "wikigg": "/Endings",
        "fandom": "Elden_Ring_Endings",
    },
    {
        "name": "Lord of the Frenzied Flame",
        "override_name": "Lord of the Frenzied Flame",
        "category": "lore",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Lord+of+Frenzied+Flame+Ending",
        "wikigg": "/Lord_of_Frenzied_Flame",
        "fandom": "Lord_of_Frenzied_Flame_(Ending)",
    },

    # =========================================================================
    # SECTION 3 — Deep lore concepts (needed to answer hard questions)
    # =========================================================================
    {
        "name": "Destined Death",
        "override_name": "Destined Death",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Destined+Death",
        "wikigg": "/Destined_Death",
        "fandom": "Destined_Death",
    },
    {
        "name": "Empyrean",
        "override_name": "Empyrean",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Empyrean",
        "wikigg": "/Empyrean",
        "fandom": "Empyrean",
    },
    {
        "name": "Night of the Black Knives",
        "override_name": "Night of the Black Knives",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Night+of+the+Black+Knives",
        "wikigg": "/Night_of_the_Black_Knives",
        "fandom": "Night_of_the_Black_Knives",
    },
    {
        "name": "Godwyn the Golden",
        "override_name": "Godwyn the Golden",
        "category": "lore",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Godwyn+the+Golden",
        "wikigg": "/Godwyn_the_Golden",
        "fandom": "Godwyn_the_Golden",
    },
    {
        "name": "Formless Mother",
        "override_name": "Formless Mother",
        "category": "lore",
        "area": "Mohgwyn Palace",
        "chapter": 23,
        "fex":    "/Formless+Mother",
        "wikigg": "/Formless_Mother",
        "fandom": "Formless_Mother",
    },
    {
        "name": "Fell God",
        "override_name": "Fell God",
        "category": "lore",
        "area": "Mountaintops of the Giants",
        "chapter": 21,
        "fex":    "/Fell+God",
        "wikigg": "/Fell_God",
        "fandom": "Fell_God",
    },
    {
        "name": "Two Fingers",
        "override_name": "Two Fingers",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Two+Fingers",
        "wikigg": "/Two_Fingers",
        "fandom": "Two_Fingers",
    },
    {
        "name": "Three Fingers",
        "override_name": "Three Fingers",
        "category": "lore",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Three+Fingers",
        "wikigg": "/Three_Fingers",
        "fandom": "Three_Fingers",
    },
    {
        "name": "Deathroot",
        "override_name": "Deathroot",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Deathroot",
        "wikigg": "/Deathroot",
        "fandom": "Deathroot",
    },
    {
        "name": "Miquella",
        "override_name": "Miquella",
        "category": "character",
        "area": "Enir-Ilim",
        "chapter": 34,
        "fex":    "/Miquella",
        "wikigg": "/Miquella",
        "fandom": "Miquella",
    },
    {
        "name": "Queen Marika the Eternal",
        "override_name": "Queen Marika the Eternal",
        "category": "character",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Queen+Marika+the+Eternal",
        "wikigg": "/Queen_Marika_the_Eternal",
        "fandom": "Queen_Marika_the_Eternal",
    },
    {
        "name": "Twinbird",
        "override_name": "Twinbird",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Twinbird",
        "wikigg": "/Twinbird",
        "fandom": "Twinbird",
    },
    {
        "name": "Gloam-Eyed Queen",
        "override_name": "Gloam-Eyed Queen",
        "category": "lore",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Gloam-Eyed+Queen",
        "wikigg": "/Gloam-Eyed_Queen",
        "fandom": "Gloam-Eyed_Queen",
    },
    {
        "name": "Serosh",
        "override_name": "Serosh",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Serosh",
        "wikigg": "/Serosh",
        "fandom": "Serosh",
    },

    # =========================================================================
    # SECTION 4 — BASE GAME NAMED NPCs / CHARACTERS not yet confirmed in DB
    # =========================================================================
    {
        "name": "Ranni the Witch",
        "override_name": "Ranni the Witch",
        "category": "character",
        "area": "Liurnia of the Lakes",
        "chapter": 4,
        "fex":    "/Ranni+the+Witch",
        "wikigg": "/Ranni_the_Witch",
        "fandom": "Ranni_the_Witch",
    },
    {
        "name": "Fia the Deathbed Companion",
        "override_name": "Fia the Deathbed Companion",
        "category": "character",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Fia",
        "wikigg": "/Fia",
        "fandom": "Fia",
    },
    {
        "name": "D Hunter of the Dead",
        "override_name": "D Hunter of the Dead",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/D+Hunter+of+the+Dead",
        "wikigg": "/D,_Hunter_of_the_Dead",
        "fandom": "D,_Hunter_of_the_Dead",
    },
    {
        "name": "Diallos",
        "override_name": "Diallos",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Diallos",
        "wikigg": "/Diallos",
        "fandom": "Diallos",
    },
    {
        "name": "Nepheli Loux",
        "override_name": "Nepheli Loux",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Nepheli+Loux",
        "wikigg": "/Nepheli_Loux",
        "fandom": "Nepheli_Loux",
    },
    {
        "name": "Kenneth Haight",
        "override_name": "Kenneth Haight",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Kenneth+Haight",
        "wikigg": "/Kenneth_Haight",
        "fandom": "Kenneth_Haight",
    },
    {
        "name": "Gostoc",
        "override_name": "Gostoc",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Gostoc",
        "wikigg": "/Gostoc",
        "fandom": "Gostoc",
    },
    {
        "name": "Sorceress Sellen",
        "override_name": "Sorceress Sellen",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Sorceress+Sellen",
        "wikigg": "/Sorceress_Sellen",
        "fandom": "Sorceress_Sellen",
    },
    {
        "name": "Blaidd the Half-Wolf",
        "override_name": "Blaidd the Half-Wolf",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Blaidd+the+Half+Wolf",
        "wikigg": "/Blaidd_the_Half-Wolf",
        "fandom": "Blaidd_the_Half-Wolf",
    },
    {
        "name": "Alexander Iron Fist",
        "override_name": "Alexander Iron Fist",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Alexander+Iron+Fist",
        "wikigg": "/Alexander,_Iron_Fist",
        "fandom": "Alexander,_Iron_Fist",
    },
    {
        "name": "Millicent",
        "override_name": "Millicent",
        "category": "character",
        "area": "Altus Plateau",
        "chapter": 13,
        "fex":    "/Millicent",
        "wikigg": "/Millicent",
        "fandom": "Millicent",
    },
    {
        "name": "Gowry",
        "override_name": "Gowry",
        "category": "character",
        "area": "Caelid",
        "chapter": 9,
        "fex":    "/Gowry",
        "wikigg": "/Gowry",
        "fandom": "Gowry",
    },
    {
        "name": "Gurranq Beast Clergyman",
        "override_name": "Gurranq Beast Clergyman",
        "category": "character",
        "area": "Caelid",
        "chapter": 9,
        "fex":    "/Gurranq+Beast+Clergyman",
        "wikigg": "/Gurranq,_Beast_Clergyman",
        "fandom": "Gurranq,_Beast_Clergyman",
    },
    {
        "name": "Roderika",
        "override_name": "Roderika",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Roderika",
        "wikigg": "/Roderika",
        "fandom": "Roderika",
    },
    {
        "name": "Rogier",
        "override_name": "Rogier",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Rogier",
        "wikigg": "/Rogier",
        "fandom": "Rogier",
    },
    {
        "name": "Preceptor Seluvis",
        "override_name": "Preceptor Seluvis",
        "category": "character",
        "area": "Liurnia of the Lakes",
        "chapter": 4,
        "fex":    "/Preceptor+Seluvis",
        "wikigg": "/Preceptor_Seluvis",
        "fandom": "Preceptor_Seluvis",
    },
    {
        "name": "Witch-Hunter Jerren",
        "override_name": "Witch-Hunter Jerren",
        "category": "character",
        "area": "Caelid",
        "chapter": 9,
        "fex":    "/Witch-Hunter+Jerren",
        "wikigg": "/Witch-Hunter_Jerren",
        "fandom": "Witch-Hunter_Jerren",
    },
    {
        "name": "Lattenn",
        "override_name": "Lattenn",
        "category": "character",
        "area": "Liurnia of the Lakes",
        "chapter": 4,
        "fex":    "/Lattenn",
        "wikigg": "/Lattenn",
        "fandom": "Lattenn",
    },
    {
        "name": "Jar-Bairn",
        "override_name": "Jar-Bairn",
        "category": "character",
        "area": "Altus Plateau",
        "chapter": 13,
        "fex":    "/Jar-Bairn",
        "wikigg": "/Jar-Bairn",
        "fandom": "Jar-Bairn",
    },
    {
        "name": "Hyetta",
        "override_name": "Hyetta",
        "category": "character",
        "area": "Liurnia of the Lakes",
        "chapter": 4,
        "fex":    "/Hyetta",
        "wikigg": "/Hyetta",
        "fandom": "Hyetta",
    },
    {
        "name": "Irina",
        "override_name": "Irina",
        "category": "character",
        "area": "Weeping Peninsula",
        "chapter": 2,
        "fex":    "/Irina",
        "wikigg": "/Irina",
        "fandom": "Irina",
    },
    {
        "name": "Edgar the Revenger",
        "override_name": "Edgar the Revenger",
        "category": "character",
        "area": "Weeping Peninsula",
        "chapter": 2,
        "fex":    "/Edgar",
        "wikigg": "/Edgar",
        "fandom": "Edgar",
    },
    {
        "name": "Boc the Seamster",
        "override_name": "Boc the Seamster",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Boc+the+Seamster",
        "wikigg": "/Boc_the_Seamster",
        "fandom": "Boc_the_Seamster",
    },
    {
        "name": "Merchant Kalé",
        "override_name": "Merchant Kalé",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Merchant+Kale",
        "wikigg": "/Merchant_Kale",
        "fandom": "Merchant_Kal%C3%A9",
    },
    {
        "name": "Patches",
        "override_name": "Patches",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Patches",
        "wikigg": "/Patches",
        "fandom": "Patches",
    },
    {
        "name": "Ensha of the Royal Remains",
        "override_name": "Ensha of the Royal Remains",
        "category": "character",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Ensha+of+the+Royal+Remains",
        "wikigg": "/Ensha_of_the_Royal_Remains",
        "fandom": "Ensha_of_the_Royal_Remains",
    },
    {
        "name": "Sir Gideon Ofnir",
        "override_name": "Sir Gideon Ofnir",
        "category": "character",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Sir+Gideon+Ofnir",
        "wikigg": "/Sir_Gideon_Ofnir",
        "fandom": "Sir_Gideon_Ofnir",
    },
    {
        "name": "Dung Eater",
        "override_name": "Dung Eater",
        "category": "character",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Dung+Eater",
        "wikigg": "/Dung_Eater",
        "fandom": "Dung_Eater",
    },
    {
        "name": "Corhyn",
        "override_name": "Corhyn",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Corhyn",
        "wikigg": "/Corhyn",
        "fandom": "Corhyn",
    },
    {
        "name": "Goldmask",
        "override_name": "Goldmask",
        "category": "character",
        "area": "Altus Plateau",
        "chapter": 13,
        "fex":    "/Goldmask",
        "wikigg": "/Goldmask",
        "fandom": "Goldmask",
    },
    {
        "name": "Enia the Finger Reader",
        "override_name": "Enia the Finger Reader",
        "category": "character",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Enia",
        "wikigg": "/Enia",
        "fandom": "Enia",
    },
    {
        "name": "Twin Maiden Husks",
        "override_name": "Twin Maiden Husks",
        "category": "character",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Twin+Maiden+Husks",
        "wikigg": "/Twin_Maiden_Husks",
        "fandom": "Twin_Maiden_Husks",
    },
    {
        "name": "Tanith",
        "override_name": "Tanith",
        "category": "character",
        "area": "Mt. Gelmir",
        "chapter": 14,
        "fex":    "/Tanith",
        "wikigg": "/Tanith",
        "fandom": "Tanith",
    },
    {
        "name": "Juno Hoslow",
        "override_name": "Juno Hoslow",
        "category": "character",
        "area": "Mountaintops of the Giants",
        "chapter": 21,
        "fex":    "/Juno+Hoslow",
        "wikigg": "/Juno_Hoslow",
        "fandom": "Juno_Hoslow",
    },
    {
        "name": "Volcano Manor",
        "override_name": "Volcano Manor",
        "category": "location",
        "area": "Mt. Gelmir",
        "chapter": 14,
        "fex":    "/Volcano+Manor",
        "wikigg": "/Volcano_Manor",
        "fandom": "Volcano_Manor",
    },

    # =========================================================================
    # SECTION 5 — BOSSES with major lore significance
    # =========================================================================
    {
        "name": "Godfrey First Elden Lord",
        "override_name": "Godfrey First Elden Lord",
        "category": "character",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Godfrey+First+Elden+Lord",
        "wikigg": "/Godfrey,_First_Elden_Lord",
        "fandom": "Godfrey,_First_Elden_Lord",
    },
    {
        "name": "Morgott the Omen King",
        "override_name": "Morgott the Omen King",
        "category": "character",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Morgott+the+Omen+King",
        "wikigg": "/Morgott,_the_Omen_King",
        "fandom": "Morgott,_the_Omen_King",
    },
    {
        "name": "Malenia Blade of Miquella",
        "override_name": "Malenia Blade of Miquella",
        "category": "character",
        "area": "Elphael",
        "chapter": 28,
        "fex":    "/Malenia+Blade+of+Miquella",
        "wikigg": "/Malenia,_Blade_of_Miquella",
        "fandom": "Malenia,_Blade_of_Miquella",
    },
    {
        "name": "Starscourge Radahn",
        "override_name": "Starscourge Radahn",
        "category": "character",
        "area": "Caelid",
        "chapter": 9,
        "fex":    "/Starscourge+Radahn",
        "wikigg": "/Starscourge_Radahn",
        "fandom": "Starscourge_Radahn",
    },
    {
        "name": "Rykard Lord of Blasphemy",
        "override_name": "Rykard Lord of Blasphemy",
        "category": "character",
        "area": "Mt. Gelmir",
        "chapter": 14,
        "fex":    "/Rykard+Lord+of+Blasphemy",
        "wikigg": "/Rykard,_Lord_of_Blasphemy",
        "fandom": "Rykard,_Lord_of_Blasphemy",
    },
    {
        "name": "Maliketh the Black Blade",
        "override_name": "Maliketh the Black Blade",
        "category": "character",
        "area": "Farum Azula",
        "chapter": 22,
        "fex":    "/Maliketh+the+Black+Blade",
        "wikigg": "/Maliketh,_the_Black_Blade",
        "fandom": "Maliketh,_the_Black_Blade",
    },
    {
        "name": "Mohg Lord of Blood",
        "override_name": "Mohg Lord of Blood",
        "category": "character",
        "area": "Mohgwyn Palace",
        "chapter": 23,
        "fex":    "/Mohg+Lord+of+Blood",
        "wikigg": "/Mohg,_Lord_of_Blood",
        "fandom": "Mohg,_Lord_of_Blood",
    },
    {
        "name": "Radagon of the Golden Order",
        "override_name": "Radagon of the Golden Order",
        "category": "character",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Radagon+of+the+Golden+Order",
        "wikigg": "/Radagon_of_the_Golden_Order",
        "fandom": "Radagon_of_the_Golden_Order",
    },
    {
        "name": "Elden Beast",
        "override_name": "Elden Beast",
        "category": "character",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Elden+Beast",
        "wikigg": "/Elden_Beast",
        "fandom": "Elden_Beast",
    },
    {
        "name": "Renalla Queen of the Full Moon",
        "override_name": "Renalla Queen of the Full Moon",
        "category": "character",
        "area": "Liurnia of the Lakes",
        "chapter": 4,
        "fex":    "/Rennala+Queen+of+the+Full+Moon",
        "wikigg": "/Rennala,_Queen_of_the_Full_Moon",
        "fandom": "Rennala,_Queen_of_the_Full_Moon",
    },
    {
        "name": "Godrick the Grafted",
        "override_name": "Godrick the Grafted",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Godrick+the+Grafted",
        "wikigg": "/Godrick_the_Grafted",
        "fandom": "Godrick_the_Grafted",
    },
    {
        "name": "Loretta Knight of the Haligtree",
        "override_name": "Loretta Knight of the Haligtree",
        "category": "character",
        "area": "Elphael",
        "chapter": 28,
        "fex":    "/Loretta+Knight+of+the+Haligtree",
        "wikigg": "/Loretta,_Knight_of_the_Haligtree",
        "fandom": "Loretta,_Knight_of_the_Haligtree",
    },
    {
        "name": "Fire Giant",
        "override_name": "Fire Giant",
        "category": "character",
        "area": "Mountaintops of the Giants",
        "chapter": 21,
        "fex":    "/Fire+Giant",
        "wikigg": "/Fire_Giant",
        "fandom": "Fire_Giant",
    },
    {
        "name": "Dragonlord Placidusax",
        "override_name": "Dragonlord Placidusax",
        "category": "character",
        "area": "Farum Azula",
        "chapter": 22,
        "fex":    "/Dragonlord+Placidusax",
        "wikigg": "/Dragonlord_Placidusax",
        "fandom": "Dragonlord_Placidusax",
    },
    {
        "name": "Astel Naturalborn of the Void",
        "override_name": "Astel Naturalborn of the Void",
        "category": "character",
        "area": "Nokron Eternal City",
        "chapter": 8,
        "fex":    "/Astel+Naturalborn+of+the+Void",
        "wikigg": "/Astel,_Naturalborn_of_the_Void",
        "fandom": "Astel,_Naturalborn_of_the_Void",
    },
    {
        "name": "Margit the Fell Omen",
        "override_name": "Margit the Fell Omen",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Margit+the+Fell+Omen",
        "wikigg": "/Margit,_the_Fell_Omen",
        "fandom": "Margit,_the_Fell_Omen",
    },
    {
        "name": "Crucible Knight",
        "override_name": "Crucible Knight",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Crucible+Knight",
        "wikigg": "/Crucible_Knight",
        "fandom": "Crucible_Knight",
    },
    {
        "name": "Valiant Gargoyle",
        "override_name": "Valiant Gargoyle",
        "category": "character",
        "area": "Nokron Eternal City",
        "chapter": 8,
        "fex":    "/Valiant+Gargoyle",
        "wikigg": "/Valiant_Gargoyle",
        "fandom": "Valiant_Gargoyle",
    },

    # =========================================================================
    # SECTION 6 — KEY LORE CONCEPTS / SYSTEMS / WORLD HISTORY
    # =========================================================================
    {
        "name": "The Shattering",
        "override_name": "The Shattering",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/The+Shattering",
        "wikigg": "/The_Shattering",
        "fandom": "The_Shattering",
    },
    {
        "name": "Elden Ring",
        "override_name": "Elden Ring",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Elden+Ring",
        "wikigg": "/Elden_Ring_(Item)",
        "fandom": "Elden_Ring_(item)",
    },
    {
        "name": "Erdtree",
        "override_name": "Erdtree",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Erdtree",
        "wikigg": "/Erdtree",
        "fandom": "Erdtree",
    },
    {
        "name": "Golden Order",
        "override_name": "Golden Order",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Golden+Order",
        "wikigg": "/Golden_Order",
        "fandom": "Golden_Order",
    },
    {
        "name": "Runes",
        "override_name": "Runes",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Runes",
        "wikigg": "/Runes",
        "fandom": "Runes",
    },
    {
        "name": "Great Runes",
        "override_name": "Great Runes",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Great+Runes",
        "wikigg": "/Great_Runes",
        "fandom": "Great_Runes",
    },
    {
        "name": "Rune of Death",
        "override_name": "Rune of Death",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Rune+of+Death",
        "wikigg": "/Rune_of_Death",
        "fandom": "Rune_of_Death",
    },
    {
        "name": "Tarnished",
        "override_name": "Tarnished",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Tarnished",
        "wikigg": "/Tarnished",
        "fandom": "Tarnished",
    },
    {
        "name": "Grace",
        "override_name": "Grace",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Grace",
        "wikigg": "/Grace",
        "fandom": "Grace",
    },
    {
        "name": "Demigods",
        "override_name": "Demigods",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Demigods",
        "wikigg": "/Demigods",
        "fandom": "Demigods",
    },
    {
        "name": "Frenzied Flame",
        "override_name": "Frenzied Flame",
        "category": "lore",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Frenzied+Flame",
        "wikigg": "/Frenzied_Flame",
        "fandom": "Frenzied_Flame",
    },
    {
        "name": "Scarlet Rot",
        "override_name": "Scarlet Rot",
        "category": "lore",
        "area": "Caelid",
        "chapter": 9,
        "fex":    "/Scarlet+Rot",
        "wikigg": "/Scarlet_Rot",
        "fandom": "Scarlet_Rot",
    },
    {
        "name": "Omen",
        "override_name": "Omen",
        "category": "lore",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Omen",
        "wikigg": "/Omen",
        "fandom": "Omen",
    },
    {
        "name": "Albinaurics",
        "override_name": "Albinaurics",
        "category": "lore",
        "area": "Liurnia of the Lakes",
        "chapter": 4,
        "fex":    "/Albinauric",
        "wikigg": "/Albinauric",
        "fandom": "Albinauric",
    },
    {
        "name": "Nox People",
        "override_name": "Nox People",
        "category": "lore",
        "area": "Nokron Eternal City",
        "chapter": 8,
        "fex":    "/Nox",
        "wikigg": "/Nox",
        "fandom": "Nox",
    },
    {
        "name": "Eternal Cities",
        "override_name": "Eternal Cities",
        "category": "lore",
        "area": "Nokron Eternal City",
        "chapter": 8,
        "fex":    "/Eternal+Cities",
        "wikigg": "/Eternal_Cities",
        "fandom": "Eternal_Cities",
    },
    {
        "name": "Ancient Dragons",
        "override_name": "Ancient Dragons",
        "category": "lore",
        "area": "Farum Azula",
        "chapter": 22,
        "fex":    "/Ancient+Dragons",
        "wikigg": "/Ancient_Dragons",
        "fandom": "Ancient_Dragons",
    },
    {
        "name": "Torrent Spirit Steed",
        "override_name": "Torrent Spirit Steed",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Torrent",
        "wikigg": "/Torrent_(Spirit_Steed)",
        "fandom": "Torrent_(Spirit_Steed)",
    },
    {
        "name": "Roundtable Hold",
        "override_name": "Roundtable Hold",
        "category": "location",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Roundtable+Hold",
        "wikigg": "/Roundtable_Hold",
        "fandom": "Roundtable_Hold",
    },
    {
        "name": "Guidance of Grace",
        "override_name": "Guidance of Grace",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Guidance+of+Grace",
        "wikigg": "/Guidance_of_Grace",
        "fandom": "Guidance_of_Grace",
    },
    {
        "name": "Mending Rune",
        "override_name": "Mending Rune",
        "category": "lore",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Mending+Rune",
        "wikigg": "/Mending_Rune",
        "fandom": "Mending_Rune",
    },
    {
        "name": "Mending Rune of the Death-Prince",
        "override_name": "Mending Rune of the Death-Prince",
        "category": "item",
        "area": "Deeproot Depths",
        "chapter": 20,
        "fex":    "/Mending+Rune+of+the+Death-Prince",
        "wikigg": "/Mending_Rune_of_the_Death-Prince",
        "fandom": "Mending_Rune_of_the_Death-Prince",
    },
    {
        "name": "Mending Rune of Perfect Order",
        "override_name": "Mending Rune of Perfect Order",
        "category": "item",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Mending+Rune+of+Perfect+Order",
        "wikigg": "/Mending_Rune_of_Perfect_Order",
        "fandom": "Mending_Rune_of_Perfect_Order",
    },
    {
        "name": "Mending Rune of the Fell Curse",
        "override_name": "Mending Rune of the Fell Curse",
        "category": "item",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Mending+Rune+of+the+Fell+Curse",
        "wikigg": "/Mending_Rune_of_the_Fell_Curse",
        "fandom": "Mending_Rune_of_the_Fell_Curse",
    },
    {
        "name": "Godskin Apostles",
        "override_name": "Godskin Apostles",
        "category": "lore",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Godskin+Apostle",
        "wikigg": "/Godskin_Apostle",
        "fandom": "Godskin_Apostle",
    },
    {
        "name": "Black Knives",
        "override_name": "Black Knives",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Black+Knife",
        "wikigg": "/Black_Knife",
        "fandom": "Black_Knife",
    },
    {
        "name": "Deathbed Dream",
        "override_name": "Deathbed Dream",
        "category": "lore",
        "area": "Deeproot Depths",
        "chapter": 20,
        "fex":    "/Fia+Questline",
        "wikigg": "/Fia",
        "fandom": "Fia",
    },
    {
        "name": "Dark Moon",
        "override_name": "Dark Moon",
        "category": "lore",
        "area": "Liurnia of the Lakes",
        "chapter": 4,
        "fex":    "/Dark+Moon",
        "wikigg": "/Dark_Moon",
        "fandom": "Dark_Moon",
    },

    # =========================================================================
    # SECTION 7 — KEY ITEMS with lore text
    # =========================================================================
    {
        "name": "Remembrance of the Elden Beast",
        "override_name": "Remembrance of the Elden Beast",
        "category": "item",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Elden+Remembrance",
        "wikigg": "/Elden_Remembrance",
        "fandom": "Elden_Remembrance",
    },
    {
        "name": "Remembrance of the Starscourge",
        "override_name": "Remembrance of the Starscourge",
        "category": "item",
        "area": "Caelid",
        "chapter": 9,
        "fex":    "/Remembrance+of+the+Starscourge",
        "wikigg": "/Remembrance_of_the_Starscourge",
        "fandom": "Remembrance_of_the_Starscourge",
    },
    {
        "name": "Remembrance of the Rot Goddess",
        "override_name": "Remembrance of the Rot Goddess",
        "category": "item",
        "area": "Elphael",
        "chapter": 28,
        "fex":    "/Remembrance+of+the+Rot+Goddess",
        "wikigg": "/Remembrance_of_the_Rot_Goddess",
        "fandom": "Remembrance_of_the_Rot_Goddess",
    },
    {
        "name": "Remembrance of the Grafted",
        "override_name": "Remembrance of the Grafted",
        "category": "item",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Remembrance+of+the+Grafted",
        "wikigg": "/Remembrance_of_the_Grafted",
        "fandom": "Remembrance_of_the_Grafted",
    },
    {
        "name": "Remembrance of the Blood Lord",
        "override_name": "Remembrance of the Blood Lord",
        "category": "item",
        "area": "Mohgwyn Palace",
        "chapter": 23,
        "fex":    "/Remembrance+of+the+Blood+Lord",
        "wikigg": "/Remembrance_of_the_Blood_Lord",
        "fandom": "Remembrance_of_the_Blood_Lord",
    },
    {
        "name": "Remembrance of the Full Moon Queen",
        "override_name": "Remembrance of the Full Moon Queen",
        "category": "item",
        "area": "Liurnia of the Lakes",
        "chapter": 4,
        "fex":    "/Remembrance+of+the+Full+Moon+Queen",
        "wikigg": "/Remembrance_of_the_Full_Moon_Queen",
        "fandom": "Remembrance_of_the_Full_Moon_Queen",
    },
    {
        "name": "Remembrance of the Dragonlord",
        "override_name": "Remembrance of the Dragonlord",
        "category": "item",
        "area": "Farum Azula",
        "chapter": 22,
        "fex":    "/Remembrance+of+the+Dragonlord",
        "wikigg": "/Remembrance_of_the_Dragonlord",
        "fandom": "Remembrance_of_the_Dragonlord",
    },
    {
        "name": "Remembrance of the Black Blade",
        "override_name": "Remembrance of the Black Blade",
        "category": "item",
        "area": "Farum Azula",
        "chapter": 22,
        "fex":    "/Remembrance+of+the+Black+Blade",
        "wikigg": "/Remembrance_of_the_Black_Blade",
        "fandom": "Remembrance_of_the_Black_Blade",
    },
    {
        "name": "Remembrance of the Omen King",
        "override_name": "Remembrance of the Omen King",
        "category": "item",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Remembrance+of+the+Omen+King",
        "wikigg": "/Remembrance_of_the_Omen_King",
        "fandom": "Remembrance_of_the_Omen_King",
    },
    {
        "name": "Remembrance of the Lord of Blood",
        "override_name": "Remembrance of the Lord of Blood",
        "category": "item",
        "area": "Mohgwyn Palace",
        "chapter": 23,
        "fex":    "/Remembrance+of+the+Lord+of+Blood",
        "wikigg": "/Remembrance_of_the_Lord_of_Blood",
        "fandom": "Remembrance_of_the_Lord_of_Blood",
    },
    {
        "name": "Dark Moon Ring",
        "override_name": "Dark Moon Ring",
        "category": "item",
        "area": "Liurnia of the Lakes",
        "chapter": 4,
        "fex":    "/Dark+Moon+Ring",
        "wikigg": "/Dark_Moon_Ring",
        "fandom": "Dark_Moon_Ring",
    },
    {
        "name": "Nokron Eternal City",
        "override_name": "Nokron Eternal City",
        "category": "location",
        "area": "Nokron Eternal City",
        "chapter": 8,
        "fex":    "/Nokron+Eternal+City",
        "wikigg": "/Nokron,_Eternal_City",
        "fandom": "Nokron,_Eternal_City",
    },
    {
        "name": "Deeproot Depths",
        "override_name": "Deeproot Depths",
        "category": "location",
        "area": "Deeproot Depths",
        "chapter": 20,
        "fex":    "/Deeproot+Depths",
        "wikigg": "/Deeproot_Depths",
        "fandom": "Deeproot_Depths",
    },
    {
        "name": "Farum Azula",
        "override_name": "Farum Azula",
        "category": "location",
        "area": "Farum Azula",
        "chapter": 22,
        "fex":    "/Crumbling+Farum+Azula",
        "wikigg": "/Crumbling_Farum_Azula",
        "fandom": "Crumbling_Farum_Azula",
    },
    {
        "name": "Consecrated Snowfield",
        "override_name": "Consecrated Snowfield",
        "category": "location",
        "area": "Consecrated Snowfield",
        "chapter": 25,
        "fex":    "/Consecrated+Snowfield",
        "wikigg": "/Consecrated_Snowfield",
        "fandom": "Consecrated_Snowfield",
    },
    {
        "name": "Mohgwyn Palace",
        "override_name": "Mohgwyn Palace",
        "category": "location",
        "area": "Mohgwyn Palace",
        "chapter": 23,
        "fex":    "/Mohgwyn+Palace",
        "wikigg": "/Mohgwyn_Palace",
        "fandom": "Mohgwyn_Palace",
    },
    {
        "name": "Siofra River",
        "override_name": "Siofra River",
        "category": "location",
        "area": "Siofra River",
        "chapter": 7,
        "fex":    "/Siofra+River",
        "wikigg": "/Siofra_River",
        "fandom": "Siofra_River",
    },

    # =========================================================================
    # SECTION 8 — SHADOW OF THE ERDTREE DLC characters and lore
    # =========================================================================
    {
        "name": "Messmer the Impaler",
        "override_name": "Messmer the Impaler",
        "category": "character",
        "area": "Shadow Keep",
        "chapter": 35,
        "fex":    "/Messmer+the+Impaler",
        "wikigg": "/Messmer_the_Impaler",
        "fandom": "Messmer_the_Impaler",
    },
    {
        "name": "Needle Knight Leda",
        "override_name": "Needle Knight Leda",
        "category": "character",
        "area": "Gravesite Plain",
        "chapter": 30,
        "fex":    "/Needle+Knight+Leda",
        "wikigg": "/Needle_Knight_Leda",
        "fandom": "Needle_Knight_Leda",
    },
    {
        "name": "Sir Ansbach",
        "override_name": "Sir Ansbach",
        "category": "character",
        "area": "Shadow Keep",
        "chapter": 35,
        "fex":    "/Sir+Ansbach",
        "wikigg": "/Sir_Ansbach",
        "fandom": "Sir_Ansbach",
    },
    {
        "name": "Thiollier",
        "override_name": "Thiollier",
        "category": "character",
        "area": "Gravesite Plain",
        "chapter": 30,
        "fex":    "/Thiollier",
        "wikigg": "/Thiollier",
        "fandom": "Thiollier",
    },
    {
        "name": "Moore",
        "override_name": "Moore",
        "category": "character",
        "area": "Gravesite Plain",
        "chapter": 30,
        "fex":    "/Moore",
        "wikigg": "/Moore",
        "fandom": "Moore",
    },
    {
        "name": "Hornsent",
        "override_name": "Hornsent",
        "category": "character",
        "area": "Gravesite Plain",
        "chapter": 30,
        "fex":    "/Hornsent",
        "wikigg": "/Hornsent",
        "fandom": "Hornsent",
    },
    {
        "name": "Freyja",
        "override_name": "Freyja",
        "category": "character",
        "area": "Gravesite Plain",
        "chapter": 30,
        "fex":    "/Freyja",
        "wikigg": "/Freyja",
        "fandom": "Freyja",
    },
    {
        "name": "Midra Lord of Frenzied Flame",
        "override_name": "Midra Lord of Frenzied Flame",
        "category": "character",
        "area": "Abyssal Woods",
        "chapter": 37,
        "fex":    "/Midra+Lord+of+Frenzied+Flame",
        "wikigg": "/Midra,_Lord_of_Frenzied_Flame",
        "fandom": "Midra,_Lord_of_Frenzied_Flame",
    },
    {
        "name": "Romina Saint of the Bud",
        "override_name": "Romina Saint of the Bud",
        "category": "character",
        "area": "Ancient Ruins of Rauh",
        "chapter": 36,
        "fex":    "/Romina+Saint+of+the+Bud",
        "wikigg": "/Romina,_Saint_of_the_Bud",
        "fandom": "Romina,_Saint_of_the_Bud",
    },
    {
        "name": "Rellana Twin Moon Knight",
        "override_name": "Rellana Twin Moon Knight",
        "category": "character",
        "area": "Shadow Keep",
        "chapter": 35,
        "fex":    "/Rellana+Twin+Moon+Knight",
        "wikigg": "/Rellana,_Twin_Moon_Knight",
        "fandom": "Rellana,_Twin_Moon_Knight",
    },
    {
        "name": "Bayle the Dread",
        "override_name": "Bayle the Dread",
        "category": "character",
        "area": "Jagged Peak",
        "chapter": 38,
        "fex":    "/Bayle+the+Dread",
        "wikigg": "/Bayle_the_Dread",
        "fandom": "Bayle_the_Dread",
    },
    {
        "name": "Metyr Mother of Fingers",
        "override_name": "Metyr Mother of Fingers",
        "category": "character",
        "area": "Shadow Keep",
        "chapter": 35,
        "fex":    "/Metyr+Mother+of+Fingers",
        "wikigg": "/Metyr,_Mother_of_Fingers",
        "fandom": "Metyr,_Mother_of_Fingers",
    },
    {
        "name": "Enir-Ilim",
        "override_name": "Enir-Ilim",
        "category": "location",
        "area": "Enir-Ilim",
        "chapter": 34,
        "fex":    "/Enir-Ilim",
        "wikigg": "/Enir-Ilim",
        "fandom": "Enir-Ilim",
    },
    {
        "name": "Shadow Keep",
        "override_name": "Shadow Keep",
        "category": "location",
        "area": "Shadow Keep",
        "chapter": 35,
        "fex":    "/Shadow+Keep",
        "wikigg": "/Shadow_Keep",
        "fandom": "Shadow_Keep",
    },
    {
        "name": "Gravesite Plain",
        "override_name": "Gravesite Plain",
        "category": "location",
        "area": "Gravesite Plain",
        "chapter": 30,
        "fex":    "/Gravesite+Plain",
        "wikigg": "/Gravesite_Plain",
        "fandom": "Gravesite_Plain",
    },
    {
        "name": "Abyssal Woods",
        "override_name": "Abyssal Woods",
        "category": "location",
        "area": "Abyssal Woods",
        "chapter": 37,
        "fex":    "/Abyssal+Woods",
        "wikigg": "/Abyssal_Woods",
        "fandom": "Abyssal_Woods",
    },
    {
        "name": "Scadutree",
        "override_name": "Scadutree",
        "category": "lore",
        "area": "Gravesite Plain",
        "chapter": 30,
        "fex":    "/Scadutree",
        "wikigg": "/Scadutree",
        "fandom": "Scadutree",
    },
    {
        "name": "Scadutree Avatar",
        "override_name": "Scadutree Avatar",
        "category": "character",
        "area": "Shadow of the Erdtree",
        "chapter": 30,
        "fex":    "/Scadutree+Avatar",
        "wikigg": "/Scadutree_Avatar",
        "fandom": "Scadutree_Avatar",
    },
    {
        "name": "Impenetrable Thorns",
        "override_name": "Impenetrable Thorns",
        "category": "lore",
        "area": "Enir-Ilim",
        "chapter": 34,
        "fex":    "/Impenetrable+Thorns",
        "wikigg": "/Impenetrable_Thorns",
        "fandom": "Impenetrable_Thorns",
    },
    {
        "name": "Land of Shadow",
        "override_name": "Land of Shadow",
        "category": "lore",
        "area": "Gravesite Plain",
        "chapter": 30,
        "fex":    "/Land+of+Shadow",
        "wikigg": "/Land_of_Shadow",
        "fandom": "Land_of_Shadow",
    },
    {
        "name": "Jagged Peak",
        "override_name": "Jagged Peak",
        "category": "location",
        "area": "Jagged Peak",
        "chapter": 38,
        "fex":    "/Jagged+Peak",
        "wikigg": "/Jagged_Peak",
        "fandom": "Jagged_Peak",
    },
    {
        "name": "Ancient Ruins of Rauh",
        "override_name": "Ancient Ruins of Rauh",
        "category": "location",
        "area": "Ancient Ruins of Rauh",
        "chapter": 36,
        "fex":    "/Ancient+Ruins+of+Rauh",
        "wikigg": "/Ancient_Ruins_of_Rauh",
        "fandom": "Ancient_Ruins_of_Rauh",
    },
    {
        "name": "Cerulean Coast",
        "override_name": "Cerulean Coast",
        "category": "location",
        "area": "Cerulean Coast",
        "chapter": 31,
        "fex":    "/Cerulean+Coast",
        "wikigg": "/Cerulean_Coast",
        "fandom": "Cerulean_Coast",
    },

    # =========================================================================
    # SECTION 9 — MINOR / EASY-TO-MISS characters and lore tidbits
    # =========================================================================
    {
        "name": "Shabriri",
        "override_name": "Shabriri",
        "category": "character",
        "area": "Mountaintops of the Giants",
        "chapter": 21,
        "fex":    "/Shabriri",
        "wikigg": "/Shabriri",
        "fandom": "Shabriri",
    },
    {
        "name": "White-Faced Varré",
        "override_name": "White-Faced Varré",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/White-Faced+Varré",
        "wikigg": "/White-Faced_Varr%C3%A9",
        "fandom": "White-Faced_Varr%C3%A9",
    },
    {
        "name": "Iji Servant of Ranni",
        "override_name": "Iji Servant of Ranni",
        "category": "character",
        "area": "Liurnia of the Lakes",
        "chapter": 4,
        "fex":    "/Iji",
        "wikigg": "/Iji",
        "fandom": "Iji",
    },
    {
        "name": "Pidia Carian Servant",
        "override_name": "Pidia Carian Servant",
        "category": "character",
        "area": "Liurnia of the Lakes",
        "chapter": 4,
        "fex":    "/Pidia+Carian+Servant",
        "wikigg": "/Pidia,_Carian_Servant",
        "fandom": "Pidia,_Carian_Servant",
    },
    {
        "name": "Miriel Pastor of Vows",
        "override_name": "Miriel Pastor of Vows",
        "category": "character",
        "area": "Liurnia of the Lakes",
        "chapter": 4,
        "fex":    "/Miriel+Pastor+of+Vows",
        "wikigg": "/Miriel,_Pastor_of_Vows",
        "fandom": "Miriel,_Pastor_of_Vows",
    },
    {
        "name": "Thops",
        "override_name": "Thops",
        "category": "character",
        "area": "Liurnia of the Lakes",
        "chapter": 4,
        "fex":    "/Thops",
        "wikigg": "/Thops",
        "fandom": "Thops",
    },
    {
        "name": "Rya",
        "override_name": "Rya",
        "category": "character",
        "area": "Liurnia of the Lakes",
        "chapter": 4,
        "fex":    "/Rya",
        "wikigg": "/Rya",
        "fandom": "Rya",
    },
    {
        "name": "Iron Fist Alexander",
        "override_name": "Iron Fist Alexander",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Alexander",
        "wikigg": "/Alexander,_Iron_Fist",
        "fandom": "Alexander,_Iron_Fist",
    },
    {
        "name": "Boggart",
        "override_name": "Boggart",
        "category": "character",
        "area": "Liurnia of the Lakes",
        "chapter": 4,
        "fex":    "/Blackguard+Big+Boggart",
        "wikigg": "/Blackguard_Big_Boggart",
        "fandom": "Blackguard_Big_Boggart",
    },
    {
        "name": "Yura Hunter of Bloody Fingers",
        "override_name": "Yura Hunter of Bloody Fingers",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Yura+Hunter+of+Bloody+Fingers",
        "wikigg": "/Yura,_Hunter_of_Bloody_Fingers",
        "fandom": "Yura,_Hunter_of_Bloody_Fingers",
    },
    {
        "name": "Eleonora Violet Bloody Finger",
        "override_name": "Eleonora Violet Bloody Finger",
        "category": "character",
        "area": "Altus Plateau",
        "chapter": 13,
        "fex":    "/Eleonora+Violet+Bloody+Finger",
        "wikigg": "/Eleonora,_Violet_Bloody_Finger",
        "fandom": "Eleonora,_Violet_Bloody_Finger",
    },
    {
        "name": "Mohg the Omen",
        "override_name": "Mohg the Omen",
        "category": "character",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Mohg+the+Omen",
        "wikigg": "/Mohg,_the_Omen",
        "fandom": "Mohg,_the_Omen",
    },
    {
        "name": "Bloody Finger Okina",
        "override_name": "Bloody Finger Okina",
        "category": "character",
        "area": "Mountaintops of the Giants",
        "chapter": 21,
        "fex":    "/Bloody+Finger+Okina",
        "wikigg": "/Bloody_Finger_Okina",
        "fandom": "Bloody_Finger_Okina",
    },
    {
        "name": "Latenna the Albinauric",
        "override_name": "Latenna the Albinauric",
        "category": "character",
        "area": "Liurnia of the Lakes",
        "chapter": 4,
        "fex":    "/Latenna+the+Albinauric",
        "wikigg": "/Latenna_the_Albinauric",
        "fandom": "Latenna_the_Albinauric",
    },
    {
        "name": "Albus",
        "override_name": "Albus",
        "category": "character",
        "area": "Liurnia of the Lakes",
        "chapter": 4,
        "fex":    "/Albus",
        "wikigg": "/Albus",
        "fandom": "Albus",
    },
    {
        "name": "Deathtouched Tarnished",
        "override_name": "Deathtouched Tarnished",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Deathtouched+Catacombs",
        "wikigg": "/Deathtouched_Catacombs",
        "fandom": "Deathtouched_Catacombs",
    },
    {
        "name": "Carian Royal Family",
        "override_name": "Carian Royal Family",
        "category": "lore",
        "area": "Liurnia of the Lakes",
        "chapter": 4,
        "fex":    "/Carian+Royal+Family",
        "wikigg": "/Carian_Royal_Family",
        "fandom": "Carian_Royal_Family",
    },
    {
        "name": "Fire Monks",
        "override_name": "Fire Monks",
        "category": "lore",
        "area": "Mountaintops of the Giants",
        "chapter": 21,
        "fex":    "/Fire+Monks",
        "wikigg": "/Fire_Monk",
        "fandom": "Fire_Monk",
    },
    {
        "name": "Rune Bears",
        "override_name": "Rune Bears",
        "category": "creature",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Runebear",
        "wikigg": "/Runebear",
        "fandom": "Runebear",
    },
    {
        "name": "Walking Mausoleums",
        "override_name": "Walking Mausoleums",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Walking+Mausoleum",
        "wikigg": "/Walking_Mausoleum",
        "fandom": "Walking_Mausoleum",
    },
    {
        "name": "Finger Maidens",
        "override_name": "Finger Maidens",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Finger+Maiden",
        "wikigg": "/Finger_Maiden",
        "fandom": "Finger_Maiden",
    },
    {
        "name": "Melina",
        "override_name": "Melina",
        "category": "character",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Melina",
        "wikigg": "/Melina",
        "fandom": "Melina",
    },
    {
        "name": "Hoslow Family",
        "override_name": "Hoslow Family",
        "category": "lore",
        "area": "Mountaintops of the Giants",
        "chapter": 21,
        "fex":    "/Juno+Hoslow",
        "wikigg": "/Juno_Hoslow",
        "fandom": "Juno_Hoslow",
    },
    {
        "name": "Volcano Manor Questline",
        "override_name": "Volcano Manor Questline",
        "category": "lore",
        "area": "Mt. Gelmir",
        "chapter": 14,
        "fex":    "/Volcano+Manor+Questline",
        "wikigg": "/Volcano_Manor",
        "fandom": "Volcano_Manor",
    },
    {
        "name": "Night Cavalry",
        "override_name": "Night Cavalry",
        "category": "creature",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Night+Cavalry",
        "wikigg": "/Night_Cavalry",
        "fandom": "Night_Cavalry",
    },
    {
        "name": "Deathbirds",
        "override_name": "Deathbirds",
        "category": "creature",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Death+Rite+Bird",
        "wikigg": "/Death_Rite_Bird",
        "fandom": "Death_Rite_Bird",
    },
    {
        "name": "Tibia Mariner",
        "override_name": "Tibia Mariner",
        "category": "creature",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Tibia+Mariner",
        "wikigg": "/Tibia_Mariner",
        "fandom": "Tibia_Mariner",
    },
    {
        "name": "Bell Bearing Hunter",
        "override_name": "Bell Bearing Hunter",
        "category": "creature",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Bell+Bearing+Hunter",
        "wikigg": "/Bell_Bearing_Hunter",
        "fandom": "Bell_Bearing_Hunter",
    },
    {
        "name": "Bloody Finger",
        "override_name": "Bloody Finger",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Bloody+Finger",
        "wikigg": "/Bloody_Finger",
        "fandom": "Bloody_Finger",
    },
    {
        "name": "Fingers",
        "override_name": "Fingers",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/Fingers",
        "wikigg": "/Fingers",
        "fandom": "Fingers",
    },
    {
        "name": "Liurnia of the Lakes",
        "override_name": "Liurnia of the Lakes",
        "category": "location",
        "area": "Liurnia of the Lakes",
        "chapter": 4,
        "fex":    "/Liurnia+of+the+Lakes",
        "wikigg": "/Liurnia_of_the_Lakes",
        "fandom": "Liurnia_of_the_Lakes",
    },
    {
        "name": "Caelid",
        "override_name": "Caelid",
        "category": "location",
        "area": "Caelid",
        "chapter": 9,
        "fex":    "/Caelid",
        "wikigg": "/Caelid",
        "fandom": "Caelid",
    },
    {
        "name": "Altus Plateau",
        "override_name": "Altus Plateau",
        "category": "location",
        "area": "Altus Plateau",
        "chapter": 13,
        "fex":    "/Altus+Plateau",
        "wikigg": "/Altus_Plateau",
        "fandom": "Altus_Plateau",
    },
    {
        "name": "Mt Gelmir",
        "override_name": "Mt Gelmir",
        "category": "location",
        "area": "Mt. Gelmir",
        "chapter": 14,
        "fex":    "/Mt.+Gelmir",
        "wikigg": "/Mt._Gelmir",
        "fandom": "Mt._Gelmir",
    },
    {
        "name": "Leyndell Royal Capital",
        "override_name": "Leyndell Royal Capital",
        "category": "location",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Leyndell+Royal+Capital",
        "wikigg": "/Leyndell,_Royal_Capital",
        "fandom": "Leyndell,_Royal_Capital",
    },
    {
        "name": "Mountaintops of the Giants",
        "override_name": "Mountaintops of the Giants",
        "category": "location",
        "area": "Mountaintops of the Giants",
        "chapter": 21,
        "fex":    "/Mountaintops+of+the+Giants",
        "wikigg": "/Mountaintops_of_the_Giants",
        "fandom": "Mountaintops_of_the_Giants",
    },
    {
        "name": "Miquella's Haligtree",
        "override_name": "Miquella's Haligtree",
        "category": "location",
        "area": "Elphael",
        "chapter": 28,
        "fex":    "/Miquella's+Haligtree",
        "wikigg": "/Miquella%27s_Haligtree",
        "fandom": "Miquella%27s_Haligtree",
    },
    {
        "name": "Weeping Peninsula",
        "override_name": "Weeping Peninsula",
        "category": "location",
        "area": "Weeping Peninsula",
        "chapter": 2,
        "fex":    "/Weeping+Peninsula",
        "wikigg": "/Weeping_Peninsula",
        "fandom": "Weeping_Peninsula",
    },
    # ── ENDINGS ──────────────────────────────────────────────────────────────
    {
        "name": "Age of Stars Ending",
        "override_name": "Age of Stars Ending",
        "category": "lore",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Age+of+Stars+Ending",
        "wikigg": "/Age_of_Stars_(Ending)",
        "fandom": "Age_of_Stars_(Ending)",
    },
    {
        "name": "Age of Order Ending",
        "override_name": "Age of Order Ending",
        "category": "lore",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Age+of+Order+Ending",
        "wikigg": "/Age_of_Order_(Ending)",
        "fandom": "Age_of_Order_(Ending)",
    },
    {
        "name": "Blessing of Despair Ending",
        "override_name": "Blessing of Despair Ending",
        "category": "lore",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Blessing+of+Despair+Ending",
        "wikigg": "/Blessing_of_Despair_(Ending)",
        "fandom": "Blessing_of_Despair_(Ending)",
    },
    {
        "name": "Elden Lord Ending",
        "override_name": "Elden Lord Ending",
        "category": "lore",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Elden+Lord+Ending",
        "wikigg": "/Elden_Lord_(Ending)",
        "fandom": "Elden_Lord_(Ending)",
    },

    # ── DLC ENDINGS ──────────────────────────────────────────────────────────
    {
        "name": "Frenzyflame Ending",
        "override_name": "Frenzyflame Ending",
        "category": "lore",
        "area": "Leyndell Royal Capital",
        "chapter": 15,
        "fex":    "/Frenzyflame+Ending",
        "wikigg": "/Frenzyflame_(Ending)",
        "fandom": "Frenzyflame_(Ending)",
    },
    {
        "name": "New Game Plus",
        "override_name": "New Game Plus",
        "category": "lore",
        "area": "Limgrave",
        "chapter": 1,
        "fex":    "/New+Game+Plus",
        "wikigg": "/New_Game_Plus",
        "fandom": "New_Game_Plus",
    },
]


def main():
    os.makedirs("data/lore", exist_ok=True)
    filepath = "data/lore/missing_lore.txt"

    # Load already-saved names to avoid duplicates
    existing = set()
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("name: "):
                    existing.add(line[6:].strip())

    print(f"=== Re-scraping {len(MISSING_ENTRIES)} missing/broken entries ===\n")

    for entry in MISSING_ENTRIES:
        name = entry["override_name"]

        if name in existing:
            print(f"  [SKIP] {name} (already saved)")
            continue

        print(f"  Scraping: {name}")
        texts = []

        if entry.get("fex"):
            t, text = scrape_fextralife(entry["fex"])
            if text:
                texts.append(text)
                print(f"    Fextralife: {len(text)} chars")
            time.sleep(1.2)

        if entry.get("wikigg"):
            t, text = scrape_wikigg(entry["wikigg"])
            if text:
                texts.append(text)
                print(f"    Wikigg:     {len(text)} chars")
            time.sleep(1.2)

        if entry.get("fandom"):
            t, text = scrape_fandom(entry["fandom"])
            if text:
                texts.append(text)
                print(f"    Fandom:     {len(text)} chars")
            time.sleep(1.2)

        if not texts:
            print(f"    [FAILED] No content scraped for {name}")
            continue

        combined = combine_sources(texts)

        if len(combined) < 50:
            print(f"    [TOO SHORT] Only {len(combined)} chars — skipping")
            continue

        save_lore(
            name=name,
            category=entry["category"],
            area=entry["area"],
            chapter=entry["chapter"],
            text=combined,
            filepath=filepath,
        )
        existing.add(name)
        print(f"    [SAVED] {name} — {len(combined)} chars\n")

    print(f"\n=== Done! File saved to: {filepath} ===")
    print("Now run: python ingest.py")
    print("\nAdd this to FILE_TO_CATEGORY in ingest.py:")
    print('    "missing_lore": "lore",')


if __name__ == "__main__":
    main()