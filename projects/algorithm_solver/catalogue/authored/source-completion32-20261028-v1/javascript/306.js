// 306 — Additive Number. Original implementation; authored candidate, not independently qualified.
function solve(num) {
  for (let a = 1; a < num.length - 1; a++) {
    if (a > 1 && num[0] === '0') break;
    for (let b = a + 1; b < num.length; b++) {
      if (b - a > 1 && num[a] === '0') break;
      let x = BigInt(num.slice(0, a)), y = BigInt(num.slice(a, b)), pos = b;
      while (pos < num.length) {
        const z = x + y, token = String(z);
        if (!num.startsWith(token, pos)) break;
        pos += token.length; x = y; y = z;
      }
      if (pos === num.length) return true;
    }
  }
  return false;
}

module.exports = { solve, isAdditiveNumber: solve };
