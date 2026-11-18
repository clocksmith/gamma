"""Independent authored development phrases, never a confirmation generator."""
import random
POOLS = [
 ["a ripe peach from the orchard", "fresh raspberries in a bowl", "a bunch of sweet grapes", "a peeled tangerine ready to eat", "a sliced melon on a plate"],
 ["a diesel bus at the station", "a bicycle chained to a rail", "a taxi waiting at the curb", "a passenger tram approaching", "a delivery van on the street"],
 ["a sleepy kitten on a blanket", "a brown horse in the paddock", "a rabbit eating green leaves", "a puppy playing with a ball", "a sheep grazing in the meadow"],
 ["a violin resting in its case", "a trumpet beside sheet music", "a piano in the concert room", "a flute played in rehearsal", "a cello in the orchestra"],
]
def build_development_tasks(seed=23017, queries_per_specialty=2):
    if seed != 23017 or queries_per_specialty != 2:
        raise ValueError("Fixed development design only")
    rng = random.Random(seed)
    tasks=[]
    for domain in range(6):
        multi = domain >= 3
        base = ["red-7", "blue-8", "green-9", "gold-6"] if multi else ["copper","violet","cedar","pearl"]
        header=f"Sorting station {domain}: infer the category-to-code rule from the examples. Return only its code.\n"
        for specialty in range(2):
            codes=base[specialty:]+base[:specialty]
            lines=[f"Item: {phrase} => {codes[c]}\n" for c,pool in enumerate(POOLS) for phrase in pool[:3]]
            rng.shuffle(lines)
            support=header+"".join(lines)
            for qi in range(2):
                c=(domain+specialty*2+qi)%4
                query=f"Item: {POOLS[c][3+specialty]} =>"
                tasks.append(dict(task_id=len(tasks),domain=f"development_sort_{domain}",
                  specialty_id=f"dev_{domain}_{specialty}",wrong_specialty_id=f"dev_{domain}_{1-specialty}",
                  header_text=header,support_text=support,query_line=query,
                  bare_prompt=header+query,prompt=support+query,expected=codes[c],max_new_tokens=8,
                  regex_lookup={}))
    return tasks
