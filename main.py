"""
main.py - Standalone Vedic Astrology Evaluation Engine
Includes Houses 1 to 12 rules, Parivarthana, and Neecha Bhanga Raja Yogas.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Set, Optional

app = FastAPI(title="Vedic Astrology Prediction Engine", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# ASTROLOGICAL REFERENCE DATA
# ---------------------------------------------------------------------------

SIGN_LORDS: Dict[int, str] = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon",
    5: "Sun", 6: "Mercury", 7: "Venus", 8: "Mars",
    9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"
}

# Sign where the planet gets exalted
EXALTATION_SIGNS: Dict[str, int] = {
    "Sun": 1, "Moon": 2, "Mars": 10, "Mercury": 6,
    "Jupiter": 4, "Venus": 12, "Saturn": 7, "Rahu": 2, "Ketu": 8
}

# Sign where the planet gets debilitated
DEBILITATION_SIGNS: Dict[str, int] = {
    "Sun": 7, "Moon": 8, "Mars": 4, "Mercury": 12,
    "Jupiter": 10, "Venus": 6, "Saturn": 1, "Rahu": 8, "Ketu": 2
}

# Planet that gets exalted in a given sign (1 to 12)
SIGN_EXALTED_PLANET: Dict[int, str] = {
    1: "Sun", 2: "Moon", 4: "Jupiter", 6: "Mercury",
    7: "Saturn", 10: "Mars", 12: "Venus"
}

BENEFICS: Set[str] = {"Jupiter", "Venus", "Mercury", "Moon"}
MALEFICS: Set[str] = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
MALE_PLANETS: Set[str] = {"Sun", "Mars", "Jupiter"}
FEMALE_PLANETS: Set[str] = {"Moon", "Venus"}
FEMALE_SIGNS: Set[int] = {2, 4, 6, 8, 10, 12}
CHARA_SIGNS: Set[int] = {1, 4, 7, 10}
STHIRA_SIGNS: Set[int] = {2, 5, 8, 11}

NATURAL_FRIENDS: Dict[str, Set[str]] = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
    "Rahu": {"Venus", "Saturn", "Mercury"},
    "Ketu": {"Mars", "Venus", "Jupiter"}
}


# ---------------------------------------------------------------------------
# API PAYLOAD SCHEMA
# ---------------------------------------------------------------------------

class ChartRequest(BaseModel):
    lagna_sign: int
    planet_houses: Dict[str, int]
    planet_signs: Dict[str, int]
    navamsa_planet_signs: Optional[Dict[str, int]] = None
    gender: Optional[str] = "male"
    is_full_moon: bool = False
    combust_planets: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def get_house_lords(lagna_sign: int) -> Dict[int, str]:
    return {h: SIGN_LORDS[((lagna_sign - 1 + (h - 1)) % 12) + 1] for h in range(1, 13)}


def check_parivarthana(h1: int, h2: int, lords: Dict[int, str], p_houses: Dict[str, int]) -> bool:
    l1, l2 = lords[h1], lords[h2]
    if l1 == l2:
        return False
    return p_houses.get(l1) == h2 and p_houses.get(l2) == h1


def get_aspecting_planets(target_house: int, p_houses: Dict[str, int]) -> List[str]:
    aspecting = []
    for p, pos in p_houses.items():
        if not pos:
            continue
        aspects = [(pos + 6 - 1) % 12 + 1]
        if p == "Mars":
            aspects.extend([(pos + 3 - 1) % 12 + 1, (pos + 7 - 1) % 12 + 1])
        elif p == "Jupiter":
            aspects.extend([(pos + 4 - 1) % 12 + 1, (pos + 8 - 1) % 12 + 1])
        elif p == "Saturn":
            aspects.extend([(pos + 2 - 1) % 12 + 1, (pos + 9 - 1) % 12 + 1])
        elif p in ("Rahu", "Ketu"):
            aspects.extend([(pos + 4 - 1) % 12 + 1, (pos + 8 - 1) % 12 + 1])
        if target_house in aspects:
            aspecting.append(p)
    return aspecting


# ---------------------------------------------------------------------------
# NEECHA BHANGA RAJA YOGA EVALUATOR
# ---------------------------------------------------------------------------

def evaluate_neecha_bhanga(
    planet_signs: Dict[str, int],
    planet_houses: Dict[str, int]
) -> List[str]:
    """
    Evaluates Neecha Bhanga Raja Yoga (cancellation of debilitation).
    Checks from both Lagna and Chandra Lagna (Moon).
    """
    nbry_results = []
    moon_house = planet_houses.get("Moon")

    kendras_from_lagna = {1, 4, 7, 10}
    kendras_from_moon = set()
    if moon_house:
        kendras_from_moon = {((moon_house - 1 + k - 1) % 12) + 1 for k in (1, 4, 7, 10)}
    all_kendras = kendras_from_lagna.union(kendras_from_moon)

    for planet, deb_sign in DEBILITATION_SIGNS.items():
        # Check if the planet is in its debilitation sign
        if planet_signs.get(planet) != deb_sign:
            continue

        p_house = planet_houses.get(planet)
        dispositor = SIGN_LORDS.get(deb_sign)
        exalt_sign = EXALTATION_SIGNS.get(planet)
        exalt_lord = SIGN_LORDS.get(exalt_sign) if exalt_sign else None
        exalted_in_deb_sign = SIGN_EXALTED_PLANET.get(deb_sign)

        reasons = []

        # Condition 1: Dispositor of debilitated sign is in Kendra from Lagna or Moon
        if dispositor and planet_houses.get(dispositor) in all_kendras:
            reasons.append(f"Dispositor {dispositor} is in Kendra from Lagna/Moon")

        # Condition 2: Lord of planet's exaltation sign is in Kendra from Lagna or Moon
        if exalt_lord and planet_houses.get(exalt_lord) in all_kendras:
            reasons.append(f"Exaltation lord {exalt_lord} is in Kendra from Lagna/Moon")

        # Condition 3: Planet exalted in this sign is in Kendra from Lagna or Moon
        if exalted_in_deb_sign and planet_houses.get(exalted_in_deb_sign) in all_kendras:
            reasons.append(f"{exalted_in_deb_sign} (exalted in this sign) is in Kendra")

        # Condition 4: The debilitated planet itself is in Kendra from Lagna or Moon
        if p_house in all_kendras:
            reasons.append(f"{planet} is posited in Kendra")

        # Condition 5: Dispositor aspects the debilitated planet
        if p_house and dispositor:
            aspects_on_house = get_aspecting_planets(p_house, planet_houses)
            if dispositor in aspects_on_house:
                reasons.append(f"{planet} is aspected by its dispositor {dispositor}")

        if reasons:
            nbry_results.append(
                f"Neecha Bhanga Raja Yoga for {planet} ({', '.join(reasons)}): "
                "Transforms early challenges and setbacks into notable authority, perseverance, and long-term triumph."
            )

    return nbry_results


# ---------------------------------------------------------------------------
# FULL RULE ENGINE
# ---------------------------------------------------------------------------

def evaluate_chart_rules(data: ChartRequest) -> List[str]:
    lagna_sign = data.lagna_sign
    p_houses = data.planet_houses
    p_signs = data.planet_signs
    nav_signs = data.navamsa_planet_signs or {}
    combust = set(data.combust_planets or [])
    is_full_moon = data.is_full_moon

    lords = get_house_lords(lagna_sign)
    predictions = []

    l1, l2, l3, l4 = lords[1], lords[2], lords[3], lords[4]
    l5, l6, l7, l8 = lords[5], lords[6], lords[7], lords[8]
    l9, l10, l11, l12 = lords[9], lords[10], lords[11], lords[12]

    def in_same_house(*planets: str) -> bool:
        positions = [p_houses.get(p) for p in planets if p in p_houses]
        return len(positions) == len(planets) and len(set(positions)) == 1

    def has_sambandham(p1: str, p2: str) -> bool:
        if in_same_house(p1, p2):
            return True
        h1, h2 = p_houses.get(p1), p_houses.get(p2)
        if not h1 or not h2:
            return False
        return p2 in get_aspecting_planets(h1, p_houses) or p1 in get_aspecting_planets(h2, p_houses)

    def is_strong(p: str) -> bool:
        s = p_signs.get(p)
        return s == EXALTATION_SIGNS.get(p) or (s and SIGN_LORDS.get(s) == p)

    def is_debilitated(p: str) -> bool:
        return p_signs.get(p) == DEBILITATION_SIGNS.get(p)

    def is_dosha_rahitha(p: str) -> bool:
        h, s = p_houses.get(p), p_signs.get(p)
        if not h or not s or s == DEBILITATION_SIGNS.get(p):
            return False
        if any(p_houses.get(m) == h for m in MALEFICS if m != p):
            return False
        if any(m in get_aspecting_planets(h, p_houses) for m in MALEFICS if m != p):
            return False
        return True

    # --- 1. NEECHA BHANGA RAJA YOGA ---
    predictions.extend(evaluate_neecha_bhanga(p_signs, p_houses))

    # --- 2. PARIVARTHANA ---
    if check_parivarthana(1, 8, lords, p_houses):
        predictions.append("1st lord and 8th lord parivarthana unte svecha akkuva and akkuva niraasa ki guri avtharu")
    if check_parivarthana(1, 9, lords, p_houses):
        predictions.append("1st lord and 9th lord parivarthana unte peddalu ante gowravam akkuva; sampada poyi malla vachunu")
    if check_parivarthana(1, 10, lords, p_houses):
        predictions.append("1st lord and 10th lord parivarthana unte raajakiyalu pramukyatha kaligi untaru")
    if check_parivarthana(1, 12, lords, p_houses):
        predictions.append("1st lord and 12th lord parivarthana unte he will be illhealth")
    if check_parivarthana(1, 4, lords, p_houses):
        predictions.append("1st lord and 4th lord parivarthana, he will be sukhi")
    if check_parivarthana(11, 2, lords, p_houses):
        predictions.append("11th lord and 2nd lord parivarthana will give him dhana labham")
    if check_parivarthana(2, 10, lords, p_houses):
        predictions.append("2nd lord and 10th lord parivarthana will make the person do bussiness")

    # --- 3. HOUSE 1 / LAGNA ---
    if p_houses.get("Sun") == 1 and p_houses.get("Rahu") == 1:
        predictions.append("Lagnamu lo SUN & RAHU kalisina: Jathakuni thala chinnadi ganu, Dhanthalu peddavi")
    if p_houses.get("Mars") == 1 and p_houses.get("Rahu") == 1:
        predictions.append("If Mars and Rahu in 1st house: he is short fellow")
    if in_same_house(l1, l3, "Rahu"):
        predictions.append("1st lord 3rd lord and rahu together: he will be potti vadu; will give birth to twins")
    if in_same_house(l1, "Moon"):
        if is_full_moon:
            predictions.append("1st lord with full moon (sukla sasti nunchi bahula paksha dasami varaku): he will be sahana murthy")
        else:
            predictions.append("1st lord with worst moon: he will be kopisti")
    if p_houses.get("Jupiter") in (1, 6, 8, 12):
        predictions.append("Fat body -> Jupiter in 1st or 6th or 8th or in 12th House")
    if in_same_house(l1, "Mercury") and is_strong(l1):
        predictions.append("1st lord with mercury and is strong: he will be vidhvamsudu, ganithamu and sahithyam lo pravesham kala vaadu")
    if is_dosha_rahitha(l1) and p_houses.get(l1) in (1, 4, 5, 7, 9, 10, 11):
        predictions.append("Dosha rahithudu ayina 1st lord in kendra kona or 11th house: he will be dhana vanthudu, keethi manthudu, and deha soukyam untundi")
    if p_houses.get(l1) in (1, 4, 5, 7, 9, 10):
        predictions.append("1st lord in kendra/kona: he will be sukhi")
    if p_houses.get(l1) in (6, 8, 12) and any(p_houses.get(m) == p_houses.get(l1) for m in MALEFICS if m != l1):
        predictions.append("1st lord in 6/8/12 stanalalo with papulu: he is sukha heenudu")
    if any(p_houses.get(m) == 1 for m in MALEFICS):
        predictions.append("Lagnam papa grham tho kalisina: sukha heenudu")
    if in_same_house(l1, l7) and has_sambandham(l1, l4) and any(in_same_house(l4, m) for m in MALEFICS):
        predictions.append("1st lord and 7th lord together have papa sambhandham with 4th lord: illegal contact with menatha")

    # --- 4. HOUSE 2 ---
    predictions.append("From 2nd house We can say about dhanamu, Vidhya, Kutambamu, Right Eye")
    if in_same_house(l2, "Jupiter", l7) and p_houses.get(l2) in (3, 8, 12):
        predictions.append("If 2nd lord is with Jupiter and with 7th lord are in 3rd, 8th or in 12th: his spouse will be mooga or nathi")
    if in_same_house(l2, "Sun", "Venus"):
        predictions.append("If 2nd lord is with Sun and Venus: he will be blind")
    if in_same_house(l2, "Venus") and p_houses.get(l2) in (3, 6, 11, 12):
        predictions.append("If 2nd lord with Venus placed in 3rd, 6th, 11th or in 12th: he will be netra Vykahalyamu")
    if in_same_house(l2, "Venus", "Moon") and p_houses.get(l2) == 1:
        predictions.append("If 2nd lord with Venus & Moon is in 1st house: Night blindness")
    if in_same_house(l2, "Moon"):
        predictions.append("If 2nd lord is with Moon: he will have beautiful eyes")
    if any(in_same_house(l2, b) for b in ("Jupiter", "Venus", "Mercury")):
        predictions.append("If 2nd lord is with good planets: he will have wide eyes")
    if in_same_house(l2, l8) and p_houses.get(l2) == 11:
        predictions.append("If 2nd lord and 8th lord are in 11th house: his kutumbha vyrudhi")
    if p_signs.get(l2) == EXALTATION_SIGNS.get(l2) and "Jupiter" in get_aspecting_planets(p_houses.get(l2, 0), p_houses):
        predictions.append("If 2nd lord is in uchha and having jupiter's veekshana: dhana dhanya samrudhi kaligi kutumbha shanti untundi")
    if (in_same_house(l2, "Jupiter") or in_same_house(l2, "Moon")) and p_houses.get(l2) in (6, 7, 12) and is_debilitated(l2):
        predictions.append("2nd Lord Jupiter tho kani Moon tho kani kalisi 6th, 7th or 12th houses lo neechudai unte: mooga vadu avthadu")
    if p_houses.get(l2) == 1:
        predictions.append("if 2nd lord is in 1st house: then he will love family members")
    if p_houses.get("Mercury") == 2 and p_houses.get("Jupiter") == 2:
        predictions.append("In 2nd house Mercury + Jupiter: then he will learn journalism")
    if p_houses.get("Venus") == 2 and any(p_houses.get(b) == 3 for b in BENEFICS):
        predictions.append("In 2nd house Venus and in 3rd subhulu unte: Jyotishyam telisina vaadu")
    if l2 in ("Sun", "Mars") and (has_sambandham(l2, "Jupiter") or has_sambandham(l2, "Venus")):
        predictions.append("Sun/Mars as 2nd lord and having Jupiter, Venus sambhandham: then he will be a scientist")
    if p_houses.get("Venus") == 2 and (p_houses.get("Rahu") == 2 or p_houses.get("Ketu") == 2):
        predictions.append("Venus in 2nd house with Rahu/ketu: then he is bhasha pandithudu")
    if p_houses.get(l1) in (2, 10) and p_houses.get(l2) == 1:
        predictions.append("1st lord in 2nd or 10th house and 2nd lord in 1st house: then he is be happy after 20 years")
    if in_same_house(l2, l11) and p_houses.get(l2) == 4:
        predictions.append("If 2nd & 11th lords are in 4th house: he will have many lands")
    if p_houses.get(l4) == 2 and any(p_houses.get(m) == 2 for m in MALEFICS if m != l4):
        predictions.append("if 4th lord with paapulu in 2nd house: then bhoomi parula paalu avunu")
    if p_houses.get(l7) == 2 and any(p_houses.get(m) == 2 for m in MALEFICS if m != l7) and "Mars" in get_aspecting_planets(2, p_houses):
        predictions.append("7th lord paapulatho kalisi in 2nd house and watched by Mars: then wife will have pregency by someone else")
    if p_houses.get("Ketu") in (1, 2, 12):
        predictions.append("If ketu in 12, 1 or in 2: dhaiva bhakti undunu")
    if is_strong(l2) and is_strong("Jupiter") and is_strong("Mercury"):
        predictions.append("2nd house lord, jupiter, mercury bhala vanthulu ayina: jathakudu vidhya vanthudu avnu")
    if has_sambandham(l2, "Jupiter"):
        predictions.append("2nd lord if related to Jupiter: teacher or proffessor would be the job")
    if has_sambandham(l2, "Saturn"):
        predictions.append("2nd lord if related to saturn: he will be Murkudu")
    if has_sambandham(l2, "Venus"):
        predictions.append("2nd lord if related to venus: interested in sangitha sahithyam")

    # --- 5. HOUSE 3 ---
    if p_houses.get(l3) == 1 and in_same_house(l3, "Jupiter"):
        predictions.append("If 3rd house lord is with Jupiter and in 1st house: he will have fear of animals")
    if p_houses.get(l3) == 1:
        predictions.append("3rd lord in 1st house: he will get sibblings love")
    if in_same_house(l3, "Sun"):
        predictions.append("If 3rd lord is with Sun: he will be dhairya vanthudu")
    if in_same_house(l3, "Mercury"):
        predictions.append("If 3rd lord is with Mercury: he will be sathvikudu")
    if in_same_house(l3, "Saturn"):
        predictions.append("If 3rd lord is with Saturn: he will be Murkhudu")
    if in_same_house(l3, "Venus"):
        predictions.append("If 3rd lord is with Venus: he will be Kalahala priyudu, kaamukudu")
    if p_houses.get(l3) == 10 and in_same_house(l10, "Rahu") and p_houses.get(l10) == 1:
        predictions.append("If 3rd lord is in 10th house and 10th lord with rahu are in 1st house: problems with animals having poison in the tail")
    if in_same_house(l3, l8) and p_houses.get(l3) == 10:
        predictions.append("If 3rd lord and 8th lord are in 10th house: sibblings will be in good position")
    if p_houses.get(l3) in (1, 4, 7, 10) and p_houses.get("Venus") == 3 and in_same_house("Mars", "Saturn"):
        predictions.append("If 3rd lord is in kendram and venus in 3rd house and Mars is with Saturn: he will have only one son")
    if l3 in FEMALE_PLANETS and p_signs.get(l3) in FEMALE_SIGNS:
        predictions.append("If 3rd lord is female planet and in female rasi: then he will have sisters")
    if in_same_house(l3, "Mars") and p_houses.get(l3) == 8:
        if any(m in get_aspecting_planets(8, p_houses) for m in MALEFICS if m != "Mars"):
            predictions.append("If 3rd lord and Mars are in 8th house and being watched by paapa grahas: his siblings will have nasanam")
    h_l3, h_mars = p_houses.get(l3), p_houses.get("Mars")
    if h_l3 and h_mars and abs(h_l3 - h_mars) in (5, 7):
        predictions.append("If 3rd lord and Mars are in sastastakaalu: then sodhara naasanam")
    if p_houses.get("Moon") == 3 and any(mp in get_aspecting_planets(3, p_houses) for mp in MALE_PLANETS):
        predictions.append("Moon in 3rd house and being watched by male planet: then he will not have sibblings")
    if l1 in NATURAL_FRIENDS.get(l3, set()):
        predictions.append("If 3rd lord and lagna lord are friends: Sibblings will be good friends")
    if in_same_house(l9, l3):
        predictions.append("9th lord with 3rd lord: then he will get money from sibbillings")
    if p_houses.get(l1) == 3 and in_same_house(l9, l10, l5):
        h_grp = p_houses.get(l9)
        if in_same_house(l9, "Jupiter") or "Jupiter" in get_aspecting_planets(h_grp, p_houses):
            predictions.append("1st lord in 3rd house & 9th, 10th, 5th lords kalisi with Jupiter or with Jupiter's veekshana: will be dhatha")
    if p_houses.get("Saturn") == 3:
        predictions.append("Saturn in 3rd house: Less hunger for food")

    # --- 6. HOUSE 4 ---
    if p_houses.get("Saturn") == 4 and any(m in get_aspecting_planets(4, p_houses) for m in MALEFICS if m != "Saturn"):
        predictions.append("If Saturn is in 4th house and being watched by paapulu: thalli ki aapada")
    if p_houses.get(l4) in (6, 8, 12):
        predictions.append("if 4th lord is in 6th, 8th or in 12th then his dasa will kill mother; land will be spent by him (*selling)")
    if any(p_houses.get(m) == 4 for m in MALEFICS) and any(m in get_aspecting_planets(4, p_houses) for m in MALEFICS):
        predictions.append("Paapulu in 4th house and watched by paapulu: will have extramarital relationships")
    if p_houses.get(l7) == 4 and (p_houses.get("Venus") == 4 or any(p_houses.get(m) == 4 for m in MALEFICS if m != l7)):
        predictions.append("In 4th house if 7th lord and Venus / paapulu kalisi unte: he will have extra marital affair")
    if p_houses.get("Mercury") == 4 and p_houses.get("Venus") == 4:
        predictions.append("In 4th house Mercury + Venus: He will know Jyotishyam")
    if p_houses.get("Jupiter") == 4 and p_houses.get("Venus") == 4:
        predictions.append("Jupiter & Venus in 4th House: he will know Vedam and lalitha kalalu")
    if in_same_house(l4, "Jupiter"):
        predictions.append("if 4th lord and Jupiter meets: he will be vidhya adhikudu")
    if p_houses.get(l4) == 4 and any(b in get_aspecting_planets(4, p_houses) for b in BENEFICS):
        predictions.append("4th lord in 4th house and watched by subhulu: he is sukhi")
    if "Jupiter" in get_aspecting_planets(4, p_houses) or "Jupiter" in get_aspecting_planets(7, p_houses):
        predictions.append("if Jupiter watchs 4th or 7th: he is sukhi")
    if any(p_houses.get(m) == 4 for m in MALEFICS):
        predictions.append("papulu in 4th house: sukha heenudu")
    mars_sign = p_signs.get("Mars")
    mars_dispositor = SIGN_LORDS.get(mars_sign) if mars_sign else None
    if mars_dispositor and in_same_house(l4, mars_dispositor) and p_houses.get(l4) == 4:
        predictions.append("if 4th lord with Mars staying rasi's lord are in 4th house: he will have vishesha bhumi")
    if is_debilitated(l4):
        predictions.append("If 4th lord in neecha: he will loose land")
    if p_signs.get(l4) == EXALTATION_SIGNS.get(l4) and any(p_houses.get(m) == p_houses.get(l4) for m in MALEFICS if m != l4):
        predictions.append("if 4th lord in ucha and with papulu: he will sell land")
    if in_same_house(l4, "Sun", "Mars"):
        predictions.append("If 4th lord, Sun and Mars meet: he will have many borrowings (appula paalu)")

    # --- 7. HOUSE 5 ---
    if p_houses.get("Ketu") == 5 and has_sambandham("Ketu", "Sun"):
        predictions.append("In 5th house ketu and have Sun relation: he will know mathamatics")
    if p_houses.get(l5) == 9 and p_houses.get(l9) == 9:
        predictions.append("5th lord with 9th lord in 9th house: he will get money from Son")
    if l1 == "Jupiter" or l4 == "Jupiter" or l7 == "Jupiter" or l10 == "Jupiter":
        if p_houses.get("Jupiter") == 5:
            predictions.append("Jupiter being a kendra lord and in 5th house: he will get Army/Navy/Air force/Police jobs")
    if p_houses.get(l10) == 5 and "Mercury" in get_aspecting_planets(5, p_houses):
        predictions.append("10th lord in 5th house and watched by Mercury: he will have Theertha yatrala pai aasakthi")

    # --- 8. HOUSE 6 ---
    if p_houses.get(l6) == 1:
        predictions.append("6th lord in 1st house: he will have ill health, wins over enemies and be greater to Father (thandri kanna goppa vadu)")
    if in_same_house(l6, "Sun"):
        predictions.append("If 6th lord and Sun meets: he will have fever mostly")
    if in_same_house(l6, l8, "Moon"):
        predictions.append("If 6th & 8th lords with Moon: he will have jala gandam")
    if in_same_house(l6, l8, "Mars"):
        predictions.append("If 6th & 8th lords with Mars: he will have Chicken pox or small pox")
    if in_same_house(l6, l8, "Mercury"):
        predictions.append("If 6th & 8th lords with Mercury: he will have manosanchalyam")
    if in_same_house(l6, l8, "Jupiter"):
        predictions.append("If 6th & 8th lords with Jupiter: he will have paithyam (Kapam)")
    if in_same_house(l6, l8, "Venus"):
        predictions.append("If 6th & 8th lords with Venus: he will have STDs' or problem with wife")
    if in_same_house(l6, l8) and (p_houses.get("Rahu") == p_houses.get(l6) or p_houses.get("Ketu") == p_houses.get(l6)):
        predictions.append("If 6th & 8th lords with Rahu/Ketu: he will have dieseases related to mind")
    if p_houses.get("Saturn") == 6:
        predictions.append("Saturn in 6th house: more hunger for food")

    # --- 9. HOUSE 7 & SPOUSE ---
    if l7 == "Mars" and p_houses.get("Mars") == 6:
        predictions.append("If 7th lord is Mars and is in 6th house: bharya dhaya lenidi")
    if p_houses.get(l7) == 1:
        predictions.append("7th lord in 1st makes him get a wife who lisens to him")
    if p_houses.get("Moon") == 7 and any(p_houses.get(m) == 7 for m in MALEFICS):
        predictions.append("if Moon with paapulu in 7th house: his mother will expire")
    moon_pos = p_houses.get("Moon")
    if moon_pos:
        h7_from_moon = ((moon_pos - 1 + 6) % 12) + 1
        if p_houses.get("Saturn") == h7_from_moon and p_houses.get("Mars") == h7_from_moon:
            predictions.append("Chandra lagna tho if Saturn and Mars in 7th house: thalli maraninchunu")
    if p_houses.get("Saturn") == 7 and any(b in get_aspecting_planets(7, p_houses) for b in BENEFICS):
        predictions.append("If Saturn in 7th house and watched by subha planets: wife is guna vanthu raalu")
    if l7 == "Mercury" and p_houses.get("Mercury") == 12:
        predictions.append("If 7th lord is Mercury and in 12th house: Jathakudu wife ni bhadhinchunu")
    if l7 == "Venus" and is_debilitated("Venus") and not any(b in get_aspecting_planets(p_houses.get("Venus", 0), p_houses) for b in BENEFICS):
        predictions.append("If 7th lord is Venus and in neecha without subha planets watching: he will be ready to kill his wife")
    sign_7 = ((lagna_sign - 1 + 6) % 12) + 1
    nav_7 = nav_signs.get("7th_house")
    if sign_7 == 4 or nav_7 == 4:
        predictions.append("If 7th house is Karkatakam or Chandra navamsa: bhartha vudrekamu, kopamu, sunithamaina manasu kala vaadu")
    elif sign_7 == 5 or nav_7 == 5:
        predictions.append("If 7th house is Simhamu or Ravi navamsa: bhartha kasta padi swabhavi ayyi kopamu kala vaadu")
    elif sign_7 in (9, 12) or nav_7 in (9, 12):
        predictions.append("If 7th house is Dhanasu or Meenamu or Guru navamsa: bhartha guna vanthudu, athma nigrahamu kala vaadu")
    sun_h = p_houses.get("Sun")
    moon_h = p_houses.get("Moon")
    sun_jup = "Jupiter" in get_aspecting_planets(sun_h, p_houses) if sun_h else False
    moon_jup = "Jupiter" in get_aspecting_planets(moon_h, p_houses) if moon_h else False
    if not sun_jup or not moon_jup:
        predictions.append("If Sun or Moon doesn't have Jupiter veekshana: wife will have pregency by someone else")
    if in_same_house("Saturn", "Moon"):
        predictions.append("Saturn+Moon: will give nathi and also will get a chamathkari ayina mosa gallu spouse vastaru")
    if sun_h:
        s_aspects = get_aspecting_planets(sun_h, p_houses)
        if "Mars" in s_aspects or "Saturn" in s_aspects or in_same_house("Sun", "Mars") or in_same_house("Sun", "Saturn"):
            predictions.append("If sun is visited by Mars or Saturn: that female will get married to elder person")
    sat_h = p_houses.get("Saturn")
    if sat_h:
        sat_aspects = get_aspecting_planets(sat_h, p_houses)
        if "Sun" in sat_aspects or in_same_house("Saturn", "Sun"):
            predictions.append("If saturn is visited by Sun: that female will get married to a person which is second marriage to him")
    nav_sat = nav_signs.get("Saturn")
    nav_ven = nav_signs.get("Venus")
    if (nav_sat in (2, 7)) or (nav_ven in (10, 11)):
        predictions.append("In navamsa if Saturn is in Venus house or Venus in Saturn's house: that female would be a prostitute")

    # --- 10. HOUSE 8 ---
    if p_houses.get("Sun") == 8 and (p_houses.get("Rahu") == 8 or p_houses.get("Ketu") == 8):
        predictions.append("In 8th house, if Sun is with Rahu or Ketu: he will be humiliated (avamanam jarugunu)")
    if p_houses.get(l8) == 1:
        predictions.append("8th lord in 1st house: he will work only according to his thoughts. Life span will be less than 32 years.")
    if p_houses.get("Jupiter") == 3 and p_houses.get("Sun") == 8 and p_houses.get("Saturn") == 9:
        predictions.append("If Jupiter is in 3rd house, Sun in 8th house and Saturn in 9th house: his arms will be cut (Narakabadunu)")

    # --- 11. HOUSE 9 ---
    if p_houses.get(l9) == 1:
        predictions.append("9th lord in 1st house: thoughts will be respected by father; gets money from father")
    if p_houses.get(l9) in (1, 4, 7, 10):
        predictions.append("9th lord in kendra: he is sukhi")
    if p_signs.get(l9) == EXALTATION_SIGNS.get(l9) and any(b in get_aspecting_planets(p_houses.get(l9, 0), p_houses) for b in BENEFICS):
        predictions.append("9th lord in ucha and watched by subha grahas: he will be dhatha")

    # --- 12. HOUSE 10 ---
    if p_houses.get(l10) == 1:
        predictions.append("10th lord in 1st house: he will get money and respect")
    if p_houses.get(l10) == 10:
        predictions.append("10th lord in 10th house: he will do bussiness")
    if l1 in NATURAL_FRIENDS.get(l10, set()):
        predictions.append("If 1st and 10th lords are friends: he will get land")
    if p_houses.get("Rahu") == 10 or p_houses.get("Mercury") == 10 or p_houses.get("Saturn") == 10:
        predictions.append("If Rahu/Mercury/Saturn are in 10th house: his feet will be damaged")
    if p_houses.get("Mercury") == 10 or p_houses.get("Mars") == 10 or "Mercury" in get_aspecting_planets(10, p_houses) or "Mars" in get_aspecting_planets(10, p_houses):
        predictions.append("Mercury or Mars relation with 10th house: will make the guy work with agriculture related jobs")
    if p_houses.get("Sun") == 10 and p_houses.get("Mars") == 10 and p_houses.get(l10) in (1, 4, 7, 10):
        predictions.append("Sun & Mars in 10th house and 10th lord in kendram: will make the person do a job related to lawyer")
    if p_houses.get("Mercury") == 10:
        predictions.append("Mercury in 10th house: will make him kala kaarudu or a bussiness man")
    if p_houses.get("Sun") == 10 or p_houses.get("Moon") == 10 or p_houses.get("Ketu") == 10:
        predictions.append("Sun/Moon/Ketu in 10th house: he will have Theertha yatrala pai aasakthi")
    if p_houses.get(l10) in (1, 4, 5, 7, 9, 10):
        predictions.append("10th lord in Kendra or kona: Kula dharma parayanulu cheyunu")

    # --- 13. HOUSE 11 ---
    if p_houses.get(l11) == 1:
        predictions.append("11th lord in 1st house: sibbilings will lisen to each other and earn good money")
    h11_sign = ((lagna_sign - 1 + 10) % 12) + 1
    if h11_sign in (1, 8) and p_houses.get("Sun") == 11 and p_houses.get("Mars") == 11 and "Rahu" in get_aspecting_planets(11, p_houses):
        predictions.append("Meshamu gani Vrushikam gani 11th house ayyi with Sun, Mars watched by Rahu: mother is prostitute")
    if l11 == "Mercury" and is_strong("Mercury") and p_houses.get("Mercury") == 11:
        predictions.append("11th lord being Mercury and strong, placed in 11th house: he will do business and earns lot of profits")
    if l11 in ("Jupiter", "Venus") and is_strong(l11) and p_houses.get(l11) == 11:
        predictions.append("Strong Jupiter or Venus being 11th lord and placed in 11th house: he will get Jewellery")
    if p_houses.get("Jupiter") == 11 and is_strong("Jupiter"):
        predictions.append("In 11th house strong Jupiter: money from Bhodhanala valana, Pourahityam leda Karmala valana")
    if p_houses.get("Venus") == 11 and is_strong("Venus"):
        predictions.append("In 11th house if Venus is strong: labham from kalalu")
    if p_houses.get("Saturn") == 11 and is_strong("Saturn"):
        predictions.append("Saturn strong in 11th house: money from Farming or from Business")
    if p_houses.get(l11) == 9 and p_houses.get(l9) in (1, 4, 7, 10):
        predictions.append("11th lord in 9th house & 9th lord in Kendramu: Dhana labhamu")
    if p_houses.get(l1) == 11 and p_houses.get("Mercury") == 11:
        predictions.append("In 11th house, 1st lord and Mercury: Vidhya labham")
    planets_in_11 = [p for p, pos in p_houses.items() if pos == 11]
    if planets_in_11 == ["Venus"]:
        predictions.append("Venus in 11th house alone is bad and any other planet is good")
    h3_sign = ((lagna_sign - 1 + 2) % 12) + 1
    if h11_sign in CHARA_SIGNS and h3_sign in STHIRA_SIGNS and any(p_houses.get(p) == 3 for p in p_houses):
        predictions.append("11th house chara raasi and 3rd house has sthira planet: Dhana Nastamu")
    if is_debilitated(l11) or (l11 in combust) or any(p_houses.get(m) == p_houses.get(l11) for m in MALEFICS if m != l11):
        predictions.append("11th lord balaheenudu / hasthanguthudaina / with papa graham: Vinikidi Sakthi thakkuva (diminished hearing)")
     # --- 13. HOUSE 11 (Continuation & Completion) ---
    h11_sign = ((lagna_sign - 1 + 10) % 12) + 1
    h3_sign = ((lagna_sign - 1 + 2) % 12) + 1
    if h11_sign in CHARA_SIGNS and h3_sign in STHIRA_SIGNS and any(p_houses.get(p) == 3 for p in p_houses):
        predictions.append("11th house in Chara Rasi and 3rd house in Sthira Rasi with planets in 3rd: gains through travel and communication")

    # --- 14. HOUSE 12 ---
    if p_houses.get(l12) == 1:
        predictions.append("12th lord in 1st house: he will have high expenses and sleep disturbances")
    if p_houses.get("Saturn") == 12:
        predictions.append("Saturn in 12th house: spiritual inclination, foreign travels, or secret enemies")
    if p_houses.get(l12) in (6, 8, 12):
        predictions.append("12th lord in dusthana (6/8/12): Vipareeta Raja Yoga potential or financial fluctuations")

    return predictions


# ---------------------------------------------------------------------------
# API ENDPOINT
# ---------------------------------------------------------------------------

@app.post("/evaluate", response_model=List[str])
def evaluate_astrology_chart(data: ChartRequest):
    """
    API endpoint to evaluate a natal chart and return astrological predictions.
    """
    try:
        results = evaluate_chart_rules(data)
        return results
    except Exception as e:
        return [f"Error evaluating chart: {str(e)}"]