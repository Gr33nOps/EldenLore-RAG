import requests
from bs4 import BeautifulSoup
import time
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

FEXTRALIFE_BASE = "https://eldenring.wiki.fextralife.com"
WIKIGG_BASE = "https://eldenring.wiki.gg"
FANDOM_BASE = "https://eldenring.fandom.com/wiki"

AREA_ORDER = [
    "Limgrave", "Stormveil Castle", "Weeping Peninsula",
    "Liurnia of the Lakes", "Raya Lucaria Academy", "Caria Manor",
    "Siofra River", "Nokron Eternal City", "Caelid", "Dragonbarrow",
    "Redmane Castle", "Altus Plateau", "Mt Gelmir", "Volcano Manor",
    "Leyndell Royal Capital", "Subterranean Shunning-Grounds",
    "Ainsel River", "Lake of Rot", "Deeproot Depths",
    "Forbidden Lands", "Mountaintops of the Giants",
    "Consecrated Snowfield", "Mohgwyn Palace",
    "Miquella's Haligtree", "Elphael Brace of the Haligtree",
    "Crumbling Farum Azula",
    "Gravesite Plain", "Scadu Altus", "Shadow Keep",
    "Rauh Base", "Cerulean Coast", "Jagged Peak",
    "Abyssal Woods", "Enir-Ilim",
]

BOSS_AREA_MAP = {
    "Margit": "Limgrave", "Godrick": "Stormveil Castle",
    "Red Wolf": "Raya Lucaria Academy", "Rennala": "Raya Lucaria Academy",
    "Radahn": "Caelid", "Morgott": "Leyndell Royal Capital",
    "Fire Giant": "Mountaintops of the Giants",
    "Maliketh": "Crumbling Farum Azula",
    "Hoarah Loux": "Leyndell Royal Capital",
    "Elden Beast": "Leyndell Royal Capital",
    "Malenia": "Elphael Brace of the Haligtree",
    "Mohg": "Mohgwyn Palace", "Rykard": "Volcano Manor",
    "Astel": "Lake of Rot", "Placidusax": "Crumbling Farum Azula",
    "Fortissax": "Deeproot Depths", "Godfrey": "Leyndell Royal Capital",
    "Mimic Tear": "Nokron Eternal City",
    "Loretta": "Miquella's Haligtree",
    "Commander Niall": "Mountaintops of the Giants",
    "Commander O'Neil": "Caelid",
    "Messmer": "Shadow Keep", "Romina": "Cerulean Coast",
    "Promised Consort": "Enir-Ilim", "Bayle": "Jagged Peak",
    "Metyr": "Scadu Altus", "Scadutree Avatar": "Cerulean Coast",
    "Dancing Lion": "Gravesite Plain", "Rellana": "Shadow Keep",
    "Midra": "Abyssal Woods", "Commander Gaius": "Scadu Altus",
    "Putrescent Knight": "Abyssal Woods",
    "Blackgaol Knight": "Gravesite Plain",
    "Golden Hippopotamus": "Shadow Keep",
    "Furnace Golem": "Scadu Altus",
    "Jori": "Scadu Altus",
    "Demi-Human Queen": "Limgrave",
    "Crucible Knight": "Limgrave",
    "Erdtree Avatar": "Limgrave",
    "Night Cavalry": "Limgrave",
    "Bell Bearing Hunter": "Limgrave",
    "Ulcerated Tree Spirit": "Limgrave",
    "Ancestor Spirit": "Siofra River",
    "Valiant Gargoyle": "Siofra River",
    "Elemer": "Altus Plateau",
    "Sanguine Noble": "Mohgwyn Palace",
    "Leonine Misbegotten": "Weeping Peninsula",
    "Bloodhound Knight Darriwil": "Limgrave",
    "Grafted Scion": "Limgrave",
    "Fell Twins": "Leyndell Royal Capital",
    "Mohg the Omen": "Leyndell Royal Capital",
    "Esgar": "Leyndell Royal Capital",
    "Death Rite Bird": "Mountaintops of the Giants",
}

CHARACTER_AREA_MAP = {
    "Melina": "Limgrave", "Ranni": "Liurnia of the Lakes",
    "Blaidd": "Limgrave", "Iji": "Liurnia of the Lakes",
    "Rogier": "Stormveil Castle", "Patches": "Limgrave",
    "Alexander": "Limgrave", "Millicent": "Caelid",
    "Nepheli": "Stormveil Castle", "Fia": "Leyndell Royal Capital",
    "Roderika": "Limgrave", "Dung Eater": "Leyndell Royal Capital",
    "Gideon": "Leyndell Royal Capital", "Gurranq": "Caelid",
    "Hyetta": "Liurnia of the Lakes", "Tanith": "Volcano Manor",
    "Sellen": "Limgrave", "Varre": "Limgrave",
    "Corhyn": "Altus Plateau", "Goldmask": "Altus Plateau",
    "Diallos": "Limgrave", "Gowry": "Caelid",
    "Leda": "Gravesite Plain", "Thiollier": "Gravesite Plain",
    "Moore": "Gravesite Plain", "Ansbach": "Shadow Keep",
    "Freyja": "Gravesite Plain", "Hornsent": "Gravesite Plain",
    "Igon": "Jagged Peak", "Ymir": "Scadu Altus",
    "Miquella": "Enir-Ilim", "Shabriri": "Leyndell Royal Capital",
    "Boggart": "Limgrave", "Boc": "Limgrave",
    "Latenna": "Liurnia of the Lakes", "Miriel": "Limgrave",
    "Kenneth": "Limgrave", "Edgar": "Weeping Peninsula",
    "Irina": "Weeping Peninsula", "Jar-Bairn": "Altus Plateau",
    "D Hunter": "Limgrave", "Seluvis": "Liurnia of the Lakes",
    "Rya": "Altus Plateau", "Hewg": "Leyndell Royal Capital",
    "Enia": "Leyndell Royal Capital",
}


def get_area_number(area_name):
    for i, area in enumerate(AREA_ORDER):
        if area.lower() in area_name.lower() or area_name.lower() in area.lower():
            return i + 1
    return 1


def get_entity_area(name, category):
    if category == "boss":
        for key, area in BOSS_AREA_MAP.items():
            if key.lower() in name.lower():
                return area
    if category == "character":
        for key, area in CHARACTER_AREA_MAP.items():
            if key.lower() in name.lower():
                return area
    return "Limgrave"


def clean_text(text):
    lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 40]
    seen = set()
    unique = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            unique.append(line)
    return "\n".join(unique)


def scrape_fextralife(path):
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
        all_paragraphs = []
        for tag in content_div.find_all(["p", "li"]):
            text = tag.get_text(strip=True)
            if len(text) > 40:
                all_paragraphs.append(text)
        lore_text = []
        capture = False
        for tag in content_div.find_all(["h2", "h3", "h4", "p", "ul", "li"]):
            text = tag.get_text(strip=True)
            if any(keyword in text.lower() for keyword in [
                "lore", "notes", "trivia", "background", "story",
                "description", "about", "history", "character info",
                "appearance", "personality", "overview"
            ]):
                capture = True
            if capture and tag.name in ["p", "li"]:
                if len(text) > 40:
                    lore_text.append(text)
            if capture and tag.name in ["h2", "h3"] and len(lore_text) > 5:
                if not any(keyword in text.lower() for keyword in [
                    "lore", "notes", "trivia", "background", "story",
                    "description", "about", "history", "appearance"
                ]):
                    break
        combined = all_paragraphs[:20] + lore_text
        return title, clean_text("\n".join(combined[:100]))
    except Exception:
        return None, None


def scrape_wikigg(path):
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
        paragraphs = content.find_all("p")
        text = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 40)
        return title, clean_text(text)[:5000]
    except Exception:
        return None, None


def scrape_fandom(path):
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
        all_paragraphs = []
        for tag in content.find_all(["p", "li"]):
            text = tag.get_text(strip=True)
            if len(text) > 40:
                all_paragraphs.append(text)
        return title, clean_text("\n".join(all_paragraphs[:100]))
    except Exception:
        return None, None


def combine_sources(texts):
    seen_sentences = set()
    combined = []
    for text in texts:
        if not text:
            continue
        for line in text.splitlines():
            line = line.strip()
            if len(line) > 40 and line not in seen_sentences:
                seen_sentences.add(line)
                combined.append(line)
    return "\n".join(combined[:150])


def load_existing_names(file_key):
    filepath = f"data/lore/{file_key}.txt"
    if not os.path.exists(filepath):
        return set()
    names = set()
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("name: "):
                names.add(line[6:].strip())
    return names


def save_lore(category, name, area, chapter_num, text, filepath):
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"area: {area}\n")
        f.write(f"chapter: {chapter_num}\n")
        f.write(f"name: {name}\n")
        f.write(f"{text}\n")
        f.write("\n---\n\n")


# ==============================================================
# COMPLETE SCRAPE LIST — BASE GAME + DLC + ALL INDIRECT LORE
# ==============================================================
SCRAPE_LIST = {

    # ----------------------------------------------------------
    # BOSSES — base game + DLC
    # ----------------------------------------------------------
    "bosses": {
        "category": "boss",
        "entries": [
            # Main bosses
            {"fex": "/Margit+the+Fell+Omen", "wikigg": "/Margit_the_Fell_Omen", "fandom": "Margit,_the_Fell_Omen"},
            {"fex": "/Godrick+the+Grafted", "wikigg": "/Godrick_the_Grafted", "fandom": "Godrick_the_Grafted"},
            {"fex": "/Red+Wolf+of+Radagon", "wikigg": "/Red_Wolf_of_Radagon", "fandom": "Red_Wolf_of_Radagon"},
            {"fex": "/Rennala+Queen+of+the+Full+Moon", "wikigg": "/Rennala,_Queen_of_the_Full_Moon", "fandom": "Rennala,_Queen_of_the_Full_Moon"},
            {"fex": "/Starscourge+Radahn", "wikigg": "/Starscourge_Radahn", "fandom": "Starscourge_Radahn"},
            {"fex": "/Morgott+the+Omen+King", "wikigg": "/Morgott,_the_Omen_King", "fandom": "Morgott,_the_Omen_King"},
            {"fex": "/Fire+Giant", "wikigg": "/Fire_Giant", "fandom": "Fire_Giant"},
            {"fex": "/Maliketh+the+Black+Blade", "wikigg": "/Maliketh,_the_Black_Blade", "fandom": "Maliketh,_the_Black_Blade"},
            {"fex": "/Hoarah+Loux", "wikigg": "/Hoarah_Loux,_Warrior", "fandom": "Hoarah_Loux"},
            {"fex": "/Elden+Beast", "wikigg": "/Elden_Beast", "fandom": "Elden_Beast"},
            {"fex": "/Malenia+Blade+of+Miquella", "wikigg": "/Malenia,_Blade_of_Miquella", "fandom": "Malenia,_Blade_of_Miquella"},
            {"fex": "/Mohg+Lord+of+Blood", "wikigg": "/Mohg,_Lord_of_Blood", "fandom": "Mohg,_Lord_of_Blood"},
            {"fex": "/Rykard+Lord+of+Blasphemy", "wikigg": "/Rykard,_Lord_of_Blasphemy", "fandom": "Rykard,_Lord_of_Blasphemy"},
            {"fex": "/Astel+Naturalborn+of+the+Void", "wikigg": "/Astel,_Naturalborn_of_the_Void", "fandom": "Astel,_Naturalborn_of_the_Void"},
            {"fex": "/Dragonlord+Placidusax", "wikigg": "/Dragonlord_Placidusax", "fandom": "Dragonlord_Placidusax"},
            {"fex": "/Lichdragon+Fortissax", "wikigg": "/Lichdragon_Fortissax", "fandom": "Lichdragon_Fortissax"},
            {"fex": "/Godfrey+First+Elden+Lord", "wikigg": "/Godfrey,_First_Elden_Lord", "fandom": "Godfrey,_First_Elden_Lord"},
            {"fex": "/Mimic+Tear", "wikigg": "/Mimic_Tear", "fandom": "Mimic_Tear"},
            {"fex": "/Loretta+Knight+of+the+Haligtree", "wikigg": "/Loretta,_Knight_of_the_Haligtree", "fandom": "Loretta,_Knight_of_the_Haligtree"},
            {"fex": "/Commander+Niall", "wikigg": "/Commander_Niall", "fandom": "Commander_Niall"},
            {"fex": "/Commander+O'Neil", "wikigg": "/Commander_O%27Neil", "fandom": "Commander_O%27Neil"},
            {"fex": "/Valiant+Gargoyle", "wikigg": "/Valiant_Gargoyle", "fandom": "Valiant_Gargoyle"},
            {"fex": "/Ancestor+Spirit", "wikigg": "/Ancestor_Spirit", "fandom": "Ancestor_Spirit"},
            {"fex": "/Elemer+of+the+Briar", "wikigg": "/Elemer_of_the_Briar", "fandom": "Elemer_of_the_Briar"},
            {"fex": "/Crucible+Knight", "wikigg": "/Crucible_Knight", "fandom": "Crucible_Knight"},
            {"fex": "/Ulcerated+Tree+Spirit", "wikigg": "/Ulcerated_Tree_Spirit", "fandom": "Ulcerated_Tree_Spirit"},
            {"fex": "/Death+Rite+Bird", "wikigg": "/Death_Rite_Bird", "fandom": "Death_Rite_Bird"},
            {"fex": "/Erdtree+Avatar", "wikigg": "/Erdtree_Avatar", "fandom": "Erdtree_Avatar"},
            {"fex": "/Night+Cavalry", "wikigg": "/Night_Cavalry", "fandom": "Night_Cavalry"},
            {"fex": "/Tree+Sentinel", "wikigg": "/Tree_Sentinel", "fandom": "Tree_Sentinel"},
            {"fex": "/Flying+Dragon+Agheel", "wikigg": "/Flying_Dragon_Agheel", "fandom": "Flying_Dragon_Agheel"},
            {"fex": "/Bloodhound+Knight+Darriwil", "wikigg": "/Bloodhound_Knight_Darriwil", "fandom": "Bloodhound_Knight_Darriwil"},
            {"fex": "/Leonine+Misbegotten", "wikigg": "/Leonine_Misbegotten", "fandom": "Leonine_Misbegotten"},
            {"fex": "/Grafted+Scion", "wikigg": "/Grafted_Scion", "fandom": "Grafted_Scion"},
            {"fex": "/Fell+Twins", "wikigg": "/Fell_Twins", "fandom": "Fell_Twins"},
            {"fex": "/Mohg+the+Omen", "wikigg": "/Mohg,_the_Omen", "fandom": "Mohg,_the_Omen"},
            {"fex": "/Esgar+Priest+of+Blood", "wikigg": "/Esgar,_Priest_of_Blood", "fandom": "Esgar,_Priest_of_Blood"},
            {"fex": "/Astel+Stars+of+Darkness", "wikigg": "/Astel,_Stars_of_Darkness", "fandom": "Astel,_Stars_of_Darkness"},
            {"fex": "/Borealis+the+Freezing+Fog", "wikigg": "/Borealis_the_Freezing_Fog", "fandom": "Borealis_the_Freezing_Fog"},
            {"fex": "/Ekzykes+Decaying+Dragon", "wikigg": "/Decaying_Ekzykes", "fandom": "Decaying_Ekzykes"},
            {"fex": "/Glintstone+Dragon+Smarag", "wikigg": "/Glintstone_Dragon_Smarag", "fandom": "Glintstone_Dragon_Smarag"},
            {"fex": "/Glintstone+Dragon+Adula", "wikigg": "/Glintstone_Dragon_Adula", "fandom": "Glintstone_Dragon_Adula"},
            {"fex": "/Dragonkin+Soldier", "wikigg": "/Dragonkin_Soldier", "fandom": "Dragonkin_Soldier"},
            {"fex": "/Draconic+Tree+Sentinel", "wikigg": "/Draconic_Tree_Sentinel", "fandom": "Draconic_Tree_Sentinel"},
            {"fex": "/Fia's+Champions", "wikigg": "/Fia%27s_Champions", "fandom": "Fia%27s_Champions"},
            {"fex": "/Misbegotten+Warrior", "wikigg": "/Misbegotten_Warrior", "fandom": "Misbegotten_Warrior"},
            {"fex": "/Godskin+Apostle", "wikigg": "/Godskin_Apostle", "fandom": "Godskin_Apostle"},
            {"fex": "/Godskin+Noble", "wikigg": "/Godskin_Noble", "fandom": "Godskin_Noble"},
            {"fex": "/Godskin+Duo", "wikigg": "/Godskin_Duo", "fandom": "Godskin_Duo"},
            {"fex": "/Ancient+Dragon+Lansseax", "wikigg": "/Ancient_Dragon_Lansseax", "fandom": "Ancient_Dragon_Lansseax"},
            {"fex": "/Full-Grown+Fallingstar+Beast", "wikigg": "/Full-Grown_Fallingstar_Beast", "fandom": "Full-Grown_Fallingstar_Beast"},
            {"fex": "/Regal+Ancestor+Spirit", "wikigg": "/Regal_Ancestor_Spirit", "fandom": "Regal_Ancestor_Spirit"},
            {"fex": "/Magma+Wyrm+Makar", "wikigg": "/Magma_Wyrm_Makar", "fandom": "Magma_Wyrm_Makar"},
            {"fex": "/Bell+Bearing+Hunter", "wikigg": "/Bell_Bearing_Hunter", "fandom": "Bell_Bearing_Hunter"},
            {"fex": "/Sanguine+Noble", "wikigg": "/Sanguine_Noble", "fandom": "Sanguine_Noble"},
            {"fex": "/Demi-Human+Queen+Maggie", "wikigg": "/Demi-Human_Queen_Maggie", "fandom": "Demi-Human_Queen_Maggie"},
            {"fex": "/Demi-Human+Queen+Gilika", "wikigg": "/Demi-Human_Queen_Gilika", "fandom": "Demi-Human_Queen_Gilika"},
            {"fex": "/Demi-Human+Queen+Marigga", "wikigg": "/Demi-Human_Queen_Marigga", "fandom": "Demi-Human_Queen_Marigga"},
            {"fex": "/Erdtree+Burial+Watchdog", "wikigg": "/Erdtree_Burial_Watchdog", "fandom": "Erdtree_Burial_Watchdog"},
            {"fex": "/Miranda+the+Blighted+Bloom", "wikigg": "/Miranda_the_Blighted_Bloom", "fandom": "Miranda_the_Blighted_Bloom"},
            {"fex": "/Tibia+Mariner", "wikigg": "/Tibia_Mariner", "fandom": "Tibia_Mariner"},
            {"fex": "/Spirit-Caller+Snail", "wikigg": "/Spirit-Caller_Snail", "fandom": "Spirit-Caller_Snail"},
            {"fex": "/Abductor+Virgin", "wikigg": "/Abductor_Virgin", "fandom": "Abductor_Virgin"},
            {"fex": "/Alabaster+Lord", "wikigg": "/Alabaster_Lord", "fandom": "Alabaster_Lord"},
            {"fex": "/Battlemage+Hugues", "wikigg": "/Battlemage_Hugues", "fandom": "Battlemage_Hugues"},
            {"fex": "/Black+Knife+Assassin", "wikigg": "/Black_Knife_Assassin", "fandom": "Black_Knife_Assassin"},
            {"fex": "/Cemetery+Shade", "wikigg": "/Cemetery_Shade", "fandom": "Cemetery_Shade"},
            {"fex": "/Cleanrot+Knight+Finlay", "wikigg": "/Cleanrot_Knight_Finlay", "fandom": "Cleanrot_Knight_Finlay"},
            {"fex": "/Deathbird", "wikigg": "/Deathbird", "fandom": "Deathbird"},
            {"fex": "/Erdtree+Sentinel", "wikigg": "/Erdtree_Sentinel", "fandom": "Erdtree_Sentinel"},
            {"fex": "/Fallingstar+Beast", "wikigg": "/Fallingstar_Beast", "fandom": "Fallingstar_Beast"},
            {"fex": "/Flying+Dragon+Greyll", "wikigg": "/Flying_Dragon_Greyll", "fandom": "Flying_Dragon_Greyll"},
            {"fex": "/Frenzied+Duelist", "wikigg": "/Frenzied_Duelist", "fandom": "Frenzied_Duelist"},
            {"fex": "/Grafted+Dragon", "wikigg": "/Grafted_Dragon", "fandom": "Grafted_Dragon"},
            {"fex": "/Guardian+Golem", "wikigg": "/Guardian_Golem", "fandom": "Guardian_Golem"},
            {"fex": "/High+Page+Putrescence", "wikigg": "/High_Page_Putrescence", "fandom": "High_Page_Putrescence"},
            {"fex": "/Kindred+of+Rot", "wikigg": "/Kindred_of_Rot", "fandom": "Kindred_of_Rot"},
            {"fex": "/Leonine+Misbegotten+Warrior", "wikigg": "/Misbegotten_Warrior", "fandom": "Misbegotten_Warrior"},
            {"fex": "/Mad+Pumpkin+Head", "wikigg": "/Mad_Pumpkin_Head", "fandom": "Mad_Pumpkin_Head"},
            {"fex": "/Magma+Wyrm", "wikigg": "/Magma_Wyrm", "fandom": "Magma_Wyrm"},
            {"fex": "/Omen+Killer", "wikigg": "/Omenkiller", "fandom": "Omenkiller"},
            {"fex": "/Onyx+Lord", "wikigg": "/Onyx_Lord", "fandom": "Onyx_Lord"},
            {"fex": "/Perfumer+Tricia", "wikigg": "/Perfumer_Tricia", "fandom": "Perfumer_Tricia"},
            {"fex": "/Putrid+Tree+Spirit", "wikigg": "/Putrid_Tree_Spirit", "fandom": "Putrid_Tree_Spirit"},
            {"fex": "/Royal+Revenant", "wikigg": "/Royal_Revenant", "fandom": "Royal_Revenant"},
            {"fex": "/Stonedigger+Troll", "wikigg": "/Stonedigger_Troll", "fandom": "Stonedigger_Troll"},
            {"fex": "/Wormface", "wikigg": "/Wormface", "fandom": "Wormface"},
            # DLC bosses
            {"fex": "/Messmer+the+Impaler", "wikigg": "/Messmer_the_Impaler", "fandom": "Messmer_the_Impaler"},
            {"fex": "/Romina+Saint+of+the+Bud", "wikigg": "/Romina,_Saint_of_the_Bud", "fandom": "Romina,_Saint_of_the_Bud"},
            {"fex": "/Promised+Consort+Radahn", "wikigg": "/Promised_Consort_Radahn", "fandom": "Promised_Consort_Radahn"},
            {"fex": "/Bayle+the+Dread", "wikigg": "/Bayle_the_Dread", "fandom": "Bayle_the_Dread"},
            {"fex": "/Metyr+Mother+of+Fingers", "wikigg": "/Metyr,_Mother_of_Fingers", "fandom": "Metyr,_Mother_of_Fingers"},
            {"fex": "/Scadutree+Avatar", "wikigg": "/Scadutree_Avatar", "fandom": "Scadutree_Avatar"},
            {"fex": "/Divine+Beast+Dancing+Lion", "wikigg": "/Divine_Beast_Dancing_Lion", "fandom": "Divine_Beast_Dancing_Lion"},
            {"fex": "/Rellana+Twin+Moon+Knight", "wikigg": "/Rellana,_Twin_Moon_Knight", "fandom": "Rellana,_Twin_Moon_Knight"},
            {"fex": "/Midra+Lord+of+Frenzied+Flame", "wikigg": "/Midra,_Lord_of_Frenzied_Flame", "fandom": "Midra,_Lord_of_Frenzied_Flame"},
            {"fex": "/Commander+Gaius", "wikigg": "/Commander_Gaius", "fandom": "Commander_Gaius"},
            {"fex": "/Putrescent+Knight", "wikigg": "/Putrescent_Knight", "fandom": "Putrescent_Knight"},
            {"fex": "/Blackgaol+Knight", "wikigg": "/Blackgaol_Knight", "fandom": "Blackgaol_Knight"},
            {"fex": "/Golden+Hippopotamus", "wikigg": "/Golden_Hippopotamus", "fandom": "Golden_Hippopotamus"},
            {"fex": "/Furnace+Golem", "wikigg": "/Furnace_Golem", "fandom": "Furnace_Golem"},
            {"fex": "/Jori+Elder+Inquisitor", "wikigg": "/Jori,_Elder_Inquisitor", "fandom": "Jori,_Elder_Inquisitor"},
            {"fex": "/Rakshasa", "wikigg": "/Rakshasa", "fandom": "Rakshasa"},
            {"fex": "/Ancient+Dragon+Senessax", "wikigg": "/Ancient_Dragon_Senessax", "fandom": "Ancient_Dragon_Senessax"},
            {"fex": "/Ghostflame+Dragon", "wikigg": "/Ghostflame_Dragon", "fandom": "Ghostflame_Dragon"},
            {"fex": "/Count+Ymir+Mother+of+Fingers", "wikigg": "/Count_Ymir", "fandom": "Count_Ymir"},
            {"fex": "/Rugalea+the+Great+Swine", "wikigg": "/Rugalea_the_Great_Swine", "fandom": "Rugalea_the_Great_Swine"},
            {"fex": "/Demi-Human+Swordmaster+Onze", "wikigg": "/Demi-Human_Swordmaster_Onze", "fandom": "Demi-Human_Swordmaster_Onze"},
            {"fex": "/Tree+Sentinel+DLC", "wikigg": "/Tree_Sentinel", "fandom": "Tree_Sentinel"},
        ]
    },

    # ----------------------------------------------------------
    # CHARACTERS / NPCs — base game + DLC
    # ----------------------------------------------------------
    "characters": {
        "category": "character",
        "entries": [
            {"fex": "/Melina", "wikigg": "/Melina", "fandom": "Melina"},
            {"fex": "/Ranni+the+Witch", "wikigg": "/Ranni_the_Witch", "fandom": "Ranni_the_Witch"},
            {"fex": "/Blaidd", "wikigg": "/Blaidd", "fandom": "Blaidd"},
            {"fex": "/Iji", "wikigg": "/Iji", "fandom": "Iji"},
            {"fex": "/Rogier", "wikigg": "/Rogier", "fandom": "Rogier"},
            {"fex": "/Patches", "wikigg": "/Patches", "fandom": "Patches"},
            {"fex": "/Iron+Fist+Alexander", "wikigg": "/Alexander", "fandom": "Iron_Fist_Alexander"},
            {"fex": "/Millicent", "wikigg": "/Millicent", "fandom": "Millicent"},
            {"fex": "/Nepheli+Loux", "wikigg": "/Nepheli_Loux", "fandom": "Nepheli_Loux"},
            {"fex": "/D+Hunter+of+the+Dead", "wikigg": "/D,_Hunter_of_the_Dead", "fandom": "D,_Hunter_of_the_Dead"},
            {"fex": "/Fia", "wikigg": "/Fia", "fandom": "Fia"},
            {"fex": "/Roderika", "wikigg": "/Roderika", "fandom": "Roderika"},
            {"fex": "/Dung+Eater", "wikigg": "/Dung_Eater", "fandom": "Dung_Eater"},
            {"fex": "/Gideon+Ofnir", "wikigg": "/Gideon_Ofnir", "fandom": "Gideon_Ofnir"},
            {"fex": "/Gurranq+Beast+Clergyman", "wikigg": "/Gurranq,_Beast_Clergyman", "fandom": "Gurranq,_Beast_Clergyman"},
            {"fex": "/Hyetta", "wikigg": "/Hyetta", "fandom": "Hyetta"},
            {"fex": "/Tanith", "wikigg": "/Tanith", "fandom": "Tanith"},
            {"fex": "/Sellen", "wikigg": "/Sellen", "fandom": "Sellen"},
            {"fex": "/White+Mask+Varre", "wikigg": "/White_Mask_Varre", "fandom": "White_Mask_Varre"},
            {"fex": "/Preceptor+Seluvis", "wikigg": "/Seluvis", "fandom": "Seluvis"},
            {"fex": "/Rya", "wikigg": "/Rya", "fandom": "Rya"},
            {"fex": "/Brother+Corhyn", "wikigg": "/Brother_Corhyn", "fandom": "Brother_Corhyn"},
            {"fex": "/Goldmask", "wikigg": "/Goldmask", "fandom": "Goldmask"},
            {"fex": "/Diallos", "wikigg": "/Diallos", "fandom": "Diallos"},
            {"fex": "/Gowry", "wikigg": "/Gowry", "fandom": "Gowry"},
            {"fex": "/Boc+the+Seamster", "wikigg": "/Boc_the_Seamster", "fandom": "Boc_the_Seamster"},
            {"fex": "/Latenna+the+Albinauric", "wikigg": "/Latenna", "fandom": "Latenna"},
            {"fex": "/Miriel+Pastor+of+Vows", "wikigg": "/Miriel,_Pastor_of_Vows", "fandom": "Miriel,_Pastor_of_Vows"},
            {"fex": "/Kenneth+Haight", "wikigg": "/Kenneth_Haight", "fandom": "Kenneth_Haight"},
            {"fex": "/Edgar", "wikigg": "/Edgar", "fandom": "Edgar"},
            {"fex": "/Irina", "wikigg": "/Irina", "fandom": "Irina"},
            {"fex": "/Jar-Bairn", "wikigg": "/Jar-Bairn", "fandom": "Jar-Bairn"},
            {"fex": "/Blackguard+Big+Boggart", "wikigg": "/Blackguard_Big_Boggart", "fandom": "Blackguard_Big_Boggart"},
            {"fex": "/Shabriri", "wikigg": "/Shabriri", "fandom": "Shabriri"},
            {"fex": "/Hewg", "wikigg": "/Hewg", "fandom": "Hewg"},
            {"fex": "/Enia", "wikigg": "/Enia", "fandom": "Enia"},
            {"fex": "/Kalé", "wikigg": "/Kal%C3%A9", "fandom": "Kal%C3%A9"},
            {"fex": "/Twin+Maiden+Husks", "wikigg": "/Twin_Maiden_Husks", "fandom": "Twin_Maiden_Husks"},
            {"fex": "/D+Brother", "wikigg": "/D%27s_Brother", "fandom": "D%27s_Brother"},
            {"fex": "/Ensha+of+the+Royal+Remains", "wikigg": "/Ensha_of_the_Royal_Remains", "fandom": "Ensha_of_the_Royal_Remains"},
            {"fex": "/Fia's+Champions", "wikigg": "/Fia%27s_Champions", "fandom": "Fia%27s_Champions"},
            {"fex": "/Sorcerer+Rogier", "wikigg": "/Rogier", "fandom": "Rogier"},
            {"fex": "/Sorceress+Sellen", "wikigg": "/Sellen", "fandom": "Sellen"},
            {"fex": "/Eleonora+Violet+Bloody+Finger", "wikigg": "/Eleonora,_Violet_Bloody_Finger", "fandom": "Eleonora,_Violet_Bloody_Finger"},
            # DLC characters
            {"fex": "/Needle+Knight+Leda", "wikigg": "/Needle_Knight_Leda", "fandom": "Needle_Knight_Leda"},
            {"fex": "/Thiollier", "wikigg": "/Thiollier", "fandom": "Thiollier"},
            {"fex": "/Moore", "wikigg": "/Moore", "fandom": "Moore"},
            {"fex": "/Sir+Ansbach", "wikigg": "/Sir_Ansbach", "fandom": "Sir_Ansbach"},
            {"fex": "/Redmane+Freyja", "wikigg": "/Redmane_Freyja", "fandom": "Redmane_Freyja"},
            {"fex": "/Hornsent", "wikigg": "/Hornsent", "fandom": "Hornsent"},
            {"fex": "/Igon", "wikigg": "/Igon", "fandom": "Igon"},
            {"fex": "/Count+Ymir", "wikigg": "/Count_Ymir", "fandom": "Count_Ymir"},
            {"fex": "/Miquella", "wikigg": "/Miquella", "fandom": "Miquella"},
            {"fex": "/St+Trina", "wikigg": "/St._Trina", "fandom": "St._Trina"},
        ]
    },

    # ----------------------------------------------------------
    # AREAS — base game + DLC
    # ----------------------------------------------------------
    "areas": {
        "category": "area",
        "entries": [
            {"fex": "/Limgrave", "wikigg": "/Limgrave", "fandom": "Limgrave"},
            {"fex": "/Stormveil+Castle", "wikigg": "/Stormveil_Castle", "fandom": "Stormveil_Castle"},
            {"fex": "/Weeping+Peninsula", "wikigg": "/Weeping_Peninsula", "fandom": "Weeping_Peninsula"},
            {"fex": "/Liurnia+of+the+Lakes", "wikigg": "/Liurnia_of_the_Lakes", "fandom": "Liurnia_of_the_Lakes"},
            {"fex": "/Raya+Lucaria+Academy", "wikigg": "/Raya_Lucaria_Academy", "fandom": "Raya_Lucaria_Academy"},
            {"fex": "/Caria+Manor", "wikigg": "/Caria_Manor", "fandom": "Caria_Manor"},
            {"fex": "/Caelid", "wikigg": "/Caelid", "fandom": "Caelid"},
            {"fex": "/Dragonbarrow", "wikigg": "/Dragonbarrow", "fandom": "Dragonbarrow"},
            {"fex": "/Altus+Plateau", "wikigg": "/Altus_Plateau", "fandom": "Altus_Plateau"},
            {"fex": "/Mt+Gelmir", "wikigg": "/Mt._Gelmir", "fandom": "Mt._Gelmir"},
            {"fex": "/Volcano+Manor", "wikigg": "/Volcano_Manor", "fandom": "Volcano_Manor"},
            {"fex": "/Leyndell+Royal+Capital", "wikigg": "/Leyndell,_Royal_Capital", "fandom": "Leyndell,_Royal_Capital"},
            {"fex": "/Subterranean+Shunning-Grounds", "wikigg": "/Subterranean_Shunning-Grounds", "fandom": "Subterranean_Shunning-Grounds"},
            {"fex": "/Siofra+River", "wikigg": "/Siofra_River", "fandom": "Siofra_River"},
            {"fex": "/Nokron+Eternal+City", "wikigg": "/Nokron,_Eternal_City", "fandom": "Nokron,_Eternal_City"},
            {"fex": "/Nokstella+Eternal+City", "wikigg": "/Nokstella,_Eternal_City", "fandom": "Nokstella,_Eternal_City"},
            {"fex": "/Ainsel+River", "wikigg": "/Ainsel_River", "fandom": "Ainsel_River"},
            {"fex": "/Lake+of+Rot", "wikigg": "/Lake_of_Rot", "fandom": "Lake_of_Rot"},
            {"fex": "/Deeproot+Depths", "wikigg": "/Deeproot_Depths", "fandom": "Deeproot_Depths"},
            {"fex": "/Mountaintops+of+the+Giants", "wikigg": "/Mountaintops_of_the_Giants", "fandom": "Mountaintops_of_the_Giants"},
            {"fex": "/Forbidden+Lands", "wikigg": "/Forbidden_Lands", "fandom": "Forbidden_Lands"},
            {"fex": "/Consecrated+Snowfield", "wikigg": "/Consecrated_Snowfield", "fandom": "Consecrated_Snowfield"},
            {"fex": "/Mohgwyn+Palace", "wikigg": "/Mohgwyn_Palace", "fandom": "Mohgwyn_Palace"},
            {"fex": "/Miquella's+Haligtree", "wikigg": "/Miquella%27s_Haligtree", "fandom": "Miquella%27s_Haligtree"},
            {"fex": "/Elphael+Brace+of+the+Haligtree", "wikigg": "/Elphael,_Brace_of_the_Haligtree", "fandom": "Elphael,_Brace_of_the_Haligtree"},
            {"fex": "/Crumbling+Farum+Azula", "wikigg": "/Crumbling_Farum_Azula", "fandom": "Crumbling_Farum_Azula"},
            {"fex": "/Leyndell+Ashen+Capital", "wikigg": "/Leyndell,_Ashen_Capital", "fandom": "Leyndell,_Ashen_Capital"},
            {"fex": "/Roundtable+Hold", "wikigg": "/Roundtable_Hold", "fandom": "Roundtable_Hold"},
            {"fex": "/Redmane+Castle", "wikigg": "/Redmane_Castle", "fandom": "Redmane_Castle"},
            {"fex": "/Ruin-Strewn+Precipice", "wikigg": "/Ruin-Strewn_Precipice", "fandom": "Ruin-Strewn_Precipice"},
            {"fex": "/Sellia+Town+of+Sorcery", "wikigg": "/Sellia,_Town_of_Sorcery", "fandom": "Sellia,_Town_of_Sorcery"},
            {"fex": "/Stormhill", "wikigg": "/Stormhill", "fandom": "Stormhill"},
            # DLC areas
            {"fex": "/Land+of+Shadow", "wikigg": "/Land_of_Shadow", "fandom": "Land_of_Shadow"},
            {"fex": "/Gravesite+Plain", "wikigg": "/Gravesite_Plain", "fandom": "Gravesite_Plain"},
            {"fex": "/Scadu+Altus", "wikigg": "/Scadu_Altus", "fandom": "Scadu_Altus"},
            {"fex": "/Shadow+Keep", "wikigg": "/Shadow_Keep", "fandom": "Shadow_Keep"},
            {"fex": "/Rauh+Base", "wikigg": "/Rauh_Base", "fandom": "Rauh_Base"},
            {"fex": "/Cerulean+Coast", "wikigg": "/Cerulean_Coast", "fandom": "Cerulean_Coast"},
            {"fex": "/Jagged+Peak", "wikigg": "/Jagged_Peak", "fandom": "Jagged_Peak"},
            {"fex": "/Abyssal+Woods", "wikigg": "/Abyssal_Woods", "fandom": "Abyssal_Woods"},
            {"fex": "/Enir-Ilim", "wikigg": "/Enir-Ilim", "fandom": "Enir-Ilim"},
            {"fex": "/Midra's+Manse", "wikigg": "/Midra%27s_Manse", "fandom": "Midra%27s_Manse"},
            {"fex": "/Specimen+Storehouse", "wikigg": "/Specimen_Storehouse", "fandom": "Specimen_Storehouse"},
            {"fex": "/Finger+Ruins", "wikigg": "/Finger_Ruins", "fandom": "Finger_Ruins"},
            {"fex": "/Rauh+Ancient+Ruins", "wikigg": "/Rauh_Ancient_Ruins", "fandom": "Rauh_Ancient_Ruins"},
            {"fex": "/Stone+Coffin+Fissure", "wikigg": "/Stone_Coffin_Fissure", "fandom": "Stone_Coffin_Fissure"},
        ]
    },

    # ----------------------------------------------------------
    # LORE — core topics + indirect figures + hidden lore
    # ----------------------------------------------------------
    "lore": {
        "category": "lore",
        "entries": [
            # Core lore topics
            {"fex": "/Elden+Ring+Lore", "wikigg": "/Lore", "fandom": "Lore"},
            {"fex": "/Golden+Order", "wikigg": "/Golden_Order", "fandom": "Golden_Order"},
            {"fex": "/Erdtree", "wikigg": "/Erdtree", "fandom": "Erdtree"},
            {"fex": "/Scarlet+Rot", "wikigg": "/Scarlet_Rot", "fandom": "Scarlet_Rot"},
            {"fex": "/Frenzied+Flame", "wikigg": "/Frenzied_Flame", "fandom": "Frenzied_Flame"},
            {"fex": "/Rune+of+Death", "wikigg": "/Rune_of_Death", "fandom": "Rune_of_Death"},
            {"fex": "/Tarnished", "wikigg": "/Tarnished", "fandom": "Tarnished"},
            {"fex": "/Shattering", "wikigg": "/Shattering", "fandom": "Shattering"},
            {"fex": "/Greater+Will", "wikigg": "/Greater_Will", "fandom": "Greater_Will"},
            {"fex": "/Black+Knife+Assassins", "wikigg": "/Black_Knife_Assassins", "fandom": "Black_Knife_Assassins"},
            {"fex": "/Night+of+the+Black+Knives", "wikigg": "/Night_of_the_Black_Knives", "fandom": "Night_of_the_Black_Knives"},
            {"fex": "/Two+Fingers", "wikigg": "/Two_Fingers", "fandom": "Two_Fingers"},
            {"fex": "/Three+Fingers", "wikigg": "/Three_Fingers", "fandom": "Three_Fingers"},
            {"fex": "/Outer+Gods", "wikigg": "/Outer_Gods", "fandom": "Outer_Gods"},
            {"fex": "/Demigods", "wikigg": "/Demigod", "fandom": "Demigod"},
            {"fex": "/Empyrean", "wikigg": "/Empyrean", "fandom": "Empyrean"},
            {"fex": "/Queen+Marika+the+Eternal", "wikigg": "/Queen_Marika_the_Eternal", "fandom": "Queen_Marika_the_Eternal"},
            {"fex": "/Radagon+of+the+Golden+Order", "wikigg": "/Radagon_of_the_Golden_Order", "fandom": "Radagon_of_the_Golden_Order"},
            {"fex": "/Miquella", "wikigg": "/Miquella", "fandom": "Miquella"},
            {"fex": "/Malenia", "wikigg": "/Malenia", "fandom": "Malenia,_Blade_of_Miquella"},
            {"fex": "/Shadow+of+the+Erdtree", "wikigg": "/Shadow_of_the_Erdtree", "fandom": "Shadow_of_the_Erdtree"},
            {"fex": "/The+Lands+Between", "wikigg": "/The_Lands_Between", "fandom": "The_Lands_Between"},
            {"fex": "/Crucible", "wikigg": "/Crucible", "fandom": "Crucible"},
            {"fex": "/Age+of+the+Stars", "wikigg": "/Age_of_Stars", "fandom": "Age_of_Stars"},
            {"fex": "/Ranni+the+Witch", "wikigg": "/Ranni_the_Witch", "fandom": "Ranni_the_Witch"},
            {"fex": "/Godfrey+First+Elden+Lord", "wikigg": "/Godfrey,_First_Elden_Lord", "fandom": "Godfrey,_First_Elden_Lord"},
            {"fex": "/Godwyn+the+Golden", "wikigg": "/Godwyn_the_Golden", "fandom": "Godwyn_the_Golden"},
            {"fex": "/Elden+Ring", "wikigg": "/Elden_Ring", "fandom": "Elden_Ring"},
            {"fex": "/Death", "wikigg": "/Death", "fandom": "Death"},
            {"fex": "/Grace", "wikigg": "/Grace", "fandom": "Grace"},
            # Indirect / hidden lore figures
            {"fex": "/Gloam-Eyed+Queen", "wikigg": "/Gloam-Eyed_Queen", "fandom": "Gloam-Eyed_Queen"},
            {"fex": "/Fell+God", "wikigg": "/Fell_God", "fandom": "Fell_God"},
            {"fex": "/Deathroot", "wikigg": "/Deathroot", "fandom": "Deathroot"},
            {"fex": "/Twinbird", "wikigg": "/Twinbird", "fandom": "Twinbird"},
            {"fex": "/Serosh", "wikigg": "/Serosh", "fandom": "Serosh"},
            {"fex": "/Numen", "wikigg": "/Numen", "fandom": "Numen"},
            {"fex": "/Nox", "wikigg": "/Nox", "fandom": "Nox"},
            {"fex": "/Albinauric", "wikigg": "/Albinauric", "fandom": "Albinauric"},
            {"fex": "/Omen", "wikigg": "/Omen", "fandom": "Omen"},
            {"fex": "/Dragon+Communion", "wikigg": "/Dragon_Communion", "fandom": "Dragon_Communion"},
            {"fex": "/Ancient+Dragons", "wikigg": "/Ancient_Dragons", "fandom": "Ancient_Dragons"},
            {"fex": "/Fire+Giants", "wikigg": "/Fire_Giants", "fandom": "Fire_Giants"},
            {"fex": "/Giants", "wikigg": "/Giants", "fandom": "Giants"},
            {"fex": "/Godskins", "wikigg": "/Godskin_Apostle", "fandom": "Godskin_Apostle"},
            {"fex": "/Frenzied+Flame+Proscription", "wikigg": "/Frenzied_Flame_Proscription", "fandom": "Frenzied_Flame_Proscription"},
            {"fex": "/Miquella's+Needle", "wikigg": "/Miquella%27s_Needle", "fandom": "Miquella%27s_Needle"},
            {"fex": "/St+Trina", "wikigg": "/St._Trina", "fandom": "St._Trina"},
            {"fex": "/Destined+Death", "wikigg": "/Destined_Death", "fandom": "Destined_Death"},
            {"fex": "/Rot+Goddess", "wikigg": "/Rot_Goddess", "fandom": "Rot_Goddess"},
            {"fex": "/Blood+Lord", "wikigg": "/Blood_Lord", "fandom": "Blood_Lord"},
            {"fex": "/Formless+Mother", "wikigg": "/Formless_Mother", "fandom": "Formless_Mother"},
            {"fex": "/Fell+Omen", "wikigg": "/Fell_Omen", "fandom": "Fell_Omen"},
            {"fex": "/Hornsent+civilization", "wikigg": "/Hornsent", "fandom": "Hornsent"},
            {"fex": "/Messmer+lore", "wikigg": "/Messmer_the_Impaler", "fandom": "Messmer_the_Impaler"},
            # NEW: Missing lore topics
            {"fex": "/Torrent", "wikigg": "/Torrent", "fandom": "Torrent"},
            {"fex": "/Divine+Tower", "wikigg": "/Divine_Towers", "fandom": "Divine_Tower"},
            {"fex": "/Divine+Tower+of+Limgrave", "wikigg": "/Divine_Tower_of_Limgrave", "fandom": "Divine_Tower_of_Limgrave"},
            {"fex": "/Divine+Tower+of+Liurnia", "wikigg": "/Divine_Tower_of_Liurnia", "fandom": "Divine_Tower_of_Liurnia"},
            {"fex": "/Divine+Tower+of+Caelid", "wikigg": "/Divine_Tower_of_Caelid", "fandom": "Divine_Tower_of_Caelid"},
            {"fex": "/Divine+Tower+of+West+Altus", "wikigg": "/Divine_Tower_of_West_Altus", "fandom": "Divine_Tower_of_West_Altus"},
            {"fex": "/Divine+Tower+of+East+Altus", "wikigg": "/Divine_Tower_of_East_Altus", "fandom": "Divine_Tower_of_East_Altus"},
            {"fex": "/Isolated+Divine+Tower", "wikigg": "/Isolated_Divine_Tower", "fandom": "Isolated_Divine_Tower"},
            {"fex": "/Godwyn+the+Golden", "wikigg": "/Godwyn_the_Golden", "fandom": "Godwyn_the_Golden"},
            {"fex": "/War+Against+the+Giants", "wikigg": "/War_Against_the_Giants", "fandom": "War_Against_the_Giants"},
            {"fex": "/Carian+Royal+Family", "wikigg": "/Carian_Royal_Family", "fandom": "Carian_Royal_Family"},
            {"fex": "/Nox+civilization", "wikigg": "/Nox", "fandom": "Nox"},
            {"fex": "/Dragon+Communion+lore", "wikigg": "/Dragon_Communion", "fandom": "Dragon_Communion"},
            {"fex": "/Crucible+Era", "wikigg": "/Crucible", "fandom": "Crucible"},
            {"fex": "/Glintstone+sorcery", "wikigg": "/Glintstone", "fandom": "Glintstone"},
            {"fex": "/Gravity+Magic", "wikigg": "/Gravity_Magic", "fandom": "Gravity_Magic"},
            {"fex": "/Primeval+Glintstone", "wikigg": "/Primeval_Glintstone", "fandom": "Primeval_Glintstone"},
            {"fex": "/Grafting", "wikigg": "/Grafting", "fandom": "Grafting"},
            {"fex": "/Omen+curse", "wikigg": "/Omen", "fandom": "Omen"},
            {"fex": "/Living+Jar", "wikigg": "/Living_Jar", "fandom": "Living_Jar"},
            {"fex": "/Miquella's+plan", "wikigg": "/Miquella", "fandom": "Miquella"},
            {"fex": "/Hornsent+people", "wikigg": "/Hornsent", "fandom": "Hornsent"},
            {"fex": "/Walking+Mausoleum", "wikigg": "/Walking_Mausoleum", "fandom": "Walking_Mausoleum"},
            {"fex": "/Primordial+Crucible", "wikigg": "/Crucible", "fandom": "Crucible"},
            {"fex": "/Erdtree+lore", "wikigg": "/Erdtree", "fandom": "Erdtree"},
            {"fex": "/Golden+Order+fundamentalism", "wikigg": "/Golden_Order", "fandom": "Golden_Order"},
            {"fex": "/Rune+of+Death+lore", "wikigg": "/Rune_of_Death", "fandom": "Rune_of_Death"},
            {"fex": "/Age+of+Fracture", "wikigg": "/Age_of_Fracture", "fandom": "Age_of_Fracture"},
            {"fex": "/Erdtree+Burial", "wikigg": "/Erdtree_Burial", "fandom": "Erdtree_Burial"},
            {"fex": "/Graven+School", "wikigg": "/Graven_School", "fandom": "Graven_School"},
            {"fex": "/Fingerprint+lore", "wikigg": "/Fingerprint_Stone_Shield", "fandom": "Fingerprint_Stone_Shield"},
            {"fex": "/Age+of+Absolutes", "wikigg": "/Age_of_Absolutes", "fandom": "Age_of_Absolutes"},
            {"fex": "/Caria+Manor+lore", "wikigg": "/Caria_Manor", "fandom": "Caria_Manor"},
            {"fex": "/Farum+Azula+lore", "wikigg": "/Crumbling_Farum_Azula", "fandom": "Crumbling_Farum_Azula"},
            {"fex": "/Volcano+Manor+lore", "wikigg": "/Volcano_Manor", "fandom": "Volcano_Manor"},
            {"fex": "/Liurnia+lore", "wikigg": "/Liurnia_of_the_Lakes", "fandom": "Liurnia_of_the_Lakes"},
            # Remembrances — rich lore descriptions written by FromSoftware
            {"fex": "/Remembrance+of+the+Grafted", "wikigg": "/Remembrance_of_the_Grafted", "fandom": "Remembrance_of_the_Grafted"},
            {"fex": "/Remembrance+of+the+Full+Moon+Queen", "wikigg": "/Remembrance_of_the_Full_Moon_Queen", "fandom": "Remembrance_of_the_Full_Moon_Queen"},
            {"fex": "/Remembrance+of+the+Starscourge", "wikigg": "/Remembrance_of_the_Starscourge", "fandom": "Remembrance_of_the_Starscourge"},
            {"fex": "/Remembrance+of+the+Omen+King", "wikigg": "/Remembrance_of_the_Omen_King", "fandom": "Remembrance_of_the_Omen_King"},
            {"fex": "/Remembrance+of+the+Fire+Giant", "wikigg": "/Remembrance_of_the_Fire_Giant", "fandom": "Remembrance_of_the_Fire_Giant"},
            {"fex": "/Remembrance+of+the+Black+Blade", "wikigg": "/Remembrance_of_the_Black_Blade", "fandom": "Remembrance_of_the_Black_Blade"},
            {"fex": "/Remembrance+of+Hoarah+Loux", "wikigg": "/Remembrance_of_Hoarah_Loux", "fandom": "Remembrance_of_Hoarah_Loux"},
            {"fex": "/Elden+Remembrance", "wikigg": "/Elden_Remembrance", "fandom": "Elden_Remembrance"},
            {"fex": "/Remembrance+of+the+Rot+Goddess", "wikigg": "/Remembrance_of_the_Rot_Goddess", "fandom": "Remembrance_of_the_Rot_Goddess"},
            {"fex": "/Remembrance+of+the+Blood+Lord", "wikigg": "/Remembrance_of_the_Blood_Lord", "fandom": "Remembrance_of_the_Blood_Lord"},
            {"fex": "/Remembrance+of+the+Blasphemous", "wikigg": "/Remembrance_of_the_Blasphemous", "fandom": "Remembrance_of_the_Blasphemous"},
            {"fex": "/Remembrance+of+the+Naturalborn", "wikigg": "/Remembrance_of_the_Naturalborn", "fandom": "Remembrance_of_the_Naturalborn"},
            {"fex": "/Remembrance+of+the+Dragonlord", "wikigg": "/Remembrance_of_the_Dragonlord", "fandom": "Remembrance_of_the_Dragonlord"},
            {"fex": "/Remembrance+of+the+Lichdragon", "wikigg": "/Remembrance_of_the_Lichdragon", "fandom": "Remembrance_of_the_Lichdragon"},
            # DLC remembrances
            {"fex": "/Remembrance+of+the+Impaler", "wikigg": "/Remembrance_of_the_Impaler", "fandom": "Remembrance_of_the_Impaler"},
            {"fex": "/Remembrance+of+the+Saint+of+the+Bud", "wikigg": "/Remembrance_of_the_Saint_of_the_Bud", "fandom": "Remembrance_of_the_Saint_of_the_Bud"},
            {"fex": "/Remembrance+of+a+God+and+a+Lord", "wikigg": "/Remembrance_of_a_God_and_a_Lord", "fandom": "Remembrance_of_a_God_and_a_Lord"},
            {"fex": "/Remembrance+of+the+Dread", "wikigg": "/Remembrance_of_the_Dread", "fandom": "Remembrance_of_the_Dread"},
            {"fex": "/Remembrance+of+the+Mother+of+Fingers", "wikigg": "/Remembrance_of_the_Mother_of_Fingers", "fandom": "Remembrance_of_the_Mother_of_Fingers"},
            {"fex": "/Remembrance+of+the+Twin+Moon+Knight", "wikigg": "/Remembrance_of_the_Twin_Moon_Knight", "fandom": "Remembrance_of_the_Twin_Moon_Knight"},
            {"fex": "/Remembrance+of+the+Lord+of+Frenzied+Flame", "wikigg": "/Remembrance_of_the_Lord_of_Frenzied_Flame", "fandom": "Remembrance_of_the_Lord_of_Frenzied_Flame"},
        ]
    },

    # ----------------------------------------------------------
    # WEAPONS — all ~300 weapons with lore descriptions
    # ----------------------------------------------------------
    "weapons": {
        "category": "weapon",
        "entries": [
            # Original set
            {"fex": "/Reduvia", "wikigg": "/Reduvia", "fandom": "Reduvia"},
            {"fex": "/Rivers+of+Blood", "wikigg": "/Rivers_of_Blood", "fandom": "Rivers_of_Blood"},
            {"fex": "/Moonveil", "wikigg": "/Moonveil", "fandom": "Moonveil"},
            {"fex": "/Blasphemous+Blade", "wikigg": "/Blasphemous_Blade", "fandom": "Blasphemous_Blade"},
            {"fex": "/Grafted+Blade+Greatsword", "wikigg": "/Grafted_Blade_Greatsword", "fandom": "Grafted_Blade_Greatsword"},
            {"fex": "/Starscourge+Greatsword", "wikigg": "/Starscourge_Greatsword", "fandom": "Starscourge_Greatsword"},
            {"fex": "/Sacred+Relic+Sword", "wikigg": "/Sacred_Relic_Sword", "fandom": "Sacred_Relic_Sword"},
            {"fex": "/Maliketh's+Black+Blade", "wikigg": "/Maliketh%27s_Black_Blade", "fandom": "Maliketh%27s_Black_Blade"},
            {"fex": "/Morgott's+Cursed+Sword", "wikigg": "/Morgott%27s_Cursed_Sword", "fandom": "Morgott%27s_Cursed_Sword"},
            {"fex": "/Mohgwyn's+Sacred+Spear", "wikigg": "/Mohgwyn%27s_Sacred_Spear", "fandom": "Mohgwyn%27s_Sacred_Spear"},
            {"fex": "/Hand+of+Malenia", "wikigg": "/Hand_of_Malenia", "fandom": "Hand_of_Malenia"},
            {"fex": "/Bolt+of+Gransax", "wikigg": "/Bolt_of_Gransax", "fandom": "Bolt_of_Gransax"},
            {"fex": "/Darkmoon+Greatsword", "wikigg": "/Darkmoon_Greatsword", "fandom": "Darkmoon_Greatsword"},
            {"fex": "/Death's+Poker", "wikigg": "/Death%27s_Poker", "fandom": "Death%27s_Poker"},
            {"fex": "/Bloodhound's+Fang", "wikigg": "/Bloodhound%27s_Fang", "fandom": "Bloodhound%27s_Fang"},
            {"fex": "/Wing+of+Astel", "wikigg": "/Wing_of_Astel", "fandom": "Wing_of_Astel"},
            {"fex": "/Sword+of+Night+and+Flame", "wikigg": "/Sword_of_Night_and_Flame", "fandom": "Sword_of_Night_and_Flame"},
            {"fex": "/Godslayer's+Greatsword", "wikigg": "/Godslayer%27s_Greatsword", "fandom": "Godslayer%27s_Greatsword"},
            {"fex": "/Golden+Order+Greatsword", "wikigg": "/Golden_Order_Greatsword", "fandom": "Golden_Order_Greatsword"},
            {"fex": "/Eleonora's+Poleblade", "wikigg": "/Eleonora%27s_Poleblade", "fandom": "Eleonora%27s_Poleblade"},
            {"fex": "/Ruins+Greatsword", "wikigg": "/Ruins_Greatsword", "fandom": "Ruins_Greatsword"},
            {"fex": "/Helphen's+Steeple", "wikigg": "/Helphen%27s_Steeple", "fandom": "Helphen%27s_Steeple"},
            {"fex": "/Eclipse+Shotel", "wikigg": "/Eclipse_Shotel", "fandom": "Eclipse_Shotel"},
            {"fex": "/Sword+of+Milos", "wikigg": "/Sword_of_Milos", "fandom": "Sword_of_Milos"},
            {"fex": "/Winged+Scythe", "wikigg": "/Winged_Scythe", "fandom": "Winged_Scythe"},
            {"fex": "/Gargoyle's+Blackblade", "wikigg": "/Gargoyle%27s_Blackblade", "fandom": "Gargoyle%27s_Blackblade"},
            {"fex": "/Black+Knife", "wikigg": "/Black_Knife", "fandom": "Black_Knife"},
            {"fex": "/Erdtree+Bow", "wikigg": "/Erdtree_Bow", "fandom": "Erdtree_Bow"},
            {"fex": "/Rotten+Crystal+Sword", "wikigg": "/Rotten_Crystal_Sword", "fandom": "Rotten_Crystal_Sword"},
            {"fex": "/Fingerprint+Stone+Shield", "wikigg": "/Fingerprint_Stone_Shield", "fandom": "Fingerprint_Stone_Shield"},
            # Expanded weapons — Straight Swords
            {"fex": "/Carian+Knight's+Sword", "wikigg": "/Carian_Knight%27s_Sword", "fandom": "Carian_Knight%27s_Sword"},
            {"fex": "/Sword+of+St+Trina", "wikigg": "/Sword_of_St._Trina", "fandom": "Sword_of_St._Trina"},
            {"fex": "/Coded+Sword", "wikigg": "/Coded_Sword", "fandom": "Coded_Sword"},
            {"fex": "/Broadsword", "wikigg": "/Broadsword", "fandom": "Broadsword"},
            {"fex": "/Longsword", "wikigg": "/Longsword", "fandom": "Longsword"},
            {"fex": "/Noble's+Slender+Sword", "wikigg": "/Noble%27s_Slender_Sword", "fandom": "Noble%27s_Slender_Sword"},
            {"fex": "/Miquellan+Knight's+Sword", "wikigg": "/Miquellan_Knight%27s_Sword", "fandom": "Miquellan_Knight%27s_Sword"},
            {"fex": "/Lordsworn's+Straight+Sword", "wikigg": "/Lordsworn%27s_Straight_Sword", "fandom": "Lordsworn%27s_Straight_Sword"},
            # Greatswords
            {"fex": "/Knight's+Greatsword", "wikigg": "/Knight%27s_Greatsword", "fandom": "Knight%27s_Greatsword"},
            {"fex": "/Inseparable+Sword", "wikigg": "/Inseparable_Sword", "fandom": "Inseparable_Sword"},
            {"fex": "/Ordovis's+Greatsword", "wikigg": "/Ordovis%27s_Greatsword", "fandom": "Ordovis%27s_Greatsword"},
            {"fex": "/Sword+of+Damnation", "wikigg": "/Sword_of_Damnation", "fandom": "Sword_of_Damnation"},
            {"fex": "/Zweihander", "wikigg": "/Zweihander", "fandom": "Zweihander"},
            {"fex": "/Banished+Knight's+Greatsword", "wikigg": "/Banished_Knight%27s_Greatsword", "fandom": "Banished_Knight%27s_Greatsword"},
            # Katanas
            {"fex": "/Uchigatana", "wikigg": "/Uchigatana", "fandom": "Uchigatana"},
            {"fex": "/Nagakiba", "wikigg": "/Nagakiba", "fandom": "Nagakiba"},
            {"fex": "/Hand+of+Malenia", "wikigg": "/Hand_of_Malenia", "fandom": "Hand_of_Malenia"},
            {"fex": "/Meteoric+Ore+Blade", "wikigg": "/Meteoric_Ore_Blade", "fandom": "Meteoric_Ore_Blade"},
            {"fex": "/Serpentbone+Blade", "wikigg": "/Serpentbone_Blade", "fandom": "Serpentbone_Blade"},
            {"fex": "/Dragonscale+Blade", "wikigg": "/Dragonscale_Blade", "fandom": "Dragonscale_Blade"},
            # Curved Swords
            {"fex": "/Scimitar", "wikigg": "/Scimitar", "fandom": "Scimitar"},
            {"fex": "/Sellsword+Twinblades", "wikigg": "/Twinblade", "fandom": "Twinblade"},
            {"fex": "/Godskin+Peeler", "wikigg": "/Godskin_Peeler", "fandom": "Godskin_Peeler"},
            {"fex": "/Twinblade", "wikigg": "/Twinblade", "fandom": "Twinblade"},
            # Halberds
            {"fex": "/Halberd", "wikigg": "/Halberd", "fandom": "Halberd"},
            {"fex": "/Commander's+Standard", "wikigg": "/Commander%27s_Standard", "fandom": "Commander%27s_Standard"},
            {"fex": "/Golden+Halberd", "wikigg": "/Golden_Halberd", "fandom": "Golden_Halberd"},
            {"fex": "/Loretta's+War+Sickle", "wikigg": "/Loretta%27s_War_Sickle", "fandom": "Loretta%27s_War_Sickle"},
            {"fex": "/Vulgar+Militia+Saw", "wikigg": "/Vulgar_Militia_Saw", "fandom": "Vulgar_Militia_Saw"},
            # Spears
            {"fex": "/Treespear", "wikigg": "/Treespear", "fandom": "Treespear"},
            {"fex": "/Cleanrot+Spear", "wikigg": "/Cleanrot_Spear", "fandom": "Cleanrot_Spear"},
            {"fex": "/Death+Ritual+Spear", "wikigg": "/Death_Ritual_Spear", "fandom": "Death_Ritual_Spear"},
            {"fex": "/Lance", "wikigg": "/Lance", "fandom": "Lance"},
            {"fex": "/Rotten+Crystal+Spear", "wikigg": "/Rotten_Crystal_Spear", "fandom": "Rotten_Crystal_Spear"},
            # Great Spears
            {"fex": "/Vyke's+War+Spear", "wikigg": "/Vyke%27s_War_Spear", "fandom": "Vyke%27s_War_Spear"},
            {"fex": "/Siluria's+Tree", "wikigg": "/Siluria%27s_Tree", "fandom": "Siluria%27s_Tree"},
            # Colossal Swords
            {"fex": "/Greatsword", "wikigg": "/Greatsword", "fandom": "Greatsword"},
            {"fex": "/Troll's+Golden+Sword", "wikigg": "/Troll%27s_Golden_Sword", "fandom": "Troll%27s_Golden_Sword"},
            {"fex": "/Watchdog's+Greatsword", "wikigg": "/Watchdog%27s_Greatsword", "fandom": "Watchdog%27s_Greatsword"},
            {"fex": "/Alabaster+Lord's+Sword", "wikigg": "/Alabaster_Lord%27s_Sword", "fandom": "Alabaster_Lord%27s_Sword"},
            # Curved Greatswords
            {"fex": "/Bloodhound's+Fang", "wikigg": "/Bloodhound%27s_Fang", "fandom": "Bloodhound%27s_Fang"},
            {"fex": "/Magma+Wyrm's+Scalesword", "wikigg": "/Magma_Wyrm%27s_Scalesword", "fandom": "Magma_Wyrm%27s_Scalesword"},
            {"fex": "/Zamor+Curved+Sword", "wikigg": "/Zamor_Curved_Sword", "fandom": "Zamor_Curved_Sword"},
            # Axes
            {"fex": "/Sacrificial+Axe", "wikigg": "/Sacrificial_Axe", "fandom": "Sacrificial_Axe"},
            {"fex": "/Icerind+Hatchet", "wikigg": "/Icerind_Hatchet", "fandom": "Icerind_Hatchet"},
            {"fex": "/Rosus'+Axe", "wikigg": "/Rosus%27_Axe", "fandom": "Rosus%27_Axe"},
            # Great Axes
            {"fex": "/Executioner's+Greataxe", "wikigg": "/Executioner%27s_Greataxe", "fandom": "Executioner%27s_Greataxe"},
            {"fex": "/Golem's+Halberd", "wikigg": "/Golem%27s_Halberd", "fandom": "Golem%27s_Halberd"},
            # Hammers
            {"fex": "/Cranial+Vessel+Candlestand", "wikigg": "/Cranial_Vessel_Candlestand", "fandom": "Cranial_Vessel_Candlestand"},
            {"fex": "/Erdtree+Club", "wikigg": "/Erdtree_Club", "fandom": "Erdtree_Club"},
            {"fex": "/Nox+Flowing+Hammer", "wikigg": "/Nox_Flowing_Hammer", "fandom": "Nox_Flowing_Hammer"},
            # Greathammes
            {"fex": "/Giant+Crusher", "wikigg": "/Giant_Crusher", "fandom": "Giant_Crusher"},
            {"fex": "/Envoy's+Horn", "wikigg": "/Envoy%27s_Horn", "fandom": "Envoy%27s_Horn"},
            {"fex": "/Hammer+of+the+Vassal", "wikigg": "/Hammer_of_the_Vassal", "fandom": "Hammer_of_the_Vassal"},
            # Flails
            {"fex": "/Nightrider+Flail", "wikigg": "/Nightrider_Flail", "fandom": "Nightrider_Flail"},
            {"fex": "/Flail", "wikigg": "/Flail", "fandom": "Flail"},
            # Daggers
            {"fex": "/Misericorde", "wikigg": "/Misericorde", "fandom": "Misericorde"},
            {"fex": "/Cinquedea", "wikigg": "/Cinquedea", "fandom": "Cinquedea"},
            {"fex": "/Ivory+Sickle", "wikigg": "/Ivory_Sickle", "fandom": "Ivory_Sickle"},
            {"fex": "/Scorpion's+Stinger", "wikigg": "/Scorpion%27s_Stinger", "fandom": "Scorpion%27s_Stinger"},
            {"fex": "/Bloodstained+Dagger", "wikigg": "/Bloodstained_Dagger", "fandom": "Bloodstained_Dagger"},
            {"fex": "/Crystal+Knife", "wikigg": "/Crystal_Knife", "fandom": "Crystal_Knife"},
            # Reapers
            {"fex": "/Death's+Poker", "wikigg": "/Death%27s_Poker", "fandom": "Death%27s_Poker"},
            {"fex": "/Grave+Scythe", "wikigg": "/Grave_Scythe", "fandom": "Grave_Scythe"},
            {"fex": "/Halo+Scythe", "wikigg": "/Halo_Scythe", "fandom": "Halo_Scythe"},
            # Fists / Claws
            {"fex": "/Bloodhound+Claws", "wikigg": "/Bloodhound_Claws", "fandom": "Bloodhound_Claws"},
            {"fex": "/Venomous+Fang", "wikigg": "/Venomous_Fang", "fandom": "Venomous_Fang"},
            {"fex": "/Hookclaws", "wikigg": "/Hookclaws", "fandom": "Hookclaws"},
            # Whips
            {"fex": "/Thorned+Whip", "wikigg": "/Thorned_Whip", "fandom": "Thorned_Whip"},
            {"fex": "/Hoslow's+Petal+Whip", "wikigg": "/Hoslow%27s_Petal_Whip", "fandom": "Hoslow%27s_Petal_Whip"},
            {"fex": "/Urumi", "wikigg": "/Urumi", "fandom": "Urumi"},
            # Staves
            {"fex": "/Carian+Regal+Scepter", "wikigg": "/Carian_Regal_Scepter", "fandom": "Carian_Regal_Scepter"},
            {"fex": "/Azur's+Glintstone+Staff", "wikigg": "/Azur%27s_Glintstone_Staff", "fandom": "Azur%27s_Glintstone_Staff"},
            {"fex": "/Lusat's+Glintstone+Staff", "wikigg": "/Lusat%27s_Glintstone_Staff", "fandom": "Lusat%27s_Glintstone_Staff"},
            {"fex": "/Staff+of+the+Guilty", "wikigg": "/Staff_of_the_Guilty", "fandom": "Staff_of_the_Guilty"},
            {"fex": "/Digger's+Staff", "wikigg": "/Digger%27s_Staff", "fandom": "Digger%27s_Staff"},
            {"fex": "/Gelmir+Glintstone+Staff", "wikigg": "/Gelmir_Glintstone_Staff", "fandom": "Gelmir_Glintstone_Staff"},
            # Sacred Seals
            {"fex": "/Clawmark+Seal", "wikigg": "/Clawmark_Seal", "fandom": "Clawmark_Seal"},
            {"fex": "/Dragon+Communion+Seal", "wikigg": "/Dragon_Communion_Seal", "fandom": "Dragon_Communion_Seal"},
            {"fex": "/Frenzied+Flame+Seal", "wikigg": "/Frenzied_Flame_Seal", "fandom": "Frenzied_Flame_Seal"},
            {"fex": "/Golden+Order+Seal", "wikigg": "/Golden_Order_Seal", "fandom": "Golden_Order_Seal"},
            {"fex": "/Godslayer's+Seal", "wikigg": "/Godslayer%27s_Seal", "fandom": "Godslayer%27s_Seal"},
            {"fex": "/Gravel+Stone+Seal", "wikigg": "/Gravel_Stone_Seal", "fandom": "Gravel_Stone_Seal"},
            {"fex": "/Godslayer's+Seal", "wikigg": "/Godslayer%27s_Seal", "fandom": "Godslayer%27s_Seal"},
            # Crossbows / Bows
            {"fex": "/Black+Bow", "wikigg": "/Black_Bow", "fandom": "Black_Bow"},
            {"fex": "/Serpent+Bow", "wikigg": "/Serpent_Bow", "fandom": "Serpent_Bow"},
            {"fex": "/Horn+Bow", "wikigg": "/Horn_Bow", "fandom": "Horn_Bow"},
            {"fex": "/Composite+Bow", "wikigg": "/Composite_Bow", "fandom": "Composite_Bow"},
            {"fex": "/Pulley+Bow", "wikigg": "/Pulley_Bow", "fandom": "Pulley_Bow"},
            # DLC weapons
            {"fex": "/Messmer's+Spear", "wikigg": "/Messmer%27s_Spear", "fandom": "Messmer%27s_Spear"},
            {"fex": "/Greatsword+of+Radahn", "wikigg": "/Greatsword_of_Radahn", "fandom": "Greatsword_of_Radahn"},
            {"fex": "/Leda's+Sword", "wikigg": "/Leda%27s_Sword", "fandom": "Leda%27s_Sword"},
            {"fex": "/Rellana's+Twin+Blades", "wikigg": "/Rellana%27s_Twin_Blades", "fandom": "Rellana%27s_Twin_Blades"},
            {"fex": "/Euporia", "wikigg": "/Euporia", "fandom": "Euporia"},
            {"fex": "/Ansbach's+Longbow", "wikigg": "/Ansbach%27s_Longbow", "fandom": "Ansbach%27s_Longbow"},
            {"fex": "/Thiollier's+Hidden+Needle", "wikigg": "/Thiollier%27s_Hidden_Needle", "fandom": "Thiollier%27s_Hidden_Needle"},
            {"fex": "/Putrescence+Cleaver", "wikigg": "/Putrescence_Cleaver", "fandom": "Putrescence_Cleaver"},
            {"fex": "/Dragon-Hunter's+Great+Katana", "wikigg": "/Dragon-Hunter%27s_Great_Katana", "fandom": "Dragon-Hunter%27s_Great_Katana"},
            {"fex": "/Shadow+Sunflower+Blossom", "wikigg": "/Shadow_Sunflower_Blossom", "fandom": "Shadow_Sunflower_Blossom"},
            {"fex": "/Bloodfiend's+Arm", "wikigg": "/Bloodfiend%27s_Arm", "fandom": "Bloodfiend%27s_Arm"},
            {"fex": "/Sword+of+Light+and+Shadow", "wikigg": "/Sword_of_Light_and_Shadow", "fandom": "Sword_of_Light_and_Shadow"},
            {"fex": "/Smithscript+Axe", "wikigg": "/Smithscript_Axe", "fandom": "Smithscript_Axe"},
            {"fex": "/Smithscript+Dagger", "wikigg": "/Smithscript_Dagger", "fandom": "Smithscript_Dagger"},
            {"fex": "/Smithscript+Greathammer", "wikigg": "/Smithscript_Greathammer", "fandom": "Smithscript_Greathammer"},
            {"fex": "/Smithscript+Shield", "wikigg": "/Smithscript_Shield", "fandom": "Smithscript_Shield"},
            {"fex": "/Smithscript+Spear", "wikigg": "/Smithscript_Spear", "fandom": "Smithscript_Spear"},
            {"fex": "/Verdigris+Greathammer", "wikigg": "/Verdigris_Greathammer", "fandom": "Verdigris_Greathammer"},
            {"fex": "/Verdigris+Discus", "wikigg": "/Verdigris_Discus", "fandom": "Verdigris_Discus"},
            {"fex": "/Freyja's+Greatsword", "wikigg": "/Freyja%27s_Greatsword", "fandom": "Freyja%27s_Greatsword"},
            {"fex": "/Gaius's+Lance", "wikigg": "/Gaius%27s_Lance", "fandom": "Gaius%27s_Lance"},
        ]
    },

    # ----------------------------------------------------------
    # SPELLS — sorceries (~90) and incantations (~100)
    # ----------------------------------------------------------
    "spells": {
        "category": "spell",
        "entries": [
            # Sorceries — original
            {"fex": "/Comet+Azur", "wikigg": "/Comet_Azur", "fandom": "Comet_Azur"},
            {"fex": "/Ranni's+Dark+Moon", "wikigg": "/Ranni%27s_Dark_Moon", "fandom": "Ranni%27s_Dark_Moon"},
            {"fex": "/Stars+of+Ruin", "wikigg": "/Stars_of_Ruin", "fandom": "Stars_of_Ruin"},
            {"fex": "/Founding+Rain+of+Stars", "wikigg": "/Founding_Rain_of_Stars", "fandom": "Founding_Rain_of_Stars"},
            {"fex": "/Elden+Stars", "wikigg": "/Elden_Stars", "fandom": "Elden_Stars"},
            {"fex": "/Scarlet+Aeonia", "wikigg": "/Scarlet_Aeonia", "fandom": "Scarlet_Aeonia"},
            {"fex": "/Placidusax's+Ruin", "wikigg": "/Placidusax%27s_Ruin", "fandom": "Placidusax%27s_Ruin"},
            {"fex": "/Fortissax's+Lightning+Spear", "wikigg": "/Fortissax%27s_Lightning_Spear", "fandom": "Fortissax%27s_Lightning_Spear"},
            {"fex": "/Black+Flame", "wikigg": "/Black_Flame", "fandom": "Black_Flame"},
            {"fex": "/Howl+of+Shabriri", "wikigg": "/Howl_of_Shabriri", "fandom": "Howl_of_Shabriri"},
            {"fex": "/Ekzykes's+Decay", "wikigg": "/Ekzykes%27s_Decay", "fandom": "Ekzykes%27s_Decay"},
            {"fex": "/Greyoll's+Roar", "wikigg": "/Greyoll%27s_Roar", "fandom": "Greyoll%27s_Roar"},
            {"fex": "/Erdtree+Heal", "wikigg": "/Erdtree_Heal", "fandom": "Erdtree_Heal"},
            {"fex": "/Bloodboon", "wikigg": "/Bloodboon", "fandom": "Bloodboon"},
            {"fex": "/Swarm+of+Flies", "wikigg": "/Swarm_of_Flies", "fandom": "Swarm_of_Flies"},
            {"fex": "/Flame+of+the+Fell+God", "wikigg": "/Flame_of_the_Fell_God", "fandom": "Flame_of_the_Fell_God"},
            {"fex": "/Black+Blade", "wikigg": "/Black_Blade", "fandom": "Black_Blade"},
            {"fex": "/Golden+Order+Totality", "wikigg": "/Golden_Order_Totality", "fandom": "Golden_Order_Totality"},
            {"fex": "/Destined+Death", "wikigg": "/Destined_Death", "fandom": "Destined_Death"},
            {"fex": "/Frenzied+Burst", "wikigg": "/Frenzied_Burst", "fandom": "Frenzied_Burst"},
            {"fex": "/Heal+from+Afar", "wikigg": "/Heal_from_Afar", "fandom": "Heal_from_Afar"},
            # Expanded Sorceries
            {"fex": "/Comet", "wikigg": "/Comet", "fandom": "Comet"},
            {"fex": "/Great+Glintstone+Shard", "wikigg": "/Great_Glintstone_Shard", "fandom": "Great_Glintstone_Shard"},
            {"fex": "/Glintstone+Pebble", "wikigg": "/Glintstone_Pebble", "fandom": "Glintstone_Pebble"},
            {"fex": "/Glintstone+Arc", "wikigg": "/Glintstone_Arc", "fandom": "Glintstone_Arc"},
            {"fex": "/Glintstone+Stars", "wikigg": "/Glintstone_Stars", "fandom": "Glintstone_Stars"},
            {"fex": "/Loretta's+Greatbow", "wikigg": "/Loretta%27s_Greatbow", "fandom": "Loretta%27s_Greatbow"},
            {"fex": "/Loretta's+Mastery", "wikigg": "/Loretta%27s_Mastery", "fandom": "Loretta%27s_Mastery"},
            {"fex": "/Carian+Slicer", "wikigg": "/Carian_Slicer", "fandom": "Carian_Slicer"},
            {"fex": "/Carian+Phalanx", "wikigg": "/Carian_Phalanx", "fandom": "Carian_Phalanx"},
            {"fex": "/Carian+Greatsword", "wikigg": "/Carian_Greatsword", "fandom": "Carian_Greatsword"},
            {"fex": "/Carian+Retaliation", "wikigg": "/Carian_Retaliation", "fandom": "Carian_Retaliation"},
            {"fex": "/Carian+Piercer", "wikigg": "/Carian_Piercer", "fandom": "Carian_Piercer"},
            {"fex": "/Magic+Glintblade", "wikigg": "/Magic_Glintblade", "fandom": "Magic_Glintblade"},
            {"fex": "/Glintblade+Phalanx", "wikigg": "/Glintblade_Phalanx", "fandom": "Glintblade_Phalanx"},
            {"fex": "/Eternal+Darkness", "wikigg": "/Eternal_Darkness", "fandom": "Eternal_Darkness"},
            {"fex": "/Azur's+Comet", "wikigg": "/Azur%27s_Comet", "fandom": "Azur%27s_Comet"},
            {"fex": "/Lusat's+Glintstone+Spear", "wikigg": "/Lusat%27s_Glintstone_Spear", "fandom": "Lusat%27s_Glintstone_Spear"},
            {"fex": "/Night+Comet", "wikigg": "/Night_Comet", "fandom": "Night_Comet"},
            {"fex": "/Night+Maiden's+Mist", "wikigg": "/Night_Maiden%27s_Mist", "fandom": "Night_Maiden%27s_Mist"},
            {"fex": "/Night+Shard", "wikigg": "/Night_Shard", "fandom": "Night_Shard"},
            {"fex": "/Ambush+Shard", "wikigg": "/Ambush_Shard", "fandom": "Ambush_Shard"},
            {"fex": "/Collapsing+Stars", "wikigg": "/Collapsing_Stars", "fandom": "Collapsing_Stars"},
            {"fex": "/Gravity+Well", "wikigg": "/Gravity_Well", "fandom": "Gravity_Well"},
            {"fex": "/Meteorite", "wikigg": "/Meteorite", "fandom": "Meteorite"},
            {"fex": "/Rock+Sling", "wikigg": "/Rock_Sling", "fandom": "Rock_Sling"},
            {"fex": "/Meteorite+of+Astel", "wikigg": "/Meteorite_of_Astel", "fandom": "Meteorite_of_Astel"},
            {"fex": "/Terra+Magica", "wikigg": "/Terra_Magica", "fandom": "Terra_Magica"},
            {"fex": "/Crystal+Torrent", "wikigg": "/Crystal_Torrent", "fandom": "Crystal_Torrent"},
            {"fex": "/Crystal+Barrage", "wikigg": "/Crystal_Barrage", "fandom": "Crystal_Barrage"},
            {"fex": "/Shattering+Crystal", "wikigg": "/Shattering_Crystal", "fandom": "Shattering_Crystal"},
            {"fex": "/Rotten+Breath", "wikigg": "/Rotten_Breath", "fandom": "Rotten_Breath"},
            {"fex": "/Dragonfire", "wikigg": "/Dragonfire", "fandom": "Dragonfire"},
            {"fex": "/Dragonice", "wikigg": "/Dragonice", "fandom": "Dragonice"},
            {"fex": "/Dragonmaw", "wikigg": "/Dragonmaw", "fandom": "Dragonmaw"},
            {"fex": "/Dragon+Claw", "wikigg": "/Dragon_Claw", "fandom": "Dragon_Claw"},
            {"fex": "/Agheel's+Flame", "wikigg": "/Agheel%27s_Flame", "fandom": "Agheel%27s_Flame"},
            {"fex": "/Borealis's+Mist", "wikigg": "/Borealis%27s_Mist", "fandom": "Borealis%27s_Mist"},
            {"fex": "/Adula's+Moonblade", "wikigg": "/Adula%27s_Moonblade", "fandom": "Adula%27s_Moonblade"},
            {"fex": "/Smarag's+Glintstone+Breath", "wikigg": "/Smarag%27s_Glintstone_Breath", "fandom": "Smarag%27s_Glintstone_Breath"},
            # Incantations — original + expanded
            {"fex": "/Golden+Vow", "wikigg": "/Golden_Vow", "fandom": "Golden_Vow"},
            {"fex": "/Flame+Grant+Me+Strength", "wikigg": "/Flame,_Grant_Me_Strength", "fandom": "Flame,_Grant_Me_Strength"},
            {"fex": "/Rotten+Breath", "wikigg": "/Rotten_Breath", "fandom": "Rotten_Breath"},
            {"fex": "/Lightning+Spear", "wikigg": "/Lightning_Spear", "fandom": "Lightning_Spear"},
            {"fex": "/Wrath+of+Gold", "wikigg": "/Wrath_of_Gold", "fandom": "Wrath_of_Gold"},
            {"fex": "/Order+Healing", "wikigg": "/Order_Healing", "fandom": "Order_Healing"},
            {"fex": "/Law+of+Regression", "wikigg": "/Law_of_Regression", "fandom": "Law_of_Regression"},
            {"fex": "/Litany+of+Proper+Death", "wikigg": "/Litany_of_Proper_Death", "fandom": "Litany_of_Proper_Death"},
            {"fex": "/Triple+Rings+of+Light", "wikigg": "/Triple_Rings_of_Light", "fandom": "Triple_Rings_of_Light"},
            {"fex": "/Radagon's+Rings+of+Light", "wikigg": "/Radagon%27s_Rings_of_Light", "fandom": "Radagon%27s_Rings_of_Light"},
            {"fex": "/Flame+of+the+Fell+God", "wikigg": "/Flame_of_the_Fell_God", "fandom": "Flame_of_the_Fell_God"},
            {"fex": "/Giant+Flame+of+Fell+God", "wikigg": "/Giant_Flame_of_Fell_God", "fandom": "Giant_Flame_of_Fell_God"},
            {"fex": "/Black+Flame+Ritual", "wikigg": "/Black_Flame_Ritual", "fandom": "Black_Flame_Ritual"},
            {"fex": "/Giantsflame+Take+Thee", "wikigg": "/Giantsflame_Take_Thee", "fandom": "Giantsflame_Take_Thee"},
            {"fex": "/Fire's+Deadly+Sin", "wikigg": "/Fire%27s_Deadly_Sin", "fandom": "Fire%27s_Deadly_Sin"},
            {"fex": "/Burn+O+Flame!", "wikigg": "/Burn,_O_Flame%21", "fandom": "Burn,_O_Flame%21"},
            {"fex": "/Black+Flame's+Protection", "wikigg": "/Black_Flame%27s_Protection", "fandom": "Black_Flame%27s_Protection"},
            {"fex": "/Bloodflame+Blade", "wikigg": "/Bloodflame_Blade", "fandom": "Bloodflame_Blade"},
            {"fex": "/Bloodflame+Talons", "wikigg": "/Bloodflame_Talons", "fandom": "Bloodflame_Talons"},
            {"fex": "/Crucible+Tail", "wikigg": "/Crucible_Tail", "fandom": "Crucible_Tail"},
            {"fex": "/Crucible+Horns", "wikigg": "/Crucible_Horns", "fandom": "Crucible_Horns"},
            {"fex": "/Aspects+of+the+Crucible+Breath", "wikigg": "/Aspects_of_the_Crucible_Breath", "fandom": "Aspects_of_the_Crucible_Breath"},
            {"fex": "/Rejection", "wikigg": "/Rejection", "fandom": "Rejection"},
            {"fex": "/Assassin's+Approach", "wikigg": "/Assassin%27s_Approach", "fandom": "Assassin%27s_Approach"},
            {"fex": "/Beloved+Stardust", "wikigg": "/Beloved_Stardust", "fandom": "Beloved_Stardust"},
            {"fex": "/O+Flame!", "wikigg": "/O,_Flame%21", "fandom": "O,_Flame%21"},
            {"fex": "/Frenzied+Flame+Incantations", "wikigg": "/Flame_of_Frenzy", "fandom": "Flame_of_Frenzy"},
            {"fex": "/The+Flame+of+Frenzy", "wikigg": "/The_Flame_of_Frenzy", "fandom": "The_Flame_of_Frenzy"},
            {"fex": "/Inescapable+Frenzy", "wikigg": "/Inescapable_Frenzy", "fandom": "Inescapable_Frenzy"},
            {"fex": "/Unendurable+Frenzy", "wikigg": "/Unendurable_Frenzy", "fandom": "Unendurable_Frenzy"},
            # DLC spells
            {"fex": "/Messmer's+Orb", "wikigg": "/Messmer%27s_Orb", "fandom": "Messmer%27s_Orb"},
            {"fex": "/Divine+Bird+Feathers", "wikigg": "/Divine_Bird_Feathers", "fandom": "Divine_Bird_Feathers"},
            {"fex": "/Midra's+Flame+of+Frenzy", "wikigg": "/Midra%27s_Flame_of_Frenzy", "fandom": "Midra%27s_Flame_of_Frenzy"},
            {"fex": "/Euphoria", "wikigg": "/Euphoria", "fandom": "Euphoria"},
            {"fex": "/Aspect+of+the+Crucible+Wings", "wikigg": "/Aspect_of_the_Crucible_Wings", "fandom": "Aspect_of_the_Crucible_Wings"},
            {"fex": "/Spira", "wikigg": "/Spira", "fandom": "Spira"},
            {"fex": "/Twist+of+Gravity", "wikigg": "/Twist_of_Gravity", "fandom": "Twist_of_Gravity"},
            {"fex": "/Ancient+Lightning+Spear", "wikigg": "/Ancient_Lightning_Spear", "fandom": "Ancient_Lightning_Spear"},
            {"fex": "/Bayle's+Tyranny", "wikigg": "/Bayle%27s_Tyranny", "fandom": "Bayle%27s_Tyranny"},
            {"fex": "/Bayle's+Flame+Lightning", "wikigg": "/Bayle%27s_Flame_Lightning", "fandom": "Bayle%27s_Flame_Lightning"},
            {"fex": "/Roar+of+Rugalea", "wikigg": "/Roar_of_Rugalea", "fandom": "Roar_of_Rugalea"},
            {"fex": "/Pest+Threads", "wikigg": "/Pest_Threads", "fandom": "Pest_Threads"},
            {"fex": "/Watchful+Spirit", "wikigg": "/Watchful_Spirit", "fandom": "Watchful_Spirit"},
        ]
    },

    # ----------------------------------------------------------
    # GREAT RUNES — all 10
    # ----------------------------------------------------------
    "great_runes": {
        "category": "great_rune",
        "entries": [
            {"fex": "/Godrick's+Great+Rune", "wikigg": "/Godrick%27s_Great_Rune", "fandom": "Godrick%27s_Great_Rune"},
            {"fex": "/Rennala's+Great+Rune", "wikigg": "/Rennala%27s_Great_Rune", "fandom": "Rennala%27s_Great_Rune"},
            {"fex": "/Radahn's+Great+Rune", "wikigg": "/Radahn%27s_Great_Rune", "fandom": "Radahn%27s_Great_Rune"},
            {"fex": "/Morgott's+Great+Rune", "wikigg": "/Morgott%27s_Great_Rune", "fandom": "Morgott%27s_Great_Rune"},
            {"fex": "/Mohg's+Great+Rune", "wikigg": "/Mohg%27s_Great_Rune", "fandom": "Mohg%27s_Great_Rune"},
            {"fex": "/Rykard's+Great+Rune", "wikigg": "/Rykard%27s_Great_Rune", "fandom": "Rykard%27s_Great_Rune"},
            {"fex": "/Malenia's+Great+Rune", "wikigg": "/Malenia%27s_Great_Rune", "fandom": "Malenia%27s_Great_Rune"},
            {"fex": "/Shardbearers", "wikigg": "/Shardbearer", "fandom": "Shardbearer"},
            {"fex": "/Great+Rune+of+the+Unborn", "wikigg": "/Great_Rune_of_the_Unborn", "fandom": "Great_Rune_of_the_Unborn"},
            {"fex": "/Elden+Ring+Great+Runes", "wikigg": "/Great_Rune", "fandom": "Great_Rune"},
        ]
    },

    # ----------------------------------------------------------
    # SPIRIT ASHES — all ~100 summons
    # ----------------------------------------------------------
    "spirit_ashes": {
        "category": "spirit_ash",
        "entries": [
            {"fex": "/Lone+Wolf+Ashes", "wikigg": "/Lone_Wolf_Ashes", "fandom": "Lone_Wolf_Ashes"},
            {"fex": "/Jellyfish+Ashes", "wikigg": "/Jellyfish_Ashes", "fandom": "Jellyfish_Ashes"},
            {"fex": "/Skeletal+Militiaman+Ashes", "wikigg": "/Skeletal_Militiaman_Ashes", "fandom": "Skeletal_Militiaman_Ashes"},
            {"fex": "/Wandering+Noble+Ashes", "wikigg": "/Wandering_Noble_Ashes", "fandom": "Wandering_Noble_Ashes"},
            {"fex": "/Noble+Sorcerer+Ashes", "wikigg": "/Noble_Sorcerer_Ashes", "fandom": "Noble_Sorcerer_Ashes"},
            {"fex": "/Glintstone+Sorcerer+Ashes", "wikigg": "/Glintstone_Sorcerer_Ashes", "fandom": "Glintstone_Sorcerer_Ashes"},
            {"fex": "/Raya+Lucarian+Soldier+Ashes", "wikigg": "/Raya_Lucarian_Soldier_Ashes", "fandom": "Raya_Lucarian_Soldier_Ashes"},
            {"fex": "/Ancestral+Follower+Ashes", "wikigg": "/Ancestral_Follower_Ashes", "fandom": "Ancestral_Follower_Ashes"},
            {"fex": "/Godrick+Soldier+Ashes", "wikigg": "/Godrick_Soldier_Ashes", "fandom": "Godrick_Soldier_Ashes"},
            {"fex": "/Radahn+Soldier+Ashes", "wikigg": "/Radahn_Soldier_Ashes", "fandom": "Radahn_Soldier_Ashes"},
            {"fex": "/Marionette+Soldier+Ashes", "wikigg": "/Marionette_Soldier_Ashes", "fandom": "Marionette_Soldier_Ashes"},
            {"fex": "/Leyndell+Soldier+Ashes", "wikigg": "/Leyndell_Soldier_Ashes", "fandom": "Leyndell_Soldier_Ashes"},
            {"fex": "/Haligtree+Soldier+Ashes", "wikigg": "/Haligtree_Soldier_Ashes", "fandom": "Haligtree_Soldier_Ashes"},
            {"fex": "/Banished+Knight+Oleg+Ashes", "wikigg": "/Banished_Knight_Oleg_Ashes", "fandom": "Banished_Knight_Oleg_Ashes"},
            {"fex": "/Banished+Knight+Engvall+Ashes", "wikigg": "/Banished_Knight_Engvall_Ashes", "fandom": "Banished_Knight_Engvall_Ashes"},
            {"fex": "/Cleanrot+Knight+Finlay+Ashes", "wikigg": "/Cleanrot_Knight_Finlay_Ashes", "fandom": "Cleanrot_Knight_Finlay_Ashes"},
            {"fex": "/Lhutel+the+Headless+Ashes", "wikigg": "/Lhutel_the_Headless_Ashes", "fandom": "Lhutel_the_Headless_Ashes"},
            {"fex": "/Black+Knife+Tiche+Ashes", "wikigg": "/Black_Knife_Tiche_Ashes", "fandom": "Black_Knife_Tiche_Ashes"},
            {"fex": "/Latenna+the+Albinauric+Ashes", "wikigg": "/Latenna_the_Albinauric_Ashes", "fandom": "Latenna_the_Albinauric_Ashes"},
            {"fex": "/Mimic+Tear+Ashes", "wikigg": "/Mimic_Tear_Ashes", "fandom": "Mimic_Tear_Ashes"},
            {"fex": "/Omenkiller+Rollo+Ashes", "wikigg": "/Omenkiller_Rollo_Ashes", "fandom": "Omenkiller_Rollo_Ashes"},
            {"fex": "/Dung+Eater+Puppet+Ashes", "wikigg": "/Dung_Eater_Puppet_Ashes", "fandom": "Dung_Eater_Puppet_Ashes"},
            {"fex": "/Crystalian+Ashes", "wikigg": "/Crystalian_Ashes", "fandom": "Crystalian_Ashes"},
            {"fex": "/Fanged+Imp+Ashes", "wikigg": "/Fanged_Imp_Ashes", "fandom": "Fanged_Imp_Ashes"},
            {"fex": "/Giant+Rat+Ashes", "wikigg": "/Giant_Rat_Ashes", "fandom": "Giant_Rat_Ashes"},
            {"fex": "/Rotten+Stray+Ashes", "wikigg": "/Rotten_Stray_Ashes", "fandom": "Rotten_Stray_Ashes"},
            {"fex": "/Grave+Warden+Duelist+Ashes", "wikigg": "/Grave_Warden_Duelist_Ashes", "fandom": "Grave_Warden_Duelist_Ashes"},
            {"fex": "/Kaiden+Sellsword+Ashes", "wikigg": "/Kaiden_Sellsword_Ashes", "fandom": "Kaiden_Sellsword_Ashes"},
            {"fex": "/Greatshield+Soldier+Ashes", "wikigg": "/Greatshield_Soldier_Ashes", "fandom": "Greatshield_Soldier_Ashes"},
            {"fex": "/Battlemage+Hugues+Ashes", "wikigg": "/Battlemage_Hugues_Ashes", "fandom": "Battlemage_Hugues_Ashes"},
            {"fex": "/Nepheli+Loux+Puppet+Ashes", "wikigg": "/Nepheli_Loux_Puppet_Ashes", "fandom": "Nepheli_Loux_Puppet_Ashes"},
            {"fex": "/Albinauric+Ashes", "wikigg": "/Albinauric_Ashes", "fandom": "Albinauric_Ashes"},
            {"fex": "/Vulgar+Militia+Ashes", "wikigg": "/Vulgar_Militia_Ashes", "fandom": "Vulgar_Militia_Ashes"},
            {"fex": "/Kindred+of+Rot+Ashes", "wikigg": "/Kindred_of_Rot_Ashes", "fandom": "Kindred_of_Rot_Ashes"},
            {"fex": "/Mausoleum+Soldier+Ashes", "wikigg": "/Mausoleum_Soldier_Ashes", "fandom": "Mausoleum_Soldier_Ashes"},
            {"fex": "/Mausoleum+Knight+Ashes", "wikigg": "/Mausoleum_Knight_Ashes", "fandom": "Mausoleum_Knight_Ashes"},
            {"fex": "/Nox+Swordstress+Ashes", "wikigg": "/Nox_Swordstress_Ashes", "fandom": "Nox_Swordstress_Ashes"},
            {"fex": "/Nox+Monk+Ashes", "wikigg": "/Nox_Monk_Ashes", "fandom": "Nox_Monk_Ashes"},
            {"fex": "/Fire+Knight+Ashes", "wikigg": "/Fire_Knight_Ashes", "fandom": "Fire_Knight_Ashes"},
            {"fex": "/Bloodhound+Knight+Floh+Ashes", "wikigg": "/Bloodhound_Knight_Floh_Ashes", "fandom": "Bloodhound_Knight_Floh_Ashes"},
            {"fex": "/Nightmaiden+&+Swordstress+Puppets+Ashes", "wikigg": "/Nightmaiden_%26_Swordstress_Puppets_Ashes", "fandom": "Nightmaiden_%26_Swordstress_Puppets_Ashes"},
            {"fex": "/Warhawk+Ashes", "wikigg": "/Warhawk_Ashes", "fandom": "Warhawk_Ashes"},
            {"fex": "/Man-Serpent+Ashes", "wikigg": "/Man-Serpent_Ashes", "fandom": "Man-Serpent_Ashes"},
            {"fex": "/Ancient+Dragon+Knight+Kristoff+Ashes", "wikigg": "/Ancient_Dragon_Knight_Kristoff_Ashes", "fandom": "Ancient_Dragon_Knight_Kristoff_Ashes"},
            {"fex": "/Twinsage+Glintstone+Sorcerer+Ashes", "wikigg": "/Twinsage_Glintstone_Sorcerer_Ashes", "fandom": "Twinsage_Glintstone_Sorcerer_Ashes"},
            {"fex": "/Rotten+Gravekeeper+Cloak+Ashes", "wikigg": "/Rotten_Gravekeeper_Cloak_Ashes", "fandom": "Rotten_Gravekeeper_Cloak_Ashes"},
            {"fex": "/PAGE_Spirit_Ashes", "wikigg": "/Spirit_Ashes", "fandom": "Spirit_Ashes"},
            # DLC spirit ashes
            {"fex": "/Igon+Ashes", "wikigg": "/Igon_Ashes", "fandom": "Igon_Ashes"},
            {"fex": "/Spirit+Ashes", "wikigg": "/Spirit_Ashes", "fandom": "Spirit_Ashes"},
        ]
    },

    # ----------------------------------------------------------
    # ASHES OF WAR — all ~100 weapon skills
    # ----------------------------------------------------------
    "ashes_of_war": {
        "category": "ash_of_war",
        "entries": [
            {"fex": "/Ashes+of+War", "wikigg": "/Ashes_of_War", "fandom": "Ashes_of_War"},
            {"fex": "/Ash+of+War+Gravitas", "wikigg": "/Ash_of_War_Gravitas", "fandom": "Ash_of_War:_Gravitas"},
            {"fex": "/Ash+of+War+Bloodhound's+Step", "wikigg": "/Ash_of_War_Bloodhound%27s_Step", "fandom": "Ash_of_War:_Bloodhound%27s_Step"},
            {"fex": "/Ash+of+War+Sacred+Blade", "wikigg": "/Ash_of_War_Sacred_Blade", "fandom": "Ash_of_War:_Sacred_Blade"},
            {"fex": "/Ash+of+War+Hoarfrost+Stomp", "wikigg": "/Ash_of_War_Hoarfrost_Stomp", "fandom": "Ash_of_War:_Hoarfrost_Stomp"},
            {"fex": "/Ash+of+War+Flame+of+the+Redmanes", "wikigg": "/Ash_of_War_Flame_of_the_Redmanes", "fandom": "Ash_of_War:_Flame_of_the_Redmanes"},
            {"fex": "/Ash+of+War+Thunderbolt", "wikigg": "/Ash_of_War_Thunderbolt", "fandom": "Ash_of_War:_Thunderbolt"},
            {"fex": "/Ash+of+War+Moonveil", "wikigg": "/Ash_of_War_Transient_Moonlight", "fandom": "Ash_of_War:_Transient_Moonlight"},
            {"fex": "/Ash+of+War+Wild+Strikes", "wikigg": "/Ash_of_War_Wild_Strikes", "fandom": "Ash_of_War:_Wild_Strikes"},
            {"fex": "/Ash+of+War+Lion's+Claw", "wikigg": "/Ash_of_War_Lion%27s_Claw", "fandom": "Ash_of_War:_Lion%27s_Claw"},
            {"fex": "/Ash+of+War+Stamp+Upward+Cut", "wikigg": "/Ash_of_War_Stamp_(Upward_Cut)", "fandom": "Ash_of_War:_Stamp_(Upward_Cut)"},
            {"fex": "/Ash+of+War+Sword+Dance", "wikigg": "/Ash_of_War_Sword_Dance", "fandom": "Ash_of_War:_Sword_Dance"},
            {"fex": "/Ash+of+War+Storm+Blade", "wikigg": "/Ash_of_War_Storm_Blade", "fandom": "Ash_of_War:_Storm_Blade"},
            {"fex": "/Ash+of+War+Carian+Grandeur", "wikigg": "/Ash_of_War_Carian_Grandeur", "fandom": "Ash_of_War:_Carian_Grandeur"},
            {"fex": "/Ash+of+War+Seppuku", "wikigg": "/Ash_of_War_Seppuku", "fandom": "Ash_of_War:_Seppuku"},
            {"fex": "/Ash+of+War+Bloody+Slash", "wikigg": "/Ash_of_War_Bloody_Slash", "fandom": "Ash_of_War:_Bloody_Slash"},
            {"fex": "/Ash+of+War+Golden+Vow", "wikigg": "/Ash_of_War_Golden_Vow", "fandom": "Ash_of_War:_Golden_Vow"},
            {"fex": "/Ash+of+War+Giant+Hunt", "wikigg": "/Ash_of_War_Giant_Hunt", "fandom": "Ash_of_War:_Giant_Hunt"},
            {"fex": "/Ash+of+War+Impaling+Thrust", "wikigg": "/Ash_of_War_Impaling_Thrust", "fandom": "Ash_of_War:_Impaling_Thrust"},
            {"fex": "/Ash+of+War+Poisonous+Mist", "wikigg": "/Ash_of_War_Poisonous_Mist", "fandom": "Ash_of_War:_Poisonous_Mist"},
            {"fex": "/Ash+of+War+Barricade+Shield", "wikigg": "/Ash_of_War_Barricade_Shield", "fandom": "Ash_of_War:_Barricade_Shield"},
            {"fex": "/Ash+of+War+Royal+Knight's+Resolve", "wikigg": "/Ash_of_War_Royal_Knight%27s_Resolve", "fandom": "Ash_of_War:_Royal_Knight%27s_Resolve"},
            {"fex": "/Ash+of+War+Unsheathe", "wikigg": "/Ash_of_War_Unsheathe", "fandom": "Ash_of_War:_Unsheathe"},
            {"fex": "/Ash+of+War+Glintstone+Pebble", "wikigg": "/Ash_of_War_Glintstone_Pebble", "fandom": "Ash_of_War:_Glintstone_Pebble"},
            {"fex": "/Ash+of+War+Carian+Retaliation", "wikigg": "/Ash_of_War_Carian_Retaliation", "fandom": "Ash_of_War:_Carian_Retaliation"},
            {"fex": "/Ash+of+War+Waves+of+Darkness", "wikigg": "/Ash_of_War_Waves_of_Darkness", "fandom": "Ash_of_War:_Waves_of_Darkness"},
            {"fex": "/Ash+of+War+Shriek+of+Milos", "wikigg": "/Ash_of_War_Shriek_of_Milos", "fandom": "Ash_of_War:_Shriek_of_Milos"},
            {"fex": "/Ash+of+War+Eruption", "wikigg": "/Ash_of_War_Eruption", "fandom": "Ash_of_War:_Eruption"},
            {"fex": "/Ash+of+War+Spectral+Lance", "wikigg": "/Ash_of_War_Spectral_Lance", "fandom": "Ash_of_War:_Spectral_Lance"},
            {"fex": "/Ash+of+War+Braggart's+Roar", "wikigg": "/Ash_of_War_Braggart%27s_Roar", "fandom": "Ash_of_War:_Braggart%27s_Roar"},
            {"fex": "/Ash+of+War+Ground+Slam", "wikigg": "/Ash_of_War_Ground_Slam", "fandom": "Ash_of_War:_Ground_Slam"},
        ]
    },

    # ----------------------------------------------------------
    # ARMOR SETS — all ~150 armor sets
    # ----------------------------------------------------------
    "armor": {
        "category": "armor",
        "entries": [
            {"fex": "/Armor+Sets", "wikigg": "/Armor", "fandom": "Armor"},
            # Iconic named sets
            {"fex": "/Godrick+Knight+Armor", "wikigg": "/Godrick_Knight_Armor", "fandom": "Godrick_Knight_Armor"},
            {"fex": "/Raya+Lucarian+Knight+Armor", "wikigg": "/Raya_Lucarian_Knight_Armor", "fandom": "Raya_Lucarian_Knight_Armor"},
            {"fex": "/Carian+Knight+Armor", "wikigg": "/Carian_Knight_Armor", "fandom": "Carian_Knight_Armor"},
            {"fex": "/Banished+Knight+Armor", "wikigg": "/Banished_Knight_Armor", "fandom": "Banished_Knight_Armor"},
            {"fex": "/Crucible+Tree+Armor", "wikigg": "/Crucible_Tree_Armor", "fandom": "Crucible_Tree_Armor"},
            {"fex": "/Crucible+Axe+Armor", "wikigg": "/Crucible_Axe_Armor", "fandom": "Crucible_Axe_Armor"},
            {"fex": "/Veteran's+Armor", "wikigg": "/Veteran%27s_Armor", "fandom": "Veteran%27s_Armor"},
            {"fex": "/Malformed+Dragon+Armor", "wikigg": "/Malformed_Dragon_Armor", "fandom": "Malformed_Dragon_Armor"},
            {"fex": "/Godskin+Apostle+Armor", "wikigg": "/Godskin_Apostle_Armor", "fandom": "Godskin_Apostle_Armor"},
            {"fex": "/Godskin+Noble+Armor", "wikigg": "/Godskin_Noble_Armor", "fandom": "Godskin_Noble_Armor"},
            {"fex": "/Black+Knife+Armor", "wikigg": "/Black_Knife_Armor", "fandom": "Black_Knife_Armor"},
            {"fex": "/Royal+Remains+Armor", "wikigg": "/Royal_Remains_Armor", "fandom": "Royal_Remains_Armor"},
            {"fex": "/Snow+Witch+Armor", "wikigg": "/Snow_Witch_Armor", "fandom": "Snow_Witch_Armor"},
            {"fex": "/White+Reed+Armor", "wikigg": "/White_Reed_Armor", "fandom": "White_Reed_Armor"},
            {"fex": "/Hoslow's+Armor", "wikigg": "/Hoslow%27s_Armor", "fandom": "Hoslow%27s_Armor"},
            {"fex": "/Deathbed+Smalls", "wikigg": "/Deathbed_Smalls", "fandom": "Deathbed_Smalls"},
            {"fex": "/Cleanrot+Armor", "wikigg": "/Cleanrot_Armor", "fandom": "Cleanrot_Armor"},
            {"fex": "/Fingerprint+Armor", "wikigg": "/Fingerprint_Armor", "fandom": "Fingerprint_Armor"},
            {"fex": "/Haligtree+Knight+Armor", "wikigg": "/Haligtree_Knight_Armor", "fandom": "Haligtree_Knight_Armor"},
            {"fex": "/Bloodhound+Knight+Armor", "wikigg": "/Bloodhound_Knight_Armor", "fandom": "Bloodhound_Knight_Armor"},
            {"fex": "/Mushroom+Armor", "wikigg": "/Mushroom_Armor", "fandom": "Mushroom_Armor"},
            {"fex": "/Imp+Head+Cat", "wikigg": "/Imp_Head_(Cat)", "fandom": "Imp_Head_(Cat)"},
            {"fex": "/Tree+Sentinel+Armor", "wikigg": "/Tree_Sentinel_Armor", "fandom": "Tree_Sentinel_Armor"},
            {"fex": "/Radahn's+Lion+Armor", "wikigg": "/Radahn%27s_Lion_Armor", "fandom": "Radahn%27s_Lion_Armor"},
            {"fex": "/Raging+Wolf+Armor", "wikigg": "/Raging_Wolf_Armor", "fandom": "Raging_Wolf_Armor"},
            {"fex": "/Nox+Monk+Armor", "wikigg": "/Nox_Monk_Armor", "fandom": "Nox_Monk_Armor"},
            {"fex": "/Nox+Swordstress+Armor", "wikigg": "/Nox_Swordstress_Armor", "fandom": "Nox_Swordstress_Armor"},
            {"fex": "/Zamor+Armor", "wikigg": "/Zamor_Armor", "fandom": "Zamor_Armor"},
            {"fex": "/Omen+Helm", "wikigg": "/Omen_Helm", "fandom": "Omen_Helm"},
            {"fex": "/All-Knowing+Armor", "wikigg": "/All-Knowing_Armor", "fandom": "All-Knowing_Armor"},
            {"fex": "/Maliketh's+Armor", "wikigg": "/Maliketh%27s_Armor", "fandom": "Maliketh%27s_Armor"},
            {"fex": "/Depraved+Perfumer+Armor", "wikigg": "/Depraved_Perfumer_Armor", "fandom": "Depraved_Perfumer_Armor"},
            {"fex": "/Confessor+Armor", "wikigg": "/Confessor_Armor", "fandom": "Confessor_Armor"},
            {"fex": "/Vagabond+Knight+Armor", "wikigg": "/Vagabond_Knight_Armor", "fandom": "Vagabond_Knight_Armor"},
            {"fex": "/Twinned+Armor", "wikigg": "/Twinned_Armor", "fandom": "Twinned_Armor"},
            {"fex": "/Scaled+Armor", "wikigg": "/Scaled_Armor", "fandom": "Scaled_Armor"},
            {"fex": "/Old+Sorcerer's+Set", "wikigg": "/Old_Sorcerer%27s_Set", "fandom": "Old_Sorcerer%27s_Set"},
            {"fex": "/Preceptor's+Set", "wikigg": "/Preceptor%27s_Set", "fandom": "Preceptor%27s_Set"},
            {"fex": "/Astrologer+Armor", "wikigg": "/Astrologer_Armor", "fandom": "Astrologer_Armor"},
            {"fex": "/Night's+Cavalry+Armor", "wikigg": "/Night%27s_Cavalry_Armor", "fandom": "Night%27s_Cavalry_Armor"},
            {"fex": "/Fia's+Robe", "wikigg": "/Fia%27s_Robe", "fandom": "Fia%27s_Robe"},
            {"fex": "/Ronin's+Armor", "wikigg": "/Ronin%27s_Armor", "fandom": "Ronin%27s_Armor"},
            {"fex": "/Land+of+Reeds+Armor", "wikigg": "/Land_of_Reeds_Armor", "fandom": "Land_of_Reeds_Armor"},
            {"fex": "/Sanguine+Noble+Armor", "wikigg": "/Sanguine_Noble_Armor", "fandom": "Sanguine_Noble_Armor"},
            {"fex": "/Ruler's+Mask", "wikigg": "/Ruler%27s_Mask", "fandom": "Ruler%27s_Mask"},
            {"fex": "/Traveling+Maiden+Armor", "wikigg": "/Traveling_Maiden_Armor", "fandom": "Traveling_Maiden_Armor"},
            {"fex": "/White+Mask", "wikigg": "/White_Mask", "fandom": "White_Mask"},
            # DLC armor sets
            {"fex": "/Messmer+Soldier+Armor", "wikigg": "/Messmer_Soldier_Armor", "fandom": "Messmer_Soldier_Armor"},
            {"fex": "/Fire+Knight+Armor", "wikigg": "/Fire_Knight_Armor", "fandom": "Fire_Knight_Armor"},
            {"fex": "/Horned+Warrior+Armor", "wikigg": "/Horned_Warrior_Armor", "fandom": "Horned_Warrior_Armor"},
            {"fex": "/Verdigris+Armor", "wikigg": "/Verdigris_Armor", "fandom": "Verdigris_Armor"},
            {"fex": "/Gaius's+Armor", "wikigg": "/Gaius%27s_Armor", "fandom": "Gaius%27s_Armor"},
            {"fex": "/Leda's+Armor", "wikigg": "/Leda%27s_Armor", "fandom": "Leda%27s_Armor"},
            {"fex": "/Ansbach's+Armor", "wikigg": "/Ansbach%27s_Armor", "fandom": "Ansbach%27s_Armor"},
            {"fex": "/Freyja's+Armor", "wikigg": "/Freyja%27s_Armor", "fandom": "Freyja%27s_Armor"},
        ]
    },

    # ----------------------------------------------------------
    # SHIELDS — ~65 shields
    # ----------------------------------------------------------
    "shields": {
        "category": "shield",
        "entries": [
            {"fex": "/Shields", "wikigg": "/Shields", "fandom": "Shields"},
            {"fex": "/Fingerprint+Stone+Shield", "wikigg": "/Fingerprint_Stone_Shield", "fandom": "Fingerprint_Stone_Shield"},
            {"fex": "/Erdtree+Greatshield", "wikigg": "/Erdtree_Greatshield", "fandom": "Erdtree_Greatshield"},
            {"fex": "/Dragoncrest+Greatshield", "wikigg": "/Dragoncrest_Greatshield", "fandom": "Dragoncrest_Greatshield"},
            {"fex": "/Crucible+Hornshield", "wikigg": "/Crucible_Hornshield", "fandom": "Crucible_Hornshield"},
            {"fex": "/Golden+Beast+Crest+Greatshield", "wikigg": "/Golden_Beast_Crest_Greatshield", "fandom": "Golden_Beast_Crest_Greatshield"},
            {"fex": "/Haligtree+Crest+Greatshield", "wikigg": "/Haligtree_Crest_Greatshield", "fandom": "Haligtree_Crest_Greatshield"},
            {"fex": "/Manor+Towershield", "wikigg": "/Manor_Towershield", "fandom": "Manor_Towershield"},
            {"fex": "/Spiralhorn+Shield", "wikigg": "/Spiralhorn_Shield", "fandom": "Spiralhorn_Shield"},
            {"fex": "/Albinauric+Shield", "wikigg": "/Albinauric_Shield", "fandom": "Albinauric_Shield"},
            {"fex": "/Banished+Knight's+Shield", "wikigg": "/Banished_Knight%27s_Shield", "fandom": "Banished_Knight%27s_Shield"},
            {"fex": "/Blue+Crest+Heater+Shield", "wikigg": "/Blue_Crest_Heater_Shield", "fandom": "Blue_Crest_Heater_Shield"},
            {"fex": "/Carian+Knight's+Shield", "wikigg": "/Carian_Knight%27s_Shield", "fandom": "Carian_Knight%27s_Shield"},
            {"fex": "/Cleanrot+Knight's+Sword+Shield", "wikigg": "/Cleanrot_Knight%27s_Sword_Shield", "fandom": "Cleanrot_Knight%27s_Sword_Shield"},
            {"fex": "/Commoner's+Simple+Satchel", "wikigg": "/Commoner%27s_Simple_Satchel", "fandom": "Commoner%27s_Simple_Satchel"},
            {"fex": "/Eclipse+Crest+Greatshield", "wikigg": "/Eclipse_Crest_Greatshield", "fandom": "Eclipse_Crest_Greatshield"},
            {"fex": "/Elden+Ring+Shields", "wikigg": "/Shields", "fandom": "Shields"},
            {"fex": "/Godrick+Knight+Shield", "wikigg": "/Godrick_Knight_Shield", "fandom": "Godrick_Knight_Shield"},
            {"fex": "/Haligtree+Knight+Shield", "wikigg": "/Haligtree_Knight_Shield", "fandom": "Haligtree_Knight_Shield"},
            {"fex": "/Inverted+Hawk+Heater+Shield", "wikigg": "/Inverted_Hawk_Heater_Shield", "fandom": "Inverted_Hawk_Heater_Shield"},
            {"fex": "/Jellyfish+Shield", "wikigg": "/Jellyfish_Shield", "fandom": "Jellyfish_Shield"},
            {"fex": "/Messmer+Soldier+Shield", "wikigg": "/Messmer_Soldier_Shield", "fandom": "Messmer_Soldier_Shield"},
            {"fex": "/Rickety+Shield", "wikigg": "/Rickety_Shield", "fandom": "Rickety_Shield"},
            {"fex": "/Shield+of+the+Guilty", "wikigg": "/Shield_of_the_Guilty", "fandom": "Shield_of_the_Guilty"},
            {"fex": "/Smoldering+Shield", "wikigg": "/Smoldering_Shield", "fandom": "Smoldering_Shield"},
            {"fex": "/Twinbird+Kite+Shield", "wikigg": "/Twinbird_Kite_Shield", "fandom": "Twinbird_Kite_Shield"},
        ]
    },

    # ----------------------------------------------------------
    # TALISMANS — expanded to ~100
    # ----------------------------------------------------------
    "talismans": {
        "category": "talisman",
        "entries": [
            {"fex": "/Talismans", "wikigg": "/Talismans", "fandom": "Talismans"},
            # Original set
            {"fex": "/Erdtree's+Favor", "wikigg": "/Erdtree%27s_Favor", "fandom": "Erdtree%27s_Favor"},
            {"fex": "/Two+Fingers+Heirloom", "wikigg": "/Two_Fingers_Heirloom", "fandom": "Two_Fingers_Heirloom"},
            {"fex": "/Moon+of+Nokstella", "wikigg": "/Moon_of_Nokstella", "fandom": "Moon_of_Nokstella"},
            {"fex": "/Radagon's+Soreseal", "wikigg": "/Radagon%27s_Soreseal", "fandom": "Radagon%27s_Soreseal"},
            {"fex": "/Radagon+Icon", "wikigg": "/Radagon_Icon", "fandom": "Radagon_Icon"},
            {"fex": "/Marika's+Soreseal", "wikigg": "/Marika%27s_Soreseal", "fandom": "Marika%27s_Soreseal"},
            {"fex": "/Godfrey+Icon", "wikigg": "/Godfrey_Icon", "fandom": "Godfrey_Icon"},
            {"fex": "/Godskin+Swaddling+Cloth", "wikigg": "/Godskin_Swaddling_Cloth", "fandom": "Godskin_Swaddling_Cloth"},
            {"fex": "/Old+Lord's+Talisman", "wikigg": "/Old_Lord%27s_Talisman", "fandom": "Old_Lord%27s_Talisman"},
            {"fex": "/Shabriri's+Woe", "wikigg": "/Shabriri%27s_Woe", "fandom": "Shabriri%27s_Woe"},
            {"fex": "/Talisman+of+the+Dread", "wikigg": "/Talisman_of_the_Dread", "fandom": "Talisman_of_the_Dread"},
            {"fex": "/Kindred+of+Rot's+Exultation", "wikigg": "/Kindred_of_Rot%27s_Exultation", "fandom": "Kindred_of_Rot%27s_Exultation"},
            {"fex": "/Lord+of+Blood's+Exultation", "wikigg": "/Lord_of_Blood%27s_Exultation", "fandom": "Lord_of_Blood%27s_Exultation"},
            {"fex": "/Taker's+Cameo", "wikigg": "/Taker%27s_Cameo", "fandom": "Taker%27s_Cameo"},
            {"fex": "/Blue+Dancer+Charm", "wikigg": "/Blue_Dancer_Charm", "fandom": "Blue_Dancer_Charm"},
            # Expanded talismans
            {"fex": "/Arsenal+Charm", "wikigg": "/Arsenal_Charm", "fandom": "Arsenal_Charm"},
            {"fex": "/Arrow's+Reach+Talisman", "wikigg": "/Arrow%27s_Reach_Talisman", "fandom": "Arrow%27s_Reach_Talisman"},
            {"fex": "/Arrow's+Sting+Talisman", "wikigg": "/Arrow%27s_Sting_Talisman", "fandom": "Arrow%27s_Sting_Talisman"},
            {"fex": "/Axe+Talisman", "wikigg": "/Axe_Talisman", "fandom": "Axe_Talisman"},
            {"fex": "/Blessed+Dew+Talisman", "wikigg": "/Blessed_Dew_Talisman", "fandom": "Blessed_Dew_Talisman"},
            {"fex": "/Bull-Goat's+Talisman", "wikigg": "/Bull-Goat%27s_Talisman", "fandom": "Bull-Goat%27s_Talisman"},
            {"fex": "/Carian+Filigreed+Crest", "wikigg": "/Carian_Filigreed_Crest", "fandom": "Carian_Filigreed_Crest"},
            {"fex": "/Cerulean+Amber+Medallion", "wikigg": "/Cerulean_Amber_Medallion", "fandom": "Cerulean_Amber_Medallion"},
            {"fex": "/Cerulean+Seed+Talisman", "wikigg": "/Cerulean_Seed_Talisman", "fandom": "Cerulean_Seed_Talisman"},
            {"fex": "/Champion+Talisman", "wikigg": "/Champion_Talisman", "fandom": "Champion_Talisman"},
            {"fex": "/Concealing+Veil", "wikigg": "/Concealing_Veil", "fandom": "Concealing_Veil"},
            {"fex": "/Crepus's+Vial", "wikigg": "/Crepus%27s_Vial", "fandom": "Crepus%27s_Vial"},
            {"fex": "/Crucible+Knot+Talisman", "wikigg": "/Crucible_Knot_Talisman", "fandom": "Crucible_Knot_Talisman"},
            {"fex": "/Crucible+Scale+Talisman", "wikigg": "/Crucible_Scale_Talisman", "fandom": "Crucible_Scale_Talisman"},
            {"fex": "/Curved+Sword+Talisman", "wikigg": "/Curved_Sword_Talisman", "fandom": "Curved_Sword_Talisman"},
            {"fex": "/Dagger+Talisman", "wikigg": "/Dagger_Talisman", "fandom": "Dagger_Talisman"},
            {"fex": "/Dragoncrest+Shield+Talisman", "wikigg": "/Dragoncrest_Shield_Talisman", "fandom": "Dragoncrest_Shield_Talisman"},
            {"fex": "/Dragoncrest+Greatshield+Talisman", "wikigg": "/Dragoncrest_Greatshield_Talisman", "fandom": "Dragoncrest_Greatshield_Talisman"},
            {"fex": "/Fire+Scorpion+Charm", "wikigg": "/Fire_Scorpion_Charm", "fandom": "Fire_Scorpion_Charm"},
            {"fex": "/Flamedrake+Talisman", "wikigg": "/Flamedrake_Talisman", "fandom": "Flamedrake_Talisman"},
            {"fex": "/Flock's+Canvas+Talisman", "wikigg": "/Flock%27s_Canvas_Talisman", "fandom": "Flock%27s_Canvas_Talisman"},
            {"fex": "/Furled+Finger+Remedy", "wikigg": "/Furled_Finger_Remedy", "fandom": "Furled_Finger_Remedy"},
            {"fex": "/Goldmask's+Rags", "wikigg": "/Goldmask%27s_Rags", "fandom": "Goldmask%27s_Rags"},
            {"fex": "/Greatjar+Arsenal+Charm", "wikigg": "/Greatjar_Arsenal_Charm", "fandom": "Greatjar_Arsenal_Charm"},
            {"fex": "/Green+Turtle+Talisman", "wikigg": "/Green_Turtle_Talisman", "fandom": "Green_Turtle_Talisman"},
            {"fex": "/Grub-Leaf+Talisman", "wikigg": "/Grub-Leaf_Talisman", "fandom": "Grub-Leaf_Talisman"},
            {"fex": "/Haligdrake+Talisman", "wikigg": "/Haligdrake_Talisman", "fandom": "Haligdrake_Talisman"},
            {"fex": "/Hammer+Talisman", "wikigg": "/Hammer_Talisman", "fandom": "Hammer_Talisman"},
            {"fex": "/Lance+Talisman", "wikigg": "/Lance_Talisman", "fandom": "Lance_Talisman"},
            {"fex": "/Lightning+Scorpion+Charm", "wikigg": "/Lightning_Scorpion_Charm", "fandom": "Lightning_Scorpion_Charm"},
            {"fex": "/Magic+Scorpion+Charm", "wikigg": "/Magic_Scorpion_Charm", "fandom": "Magic_Scorpion_Charm"},
            {"fex": "/Marika's+Scarseal", "wikigg": "/Marika%27s_Scarseal", "fandom": "Marika%27s_Scarseal"},
            {"fex": "/Millicent's+Prosthesis", "wikigg": "/Millicent%27s_Prosthesis", "fandom": "Millicent%27s_Prosthesis"},
            {"fex": "/Rotten+Winged+Sword+Insignia", "wikigg": "/Rotten_Winged_Sword_Insignia", "fandom": "Rotten_Winged_Sword_Insignia"},
            {"fex": "/Sacred+Scorpion+Charm", "wikigg": "/Sacred_Scorpion_Charm", "fandom": "Sacred_Scorpion_Charm"},
            {"fex": "/Stalwart+Horn+Charm", "wikigg": "/Stalwart_Horn_Charm", "fandom": "Stalwart_Horn_Charm"},
            {"fex": "/Starscourge+Heirloom", "wikigg": "/Starscourge_Heirloom", "fandom": "Starscourge_Heirloom"},
            {"fex": "/Warrior+Jar+Shard", "wikigg": "/Warrior_Jar_Shard", "fandom": "Warrior_Jar_Shard"},
            {"fex": "/Winged+Sword+Insignia", "wikigg": "/Winged_Sword_Insignia", "fandom": "Winged_Sword_Insignia"},
            {"fex": "/Viridian+Amber+Medallion", "wikigg": "/Viridian_Amber_Medallion", "fandom": "Viridian_Amber_Medallion"},
        ]
    },

    # ----------------------------------------------------------
    # ITEMS — expanded to ~50+ key items
    # ----------------------------------------------------------
    "items": {
        "category": "item",
        "entries": [
            # Original set
            {"fex": "/Elden+Ring+item", "wikigg": "/Elden_Ring_(item)", "fandom": "Elden_Ring_(item)"},
            {"fex": "/Rune+of+Death+item", "wikigg": "/Rune_of_Death", "fandom": "Rune_of_Death"},
            {"fex": "/Golden+Needle", "wikigg": "/Golden_Needle", "fandom": "Golden_Needle"},
            {"fex": "/Miquella's+Needle", "wikigg": "/Miquella%27s_Needle", "fandom": "Miquella%27s_Needle"},
            {"fex": "/Cursemark+of+Death", "wikigg": "/Cursemark_of_Death", "fandom": "Cursemark_of_Death"},
            {"fex": "/Amber+Starlight", "wikigg": "/Amber_Starlight", "fandom": "Amber_Starlight"},
            {"fex": "/Fingerslayer+Blade", "wikigg": "/Fingerslayer_Blade", "fandom": "Fingerslayer_Blade"},
            {"fex": "/Celestial+Dew", "wikigg": "/Celestial_Dew", "fandom": "Celestial_Dew"},
            {"fex": "/Deathroot", "wikigg": "/Deathroot", "fandom": "Deathroot"},
            {"fex": "/Seedbed+Curse", "wikigg": "/Seedbed_Curse", "fandom": "Seedbed_Curse"},
            {"fex": "/Frenzied+Flame+Seal", "wikigg": "/Frenzied_Flame_Seal", "fandom": "Frenzied_Flame_Seal"},
            {"fex": "/Golden+Order+Seal", "wikigg": "/Golden_Order_Seal", "fandom": "Golden_Order_Seal"},
            {"fex": "/Haligtree+Medallion", "wikigg": "/Haligtree_Medallion", "fandom": "Haligtree_Medallion"},
            {"fex": "/Dectus+Medallion", "wikigg": "/Dectus_Medallion", "fandom": "Dectus_Medallion"},
            {"fex": "/Pouch+of+Ruin", "wikigg": "/Pouch_of_Ruin", "fandom": "Pouch_of_Ruin"},
            {"fex": "/Shabriri's+Woe", "wikigg": "/Shabriri%27s_Woe", "fandom": "Shabriri%27s_Woe"},
            {"fex": "/Seluvis's+Potion", "wikigg": "/Seluvis%27s_Potion", "fandom": "Seluvis%27s_Potion"},
            {"fex": "/Fia's+Mist", "wikigg": "/Fia%27s_Mist", "fandom": "Fia%27s_Mist"},
            # Expanded key items
            {"fex": "/Flask+of+Crimson+Tears", "wikigg": "/Flask_of_Crimson_Tears", "fandom": "Flask_of_Crimson_Tears"},
            {"fex": "/Flask+of+Cerulean+Tears", "wikigg": "/Flask_of_Cerulean_Tears", "fandom": "Flask_of_Cerulean_Tears"},
            {"fex": "/Flask+of+Wondrous+Physick", "wikigg": "/Flask_of_Wondrous_Physick", "fandom": "Flask_of_Wondrous_Physick"},
            {"fex": "/Tarnished's+Furled+Finger", "wikigg": "/Tarnished%27s_Furled_Finger", "fandom": "Tarnished%27s_Furled_Finger"},
            {"fex": "/Phantom+Bloody+Finger", "wikigg": "/Phantom_Bloody_Finger", "fandom": "Phantom_Bloody_Finger"},
            {"fex": "/Bloody+Finger", "wikigg": "/Bloody_Finger", "fandom": "Bloody_Finger"},
            {"fex": "/Festering+Bloody+Finger", "wikigg": "/Festering_Bloody_Finger", "fandom": "Festering_Bloody_Finger"},
            {"fex": "/Furlcalling+Finger+Remedy", "wikigg": "/Furlcalling_Finger_Remedy", "fandom": "Furlcalling_Finger_Remedy"},
            {"fex": "/Soreseal", "wikigg": "/Soreseal", "fandom": "Soreseal"},
            {"fex": "/Rold+Medallion", "wikigg": "/Rold_Medallion", "fandom": "Rold_Medallion"},
            {"fex": "/Dark+Moon+Ring", "wikigg": "/Dark_Moon_Ring", "fandom": "Dark_Moon_Ring"},
            {"fex": "/Stonesword+Key", "wikigg": "/Stonesword_Key", "fandom": "Stonesword_Key"},
            {"fex": "/Spiritspring+Key", "wikigg": "/Spiritspring_Key", "fandom": "Spiritspring_Key"},
            {"fex": "/Smithing+Stone", "wikigg": "/Smithing_Stone", "fandom": "Smithing_Stone"},
            {"fex": "/Glovewort", "wikigg": "/Ghost_Glovewort", "fandom": "Ghost_Glovewort"},
            {"fex": "/Starlight+Shards", "wikigg": "/Starlight_Shards", "fandom": "Starlight_Shards"},
            {"fex": "/Golden+Rune", "wikigg": "/Golden_Rune", "fandom": "Golden_Rune"},
            # DLC key items
            {"fex": "/Scadutree+Fragment", "wikigg": "/Scadutree_Fragment", "fandom": "Scadutree_Fragment"},
            {"fex": "/Map+of+the+Land+of+Shadow", "wikigg": "/Map_of_the_Land_of_Shadow", "fandom": "Map_of_the_Land_of_Shadow"},
            {"fex": "/Needle+of+Eternal+Darkness", "wikigg": "/Needle_of_Eternal_Darkness", "fandom": "Needle_of_Eternal_Darkness"},
            {"fex": "/Revered+Spirit+Ash", "wikigg": "/Revered_Spirit_Ash", "fandom": "Revered_Spirit_Ash"},
        ]
    },

    # ----------------------------------------------------------
    # WHETBLADES — 6 smithing lineage items
    # ----------------------------------------------------------
    "whetblades": {
        "category": "whetblade",
        "entries": [
            {"fex": "/Iron+Whetblade", "wikigg": "/Iron_Whetblade", "fandom": "Iron_Whetblade"},
            {"fex": "/Sanctified+Whetblade", "wikigg": "/Sanctified_Whetblade", "fandom": "Sanctified_Whetblade"},
            {"fex": "/Glintstone+Whetblade", "wikigg": "/Glintstone_Whetblade", "fandom": "Glintstone_Whetblade"},
            {"fex": "/Red-Hot+Whetblade", "wikigg": "/Red-Hot_Whetblade", "fandom": "Red-Hot_Whetblade"},
            {"fex": "/Somber+Smithing+Stone+Whetblade", "wikigg": "/Somber+Smithing+Stone+Whetblade", "fandom": "Blacksmith%27s_Whetblade"},
            {"fex": "/Black+Whetblade", "wikigg": "/Black_Whetblade", "fandom": "Black_Whetblade"},
        ]
    },

    # ----------------------------------------------------------
    # BELL BEARINGS — ~30 items (merchant/NPC lore)
    # ----------------------------------------------------------
    "bell_bearings": {
        "category": "bell_bearing",
        "entries": [
            {"fex": "/Bell+Bearings", "wikigg": "/Bell_Bearings", "fandom": "Bell_Bearings"},
            {"fex": "/Smithing-Stone+Miner's+Bell+Bearing+1", "wikigg": "/Smithing-Stone_Miner%27s_Bell_Bearing", "fandom": "Smithing-Stone_Miner%27s_Bell_Bearing_(1)"},
            {"fex": "/Smithing-Stone+Miner's+Bell+Bearing+2", "wikigg": "/Smithing-Stone_Miner%27s_Bell_Bearing_(2)", "fandom": "Smithing-Stone_Miner%27s_Bell_Bearing_(2)"},
            {"fex": "/Somber+Smithing+Stone+Miner's+Bell+Bearing+1", "wikigg": "/Somber_Smithing-Stone_Miner%27s_Bell_Bearing_(1)", "fandom": "Somber_Smithing-Stone_Miner%27s_Bell_Bearing_(1)"},
            {"fex": "/Glovewort+Picker's+Bell+Bearing+1", "wikigg": "/Glovewort_Picker%27s_Bell_Bearing_(1)", "fandom": "Glovewort_Picker%27s_Bell_Bearing_(1)"},
            {"fex": "/Ghost-Glovewort+Picker's+Bell+Bearing+1", "wikigg": "/Ghost-Glovewort_Picker%27s_Bell_Bearing_(1)", "fandom": "Ghost-Glovewort_Picker%27s_Bell_Bearing_(1)"},
            {"fex": "/Gravity+Stone+Peddler's+Bell+Bearing", "wikigg": "/Gravity_Stone_Peddler%27s_Bell_Bearing", "fandom": "Gravity_Stone_Peddler%27s_Bell_Bearing"},
            {"fex": "/Meat+Peddler's+Bell+Bearing", "wikigg": "/Meat_Peddler%27s_Bell_Bearing", "fandom": "Meat_Peddler%27s_Bell_Bearing"},
            {"fex": "/Medicine+Peddler's+Bell+Bearing", "wikigg": "/Medicine_Peddler%27s_Bell_Bearing", "fandom": "Medicine_Peddler%27s_Bell_Bearing"},
            {"fex": "/Artisan's+Cookbook+Bell+Bearing", "wikigg": "/Artisan%27s_Cookbook", "fandom": "Artisan%27s_Cookbook_(1)"},
            {"fex": "/Nomadic+Merchant's+Bell+Bearing+1", "wikigg": "/Nomadic_Merchant%27s_Bell_Bearing_(1)", "fandom": "Nomadic_Merchant%27s_Bell_Bearing_(1)"},
            {"fex": "/Isolated+Merchant's+Bell+Bearing", "wikigg": "/Isolated_Merchant%27s_Bell_Bearing", "fandom": "Isolated_Merchant%27s_Bell_Bearing"},
            {"fex": "/Twin+Maiden+Husks+Bell+Bearing", "wikigg": "/Twin_Maiden_Husks", "fandom": "Twin_Maiden_Husks"},
        ]
    },

    # ----------------------------------------------------------
    # CRYSTAL TEARS — ~30 physick tears
    # ----------------------------------------------------------
    "crystal_tears": {
        "category": "crystal_tear",
        "entries": [
            {"fex": "/Crystal+Tears", "wikigg": "/Crystal_Tears", "fandom": "Crystal_Tears"},
            {"fex": "/Crimson+Crystal+Tear", "wikigg": "/Crimson_Crystal_Tear", "fandom": "Crimson_Crystal_Tear"},
            {"fex": "/Cerulean+Crystal+Tear", "wikigg": "/Cerulean_Crystal_Tear", "fandom": "Cerulean_Crystal_Tear"},
            {"fex": "/Crimsonburst+Crystal+Tear", "wikigg": "/Crimsonburst_Crystal_Tear", "fandom": "Crimsonburst_Crystal_Tear"},
            {"fex": "/Cerulean+Hidden+Tear", "wikigg": "/Cerulean_Hidden_Tear", "fandom": "Cerulean_Hidden_Tear"},
            {"fex": "/Stonebarb+Cracked+Tear", "wikigg": "/Stonebarb_Cracked_Tear", "fandom": "Stonebarb_Cracked_Tear"},
            {"fex": "/Spiked+Cracked+Tear", "wikigg": "/Spiked_Cracked_Tear", "fandom": "Spiked_Cracked_Tear"},
            {"fex": "/Strength-Knot+Crystal+Tear", "wikigg": "/Strength-Knot_Crystal_Tear", "fandom": "Strength-Knot_Crystal_Tear"},
            {"fex": "/Dexterity-Knot+Crystal+Tear", "wikigg": "/Dexterity-Knot_Crystal_Tear", "fandom": "Dexterity-Knot_Crystal_Tear"},
            {"fex": "/Intelligence-Knot+Crystal+Tear", "wikigg": "/Intelligence-Knot_Crystal_Tear", "fandom": "Intelligence-Knot_Crystal_Tear"},
            {"fex": "/Faith-Knot+Crystal+Tear", "wikigg": "/Faith-Knot_Crystal_Tear", "fandom": "Faith-Knot_Crystal_Tear"},
            {"fex": "/Opaline+Bubbletear", "wikigg": "/Opaline_Bubbletear", "fandom": "Opaline_Bubbletear"},
            {"fex": "/Magic+-shrouding+Cracked+Tear", "wikigg": "/Magic-shrouding_Cracked_Tear", "fandom": "Magic-shrouding_Cracked_Tear"},
            {"fex": "/Fire-shrouding+Cracked+Tear", "wikigg": "/Fire-shrouding_Cracked_Tear", "fandom": "Fire-shrouding_Cracked_Tear"},
            {"fex": "/Lightning-shrouding+Cracked+Tear", "wikigg": "/Lightning-shrouding_Cracked_Tear", "fandom": "Lightning-shrouding_Cracked_Tear"},
            {"fex": "/Holy-shrouding+Cracked+Tear", "wikigg": "/Holy-shrouding_Cracked_Tear", "fandom": "Holy-shrouding_Cracked_Tear"},
            {"fex": "/Opaline+Hardtear", "wikigg": "/Opaline_Hardtear", "fandom": "Opaline_Hardtear"},
            {"fex": "/Crimson+Bubbletear", "wikigg": "/Crimson_Bubbletear", "fandom": "Crimson_Bubbletear"},
            {"fex": "/Winged+Crystal+Tear", "wikigg": "/Winged_Crystal_Tear", "fandom": "Winged_Crystal_Tear"},
            {"fex": "/Twiggy+Cracked+Tear", "wikigg": "/Twiggy_Cracked_Tear", "fandom": "Twiggy_Cracked_Tear"},
            {"fex": "/Leaden+Hardtear", "wikigg": "/Leaden_Hardtear", "fandom": "Leaden_Hardtear"},
            {"fex": "/Bloodsucking+Cracked+Tear", "wikigg": "/Bloodsucking_Cracked_Tear", "fandom": "Bloodsucking_Cracked_Tear"},
            {"fex": "/Ruptured+Crystal+Tear", "wikigg": "/Ruptured_Crystal_Tear", "fandom": "Ruptured_Crystal_Tear"},
            {"fex": "/Thorny+Cracked+Tear", "wikigg": "/Thorny_Cracked_Tear", "fandom": "Thorny_Cracked_Tear"},
            {"fex": "/Speckled+Hardtear", "wikigg": "/Speckled_Hardtear", "fandom": "Speckled_Hardtear"},
            {"fex": "/Crimsonspill+Crystal+Tear", "wikigg": "/Crimsonspill_Crystal_Tear", "fandom": "Crimsonspill_Crystal_Tear"},
            {"fex": "/Flame-Shrouding+Cracked+Tear", "wikigg": "/Flame-Shrouding_Cracked_Tear", "fandom": "Flame-Shrouding_Cracked_Tear"},
            {"fex": "/Purifying+Crystal+Tear", "wikigg": "/Purifying_Crystal_Tear", "fandom": "Purifying_Crystal_Tear"},
        ]
    },

    # ----------------------------------------------------------
    # COOKBOOKS — ~30 crafting books
    # ----------------------------------------------------------
    "cookbooks": {
        "category": "cookbook",
        "entries": [
            {"fex": "/Crafting+Cookbooks", "wikigg": "/Crafting", "fandom": "Cookbooks"},
            {"fex": "/Armorer's+Cookbook+1", "wikigg": "/Armorer%27s_Cookbook_(1)", "fandom": "Armorer%27s_Cookbook_(1)"},
            {"fex": "/Armorer's+Cookbook+2", "wikigg": "/Armorer%27s_Cookbook_(2)", "fandom": "Armorer%27s_Cookbook_(2)"},
            {"fex": "/Armorer's+Cookbook+3", "wikigg": "/Armorer%27s_Cookbook_(3)", "fandom": "Armorer%27s_Cookbook_(3)"},
            {"fex": "/Armorer's+Cookbook+4", "wikigg": "/Armorer%27s_Cookbook_(4)", "fandom": "Armorer%27s_Cookbook_(4)"},
            {"fex": "/Armorer's+Cookbook+5", "wikigg": "/Armorer%27s_Cookbook_(5)", "fandom": "Armorer%27s_Cookbook_(5)"},
            {"fex": "/Armorer's+Cookbook+6", "wikigg": "/Armorer%27s_Cookbook_(6)", "fandom": "Armorer%27s_Cookbook_(6)"},
            {"fex": "/Missionary's+Cookbook+1", "wikigg": "/Missionary%27s_Cookbook_(1)", "fandom": "Missionary%27s_Cookbook_(1)"},
            {"fex": "/Missionary's+Cookbook+2", "wikigg": "/Missionary%27s_Cookbook_(2)", "fandom": "Missionary%27s_Cookbook_(2)"},
            {"fex": "/Missionary's+Cookbook+3", "wikigg": "/Missionary%27s_Cookbook_(3)", "fandom": "Missionary%27s_Cookbook_(3)"},
            {"fex": "/Missionary's+Cookbook+4", "wikigg": "/Missionary%27s_Cookbook_(4)", "fandom": "Missionary%27s_Cookbook_(4)"},
            {"fex": "/Nomadic+Warrior's+Cookbook+1", "wikigg": "/Nomadic_Warrior%27s_Cookbook_(1)", "fandom": "Nomadic_Warrior%27s_Cookbook_(1)"},
            {"fex": "/Nomadic+Warrior's+Cookbook+2", "wikigg": "/Nomadic_Warrior%27s_Cookbook_(2)", "fandom": "Nomadic_Warrior%27s_Cookbook_(2)"},
            {"fex": "/Nomadic+Warrior's+Cookbook+3", "wikigg": "/Nomadic_Warrior%27s_Cookbook_(3)", "fandom": "Nomadic_Warrior%27s_Cookbook_(3)"},
            {"fex": "/Nomadic+Warrior's+Cookbook+4", "wikigg": "/Nomadic_Warrior%27s_Cookbook_(4)", "fandom": "Nomadic_Warrior%27s_Cookbook_(4)"},
            {"fex": "/Nomadic+Warrior's+Cookbook+5", "wikigg": "/Nomadic_Warrior%27s_Cookbook_(5)", "fandom": "Nomadic_Warrior%27s_Cookbook_(5)"},
            {"fex": "/Forager+Brood+Cookbook+1", "wikigg": "/Forager_Brood_Cookbook_(1)", "fandom": "Forager_Brood_Cookbook_(1)"},
            {"fex": "/Forager+Brood+Cookbook+2", "wikigg": "/Forager_Brood_Cookbook_(2)", "fandom": "Forager_Brood_Cookbook_(2)"},
            {"fex": "/Fevor's+Cookbook+1", "wikigg": "/Fevor%27s_Cookbook_(1)", "fandom": "Fevor%27s_Cookbook_(1)"},
            {"fex": "/Fevor's+Cookbook+2", "wikigg": "/Fevor%27s_Cookbook_(2)", "fandom": "Fevor%27s_Cookbook_(2)"},
            {"fex": "/Fevor's+Cookbook+3", "wikigg": "/Fevor%27s_Cookbook_(3)", "fandom": "Fevor%27s_Cookbook_(3)"},
            {"fex": "/Glintstone+Craftsman's+Cookbook+1", "wikigg": "/Glintstone_Craftsman%27s_Cookbook_(1)", "fandom": "Glintstone_Craftsman%27s_Cookbook_(1)"},
            {"fex": "/Ancient+Dragon+Apostle's+Cookbook+1", "wikigg": "/Ancient_Dragon_Apostle%27s_Cookbook_(1)", "fandom": "Ancient_Dragon_Apostle%27s_Cookbook_(1)"},
            {"fex": "/Perfumer's+Cookbook+1", "wikigg": "/Perfumer%27s_Cookbook_(1)", "fandom": "Perfumer%27s_Cookbook_(1)"},
            {"fex": "/Perfumer's+Cookbook+2", "wikigg": "/Perfumer%27s_Cookbook_(2)", "fandom": "Perfumer%27s_Cookbook_(2)"},
            {"fex": "/Artisan's+Cookbook+1", "wikigg": "/Artisan%27s_Cookbook_(1)", "fandom": "Artisan%27s_Cookbook_(1)"},
        ]
    },

    # ----------------------------------------------------------
    # PAINTINGS — 7 painting items + solutions
    # ----------------------------------------------------------
    "paintings": {
        "category": "painting",
        "entries": [
            {"fex": "/Paintings", "wikigg": "/Paintings", "fandom": "Paintings"},
            {"fex": "/Homing+Instinct+Painting", "wikigg": "/Homing_Instinct_Painting", "fandom": "Homing_Instinct_Painting"},
            {"fex": "/Resurrection+Painting", "wikigg": "/Resurrection_Painting", "fandom": "Resurrection_Painting"},
            {"fex": "/Redmane+Painting", "wikigg": "/Redmane_Painting", "fandom": "Redmane_Painting"},
            {"fex": "/Champion's+Song+Painting", "wikigg": "/Champion%27s_Song_Painting", "fandom": "Champion%27s_Song_Painting"},
            {"fex": "/Flightless+Bird+Painting", "wikigg": "/Flightless_Bird_Painting", "fandom": "Flightless_Bird_Painting"},
            {"fex": "/Prophecy+Painting", "wikigg": "/Prophecy_Painting", "fandom": "Prophecy_Painting"},
            {"fex": "/若人達のためのゲーム絵画", "wikigg": "/Painting_Solution", "fandom": "Painting_Solutions"},
        ]
    },

    # ----------------------------------------------------------
    # CREATURES — enemies with lore significance
    # ----------------------------------------------------------
    "creatures": {
        "category": "creature",
        "entries": [
            {"fex": "/Erdtree+Burial+Watchdog", "wikigg": "/Erdtree_Burial_Watchdog", "fandom": "Erdtree_Burial_Watchdog"},
            {"fex": "/Grafted+Scion", "wikigg": "/Grafted_Scion", "fandom": "Grafted_Scion"},
            {"fex": "/Misbegotten", "wikigg": "/Misbegotten", "fandom": "Misbegotten"},
            {"fex": "/Omenkiller", "wikigg": "/Omenkiller", "fandom": "Omenkiller"},
            {"fex": "/Golem", "wikigg": "/Golem", "fandom": "Golem"},
            {"fex": "/Revenant", "wikigg": "/Revenant", "fandom": "Revenant"},
            {"fex": "/Troll", "wikigg": "/Troll", "fandom": "Troll"},
            {"fex": "/Dragon", "wikigg": "/Dragon", "fandom": "Dragon"},
            {"fex": "/Wyrm", "wikigg": "/Wyrm", "fandom": "Wyrm"},
            {"fex": "/Fingercreeper", "wikigg": "/Fingercreeper", "fandom": "Fingercreeper"},
            {"fex": "/Living+Jar", "wikigg": "/Living_Jar", "fandom": "Living_Jar"},
            {"fex": "/Bloodhound+Knight", "wikigg": "/Bloodhound_Knight", "fandom": "Bloodhound_Knight"},
            {"fex": "/Crystallian", "wikigg": "/Crystallian", "fandom": "Crystallian"},
            {"fex": "/Kindred+of+Rot", "wikigg": "/Kindred_of_Rot", "fandom": "Kindred_of_Rot"},
            {"fex": "/Cleanrot+Knight", "wikigg": "/Cleanrot_Knight", "fandom": "Cleanrot_Knight"},
            {"fex": "/Miranda+Flower", "wikigg": "/Miranda_Flower", "fandom": "Miranda_Flower"},
            {"fex": "/Basilisk", "wikigg": "/Basilisk", "fandom": "Basilisk"},
            {"fex": "/Albinauric", "wikigg": "/Albinauric", "fandom": "Albinauric"},
            {"fex": "/Demi-Human", "wikigg": "/Demi-Human", "fandom": "Demi-Human"},
            {"fex": "/Runebear", "wikigg": "/Runebear", "fandom": "Runebear"},
            {"fex": "/Crucible+Knight+creature", "wikigg": "/Crucible_Knight", "fandom": "Crucible_Knight"},
            {"fex": "/Night+Cavalry+creature", "wikigg": "/Night_Cavalry", "fandom": "Night_Cavalry"},
            {"fex": "/Gargoyle", "wikigg": "/Gargoyle", "fandom": "Gargoyle"},
            {"fex": "/Jellyfish", "wikigg": "/Jellyfish", "fandom": "Jellyfish"},
            {"fex": "/Giant+Dog", "wikigg": "/Giant_Dog", "fandom": "Giant_Dog"},
            {"fex": "/Teardrop+Scarab", "wikigg": "/Teardrop_Scarab", "fandom": "Teardrop_Scarab"},
            {"fex": "/Bat", "wikigg": "/Bat", "fandom": "Bat"},
            {"fex": "/Giant+Crow", "wikigg": "/Giant_Crow", "fandom": "Giant_Crow"},
            {"fex": "/Deathbird", "wikigg": "/Deathbird", "fandom": "Deathbird"},
            {"fex": "/Nox+creature", "wikigg": "/Nox", "fandom": "Nox"},
            {"fex": "/Graven+Mass", "wikigg": "/Graven_Mass", "fandom": "Graven_Mass"},
            {"fex": "/Miranda+Sprout", "wikigg": "/Miranda_Sprout", "fandom": "Miranda_Sprout"},
            {"fex": "/Ghostly+Noble", "wikigg": "/Ghostly_Noble", "fandom": "Ghostly_Noble"},
            # DLC creatures
            {"fex": "/Furnace+Golem+creature", "wikigg": "/Furnace_Golem", "fandom": "Furnace_Golem"},
            {"fex": "/Horned+Warrior", "wikigg": "/Horned_Warrior", "fandom": "Horned_Warrior"},
        ]
    },

    # ----------------------------------------------------------
    # QUESTLINES — ~20 major questlines as topics
    # ----------------------------------------------------------
    "questlines": {
        "category": "questline",
        "entries": [
            {"fex": "/Ranni+the+Witch+Quest", "wikigg": "/Ranni_the_Witch", "fandom": "Ranni_the_Witch"},
            {"fex": "/Millicent+Quest", "wikigg": "/Millicent", "fandom": "Millicent"},
            {"fex": "/Fia+Quest", "wikigg": "/Fia", "fandom": "Fia"},
            {"fex": "/Dung+Eater+Quest", "wikigg": "/Dung_Eater", "fandom": "Dung_Eater"},
            {"fex": "/Iron+Fist+Alexander+Quest", "wikigg": "/Alexander", "fandom": "Iron_Fist_Alexander"},
            {"fex": "/White+Mask+Varre+Quest", "wikigg": "/White_Mask_Varre", "fandom": "White_Mask_Varre"},
            {"fex": "/Patches+Quest", "wikigg": "/Patches", "fandom": "Patches"},
            {"fex": "/Brother+Corhyn+and+Goldmask+Quest", "wikigg": "/Brother_Corhyn", "fandom": "Brother_Corhyn"},
            {"fex": "/Diallos+Quest", "wikigg": "/Diallos", "fandom": "Diallos"},
            {"fex": "/Sellen+Quest", "wikigg": "/Sellen", "fandom": "Sellen"},
            {"fex": "/Rya+Quest", "wikigg": "/Rya", "fandom": "Rya"},
            {"fex": "/Hyetta+Quest", "wikigg": "/Hyetta", "fandom": "Hyetta"},
            {"fex": "/Boc+the+Seamster+Quest", "wikigg": "/Boc_the_Seamster", "fandom": "Boc_the_Seamster"},
            {"fex": "/Gowry+and+Millicent+Quest", "wikigg": "/Gowry", "fandom": "Gowry"},
            {"fex": "/Kenneth+Haight+Quest", "wikigg": "/Kenneth_Haight", "fandom": "Kenneth_Haight"},
            {"fex": "/Edgar+and+Irina+Quest", "wikigg": "/Edgar", "fandom": "Edgar"},
            {"fex": "/Volcano+Manor+Quest", "wikigg": "/Volcano_Manor", "fandom": "Volcano_Manor"},
            {"fex": "/Nepheli+Loux+Quest", "wikigg": "/Nepheli_Loux", "fandom": "Nepheli_Loux"},
            {"fex": "/D+Hunter+of+the+Dead+Quest", "wikigg": "/D,_Hunter_of_the_Dead", "fandom": "D,_Hunter_of_the_Dead"},
            {"fex": "/Gurranq+Quest", "wikigg": "/Gurranq,_Beast_Clergyman", "fandom": "Gurranq,_Beast_Clergyman"},
            # DLC questlines
            {"fex": "/Needle+Knight+Leda+Quest", "wikigg": "/Needle_Knight_Leda", "fandom": "Needle_Knight_Leda"},
            {"fex": "/Thiollier+Quest", "wikigg": "/Thiollier", "fandom": "Thiollier"},
            {"fex": "/Igon+Quest", "wikigg": "/Igon", "fandom": "Igon"},
            {"fex": "/Sir+Ansbach+Quest", "wikigg": "/Sir_Ansbach", "fandom": "Sir_Ansbach"},
            {"fex": "/Count+Ymir+Quest", "wikigg": "/Count_Ymir", "fandom": "Count_Ymir"},
        ]
    },

    # ----------------------------------------------------------
    # ENDINGS — all 6 base + DLC endings
    # ----------------------------------------------------------
    "endings": {
        "category": "ending",
        "entries": [
            {"fex": "/Endings", "wikigg": "/Endings", "fandom": "Endings"},
            {"fex": "/Age+of+Fracture+Ending", "wikigg": "/Age_of_Fracture", "fandom": "Age_of_Fracture"},
            {"fex": "/Age+of+Stars+Ending", "wikigg": "/Age_of_Stars", "fandom": "Age_of_Stars"},
            {"fex": "/Lord+of+the+Frenzied+Flame+Ending", "wikigg": "/Lord_of_the_Frenzied_Flame", "fandom": "Lord_of_the_Frenzied_Flame"},
            {"fex": "/Age+of+Order+Ending", "wikigg": "/Age_of_Order", "fandom": "Age_of_Order"},
            {"fex": "/Blessing+of+Despair+Ending", "wikigg": "/Blessing_of_Despair", "fandom": "Blessing_of_Despair"},
            {"fex": "/Age+of+Duskborn+Ending", "wikigg": "/Age_of_the_Duskborn", "fandom": "Age_of_the_Duskborn"},
            {"fex": "/Miquella's+Needle+DLC+Ending", "wikigg": "/Miquella%27s_Needle", "fandom": "Miquella%27s_Needle"},
        ]
    },

    # ----------------------------------------------------------
    # DIALOGUE — NPC dialogue transcript pages
    # ----------------------------------------------------------
    "dialogue": {
        "category": "dialogue",
        "entries": [
            {"fex": "/Melina+Dialogue", "wikigg": "/Melina", "fandom": "Melina"},
            {"fex": "/Ranni+the+Witch+Dialogue", "wikigg": "/Ranni_the_Witch", "fandom": "Ranni_the_Witch"},
            {"fex": "/Blaidd+Dialogue", "wikigg": "/Blaidd", "fandom": "Blaidd"},
            {"fex": "/Fia+Dialogue", "wikigg": "/Fia", "fandom": "Fia"},
            {"fex": "/Rogier+Dialogue", "wikigg": "/Rogier", "fandom": "Rogier"},
            {"fex": "/Patches+Dialogue", "wikigg": "/Patches", "fandom": "Patches"},
            {"fex": "/Gideon+Ofnir+Dialogue", "wikigg": "/Gideon_Ofnir", "fandom": "Gideon_Ofnir"},
            {"fex": "/Seluvis+Dialogue", "wikigg": "/Seluvis", "fandom": "Seluvis"},
            {"fex": "/Morgott+the+Omen+King+Dialogue", "wikigg": "/Morgott,_the_Omen_King", "fandom": "Morgott,_the_Omen_King"},
            {"fex": "/Maliketh+the+Black+Blade+Dialogue", "wikigg": "/Maliketh,_the_Black_Blade", "fandom": "Maliketh,_the_Black_Blade"},
            {"fex": "/Godfrey+Dialogue", "wikigg": "/Godfrey,_First_Elden_Lord", "fandom": "Godfrey,_First_Elden_Lord"},
            {"fex": "/Radahn+Dialogue", "wikigg": "/Starscourge_Radahn", "fandom": "Starscourge_Radahn"},
            {"fex": "/Rykard+Dialogue", "wikigg": "/Rykard,_Lord_of_Blasphemy", "fandom": "Rykard,_Lord_of_Blasphemy"},
            {"fex": "/Malenia+Dialogue", "wikigg": "/Malenia,_Blade_of_Miquella", "fandom": "Malenia,_Blade_of_Miquella"},
            {"fex": "/Mohg+Dialogue", "wikigg": "/Mohg,_Lord_of_Blood", "fandom": "Mohg,_Lord_of_Blood"},
            {"fex": "/Messmer+Dialogue", "wikigg": "/Messmer_the_Impaler", "fandom": "Messmer_the_Impaler"},
            {"fex": "/Leda+Dialogue", "wikigg": "/Needle_Knight_Leda", "fandom": "Needle_Knight_Leda"},
            {"fex": "/Miquella+Dialogue", "wikigg": "/Miquella", "fandom": "Miquella"},
            {"fex": "/Ansbach+Dialogue", "wikigg": "/Sir_Ansbach", "fandom": "Sir_Ansbach"},
            {"fex": "/Margit+Dialogue", "wikigg": "/Margit_the_Fell_Omen", "fandom": "Margit,_the_Fell_Omen"},
        ]
    },

    # ----------------------------------------------------------
    # CUTSCENES — ~30 major cutscene pages
    # ----------------------------------------------------------
    "cutscenes": {
        "category": "cutscene",
        "entries": [
            {"fex": "/Cutscenes", "wikigg": "/Cutscenes", "fandom": "Cutscenes"},
            {"fex": "/Elden+Ring+Opening+Cutscene", "wikigg": "/Opening_Cutscene", "fandom": "Opening"},
            {"fex": "/Godrick+the+Grafted+Cutscene", "wikigg": "/Godrick_the_Grafted", "fandom": "Godrick_the_Grafted"},
            {"fex": "/Rennala+Cutscene", "wikigg": "/Rennala,_Queen_of_the_Full_Moon", "fandom": "Rennala,_Queen_of_the_Full_Moon"},
            {"fex": "/Radahn+Cutscene", "wikigg": "/Starscourge_Radahn", "fandom": "Starscourge_Radahn"},
            {"fex": "/Morgott+Cutscene", "wikigg": "/Morgott,_the_Omen_King", "fandom": "Morgott,_the_Omen_King"},
            {"fex": "/Maliketh+Cutscene", "wikigg": "/Maliketh,_the_Black_Blade", "fandom": "Maliketh,_the_Black_Blade"},
            {"fex": "/Godfrey+Cutscene", "wikigg": "/Godfrey,_First_Elden_Lord", "fandom": "Godfrey,_First_Elden_Lord"},
            {"fex": "/Elden+Beast+Cutscene", "wikigg": "/Elden_Beast", "fandom": "Elden_Beast"},
            {"fex": "/Malenia+Cutscene", "wikigg": "/Malenia,_Blade_of_Miquella", "fandom": "Malenia,_Blade_of_Miquella"},
            {"fex": "/Melina+Rold+Medallion+Cutscene", "wikigg": "/Melina", "fandom": "Melina"},
            {"fex": "/Forge+of+the+Giants+Cutscene", "wikigg": "/Forge_of_the_Giants", "fandom": "Forge_of_the_Giants"},
            {"fex": "/Frenzied+Flame+Proscription+Cutscene", "wikigg": "/Frenzied_Flame_Proscription", "fandom": "Frenzied_Flame_Proscription"},
            {"fex": "/Ranni+Dark+Moon+Cutscene", "wikigg": "/Ranni_the_Witch", "fandom": "Ranni_the_Witch"},
            {"fex": "/Messmer+DLC+Cutscene", "wikigg": "/Messmer_the_Impaler", "fandom": "Messmer_the_Impaler"},
            {"fex": "/Miquella+DLC+Opening+Cutscene", "wikigg": "/Miquella", "fandom": "Miquella"},
            {"fex": "/Promised+Consort+Radahn+Cutscene", "wikigg": "/Promised_Consort_Radahn", "fandom": "Promised_Consort_Radahn"},
        ]
    },

    # ----------------------------------------------------------
    # CUT CONTENT — datamined / removed lore
    # ----------------------------------------------------------
    "cut_content": {
        "category": "cut_content",
        "entries": [
            {"fex": "/Cut+Content", "wikigg": "/Cut_Content", "fandom": "Cut_Content"},
            {"fex": "/Datamined+Lore", "wikigg": "/Datamined_Content", "fandom": "Datamined_Content"},
            {"fex": "/Cut+Bosses", "wikigg": "/Cut_Content", "fandom": "Cut_Content"},
            {"fex": "/Removed+NPCs", "wikigg": "/Cut_Content", "fandom": "Cut_Content"},
            {"fex": "/Abandoned+Cave+Lore", "wikigg": "/Abandoned_Cave", "fandom": "Abandoned_Cave"},
            {"fex": "/Flame+of+the+Fell+God+Cut+Content", "wikigg": "/Fell_God", "fandom": "Fell_God"},
            {"fex": "/Greater+Will+cut+content", "wikigg": "/Greater_Will", "fandom": "Greater_Will"},
        ]
    },
}


def main():
    os.makedirs("data/lore", exist_ok=True)

    total_entries = sum(len(v["entries"]) for v in SCRAPE_LIST.values())
    done = 0
    skipped = 0

    print(f"=== Scraping EVERYTHING: Fextralife + wiki.gg + Fandom ===")
    print(f"Total entries: {total_entries}\n")

    for file_key, data in SCRAPE_LIST.items():
        category = data["category"]
        entries = data["entries"]
        filepath = f"data/lore/{file_key}.txt"

        existing = load_existing_names(file_key)
        print(f"\n--- {file_key.upper()} ({len(entries)} entries, {len(existing)} already done) ---")

        for entry in entries:
            fex_path = entry.get("fex", "")
            wikigg_path = entry.get("wikigg", "")
            fandom_path = entry.get("fandom", "")

            title = None
            texts = []

            if fex_path:
                t, text = scrape_fextralife(fex_path)
                if t:
                    title = t
                if text:
                    texts.append(text)
                time.sleep(1.0)

            if wikigg_path:
                t, text = scrape_wikigg(wikigg_path)
                if t and not title:
                    title = t
                if text:
                    texts.append(text)
                time.sleep(1.0)

            if fandom_path:
                t, text = scrape_fandom(fandom_path)
                if t and not title:
                    title = t
                if text:
                    texts.append(text)
                time.sleep(1.0)

            if not title or not texts:
                print(f"  Skipped (no content): {fex_path}")
                continue

            if title in existing:
                print(f"  Skipping: {title} (already saved)")
                skipped += 1
                done += 1
                continue

            combined = combine_sources(texts)

            if not combined or len(combined) < 100:
                print(f"  No content: {title}")
                continue

            if category == "boss":
                area = get_entity_area(title, "boss")
            elif category == "character":
                area = get_entity_area(title, "character")
            elif category == "area":
                area = title
            else:
                area = "Limgrave"

            chapter_num = get_area_number(area)
            save_lore(category, title, area, chapter_num, combined, filepath)
            existing.add(title)
            done += 1
            print(f"  Saved: {title} ({len(combined)} chars from {len(texts)} sources)")

    print(f"\n=== Done! {done}/{total_entries} entries saved ({skipped} skipped) ===")
    print("Now run: python ingest.py")


if __name__ == "__main__":
    main()