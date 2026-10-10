export function seedToUint32(value) {
  let hash = 2166136261;
  for (const character of String(value)) {
    hash ^= character.codePointAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

export function createRng(seed) {
  let value = seedToUint32(seed);
  return () => {
    value += 0x6d2b79f5;
    let mixed = value;
    mixed = Math.imul(mixed ^ (mixed >>> 15), mixed | 1);
    mixed ^= mixed + Math.imul(mixed ^ (mixed >>> 7), mixed | 61);
    return ((mixed ^ (mixed >>> 14)) >>> 0) / 4294967296;
  };
}

export function shuffle(values, rng) {
  const copy = [...values];
  for (let index = copy.length - 1; index > 0; index -= 1) {
    const target = Math.floor(rng() * (index + 1));
    [copy[index], copy[target]] = [copy[target], copy[index]];
  }
  return copy;
}

export function generateBoard(config) {
  if (config.board.layout !== "shared-action-areas" || config.board.tiles.length !== 6) throw new Error("Six shared action areas are required.");
  return config.board.tiles.map((area, index) => ({...structuredClone(area), instanceId: area.id, order:index}));
}
export function resolveTieByInitiative(seats, order, index=0) {
  for(let n=0;n<order.length;n++){const seat=order[(index+n)%order.length];if(seats.includes(seat))return seat;}
  return null;
}
export function buildTrainingDeck(config, seed) {
  const cards = config.trainingDeck.cards.flatMap((entry) =>
    Array.from({ length: entry.count }, (_, index) => ({
      id: `${entry.id}-${index + 1}`,
      type: entry.id,
      kind: entry.kind
    }))
  );
  return shuffle(cards, createRng(seed));
}

export const TRAINING_DOMAINS = Object.freeze([
  "code",
  "science",
  "web",
  "books",
  "images",
  "video",
  "synthetic"
]);

function firstMissingDomain(seen) {
  return TRAINING_DOMAINS.find((domain) => !seen.has(domain));
}

export function simulateTrainingRun(config, seed, options={}) {
  const seen=new Set(), revealed=[], permanentEffects=[];let capability=0,reputation=0,runwaySpent=0,outcome="banked";
  for(const card of options.deck || buildTrainingDeck(config,seed)) {
    revealed.push(card.type);let duplicate=false;
    if(card.kind==="domain"){duplicate=seen.has(card.type);if(!duplicate){seen.add(card.type);capability++;}}
    else if(card.type==="curated_corpus"){const domain=firstMissingDomain(seen);if(domain){seen.add(domain);capability++;}else duplicate=true;}
    else if(card.type==="benchmark_leak"){capability+=2;reputation--;permanentEffects.push({type:"reputation",amount:-1});}
    else if(card.type==="human_evaluation"){reputation++;permanentEffects.push({type:"reputation",amount:1});outcome="human-evaluation";break;}
    if(duplicate){if(options.scientificMethod&&(options.runway??1)>=1){runwaySpent=1;outcome="scientific-method-banked";}else{capability=Math.min(capability,options.crashRetain||0);outcome="crashed";}break;}
    if(capability>=(options.stopAt||3))break;
  }
  return {seed:String(seed),outcome,capability,reputation,runwaySpent,permanentEffects,ordinaryDomains:[...seen],ordinaryDomainCount:seen.size,distinctDomains:seen.size,revealed,cardsDrawn:revealed.length};
}
export function availableHeadlines(document,round){return document.headlines.filter(card=>card.round===round);}
