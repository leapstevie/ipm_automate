import random
_PRODUCTS = [
    ("T-shirts & Polo Shirts",              "610910"),
    ("Sneakers & Sports Shoes",             "640319"),
    ("Jasmine Rice (Hom Mali)",             "100630"),
    ("Natural Rubber Latex",                "400110"),
    ("Cashew Nuts (Processed)",             "080132"),
    ("Bicycles (Complete)",                 "871200"),
    ("Travel Bags & Backpacks",             "420292"),
    ("Plastic Packaging Bags",              "392321"),
    ("Wooden Furniture Sets",               "940360"),
    ("Solar Panels 540W",                   "854143"),
    ("Frozen Shrimp (Vannamei)",            "030617"),
    ("Black Pepper Whole",                  "090411"),
    ("Ceramic Floor Tiles",                 "690721"),
    ("LED Bulbs 9-15W",                     "853950"),
    ("Pharmaceutical Tablets",             "300490"),
]

def field_override(code):
    name, hs_base = random.choice(_PRODUCTS)

    if code == "product_output_name":
        return name

    if code == "product_output_hs_code":
     
        return hs_base + f"{random.randint(10, 99):02d}"

    if code == "product_output_note":
        return random.choice([
            "Main export product",
            "High demand in EU & USA",
            "100% Cambodian origin",
            "GSP/EBA eligible",
            "Organic certified",
            "Eco-friendly production",
        ])
        

    return None
