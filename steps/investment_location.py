
import random
import string

# ======================================================
# ADDRESS DETAILS
# ======================================================

def random_land_number():
    return f"{random.randint(100, 9999)}{random.choice(['', '-A', '-B', 'E', 'W'])}"


def random_house_number():
    suffix = random.choice(["", "A", "B", "-1", "-2", "/1", "/2"])
    return f"No.{random.randint(1, 999)}{suffix}"


def random_building_number():
    return random.choice(["", f"B{random.randint(1, 50)}", f"F{random.randint(1, 20)}"])
    

def random_street_km():
    return random.choice([
        "ផ្លូវជាតិលេខ៤", "ផ្លូវជាតិលេខ៥", "ផ្លូវជាតិលេខ៦",
        "ផ្លូវ ២៧១", "ផ្លូវ ៣៧០", "ផ្លូវ ៥៩៨", "ផ្លូវ ២០០៤",
        "មហាវិថី ព្រះមុនីវង្ស", "មហាវិថី សម្តេចតេជោ", "ផ្លូវ វេង ស្រេង",
    ])


def random_street_en():
    return random.choice([
        "National Road No.4", "National Road No.5", "National Road No.6",
        "Street 271", "Street 598", "Street 2004", "Veng Sreng Blvd",
        "Monivong Blvd", "Russian Blvd", "Sihanouk Blvd", "Hanoi Road",
    ])


# ======================================================
# FIELD-LEVEL OVERRIDE (Hook for generic_value_resolver)
# ======================================================

def field_override(code):


    if code == "investment_location_land_number":
        return random_land_number()

    if code == "investment_location_house_number":
        return random_house_number()

    if code == "investment_location_building_number":
        return random_building_number()

    if code == "investment_location_street_number":
        return random_street_km()

    if code == "investment_location_street_number_en":
        return random_street_en()

    return None
