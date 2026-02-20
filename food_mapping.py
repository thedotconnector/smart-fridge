"""Food item mapping with emoji, categories, and fuzzy matching."""

FOOD_MAP = {
    # Dairy
    "milk": {"emoji": "\U0001F95B", "category": "Dairy", "aliases": ["whole milk", "semi-skimmed", "skimmed milk", "oat milk", "almond milk"]},
    "cheese": {"emoji": "\U0001F9C0", "category": "Dairy", "aliases": ["cheddar", "mozzarella", "parmesan", "brie", "gruyere", "gouda"]},
    "butter": {"emoji": "\U0001F9C8", "category": "Dairy", "aliases": ["unsalted butter", "salted butter", "lurpak"]},
    "yogurt": {"emoji": "\U0001F95B", "category": "Dairy", "aliases": ["yoghurt", "greek yogurt", "natural yogurt"]},
    "cream": {"emoji": "\U0001F95B", "category": "Dairy", "aliases": ["double cream", "single cream", "sour cream", "creme fraiche"]},
    "eggs": {"emoji": "\U0001F95A", "category": "Dairy", "aliases": ["egg", "free range eggs"]},

    # Meat
    "chicken": {"emoji": "\U0001F357", "category": "Meat", "aliases": ["chicken breast", "chicken thigh", "chicken drumstick", "roast chicken"]},
    "beef": {"emoji": "\U0001F969", "category": "Meat", "aliases": ["steak", "mince", "beef mince", "ground beef", "sirloin"]},
    "pork": {"emoji": "\U0001F969", "category": "Meat", "aliases": ["pork chops", "pork loin", "pork belly"]},
    "bacon": {"emoji": "\U0001F953", "category": "Meat", "aliases": ["streaky bacon", "back bacon", "smoked bacon"]},
    "sausages": {"emoji": "\U0001F32D", "category": "Meat", "aliases": ["sausage", "pork sausages", "chipolatas"]},
    "ham": {"emoji": "\U0001F969", "category": "Meat", "aliases": ["sliced ham", "cooked ham", "parma ham", "prosciutto"]},
    "salmon": {"emoji": "\U0001F41F", "category": "Meat", "aliases": ["salmon fillet", "smoked salmon"]},
    "prawns": {"emoji": "\U0001F990", "category": "Meat", "aliases": ["shrimp", "king prawns"]},

    # Produce
    "lettuce": {"emoji": "\U0001F96C", "category": "Produce", "aliases": ["salad", "romaine", "iceberg", "mixed leaves", "rocket"]},
    "tomatoes": {"emoji": "\U0001F345", "category": "Produce", "aliases": ["tomato", "cherry tomatoes", "vine tomatoes"]},
    "cucumber": {"emoji": "\U0001F952", "category": "Produce", "aliases": ["cucumbers"]},
    "carrots": {"emoji": "\U0001F955", "category": "Produce", "aliases": ["carrot"]},
    "peppers": {"emoji": "\U0001FAD1", "category": "Produce", "aliases": ["pepper", "bell pepper", "red pepper", "green pepper"]},
    "onions": {"emoji": "\U0001F9C5", "category": "Produce", "aliases": ["onion", "red onion", "spring onions"]},
    "mushrooms": {"emoji": "\U0001F344", "category": "Produce", "aliases": ["mushroom", "chestnut mushrooms"]},
    "broccoli": {"emoji": "\U0001F966", "category": "Produce", "aliases": []},
    "spinach": {"emoji": "\U0001F96C", "category": "Produce", "aliases": ["baby spinach"]},
    "avocado": {"emoji": "\U0001F951", "category": "Produce", "aliases": ["avocados"]},
    "lemons": {"emoji": "\U0001F34B", "category": "Produce", "aliases": ["lemon"]},
    "limes": {"emoji": "\U0001F34B", "category": "Produce", "aliases": ["lime"]},
    "garlic": {"emoji": "\U0001F9C4", "category": "Produce", "aliases": []},
    "ginger": {"emoji": "\U0001FAD0", "category": "Produce", "aliases": ["fresh ginger"]},
    "herbs": {"emoji": "\U0001F33F", "category": "Produce", "aliases": ["coriander", "parsley", "basil", "mint", "chives", "dill"]},
    "berries": {"emoji": "\U0001FAD0", "category": "Produce", "aliases": ["strawberries", "blueberries", "raspberries"]},
    "grapes": {"emoji": "\U0001F347", "category": "Produce", "aliases": ["grape"]},
    "apples": {"emoji": "\U0001F34E", "category": "Produce", "aliases": ["apple"]},

    # Beverages
    "juice": {"emoji": "\U0001F9C3", "category": "Beverages", "aliases": ["orange juice", "apple juice", "fruit juice"]},
    "beer": {"emoji": "\U0001F37A", "category": "Beverages", "aliases": ["lager", "ale", "ipa", "craft beer"]},
    "wine": {"emoji": "\U0001F377", "category": "Beverages", "aliases": ["white wine", "rose", "prosecco"]},
    "water": {"emoji": "\U0001F4A7", "category": "Beverages", "aliases": ["sparkling water", "mineral water"]},
    "soda": {"emoji": "\U0001F964", "category": "Beverages", "aliases": ["coke", "cola", "lemonade", "tonic water", "fizzy drink"]},

    # Condiments
    "ketchup": {"emoji": "\U0001F952", "category": "Condiments", "aliases": ["tomato ketchup", "tomato sauce"]},
    "mustard": {"emoji": "\U0001F952", "category": "Condiments", "aliases": ["dijon", "english mustard", "wholegrain mustard"]},
    "mayo": {"emoji": "\U0001F952", "category": "Condiments", "aliases": ["mayonnaise", "hellmanns"]},
    "hot sauce": {"emoji": "\U0001F336\uFE0F", "category": "Condiments", "aliases": ["sriracha", "tabasco", "chilli sauce"]},
    "soy sauce": {"emoji": "\U0001F952", "category": "Condiments", "aliases": []},
    "jam": {"emoji": "\U0001F353", "category": "Condiments", "aliases": ["strawberry jam", "marmalade", "preserve"]},
    "hummus": {"emoji": "\U0001F952", "category": "Condiments", "aliases": ["houmous"]},
    "pesto": {"emoji": "\U0001F33F", "category": "Condiments", "aliases": ["green pesto", "red pesto"]},
    "pickles": {"emoji": "\U0001F952", "category": "Condiments", "aliases": ["gherkins", "pickle", "cornichons"]},
    "olives": {"emoji": "\U0001FAD2", "category": "Condiments", "aliases": ["olive", "black olives", "green olives"]},

    # Prepared
    "leftovers": {"emoji": "\U0001F372", "category": "Prepared", "aliases": ["leftover", "meal prep"]},
    "dip": {"emoji": "\U0001F958", "category": "Prepared", "aliases": ["tzatziki", "guacamole", "salsa"]},
    "soup": {"emoji": "\U0001F372", "category": "Prepared", "aliases": ["fresh soup"]},
    "pasta": {"emoji": "\U0001F35D", "category": "Prepared", "aliases": ["fresh pasta", "tortellini", "ravioli"]},
    "tofu": {"emoji": "\U0001F9C6", "category": "Prepared", "aliases": []},
}

# Build reverse alias lookup
_ALIAS_MAP = {}
for food_name, info in FOOD_MAP.items():
    for alias in info["aliases"]:
        _ALIAS_MAP[alias.lower()] = food_name


def resolve_food(name):
    """Resolve a food name to its FOOD_MAP entry using fuzzy matching.

    Tries: exact match -> alias match -> substring match.
    Returns (canonical_name, info_dict) or (original_name, default_info).
    """
    lower = name.lower().strip()

    # Exact match
    if lower in FOOD_MAP:
        return lower, FOOD_MAP[lower]

    # Alias match
    if lower in _ALIAS_MAP:
        canonical = _ALIAS_MAP[lower]
        return canonical, FOOD_MAP[canonical]

    # Substring match — check if any key or alias is contained in the name
    for food_name, info in FOOD_MAP.items():
        if food_name in lower:
            return food_name, info
        for alias in info["aliases"]:
            if alias.lower() in lower:
                return food_name, info

    # Reverse substring — check if the name is contained in any key
    for food_name, info in FOOD_MAP.items():
        if lower in food_name:
            return food_name, info

    # No match — return with generic emoji
    return name.lower(), {"emoji": "\U0001F37D\uFE0F", "category": "Other", "aliases": []}
