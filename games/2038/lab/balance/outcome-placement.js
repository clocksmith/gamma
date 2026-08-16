const TIEBREAK_FIELDS = ["score", "trust", "customers", "compute"];

function compareMerit(left, right) {
  for (const field of TIEBREAK_FIELDS) {
    const difference = Number(left?.[field] || 0) - Number(right?.[field] || 0);
    if (difference !== 0) return Math.sign(difference);
  }
  return 0;
}

function winnerSet(outcome) {
  return new Set(outcome?.winnerSeats || []);
}

export function outcomePlacementPoint(outcome, left, right) {
  const winners = winnerSet(outcome);
  const leftWon = winners.has(left.seat);
  const rightWon = winners.has(right.seat);
  if (leftWon !== rightWon) return Number(leftWon);
  if (leftWon) return 0.5;
  const comparison = compareMerit(left, right);
  return comparison === 0 ? 0.5 : Number(comparison > 0);
}

export function outcomeRanks(outcome) {
  const winners = winnerSet(outcome);
  const ordered = [...(outcome?.standings || [])].sort((left, right) => {
    const leftWon = winners.has(left.seat);
    const rightWon = winners.has(right.seat);
    if (leftWon !== rightWon) return leftWon ? -1 : 1;
    const merit = compareMerit(left, right);
    return merit === 0 ? left.seat - right.seat : -merit;
  });
  const ranks = new Map();
  let prior = null;
  let priorRank = 0;
  for (const [index, standing] of ordered.entries()) {
    const tiedWithPrior = prior && (
      (winners.has(standing.seat) && winners.has(prior.seat)) ||
      (!winners.has(standing.seat) &&
        !winners.has(prior.seat) &&
        compareMerit(standing, prior) === 0)
    );
    const rank = tiedWithPrior ? priorRank : index + 1;
    ranks.set(standing.seat, rank);
    prior = standing;
    priorRank = rank;
  }
  return ranks;
}
