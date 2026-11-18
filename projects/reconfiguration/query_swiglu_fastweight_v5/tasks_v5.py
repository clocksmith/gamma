"""B1 v5 task generator: sort an item into one of four groups and return that group's arbitrary code.

Two disjoint splits. `dev` uses eight item groups; `confirm` uses eight different groups, so no
confirmation noun, group or table is ever seen in development. Codes are arbitrary words (or
word-digit pairs) with no relation to the groups, so the mapping exists only in the support table.

Each "specialty" is one support table (four groups, one code each, `shots` examples per group)
plus `queries` unseen items per group. Query nouns never appear in that table.
"""
from __future__ import annotations

import json
import random
import sys

GROUPS: dict[str, dict[str, list[str]]] = {
    "dev": {
        "fruit": ["apple", "banana", "mango", "peach", "plum", "cherry", "grape", "lemon", "lime", "pear",
                  "apricot", "papaya", "melon", "kiwi", "fig", "orange", "raspberry", "strawberry",
                  "blueberry", "pineapple", "coconut", "nectarine", "tangerine", "pomegranate",
                  "guava", "lychee", "cranberry", "grapefruit"],
        "vehicle": ["bus", "truck", "taxi", "tram", "van", "scooter", "bicycle", "motorcycle", "tractor",
                    "ambulance", "limousine", "minivan", "jeep", "sedan", "trolley", "ferry", "canoe",
                    "kayak", "yacht", "helicopter", "airplane", "glider", "locomotive", "bulldozer",
                    "forklift", "snowmobile", "rickshaw", "hovercraft"],
        "mammal": ["horse", "rabbit", "sheep", "goat", "donkey", "camel", "tiger", "lion", "leopard", "wolf",
                   "fox", "bear", "otter", "beaver", "squirrel", "hamster", "hedgehog", "giraffe", "zebra",
                   "elephant", "kangaroo", "koala", "monkey", "gorilla", "moose", "bison", "raccoon",
                   "badger"],
        "instrument": ["violin", "cello", "trumpet", "flute", "piano", "guitar", "banjo", "harp", "clarinet",
                       "oboe", "trombone", "tuba", "saxophone", "accordion", "harmonica", "mandolin",
                       "ukulele", "xylophone", "tambourine", "bassoon", "viola", "piccolo", "organ",
                       "bagpipes", "sitar", "lute", "cymbals", "bongos"],
        "tool": ["hammer", "wrench", "screwdriver", "pliers", "chisel", "handsaw", "drill", "crowbar", "mallet",
                 "trowel", "shovel", "rake", "hoe", "pickaxe", "hatchet", "sander", "clamp", "vise",
                 "soldering iron", "tape measure", "spirit level", "paintbrush", "putty knife", "hacksaw",
                 "ratchet", "wire cutters", "staple gun", "sledgehammer"],
        "clothing": ["shirt", "sweater", "jacket", "raincoat", "scarf", "glove", "sock", "skirt", "blouse",
                     "trousers", "jeans", "shorts", "cardigan", "hoodie", "waistcoat", "necktie", "apron",
                     "pajamas", "swimsuit", "overcoat", "tunic", "poncho", "kimono", "beanie", "mitten",
                     "legging", "dungarees", "blazer"],
        "furniture": ["sofa", "armchair", "bookshelf", "wardrobe", "dresser", "nightstand", "footstool",
                      "bench", "cabinet", "cupboard", "bunk bed", "crib", "desk", "dining table", "recliner",
                      "hammock", "coffee table", "sideboard", "chest of drawers", "rocking chair", "futon",
                      "barstool", "headboard", "mattress", "shoe rack", "coat stand", "ottoman", "bureau"],
        "kitchenware": ["saucepan", "skillet", "ladle", "whisk", "spatula", "colander", "teapot", "kettle",
                        "grater", "cutting board", "rolling pin", "measuring cup", "casserole dish", "wok",
                        "corkscrew", "can opener", "peeler", "strainer", "mixing bowl", "baking tray",
                        "soup spoon", "butter knife", "salad tongs", "pepper mill", "cake tin", "funnel",
                        "sieve", "teaspoon"],
    },
    "confirm": {
        "bird": ["sparrow", "robin", "eagle", "falcon", "owl", "heron", "pelican", "penguin", "parrot",
                 "pigeon", "swan", "goose", "duck", "crow", "raven", "magpie", "woodpecker", "kingfisher",
                 "flamingo", "ostrich", "seagull", "swallow", "finch", "canary", "vulture", "stork", "wren",
                 "hummingbird"],
        "vegetable": ["carrot", "potato", "onion", "cabbage", "spinach", "broccoli", "cauliflower", "celery",
                      "radish", "turnip", "leek", "zucchini", "eggplant", "cucumber", "lettuce", "kale",
                      "beetroot", "parsnip", "asparagus", "artichoke", "pumpkin", "okra", "shallot",
                      "sweet potato", "green bean", "bell pepper", "brussels sprout", "chard"],
        "sport": ["tennis", "soccer", "rugby", "cricket", "hockey", "baseball", "basketball", "volleyball",
                  "badminton", "golf", "fencing", "archery", "rowing", "sailing", "surfing", "skiing",
                  "snowboarding", "wrestling", "boxing", "judo", "karate", "gymnastics", "cycling",
                  "swimming", "diving", "handball", "squash", "curling"],
        "profession": ["plumber", "electrician", "carpenter", "nurse", "surgeon", "dentist", "lawyer",
                       "accountant", "architect", "librarian", "journalist", "pharmacist", "firefighter",
                       "bricklayer", "tailor", "barber", "translator", "surveyor", "midwife", "optician",
                       "locksmith", "baker", "butcher", "florist", "welder", "auditor", "paramedic",
                       "veterinarian"],
        "building": ["cathedral", "warehouse", "lighthouse", "barn", "castle", "cottage", "skyscraper",
                     "library", "hospital", "stadium", "factory", "windmill", "monastery", "bungalow",
                     "pavilion", "fortress", "chapel", "mansion", "garage", "greenhouse", "town hall",
                     "observatory", "courthouse", "boathouse", "farmhouse", "pagoda", "cabin", "silo"],
        "flower": ["tulip", "daffodil", "orchid", "lily", "sunflower", "daisy", "peony", "carnation",
                   "lavender", "poppy", "marigold", "hyacinth", "snowdrop", "bluebell", "geranium",
                   "petunia", "begonia", "chrysanthemum", "dahlia", "foxglove", "hibiscus", "magnolia",
                   "primrose", "buttercup", "crocus", "freesia", "pansy", "zinnia"],
        "insect": ["beetle", "ant", "wasp", "hornet", "butterfly", "moth", "dragonfly", "grasshopper",
                   "cricket insect", "ladybug", "mosquito", "termite", "cockroach", "firefly", "cicada",
                   "locust", "earwig", "weevil", "aphid", "mantis", "bumblebee", "housefly", "gnat", "flea",
                   "caterpillar", "stick insect", "horsefly", "silverfish"],
        "drink": ["coffee", "tea", "lemonade", "milkshake", "cider", "espresso", "smoothie", "cocoa",
                  "ginger ale", "tonic water", "iced tea", "cappuccino", "latte", "buttermilk", "kombucha",
                  "root beer", "soda water", "orange juice", "apple juice", "tomato juice", "hot chocolate",
                  "green tea", "sparkling water", "eggnog", "lassi", "horchata", "malted milk", "cordial"],
    },
}

TAILS = ["on the table", "in the photo", "near the door", "from the catalog", "in the box", "at the market",
         "by the window", "in the picture", "on the list", "in the corner", "on the shelf", "in the drawing"]

WORD_CODES = ["north", "south", "east", "west", "alpha", "beta", "gamma", "delta", "omega", "sigma", "kappa",
              "theta"]
PAIR_WORDS = ["red", "blue", "green", "gold", "gray", "pink", "black", "white"]


def build_tasks(seed: int, split: str, specialties: int = 8, shots: int = 3, queries: int = 2,
                multi_fraction: float = 0.5) -> list[dict]:
    """Return `specialties * 4 * queries` tasks. Half the tables use word-digit codes by default."""
    if split not in GROUPS:
        raise ValueError(f"unknown split {split!r}")
    if split == "confirm" and seed < 2_000_000:
        raise ValueError("confirmation seeds start at 2,000,000 so they cannot collide with development")
    if split == "dev" and seed >= 2_000_000:
        raise ValueError("development seeds must be below 2,000,000")
    rng = random.Random(seed)
    groups = GROUPS[split]
    names = sorted(groups)
    n_multi = round(specialties * multi_fraction)
    tasks: list[dict] = []
    for s in range(specialties):
        multi = s >= specialties - n_multi
        chosen = rng.sample(names, 4)
        if multi:
            words = rng.sample(PAIR_WORDS, 4)
            digits = rng.sample(range(1, 10), 4)
            codes = [f"{w}-{d}" for w, d in zip(words, digits)]
        else:
            codes = rng.sample(WORD_CODES, 4)
        header = f"Sorting desk {s + 1}: each item gets the code of its group. Return only the code.\n"
        pools = []
        for g in chosen:
            items = list(groups[g])
            rng.shuffle(items)
            if shots + queries > len(items):
                raise ValueError(f"group {g} has {len(items)} items; need {shots + queries}")
            pools.append((items[:shots], items[shots:shots + queries]))
        lines = [(f"Item: a {noun} {rng.choice(TAILS)} => {codes[c]}\n", c)
                 for c, (sup, _) in enumerate(pools) for noun in sup]
        rng.shuffle(lines)
        support_text = header + "".join(line for line, _ in lines)
        spec_id = f"{split}_{seed}_s{s}_{'pair' if multi else 'word'}"
        for qi in range(queries):
            for c, (_, qry) in enumerate(pools):
                query_line = f"Item: a {qry[qi]} {rng.choice(TAILS)} =>"
                tasks.append({
                    "task_id": len(tasks), "specialty_id": spec_id, "multi_token": multi,
                    "groups": chosen, "group": chosen[c], "codes": codes, "expected": codes[c],
                    "header_text": header, "support_text": support_text, "query_line": query_line,
                    "bare_prompt": header + query_line, "prompt": support_text + query_line,
                    "max_new_tokens": 8,
                })
    return tasks


if __name__ == "__main__":
    a = sys.argv[1:]
    print(json.dumps(build_tasks(int(a[0]), a[1], int(a[2]), int(a[3]), int(a[4]))))
