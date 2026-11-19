"""B1 v5 task generator: sort an item into one of four groups and return that group's arbitrary code.

Two disjoint splits. `dev` uses eight item groups; `confirm` uses 37 different groups, so no
confirmation noun, group or table is ever seen in development. Confirmation tables follow a block
design in which any two tables share at most one group (see `confirm_design`); development tables
sample four of the eight development groups at random, unchanged. Codes are arbitrary words (or
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
        # Added 2026-11-19, before any confirmation task was generated: 29 more groups, so that the 37
        # confirmation groups carry the table design below. No noun here is a development noun.
        "fish": ["salmon", "trout", "cod", "tuna", "herring", "mackerel", "sardine", "anchovy", "carp", "pike",
                 "perch", "catfish", "eel", "haddock", "halibut", "sole", "flounder", "swordfish", "barracuda",
                 "piranha", "bream", "minnow", "sturgeon", "tilapia", "snapper", "grouper", "marlin", "guppy"],
        "reptile": ["lizard", "gecko", "iguana", "chameleon", "crocodile", "alligator", "tortoise", "turtle",
                    "cobra", "python", "viper", "rattlesnake", "anaconda", "boa", "skink", "horned lizard",
                    "komodo dragon", "terrapin", "caiman", "gila monster", "adder", "mamba", "garter snake",
                    "copperhead", "sidewinder", "tuatara", "gharial", "bearded dragon"],
        "tree": ["oak", "maple", "birch", "pine", "spruce", "cedar", "willow", "elm", "beech", "poplar",
                 "sycamore", "redwood", "sequoia", "cypress", "juniper", "larch", "hemlock", "baobab",
                 "eucalyptus", "mahogany", "teak", "hawthorn", "alder", "yew", "fir", "aspen", "linden",
                 "acacia"],
        "gem": ["diamond", "ruby", "emerald", "sapphire", "topaz", "opal", "amethyst", "garnet", "jade",
                "turquoise", "pearl", "onyx", "agate", "quartz", "aquamarine", "tourmaline", "peridot",
                "citrine", "moonstone", "lapis lazuli", "obsidian", "amber", "jasper", "zircon", "malachite",
                "beryl", "carnelian", "spinel"],
        "metal": ["gallium", "copper", "zinc", "nickel", "rhodium", "lead", "aluminum", "titanium", "tungsten",
                  "platinum", "silver", "mercury", "cobalt", "chromium", "magnesium", "lithium", "sodium",
                  "potassium", "calcium", "uranium", "bronze", "brass", "steel", "pewter", "palladium",
                  "manganese", "bismuth", "iridium"],
        "weather": ["thunderstorm", "blizzard", "hurricane", "tornado", "drizzle", "hailstorm", "fog", "mist",
                    "sleet", "snowfall", "heatwave", "monsoon", "typhoon", "cyclone", "frost", "rainbow",
                    "lightning", "downpour", "gale", "breeze", "drought", "sandstorm", "whirlwind", "dew",
                    "cloudburst", "squall", "cold snap", "flurry"],
        "body_part": ["elbow", "knee", "ankle", "wrist", "shoulder", "thumb", "eyebrow", "eyelash", "nostril",
                      "forehead", "chin", "cheek", "jaw", "tongue", "throat", "spine", "rib", "hip", "thigh",
                      "shin", "heel", "toe", "palm", "knuckle", "earlobe", "collarbone", "kneecap", "forearm"],
        "dance": ["waltz", "tango", "salsa", "samba", "rumba", "foxtrot", "polka", "ballet", "flamenco", "jive",
                  "mambo", "bachata", "quickstep", "bolero", "mazurka", "minuet", "tap dance", "breakdance",
                  "line dance", "square dance", "hula", "limbo", "swing dance", "lindy hop", "charleston",
                  "fandango", "tarantella", "paso doble"],
        "landform": ["mountain", "valley", "canyon", "plateau", "glacier", "volcano", "desert", "peninsula",
                     "island", "cliff", "ridge", "gorge", "ravine", "dune", "prairie", "tundra", "savanna",
                     "marsh", "swamp", "butte", "fjord", "isthmus", "archipelago", "mesa", "foothill", "crater",
                     "cavern", "atoll"],
        "fabric": ["cotton", "wool", "silk", "linen", "denim", "velvet", "satin", "corduroy", "tweed", "flannel",
                   "nylon", "polyester", "cashmere", "chiffon", "lace", "burlap", "canvas", "felt", "fleece",
                   "suede", "leather", "muslin", "taffeta", "gingham", "jersey", "twill", "hessian", "organza"],
        "spice": ["cinnamon", "nutmeg", "paprika", "turmeric", "cumin", "coriander", "cardamom", "saffron",
                  "oregano", "basil", "thyme", "rosemary", "parsley", "dill", "sage", "tarragon", "cloves",
                  "caraway", "vanilla", "fennel", "mustard", "chili powder", "sumac", "marjoram", "chives",
                  "mint", "anise", "allspice"],
        "dessert": ["cheesecake", "brownie", "cupcake", "pudding", "custard", "tiramisu", "macaron", "eclair",
                    "doughnut", "muffin", "pancake", "waffle", "trifle", "sorbet", "gelato", "meringue", "fudge",
                    "truffle", "tart", "strudel", "cobbler", "shortbread", "biscotti", "flan", "mousse",
                    "baklava", "profiterole", "cannoli"],
        "grain": ["wheat", "barley", "oats", "rye", "rice", "corn", "millet", "sorghum", "quinoa", "buckwheat",
                  "spelt", "amaranth", "bulgur", "couscous", "semolina", "farro", "teff", "wild rice",
                  "cornmeal", "bran", "polenta", "grits", "muesli", "granola", "porridge", "oatmeal", "tapioca",
                  "sago"],
        "nut": ["almond", "walnut", "cashew", "pecan", "hazelnut", "pistachio", "peanut", "chestnut",
                "macadamia", "brazil nut", "acorn", "sesame seed", "chia seed", "flaxseed", "hemp seed",
                "beechnut", "kola nut", "candlenut", "hickory nut", "butternut", "ginkgo nut", "lotus seed",
                "filbert", "cobnut", "betel nut", "shea nut", "pili nut", "soy nut"],
        "shape": ["circle", "triangle", "rectangle", "pentagon", "hexagon", "octagon", "oval", "rhombus",
                  "trapezoid", "cube", "sphere", "cylinder", "cone", "pyramid", "prism", "ellipse", "crescent",
                  "spiral", "parallelogram", "heptagon", "decagon", "torus", "tetrahedron", "semicircle",
                  "polygon", "hemisphere", "cuboid", "nonagon"],
        "celestial": ["planet", "comet", "asteroid", "meteor", "galaxy", "nebula", "quasar", "pulsar",
                      "supernova", "moon", "star", "sun", "constellation", "satellite", "meteorite", "exoplanet",
                      "neutron star", "star cluster", "solar flare", "eclipse", "aurora", "dwarf planet",
                      "gas giant", "binary star", "protostar", "magnetar", "cosmic ray", "wormhole"],
        "toy": ["doll", "rag doll", "kite", "puzzle", "marble", "rattle", "spinning top", "finger puppet",
                "building blocks", "skipping rope", "flying disc", "toy drum", "toy boat", "jigsaw",
                "toy soldier", "bubble wand", "pinwheel", "kaleidoscope", "snow globe", "music box",
                "play dough", "dollhouse", "action figure", "stuffed animal", "bouncy ball", "toy robot",
                "paper plane", "balloon"],
        "stationery": ["pencil", "eraser", "stapler", "notebook", "envelope", "paperclip", "highlighter",
                       "ruler", "protractor", "compass", "marker", "crayon", "binder", "folder", "sticky note",
                       "fountain pen", "ballpoint pen", "sharpener", "glue", "scissors", "hole punch",
                       "clipboard", "notepad", "index card", "rubber band", "thumbtack", "correction fluid",
                       "ink cartridge"],
        "device": ["laptop", "tablet", "smartphone", "television", "radio", "router", "printer", "scanner",
                   "headphones", "microphone", "loudspeaker", "webcam", "projector", "calculator", "smartwatch",
                   "game console", "modem", "hard drive", "flash drive", "power bank", "remote control",
                   "thermostat", "digital camera", "camcorder", "turntable", "walkie talkie", "photocopier",
                   "intercom"],
        "jewelry": ["necklace", "bracelet", "earring", "brooch", "pendant", "anklet", "tiara", "cufflink",
                    "locket", "bangle", "choker", "signet ring", "wedding ring", "nose stud", "charm bracelet",
                    "tie clip", "hairpin", "crown", "medallion", "amulet", "eternity ring", "wristwatch",
                    "pocket watch", "stickpin", "hatpin", "armlet", "diadem", "cameo"],
        "subject": ["algebra", "geometry", "chemistry", "physics", "biology", "history", "geography",
                    "literature", "grammar", "calculus", "astronomy", "economics", "philosophy", "civics",
                    "statistics", "trigonometry", "botany", "zoology", "geology", "anatomy", "psychology",
                    "sociology", "linguistics", "ecology", "genetics", "archaeology", "theology", "rhetoric"],
        "container": ["bucket", "barrel", "crate", "jar", "bottle", "basket", "suitcase", "backpack",
                      "briefcase", "carton", "sack", "pouch", "urn", "vase", "flask", "canister", "hamper",
                      "satchel", "tote bag", "lunchbox", "toolbox", "jerrycan", "thermos", "keg", "cask", "vat",
                      "duffel bag", "pillbox"],
        "currency": ["dollar", "euro", "pound sterling", "yen", "rupee", "peso", "franc", "krona", "ruble",
                     "dinar", "shekel", "rand", "baht", "lira", "zloty", "ringgit", "dirham", "forint", "rupiah",
                     "shilling", "kwacha", "guilder", "drachma", "florin", "doubloon", "ducat", "peseta",
                     "escudo"],
        "game": ["chess", "checkers", "backgammon", "dominoes", "poker", "solitaire", "bingo", "charades",
                 "hopscotch", "ludo", "mahjong", "cribbage", "roulette", "snakes and ladders", "hide and seek",
                 "darts", "billiards", "snooker", "rummy", "canasta", "parcheesi", "crossword", "sudoku",
                 "tiddlywinks", "pinball", "foosball", "bagatelle", "jacks"],
        "medical": ["stethoscope", "thermometer", "syringe", "scalpel", "forceps", "bandage", "crutch",
                    "wheelchair", "stretcher", "defibrillator", "inhaler", "splint", "tourniquet", "catheter",
                    "otoscope", "pulse oximeter", "hearing aid", "pacemaker", "speculum", "tweezers", "gauze",
                    "plaster cast", "eye patch", "neck brace", "nebulizer", "heating pad", "ice pack",
                    "walking frame"],
        "shellfish": ["crab", "lobster", "shrimp", "prawn", "oyster", "clam", "mussel", "scallop", "squid",
                      "octopus", "cuttlefish", "jellyfish", "starfish", "urchin", "barnacle", "krill",
                      "crayfish", "limpet", "cockle", "whelk", "periwinkle", "abalone", "nautilus", "razor clam",
                      "conch", "cowrie", "hermit crab", "geoduck"],
        "bread": ["baguette", "croissant", "bagel", "pretzel", "sourdough", "ciabatta", "focaccia", "brioche",
                  "pita", "naan", "tortilla", "crumpet", "scone", "flatbread", "breadstick", "bun", "loaf",
                  "toast", "crouton", "pumpernickel", "challah", "matzo", "chapati", "bao", "garlic bread",
                  "panini", "rusk", "crispbread"],
        "room": ["kitchen", "bedroom", "bathroom", "attic", "basement", "hallway", "pantry", "cellar", "nursery",
                 "study", "lounge", "conservatory", "balcony", "porch", "veranda", "corridor", "foyer",
                 "laundry room", "living room", "guest room", "cloakroom", "scullery", "loft", "den",
                 "utility room", "playroom", "sunroom", "vestibule"],
        "water": ["river", "lake", "ocean", "sea", "pond", "stream", "creek", "lagoon", "bay", "gulf", "strait",
                  "estuary", "reservoir", "waterfall", "geyser", "cove", "canal", "harbor", "inlet",
                  "tributary", "rapids", "brook", "loch", "oasis", "whirlpool", "tide pool", "billabong",
                  "backwater"],
    },
}

# Confirmation tables are not drawn at random. With eight groups, any two tables shared about two groups, so
# tables were far from independent. The 37 confirmation groups carry a Steiner system S(2, 4, 37): 111 tables
# of four groups in which every pair of groups meets in exactly one table, so two tables share at most one
# group and each group sits in 12 tables. It is the cyclic design developed from these base blocks mod 37
# (every non-zero residue is the difference of exactly one pair in one block). `confirm_design` re-checks it.
CONFIRM_POINTS = 37
CONFIRM_BASE_BLOCKS = ((0, 1, 3, 24), (0, 4, 9, 15), (0, 7, 17, 25))
CONFIRM_MAX_TABLES = 111


def confirm_design(names: list[str], seed: int) -> list[list[str]]:
    """The 111 confirmation tables as lists of four group names, in a seeded order.

    The seed decides which group takes which point of the design, the order of the tables, and the order
    of the four groups inside each table. It draws from its own generator, not from the task generator's.
    """
    if len(names) != CONFIRM_POINTS:
        raise ValueError(f"the confirmation design needs {CONFIRM_POINTS} groups; got {len(names)}")
    blocks = [tuple(sorted((p + shift) % CONFIRM_POINTS for p in base))
              for base in CONFIRM_BASE_BLOCKS for shift in range(CONFIRM_POINTS)]
    pairs = [(a, b) for block in blocks for i, a in enumerate(block) for b in block[i + 1:]]
    if len(blocks) != CONFIRM_MAX_TABLES or len(set(pairs)) != len(pairs) \
            or len(pairs) != CONFIRM_POINTS * (CONFIRM_POINTS - 1) // 2:
        raise AssertionError("confirmation design broken: some pair of groups does not meet exactly once")
    rng = random.Random(f"b1-v5-confirm-design:{seed}")
    order = sorted(names)
    rng.shuffle(order)
    rng.shuffle(blocks)
    return [[order[p] for p in rng.sample(block, 4)] for block in blocks]

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
    design = None
    if split == "confirm":
        if specialties > CONFIRM_MAX_TABLES:
            raise ValueError(f"the confirmation design has {CONFIRM_MAX_TABLES} tables; asked for {specialties}")
        design = confirm_design(names, seed)
    tasks: list[dict] = []
    for s in range(specialties):
        multi = s >= specialties - n_multi
        # Development tables sample four of the eight development groups, exactly as before.
        chosen = design[s] if design is not None else rng.sample(names, 4)
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
